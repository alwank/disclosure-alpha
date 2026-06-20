"""Tests for L3 quintile monotonicity gates."""

from __future__ import annotations

from disclosure_alpha.validation.monotonicity import (
    assign_quintiles,
    evaluate_quintile_monotonicity,
    overall_l3_pass,
)


def test_assign_quintiles_equal_buckets():
    labels = assign_quintiles([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    assert min(labels) == 1
    assert max(labels) == 5


def test_monotonicity_passes_when_q5_gt_q1():
    scores = list(range(100))
    outcomes = [float(s) * 2.0 for s in scores]
    gate = evaluate_quintile_monotonicity(
        scores,
        outcomes,
        name="test",
        score_field="score",
        outcome_field="outcome",
        min_n=50,
    )
    assert gate.status == "pass"
    assert gate.q5_mean is not None and gate.q1_mean is not None
    assert gate.q5_mean > gate.q1_mean


def test_monotonicity_fails_when_flat():
    scores = list(range(100))
    outcomes = [1.0] * 100
    gate = evaluate_quintile_monotonicity(
        scores,
        outcomes,
        name="test",
        score_field="score",
        outcome_field="outcome",
        min_n=50,
    )
    assert gate.status == "fail"


def test_overall_l3_pass_requires_min_count():
    from disclosure_alpha.validation.monotonicity import MonotonicityGateResult

    gates = [
        MonotonicityGateResult(
            name="a",
            status="pass",
            score_field="s",
            outcome_field="o",
            n=100,
            q1_mean=1.0,
            q5_mean=2.0,
            q5_q1_ratio=2.0,
            threshold_direction="Q5 > Q1",
        ),
        MonotonicityGateResult(
            name="b",
            status="fail",
            score_field="s",
            outcome_field="o",
            n=100,
            q1_mean=2.0,
            q5_mean=1.0,
            q5_q1_ratio=0.5,
            threshold_direction="Q5 > Q1",
        ),
    ]
    assert overall_l3_pass(gates, min_pass=1)
    assert not overall_l3_pass(gates, min_pass=2)
