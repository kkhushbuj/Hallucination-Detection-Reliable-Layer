"""Unit tests for the pure scoring logic. None of these call an LLM."""

import pytest

from core.nli import calculate_consistency_score, get_per_answer_consistency
from core.verification import calculate_answer_score, parse_verdict


@pytest.mark.parametrize("reply", ["CORRECT", "correct", " Correct.", "CORRECT\n"])
def test_parse_verdict_reads_correct(reply):
    assert parse_verdict(reply) is True


@pytest.mark.parametrize(
    "reply",
    ["HALLUCINATED", "INCORRECT", "This is not correct.", "Not  correct", "That answer is wrong"],
)
def test_parse_verdict_negations_are_not_read_as_correct(reply):
    assert parse_verdict(reply) is False


def test_parse_verdict_rejects_unreadable_reply():
    with pytest.raises(ValueError):
        parse_verdict("I am not sure what you mean")


def judge(correct, failed=False):
    return {"provider": "x", "correct": correct, "failed": failed}


def test_score_is_equal_share_per_judge_plus_consistency():
    result = calculate_answer_score([judge(True), judge(True), judge(True)], consistency_fraction=0.5)
    assert result["score"] == pytest.approx(0.875)
    assert result["any_hallucinated"] is False


def test_score_is_zero_when_everything_disagrees():
    result = calculate_answer_score([judge(False)] * 3, consistency_fraction=0.0)
    assert result["score"] == 0.0
    assert result["any_hallucinated"] is True


def test_failed_judge_is_dropped_and_weights_rebalance():
    judges = [judge(True), judge(True), judge(None, failed=True)]
    result = calculate_answer_score(judges, consistency_fraction=1.0)
    assert result["score"] == pytest.approx(1.0)


def test_per_answer_consistency_counts_agreeing_others():
    clusters = [[0, 1], [2]]
    assert get_per_answer_consistency(clusters, 0, 3) == 0.5
    assert get_per_answer_consistency(clusters, 2, 3) == 0.0


def test_overall_consistency_bounds():
    assert calculate_consistency_score([[0, 1, 2]], 3) == 1.0
    assert calculate_consistency_score([[0], [1], [2]], 3) == pytest.approx(0.0)
