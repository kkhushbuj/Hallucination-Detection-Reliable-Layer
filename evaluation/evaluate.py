import sys
import os
import csv
import json
import time
import random
import argparse
import requests
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from graph import build_graph
from models.llm_providers import call_model
from core.verification import reset_tie_breaker_call_count, get_tie_breaker_call_count
import config

BATCH_SIZE = 50
NUM_BATCHES = 4
FIELDNAMES = ["question", "source", "model_answer", "best_answer", "trust_score", "label", "flagged_count", "majority_flagged", "correct"]

# Models used to independently check correctness against the benchmark answer. A majority
# vote (2-of-3) is taken as the final label, and 2-1 splits are tracked as a disagreement.
GROUND_TRUTH_CHECKERS = [
    {"provider": "groq", "model": "qwen/qwen3.8-27b"},
    {"provider": "gemini", "model": "gemini-3.5-flash"},
    {"provider": "mistral", "model": "mistral-small-latest"},
]

# Running counts of how often the 3 correctness-checkers disagreed (2-1 split), reset per run.
checker_disagreement_count = 0
checker_total_count = 0


def load_truthfulqa(path="evaluation/datasets/truthfulqa_full.csv", n=67, seed=42):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "question": row["Question"],
                "best_answer": row["Best Answer"],
                "source": "TruthfulQA",
            })
    random.seed(seed)
    return random.sample(rows, min(n, len(rows)))


def load_halueval(path="evaluation/datasets/halueval_qa.json", n=67, seed=42):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            rows.append({
                "question": item["question"],
                "best_answer": item["right_answer"],
                "source": "HaluEval",
            })
    random.seed(seed)
    return random.sample(rows, min(n, len(rows)))


def load_triviaqa(n=66, seed=42, max_retries=4, cache_path="evaluation/datasets/triviaqa_cache.json"):
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            rows = json.load(f)
    else:
        url = "https://datasets-server.huggingface.co/rows"
        params = {
            "dataset": "mandarjoshi/trivia_qa",
            "config": "rc.nocontext",
            "split": "validation",
            "offset": 0,
            "length": min(n * 3, 100),
        }

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                break
            except (requests.exceptions.RequestException, ValueError) as e:
                last_error = e
                wait = 2 ** attempt  # 2s, 4s, 8s, 16s
                print(f"  TriviaQA fetch attempt {attempt}/{max_retries} failed ({e}); retrying in {wait}s...")
                time.sleep(wait)
        else:
            raise RuntimeError(f"Failed to fetch TriviaQA data after {max_retries} attempts") from last_error

        rows = []
        for item in data.get("rows", []):
            row = item["row"]
            question = row.get("question")
            answer = row.get("answer", {}).get("value")
            if question and answer:
                rows.append({
                    "question": question,
                    "best_answer": answer,
                    "source": "TriviaQA",
                })

        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(rows, f)

    random.seed(seed)
    return random.sample(rows, min(n, len(rows)))


def load_combined_dataset(total=200, seed=42):
    """Deterministic full 200-question set (same seed -> same 200, same order, every run)."""
    per_source = total // 3
    truthfulqa = load_truthfulqa(n=per_source, seed=seed)
    halueval = load_halueval(n=per_source, seed=seed)
    triviaqa = load_triviaqa(n=total - len(truthfulqa) - len(halueval), seed=seed)

    combined = truthfulqa + halueval + triviaqa
    random.seed(seed)
    random.shuffle(combined)
    return combined


def get_batch(batch_num: int, batch_size: int = BATCH_SIZE):
    """Slice out one 50-question batch (1-indexed) from the full deterministic 200-question set."""
    dataset = load_combined_dataset(total=200)
    start = (batch_num - 1) * batch_size
    end = start + batch_size
    return dataset[start:end], start


def _check_correctness_once(question: str, model_answer: str, best_answer: str, provider: str, model: str, max_retries: int = 3) -> bool:
    """Ask one checker model for a YES/NO correctness verdict, with retry/backoff."""
    prompt = (
        f"Question: {question}\n\n"
        f"Expected correct answer: {best_answer}\n\n"
        f"Model's actual answer: {model_answer}\n\n"
        "Does the model's answer convey the same core truth/conclusion as the expected "
        "correct answer, even if worded very differently or with more detail? "
        "Ignore extra explanation, tone, or length. Focus only on whether the core "
        "factual conclusion matches.\n\n"
        "Respond with exactly one word: YES or NO."
    )

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response_text = call_model(provider=provider, model=model, question=prompt, temperature=0)
            return response_text.strip().upper().startswith("YES")
        except Exception as e:
            last_error = e
            wait = 2 ** attempt  # 2s, 4s, 8s
            print(f"    {provider} correctness-check attempt {attempt}/{max_retries} failed ({e}); retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"{provider} correctness-check failed after {max_retries} attempts") from last_error


def is_correct(question: str, model_answer: str, best_answer: str) -> bool:
    """Majority vote (2-of-3) across independent checker models. Tracks 2-1 disagreement splits."""
    global checker_disagreement_count, checker_total_count

    votes = []
    for checker in GROUND_TRUTH_CHECKERS:
        try:
            votes.append(_check_correctness_once(question, model_answer, best_answer, checker["provider"], checker["model"]))
        except Exception as e:
            print(f"    Checker {checker['provider']} gave up: {e}")

    if not votes:
        raise RuntimeError("All correctness-checker models failed")

    yes_votes = sum(votes)
    no_votes = len(votes) - yes_votes
    majority_correct = yes_votes > no_votes

    checker_total_count += 1
    if len(votes) == 3 and yes_votes in (1, 2):
        checker_disagreement_count += 1
        print(f"    Checkers split {yes_votes}-{no_votes} on this question.")

    return majority_correct


def run_evaluation(dataset, global_offset=0, total_overall=200):
    trust_graph = build_graph()

    print(f"Running {len(dataset)} questions (overall #{global_offset + 1}-{global_offset + len(dataset)} of {total_overall}).\n")

    reset_tie_breaker_call_count()
    results = []

    for i, row in enumerate(dataset, 1):
        question = row["question"]
        best_answer = row["best_answer"]
        source = row["source"]
        overall_i = global_offset + i

        print(f"[{i}/{len(dataset)}] (overall #{overall_i}/{total_overall}) ({source}) {question}")

        try:
            result = trust_graph.invoke({"question": question})
            verification = result["verification_result"]

            model_answer = verification["winner_answer"]
            trust_score = verification["trust_score"]
            label = verification["label"]

            per_answer = verification.get("per_answer", [])
            flagged_count = sum(1 for a in per_answer if a["any_hallucinated"])
            total_answers = len(per_answer)
            majority_flagged = flagged_count > total_answers / 2 if total_answers > 0 else False

            correct = is_correct(question, model_answer, best_answer)

            results.append({
                "question": question,
                "source": source,
                "model_answer": model_answer,
                "best_answer": best_answer,
                "trust_score": trust_score,
                "label": label,
                "flagged_count": f"{flagged_count}/{total_answers}",
                "majority_flagged": majority_flagged,
                "correct": correct,
            })

            print(f"  Trust Score: {trust_score}% | Correct: {correct} | Flagged: {flagged_count}/{total_answers}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "question": question,
                "source": source,
                "model_answer": None,
                "best_answer": best_answer,
                "trust_score": None,
                "label": None,
                "flagged_count": None,
                "majority_flagged": None,
                "correct": None,
            })

        time.sleep(1)

    if config.USE_TIE_BREAKER:
        print(f"\nTie-breaker (Llama 3.3 70B) calls used this run: {get_tie_breaker_call_count()}")

    return results


def save_csv(results, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            # CSV round-trips everything as strings - convert back to real types.
            row["trust_score"] = float(row["trust_score"]) if row["trust_score"] not in ("", None) else None
            row["correct"] = {"True": True, "False": False, "": None}.get(row["correct"], None)
            rows.append(row)
        return rows


def summarize(results, out_path="evaluation/results_final.csv", title="EVALUATION SUMMARY"):
    valid = [r for r in results if r["trust_score"] is not None]
    total = len(valid)

    if total == 0:
        print("No valid results to summarize.")
        return

    correct_results = [r for r in valid if r["correct"]]
    incorrect_results = [r for r in valid if not r["correct"]]

    overall_accuracy = len(correct_results) / total * 100
    avg_trust_correct = sum(r["trust_score"] for r in correct_results) / len(correct_results) if correct_results else 0
    avg_trust_incorrect = sum(r["trust_score"] for r in incorrect_results) / len(incorrect_results) if incorrect_results else 0

    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)
    print(f"Total questions evaluated: {total}")
    print(f"Model answer accuracy: {overall_accuracy:.1f}% ({len(correct_results)}/{total})")
    print(f"Average Trust Score on CORRECT answers: {avg_trust_correct:.1f}%")
    print(f"Average Trust Score on INCORRECT answers: {avg_trust_incorrect:.1f}%")
    print(f"Gap: {avg_trust_correct - avg_trust_incorrect:.1f} points")

    print("\nBreakdown by source:")
    for source in ["TruthfulQA", "HaluEval", "TriviaQA"]:
        source_results = [r for r in valid if r["source"] == source]
        if source_results:
            source_correct = [r for r in source_results if r["correct"]]
            acc = len(source_correct) / len(source_results) * 100
            print(f"  {source}: {acc:.1f}% accuracy ({len(source_correct)}/{len(source_results)})")

    if checker_total_count > 0:
        disagreement_rate = checker_disagreement_count / checker_total_count * 100
        print(
            f"\nGround-truth checker disagreement (2-1 splits): "
            f"{checker_disagreement_count}/{checker_total_count} ({disagreement_rate:.1f}%)"
        )

    save_csv(results, out_path)
    print(f"\nDetailed results saved to {out_path}")


def run_batch(batch_num: int):
    dataset, offset = get_batch(batch_num)
    print(f"=== Batch {batch_num}/{NUM_BATCHES} ({len(dataset)} questions) ===\n")
    results = run_evaluation(dataset, global_offset=offset, total_overall=200)
    out_path = f"evaluation/results_batch{batch_num}.csv"
    summarize(results, out_path=out_path, title=f"BATCH {batch_num} SUMMARY (questions {offset + 1}-{offset + len(dataset)})")


def evaluate_one(trust_graph, question, best_answer, source):
    """Run the full pipeline + correctness check for a single question. Raises on failure."""
    result = trust_graph.invoke({"question": question})
    verification = result["verification_result"]

    model_answer = verification["winner_answer"]
    per_answer = verification.get("per_answer", [])
    flagged_count = sum(1 for a in per_answer if a["any_hallucinated"])
    total_answers = len(per_answer)

    return {
        "question": question,
        "source": source,
        "model_answer": model_answer,
        "best_answer": best_answer,
        "trust_score": verification["trust_score"],
        "label": verification["label"],
        "flagged_count": f"{flagged_count}/{total_answers}",
        "majority_flagged": flagged_count > total_answers / 2 if total_answers > 0 else False,
        "correct": is_correct(question, model_answer, best_answer),
    }


def run_backfill():
    """Re-run only the failed (empty trust_score) rows across all batch CSVs, updating them in place."""
    trust_graph = build_graph()
    reset_tie_breaker_call_count()
    total_fixed = 0
    total_still_failing = 0

    for b in range(1, NUM_BATCHES + 1):
        path = f"evaluation/results_batch{b}.csv"
        if not os.path.exists(path):
            print(f"Batch {b}: no CSV, skipping.")
            continue

        rows = load_csv(path)
        failed_idx = [i for i, r in enumerate(rows) if r["trust_score"] is None]
        if not failed_idx:
            print(f"Batch {b}: no failed rows.")
            continue

        print(f"\n=== Batch {b}: retrying {len(failed_idx)} failed question(s) ===")
        for i in failed_idx:
            q = rows[i]["question"]
            print(f"  ({rows[i]['source']}) {q}")
            try:
                rows[i] = evaluate_one(trust_graph, q, rows[i]["best_answer"], rows[i]["source"])
                print(f"    -> Trust Score: {rows[i]['trust_score']}% | Correct: {rows[i]['correct']}")
                total_fixed += 1
            except Exception as e:
                print(f"    -> STILL FAILING: {e}")
                total_still_failing += 1
            time.sleep(1)

        save_csv(rows, path)
        print(f"Batch {b}: saved.")

    print(f"\nBackfill complete: {total_fixed} fixed, {total_still_failing} still failing.")
    if config.USE_TIE_BREAKER:
        print(f"Tie-breaker (Llama 3.3 70B) calls used this backfill: {get_tie_breaker_call_count()}")
    if total_still_failing == 0:
        print("Running merge for the complete 200-question result...\n")
        merge_batches()


def merge_batches():
    all_results = []
    missing = []
    for b in range(1, NUM_BATCHES + 1):
        path = f"evaluation/results_batch{b}.csv"
        if os.path.exists(path):
            all_results.extend(load_csv(path))
        else:
            missing.append(b)

    if missing:
        print(f"WARNING: missing batch(es) {missing} - merge will be incomplete ({len(all_results)}/200 questions).")

    summarize(all_results, out_path="evaluation/results_final.csv", title=f"MERGED FINAL SUMMARY (Full {len(all_results)}, Groq GPT-OSS-20B correctness-checker)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the 200-question evaluation in 50-question batches, or merge completed batches.")
    parser.add_argument("--batch", type=int, choices=range(1, NUM_BATCHES + 1), help="Run one 50-question batch (1-4).")
    parser.add_argument("--merge", action="store_true", help="Merge all completed result_batch*.csv files into the final summary.")
    parser.add_argument("--backfill", action="store_true", help="Re-run only the failed rows across all batch CSVs, then merge.")
    args = parser.parse_args()

    if args.backfill:
        run_backfill()
    elif args.merge:
        merge_batches()
    elif args.batch:
        run_batch(args.batch)
    else:
        # Fallback: run the full 200 in one go (original behavior).
        dataset = load_combined_dataset(total=200)
        results = run_evaluation(dataset)
        summarize(results, out_path="evaluation/results_final.csv", title="EVALUATION SUMMARY (Full 200, Groq GPT-OSS-20B correctness-checker)")
