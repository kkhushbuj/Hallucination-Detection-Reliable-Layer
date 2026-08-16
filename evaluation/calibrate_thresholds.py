import csv

RESULTS_FILE = "evaluation/results_v4_claude_checker.csv"


def load_results(path=RESULTS_FILE):
    data = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["trust_score"] and row["correct"]:
                data.append({
                    "trust_score": float(row["trust_score"]),
                    "correct": row["correct"].strip().lower() == "true",
                })
    return data


def accuracy_at_threshold(data, threshold):
    correct_predictions = 0
    for row in data:
        predicted_reliable = row["trust_score"] >= threshold
        if predicted_reliable == row["correct"]:
            correct_predictions += 1
    return correct_predictions / len(data) if data else 0


def precision_at_threshold(data, threshold):
    above = [row for row in data if row["trust_score"] >= threshold]
    if not above:
        return 0, 0
    correct_above = sum(1 for row in above if row["correct"])
    return correct_above / len(above), len(above)


def find_best_medium_threshold(data):
    candidates = sorted(set(row["trust_score"] for row in data))
    best_threshold, best_accuracy = 50, 0
    for t in candidates:
        acc = accuracy_at_threshold(data, t)
        if acc > best_accuracy:
            best_accuracy, best_threshold = acc, t
    return best_threshold, best_accuracy


def find_high_threshold(data, target_precision=0.90):
    candidates = sorted(set(row["trust_score"] for row in data))
    for t in candidates:
        precision, count = precision_at_threshold(data, t)
        if precision >= target_precision and count >= 5:
            return t, precision, count
    return None, None, None


def evaluate_thresholds(data, high, medium):
    def label_for(score):
        if score >= high:
            return "high"
        elif score >= medium:
            return "medium"
        return "low"

    breakdown = {"high": [0, 0], "medium": [0, 0], "low": [0, 0]}
    for row in data:
        label = label_for(row["trust_score"])
        breakdown[label][1] += 1
        if row["correct"]:
            breakdown[label][0] += 1
    return breakdown


def main():
    data = load_results()
    print(f"Loaded {len(data)} results with valid trust scores.\n")

    print("=" * 60)
    print("CURRENT THRESHOLDS (guessed: High=80%, Medium=50%)")
    print("=" * 60)
    current = evaluate_thresholds(data, high=80, medium=50)
    for label in ["high", "medium", "low"]:
        correct, total = current[label]
        pct = (correct / total * 100) if total else 0
        print(f"  {label.capitalize()} confidence: {correct}/{total} actually correct ({pct:.1f}%)")

    print("\n" + "=" * 60)
    print("CALIBRATING NEW THRESHOLDS FROM REAL DATA")
    print("=" * 60)

    medium_threshold, medium_accuracy = find_best_medium_threshold(data)
    print(f"\nBest MEDIUM confidence threshold: {medium_threshold}%")
    print(f"  (Correctly separates right/wrong {medium_accuracy*100:.1f}% of the time)")

    high_threshold, high_precision, high_count = find_high_threshold(data, target_precision=0.90)
    if not high_threshold:
        high_threshold, high_precision, high_count = find_high_threshold(data, target_precision=0.85)
    if high_threshold:
        print(f"\nBest HIGH confidence threshold: {high_threshold}%")
        print(f"  (Answers at/above this are correct {high_precision*100:.1f}% of the time, based on {high_count} examples)")
    else:
        print(f"\nNo threshold reached 85%+ precision. Falling back to 80% as HIGH.")

    effective_high = high_threshold if high_threshold else 80
    effective_medium = medium_threshold if medium_threshold else 50

    print("\n" + "=" * 60)
    print(f"PERFORMANCE WITH RECOMMENDED THRESHOLDS (High={effective_high}%, Medium={effective_medium}%)")
    print("=" * 60)
    new = evaluate_thresholds(data, high=effective_high, medium=effective_medium)
    for label in ["high", "medium", "low"]:
        correct, total = new[label]
        pct = (correct / total * 100) if total else 0
        print(f"  {label.capitalize()} confidence: {correct}/{total} actually correct ({pct:.1f}%)")

    print("\n" + "=" * 60)
    print("RECOMMENDATION — update config.py to:")
    print("=" * 60)
    print(f"  HIGH_CONFIDENCE_THRESHOLD = {effective_high / 100}")
    print(f"  MEDIUM_CONFIDENCE_THRESHOLD = {effective_medium / 100}")


if __name__ == "__main__":
    main()