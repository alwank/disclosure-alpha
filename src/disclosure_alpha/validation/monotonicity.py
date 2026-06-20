"""Quintile monotonicity gates for L3 outcome validation."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np

GateStatus = Literal["pass", "fail", "skipped"]


@dataclass
class MonotonicityGateResult:
    name: str
    status: GateStatus
    score_field: str
    outcome_field: str
    n: int
    q1_mean: float | None
    q5_mean: float | None
    q5_q1_ratio: float | None
    threshold_direction: str
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assign_quintiles(values: list[float], *, n_quintiles: int = 5) -> list[int]:
    """Equal-count quintile labels 1..n_quintiles (1 = lowest score)."""
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    if n == 0:
        return []
    order = np.argsort(arr, kind="mergesort")
    labels = np.empty(n, dtype=int)
    for rank, idx in enumerate(order):
        labels[idx] = min(n_quintiles, (rank * n_quintiles) // n + 1)
    return labels.tolist()


def evaluate_quintile_monotonicity(
    scores: list[float],
    outcomes: list[float],
    *,
    name: str,
    score_field: str,
    outcome_field: str,
    min_n: int = 50,
    min_per_quintile: int = 5,
) -> MonotonicityGateResult:
    if len(scores) != len(outcomes):
        return MonotonicityGateResult(
            name=name,
            status="skipped",
            score_field=score_field,
            outcome_field=outcome_field,
            n=0,
            q1_mean=None,
            q5_mean=None,
            q5_q1_ratio=None,
            threshold_direction="Q5 > Q1",
            message="score/outcome length mismatch",
        )

    pairs = [(s, o) for s, o in zip(scores, outcomes) if math.isfinite(s) and math.isfinite(o)]
    if len(pairs) < min_n:
        return MonotonicityGateResult(
            name=name,
            status="skipped",
            score_field=score_field,
            outcome_field=outcome_field,
            n=len(pairs),
            q1_mean=None,
            q5_mean=None,
            q5_q1_ratio=None,
            threshold_direction="Q5 > Q1",
            message=f"insufficient pairs (n={len(pairs)}, min_n={min_n})",
        )

    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    quintiles = assign_quintiles(xs)
    by_q: dict[int, list[float]] = {i: [] for i in range(1, 6)}
    for q, y in zip(quintiles, ys):
        by_q[q].append(y)

    if any(len(by_q[q]) < min_per_quintile for q in (1, 5)):
        return MonotonicityGateResult(
            name=name,
            status="skipped",
            score_field=score_field,
            outcome_field=outcome_field,
            n=len(pairs),
            q1_mean=None,
            q5_mean=None,
            q5_q1_ratio=None,
            threshold_direction="Q5 > Q1",
            message="Q1 or Q5 under min_per_quintile",
        )

    q1_mean = float(np.mean(by_q[1]))
    q5_mean = float(np.mean(by_q[5]))
    ratio = q5_mean / q1_mean if q1_mean > 0 else None
    passed = q5_mean > q1_mean

    return MonotonicityGateResult(
        name=name,
        status="pass" if passed else "fail",
        score_field=score_field,
        outcome_field=outcome_field,
        n=len(pairs),
        q1_mean=round(q1_mean, 6),
        q5_mean=round(q5_mean, 6),
        q5_q1_ratio=round(ratio, 4) if ratio is not None else None,
        threshold_direction="Q5 > Q1",
        message="",
    )


def overall_l3_pass(gates: list[MonotonicityGateResult], *, min_pass: int = 1) -> bool:
    """L3 partial: pass if at least ``min_pass`` monotonicity gates pass (full protocol: 2 of 4)."""
    passed = sum(1 for g in gates if g.status == "pass")
    return passed >= min_pass
