import sys
import os
import csv
import json
import time
import random
import requests
import anthropic
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from graph import build_graph

judge_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


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
    per_source = total // 3
    truthfulqa = load_truthfulqa(n=per_source, seed=seed)
    halueval = load_halueval(n=per_source, seed=seed)
    triviaqa = load_triviaqa(n=total - len(truthfulqa) - len(halueval), seed=seed)

    combined = truthfulqa + halueval + triviaqa
    random.seed(seed)
    random.shuffle(combined)
    return combined


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
    response = judge_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    answer = response.content[0].text.strip().upper()
    return answer.startswith("YES")


def run_evaluation():
    dataset = load_combined_dataset(total=200)
    trust_graph = build_graph()

    print(f"Loaded {len(dataset)} questions from 3 sources.\n")

    results = []

    for i, row in enumerate(dataset, 1):
        question = row["question"]
        best_answer = row["best_answer"]
        source = row["source"]

        print(f"[{i}/{len(dataset)}] ({source}) {question}")

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


def summarize(results):
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
    print("EVALUATION SUMMARY (Full 200, Claude correctness-checker)")
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

    with open("evaluation/results_v4_claude_checker.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "source", "model_answer", "best_answer", "trust_score", "label", "flagged_count", "majority_flagged", "correct"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print("\nDetailed results saved to evaluation/results_v4_claude_checker.csv")


if __name__ == "__main__":
    results = run_evaluation()
    summarize(results)