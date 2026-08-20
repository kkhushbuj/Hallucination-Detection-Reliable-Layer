import os
import math
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def check_entailment(answer_a: str, answer_b: str) -> bool:
    """Ask a model if two answers logically agree on the same core conclusion."""
    prompt = (
        f"Answer A: {answer_a}\n\n"
        f"Answer B: {answer_b}\n\n"
        "Do these two answers reach the SAME final conclusion? "
        "IMPORTANT: one answer may include extra explanation, steps, or detail "
        "that the other doesn't have — this does NOT count as disagreement. "
        "Only judge based on the final conclusion/result itself.\n\n"
        "Example: 'The answer is 12.' and 'To solve this, multiply 80 by 0.15, "
        "which equals 12.' → these AGREE, both conclude 12.\n\n"
        "Respond with ONLY the single word YES or the single word NO. "
        "Do not include any explanation or other text."
    )
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    result_text = response.choices[0].message.content.strip().upper()
    return "YES" in result_text


def cluster_answers(answers: list[str]) -> list[list[int]]:
    """Group answer indices into clusters where every answer in a cluster agrees with each other."""
    n = len(answers)
    clusters = []
    assigned = [False] * n

    for i in range(n):
        if assigned[i]:
            continue
        cluster = [i]
        assigned[i] = True
        for j in range(i + 1, n):
            if assigned[j]:
                continue
            try:
                agrees = check_entailment(answers[i], answers[j])
            except Exception:
                agrees = False
            if agrees:
                cluster.append(j)
                assigned[j] = True
        clusters.append(cluster)

    return clusters


def calculate_consistency_score(clusters: list[list[int]], total: int) -> float:
    """Turn cluster sizes into a 0-1 overall confidence score using entropy. All-agree = 1.0."""
    if len(clusters) == 1:
        return 1.0

    entropy = 0.0
    for cluster in clusters:
        p = len(cluster) / total
        if p > 0:
            entropy -= p * math.log2(p)

    max_entropy = math.log2(total) if total > 1 else 1
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

    return max(0.0, 1 - normalized_entropy)


def get_per_answer_consistency(clusters: list[list[int]], answer_index: int, total: int) -> float:
    """For one specific answer, what fraction of the OTHER answers agree with it?"""
    if total <= 1:
        return 1.0
    for cluster in clusters:
        if answer_index in cluster:
            return (len(cluster) - 1) / (total - 1)
    return 0.0