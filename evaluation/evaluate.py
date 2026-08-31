import sys
import os
import csv
import json
import time
import random
import argparse
import requests
from groq import Groq
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from graph import build_graph

judge_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

BATCH_SIZE = 50
NUM_BATCHES = 4
FIELDNAMES = ["question", "source", "model_answer", "best_answer", "trust_score", "label", "flagged_count", "majority_flagged", "correct"]


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


def load_triviaqa(n=66, seed=42):
    url = "https://datasets-server.huggingface.co/rows"
    params = {
        "dataset": "mandarjoshi/trivia_qa",
        "config": "rc.nocontext",
        "split": "validation",
        "offset": 0,
        "length": min(n * 3, 100),
    }
    response = requests.get(url, params=params)
    data = response.json()

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


def is_correct(question: str, model_answer: str, best_answer: str) -> bool:
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
    response = judge_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        reasoning_effort="low",
    )
    answer = response.choices[0].message.content.strip().upper()
    return answer.startswith("YES")


def run_evaluation(dataset, global_offset=0, total_overall=200):
    trust_graph = build_graph()

    print(f"Running {len(dataset)} questions (overall #{global_offset + 1}-{global_offset + len(dataset)} of {total_overall}).\n")

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

    save_csv(results, out_path)
    print(f"\nDetailed results saved to {out_path}")


def run_batch(batch_num: int):
    dataset, offset = get_batch(batch_num)
    print(f"=== Batch {batch_num}/{NUM_BATCHES} ({len(dataset)} questions) ===\n")
    results = run_evaluation(dataset, global_offset=offset, total_overall=200)
    out_path = f"evaluation/results_batch{batch_num}.csv"
    summarize(results, out_path=out_path, title=f"BATCH {batch_num} SUMMARY (questions {offset + 1}-{offset + len(dataset)})")


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
    args = parser.parse_args()

    if args.merge:
        merge_batches()
    elif args.batch:
        run_batch(args.batch)
    else:
        # Fallback: run the full 200 in one go (original behavior).
        dataset = load_combined_dataset(total=200)
        results = run_evaluation(dataset)
        summarize(results, out_path="evaluation/results_final.csv", title="EVALUATION SUMMARY (Full 200, Groq GPT-OSS-20B correctness-checker)")
