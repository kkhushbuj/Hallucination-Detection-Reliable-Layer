from models.llm_providers import call_model
from core.nli import cluster_answers, calculate_consistency_score, get_per_answer_consistency
import config


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


def verify_answer(question: str, answer: str, provider: str, model: str) -> bool:
    """Ask one model to judge whether an answer is correct or hallucinated."""
    prompt = (
        f"Question: {question}\n\n"
        f"Proposed answer: {answer}\n\n"
        "Based on your own knowledge, is this answer factually correct and not "
        "hallucinated? Respond with exactly one word: CORRECT or HALLUCINATED."
    )
    response_text = call_model(provider=provider, model=model, question=prompt, temperature=0)
    return "CORRECT" in response_text.upper()


def judge_one_answer(question: str, answer: str) -> list[dict]:
    """Ask all 3 judge models to verify one specific answer."""
    results = []
    for judge in config.VOTING_MODELS:
        try:
            correct = verify_answer(question, answer, judge["provider"], judge["model"])
            results.append({"provider": judge["provider"], "correct": correct, "failed": False})
        except Exception as e:
            results.append({"provider": judge["provider"], "correct": None, "failed": True, "error": str(e)})
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

    if final_score >= config.HIGH_CONFIDENCE_THRESHOLD:
        label = "High confidence — likely reliable"
    elif final_score >= config.MEDIUM_CONFIDENCE_THRESHOLD:
        label = "Medium confidence — verify independently"
    else:
        label = "Low confidence — likely unreliable, treat with caution"

    correct_judges = sum(1 for j in winner["judges"] if j["correct"])
    total_judges = sum(1 for j in winner["judges"] if not j["failed"])
    reasoning = (
        f"{correct_judges}/{total_judges} independent models confirmed this answer as correct. "
        f"It agreed with {round(winner['consistency_fraction'] * 100)}% of the other generated answers."
    )
    if winner["any_hallucinated"]:
        reasoning += " Note: at least one model flagged possible hallucination for this answer."
    if failed_generations:
        reasoning += f" Note: {len(failed_generations)} of {len(config.TEMPERATURES)} answer attempts failed to generate."

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
    }