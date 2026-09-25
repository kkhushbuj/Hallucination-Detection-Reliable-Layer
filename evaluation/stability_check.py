import sys
import os
import csv
import argparse
import statistics

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.evaluate import load_combined_dataset, run_evaluation

FIELDNAMES = ["run", "accuracy", "avg_trust_correct", "avg_trust_incorrect", "gap"]


def compute_run_metrics(results):
    """Reduce one run_evaluation() result list to the accuracy/gap numbers we track for stability."""
    valid = [r for r in results if r["trust_score"] is not None]
    if not valid:
        return {"accuracy": None, "avg_trust_correct": None, "avg_trust_incorrect": None, "gap": None}

    correct_results = [r for r in valid if r["correct"]]
    incorrect_results = [r for r in valid if not r["correct"]]

    accuracy = len(correct_results) / len(valid) * 100
    avg_trust_correct = sum(r["trust_score"] for r in correct_results) / len(correct_results) if correct_results else 0
    avg_trust_incorrect = sum(r["trust_score"] for r in incorrect_results) / len(incorrect_results) if incorrect_results else 0

    return {
        "accuracy": accuracy,
        "avg_trust_correct": avg_trust_correct,
        "avg_trust_incorrect": avg_trust_incorrect,
        "gap": avg_trust_correct - avg_trust_incorrect,
    }


def run_stability_check(n_runs: int, out_path: str = "evaluation/results_stability.csv"):
    dataset = load_combined_dataset(total=200)
    run_metrics = []

    for run_num in range(1, n_runs + 1):
        print(f"\n{'=' * 50}\nSTABILITY RUN {run_num}/{n_runs}\n{'=' * 50}\n")
        results = run_evaluation(dataset, global_offset=0, total_overall=200)
        metrics = compute_run_metrics(results)
        run_metrics.append(metrics)
        print(f"\nRun {run_num} -> Accuracy: {metrics['accuracy']:.1f}% | Gap: {metrics['gap']:.1f} points")

    valid_runs = [m for m in run_metrics if m["accuracy"] is not None]
    if not valid_runs:
        print("No valid runs to summarize.")
        return

    accuracies = [m["accuracy"] for m in valid_runs]
    gaps = [m["gap"] for m in valid_runs]

    mean_accuracy = statistics.mean(accuracies)
    mean_gap = statistics.mean(gaps)
    stdev_accuracy = statistics.stdev(accuracies) if len(accuracies) > 1 else 0.0
    stdev_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0.0

    print(f"\n{'=' * 50}\nSTABILITY SUMMARY ({len(valid_runs)} run(s))\n{'=' * 50}")
    for i, m in enumerate(run_metrics, 1):
        if m["accuracy"] is None:
            print(f"Run {i}: FAILED")
        else:
            print(f"Run {i}: Accuracy: {m['accuracy']:.1f}% | Gap: {m['gap']:.1f} points")
    print(f"\nAccuracy: {mean_accuracy:.1f}% ± {stdev_accuracy:.1f}%")
    print(f"Gap: {mean_gap:.1f} ± {stdev_gap:.1f} points")

    rows = []
    for i, m in enumerate(run_metrics, 1):
        rows.append({
            "run": i,
            "accuracy": m["accuracy"],
            "avg_trust_correct": m["avg_trust_correct"],
            "avg_trust_incorrect": m["avg_trust_incorrect"],
            "gap": m["gap"],
        })
    rows.append({
        "run": "mean ± stdev",
        "accuracy": f"{mean_accuracy:.1f} ± {stdev_accuracy:.1f}",
        "avg_trust_correct": "",
        "avg_trust_incorrect": "",
        "gap": f"{mean_gap:.1f} ± {stdev_gap:.1f}",
    })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full 200-question evaluation N times with the same config, to measure run-to-run stability.")
    parser.add_argument("--runs", type=int, default=3, help="Number of times to repeat the full evaluation (default 3).")
    args = parser.parse_args()

    run_stability_check(args.runs)
