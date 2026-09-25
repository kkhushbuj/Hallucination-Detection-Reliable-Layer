import time
from models.llm_providers import call_model
from core.nli import cluster_answers, calculate_consistency_score, get_per_answer_consistency
from core.search import search_web
import config

RATE_LIMIT_MARKERS = ("429", "rate limit", "usage limit", "quota")


def _is_rate_limit_error(error: Exception) -> bool:
    text = str(error).lower()
    return any(marker in text for marker in RATE_LIMIT_MARKERS)

# Tracks how many tie-breaker calls have been made, since they share Groq's daily quota
# with the rest of the judge panel. Reset per evaluation run so usage stays visible.
tie_breaker_call_count = 0


def reset_tie_breaker_call_count():
    global tie_breaker_call_count
    tie_breaker_call_count = 0


def get_tie_breaker_call_count() -> int:
    return tie_breaker_call_count


def generate_temperature_answers(question: str):
    """Generate answers at different temperatures. Returns (successful answers, failed attempts)."""
    answers = []
    failed = []
    for temp in config.TEMPERATURES:
        try:
            answer = call_model(
                provider=config.CONSISTENCY_MODEL["provider"],
                model=config.CONSISTENCY_MODEL["model"],
                question=question,
                temperature=temp,
            )
            answers.append(answer)
        except Exception as e:
            failed.append({"temperature": temp, "error": str(e)})
    return answers, failed


def verify_answer(question: str, answer: str, provider: str, model: str, search_context: str | None = None, max_retries: int = 4) -> bool:
    """Ask one model to judge whether an answer is correct or hallucinated. Retries with backoff on a rate-limit error."""
    prompt = (
        f"Question: {question}\n\n"
        f"Proposed answer: {answer}\n\n"
    )
    if search_context:
        prompt += f"Web search context:\n{search_context}\n\n"
    prompt += (
        "Based on your own knowledge"
        + (" and the web search context above" if search_context else "")
        + ", is this answer factually correct and not "
        "hallucinated? Respond with exactly one word: CORRECT or HALLUCINATED."
    )

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response_text = call_model(provider=provider, model=model, question=prompt, temperature=0)
            return "CORRECT" in response_text.upper()
        except Exception as e:
            last_error = e
            if attempt < max_retries and _is_rate_limit_error(e):
                time.sleep(3 * (2 ** (attempt - 1)))  # 3s, 6s, 12s - only worth retrying a rate limit, not a hard failure
                continue
            raise last_error


def judge_one_answer(question: str, answer: str) -> list[dict]:
    """Ask all 3 judge models to verify one specific answer, grounded with a web search when enabled."""
    search_context = None
    search_used = False
    if config.USE_WEB_SEARCH:
        try:
            search_context = search_web(f"{question} {answer}")
            search_used = True
        except Exception:
            search_context = None
            search_used = False

    results = []
    for judge in config.VOTING_MODELS:
        try:
            correct = verify_answer(question, answer, judge["provider"], judge["model"], search_context=search_context)
            results.append({"provider": judge["provider"], "correct": correct, "failed": False, "search_used": search_used})
        except Exception as e:
            results.append({"provider": judge["provider"], "correct": None, "failed": True, "error": str(e), "search_used": search_used})
    return results


def calculate_answer_score(judge_results: list[dict], consistency_fraction: float) -> dict:
    """Weighted score: each responding judge + consistency each get an equal share, summing to 100%."""
    responding_judges = [j for j in judge_results if not j["failed"]]
    num_items = len(responding_judges) + 1
    weight_per_item = 1 / num_items if num_items > 0 else 0

    score = 0.0
    any_hallucinated = False

    for j in responding_judges:
        if j["correct"]:
            score += weight_per_item
        else:
            any_hallucinated = True

    score += consistency_fraction * weight_per_item

    return {"score": score, "any_hallucinated": any_hallucinated}


def tie_breaker_check(question: str, winning_answer: str) -> dict:
    """Ask GPT-OSS-20B (via Groq) for a single correct/hallucinated verdict on only the winning answer."""
    global tie_breaker_call_count
    prompt = (
        f"Question: {question}\n\n"
        f"Proposed answer: {winning_answer}\n\n"
        "Based on your own knowledge, is this answer factually correct and not "
        "hallucinated? Respond with exactly one word: CORRECT or HALLUCINATED."
    )
    tie_breaker_call_count += 1
    try:
        response_text = call_model(
            provider=config.TIE_BREAKER_MODEL["provider"],
            model=config.TIE_BREAKER_MODEL["model"],
            question=prompt,
            temperature=0,
        )
        return {"correct": "CORRECT" in response_text.upper(), "failed": False}
    except Exception as e:
        return {"correct": None, "failed": True, "error": str(e)}


def run_verification_check(question: str) -> dict:
    """Full pipeline: generate temp-answers, judge each, score with equal weighting, pick winner."""
    answers, failed_generations = generate_temperature_answers(question)

    if len(answers) == 0:
        return {
            "answers": [],
            "per_answer": [],
            "overall_consistency": 0,
            "winner_answer": "Unable to generate an answer right now — all attempts failed. Please try again.",
            "trust_score": 0,
            "label": "Error — no models responded",
            "reasoning": f"All {len(config.TEMPERATURES)} answer-generation attempts failed.",
            "failed_generations": failed_generations,
        }

    clusters = cluster_answers(answers)
    overall_consistency = calculate_consistency_score(clusters, len(answers))

    per_answer = []
    for idx, answer in enumerate(answers):
        judge_results = judge_one_answer(question, answer)
        consistency_fraction = get_per_answer_consistency(clusters, idx, len(answers))
        scoring = calculate_answer_score(judge_results, consistency_fraction)

        per_answer.append({
            "answer": answer,
            "judges": judge_results,
            "consistency_fraction": consistency_fraction,
            "score": scoring["score"],
            "any_hallucinated": scoring["any_hallucinated"],
        })

    winner_index = max(range(len(per_answer)), key=lambda i: per_answer[i]["score"])
    winner = per_answer[winner_index]
    final_score = winner["score"]

    correct_judges = sum(1 for j in winner["judges"] if j["correct"])
    total_judges = sum(1 for j in winner["judges"] if not j["failed"])
    panel_majority_correct = correct_judges > total_judges / 2 if total_judges > 0 else True

    tie_breaker = None
    if config.USE_TIE_BREAKER:
        tie_breaker = tie_breaker_check(question, winner["answer"])
        if not tie_breaker["failed"] and tie_breaker["correct"] != panel_majority_correct:
            final_score = max(0.0, final_score - config.TIE_BREAKER_PENALTY / 100)

    if final_score >= config.HIGH_CONFIDENCE_THRESHOLD:
        label = "High confidence — likely reliable"
    elif final_score >= config.MEDIUM_CONFIDENCE_THRESHOLD:
        label = "Medium confidence — verify independently"
    else:
        label = "Low confidence — likely unreliable, treat with caution"

    reasoning = (
        f"{correct_judges}/{total_judges} independent models confirmed this answer as correct. "
        f"It agreed with {round(winner['consistency_fraction'] * 100)}% of the other generated answers."
    )
    if winner["any_hallucinated"]:
        reasoning += " Note: at least one model flagged possible hallucination for this answer."
    if failed_generations:
        reasoning += f" Note: {len(failed_generations)} of {len(config.TEMPERATURES)} answer attempts failed to generate."

    tie_breaker_disagreed = bool(
        tie_breaker and not tie_breaker["failed"] and tie_breaker["correct"] != panel_majority_correct
    )
    if tie_breaker_disagreed:
        reasoning += (
            " Note: an independent high-capability check disagreed with this result — "
            "treat with extra caution."
        )

    return {
        "answers": answers,
        "per_answer": per_answer,
        "overall_consistency": round(overall_consistency * 100, 1),
        "winner_index": winner_index,
        "winner_answer": winner["answer"],
        "trust_score": round(final_score * 100, 1),
        "label": label,
        "reasoning": reasoning,
        "failed_generations": failed_generations,
        "tie_breaker": tie_breaker,
        "tie_breaker_disagreed": tie_breaker_disagreed,
    }