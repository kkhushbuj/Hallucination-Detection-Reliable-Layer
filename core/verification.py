from concurrent.futures import ThreadPoolExecutor, as_completed
from models.llm_providers import call_model
from core.nli import cluster_answers, calculate_consistency_score, get_per_answer_consistency
import config


def generate_temperature_answers(question: str):
    """Generate answers at different temperatures in parallel."""
    answers = [None] * len(config.TEMPERATURES)
    failed = []

    def gen(idx, temp):
        return idx, call_model(
            provider=config.CONSISTENCY_MODEL["provider"],
            model=config.CONSISTENCY_MODEL["model"],
            question=question,
            temperature=temp,
        )

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(gen, i, t): i for i, t in enumerate(config.TEMPERATURES)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                i, answer = future.result()
                answers[i] = answer
            except Exception as e:
                failed.append({"temperature": config.TEMPERATURES[idx], "error": str(e)})

    answers = [a for a in answers if a is not None]
    return answers, failed


def verify_answer(question: str, answer: str, provider: str, model: str) -> bool:
    prompt = (
        f"Question: {question}\n\n"
        f"Proposed answer: {answer}\n\n"
        "Based on your own knowledge, is this answer factually correct and not "
        "hallucinated? Respond with exactly one word: CORRECT or HALLUCINATED."
    )
    response_text = call_model(provider=provider, model=model, question=prompt, temperature=0)
    return "CORRECT" in response_text.upper()


def judge_one_answer(question: str, answer: str) -> list[dict]:
    """Ask all 3 judge models in parallel."""
    results = [None] * len(config.VOTING_MODELS)

    def judge(idx, j):
        correct = verify_answer(question, answer, j["provider"], j["model"])
        return idx, {"provider": j["provider"], "correct": correct, "failed": False}

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(judge, i, j): i for i, j in enumerate(config.VOTING_MODELS)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                i, result = future.result()
                results[i] = result
            except Exception as e:
                results[idx] = {"provider": config.VOTING_MODELS[idx]["provider"], "correct": None, "failed": True, "error": str(e)}

    return results


def calculate_answer_score(judge_results: list[dict], consistency_fraction: float) -> dict:
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

    # Judge all answers in parallel
    def judge_answer(idx, answer):
        judge_results = judge_one_answer(question, answer)
        consistency_fraction = get_per_answer_consistency(clusters, idx, len(answers))
        scoring = calculate_answer_score(judge_results, consistency_fraction)
        return idx, {
            "answer": answer,
            "judges": judge_results,
            "consistency_fraction": consistency_fraction,
            "score": scoring["score"],
            "any_hallucinated": scoring["any_hallucinated"],
        }

    per_answer = [None] * len(answers)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(judge_answer, i, a): i for i, a in enumerate(answers)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                i, result = future.result()
                per_answer[i] = result
            except Exception:
                per_answer[idx] = {
                    "answer": answers[idx],
                    "judges": [{"provider": j["provider"], "correct": None, "failed": True} for j in config.VOTING_MODELS],
                    "consistency_fraction": 0,
                    "score": 0,
                    "any_hallucinated": False,
                }

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
