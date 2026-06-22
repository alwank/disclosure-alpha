"""Sector/form-aware calibration transforms for scoring v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from disclosure_alpha.baselines import CalibrationContext, lookup_baseline

# ponytail: minimal committed defaults; expand from validation corpus over time
_DEFAULT_PERCENTILES: dict[str, dict[str, list[float]]] = {
    "10-K": {
        "negative_word_ratio": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15],
        "uncertainty_word_ratio": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.09, 0.11, 0.14],
        "boilerplate_phrase_ratio": [0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.22],
        "readability_score": [20.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 75.0],
    }
}


@dataclass(frozen=True)
class CalibratedValue:
    raw_value: float
    calibrated_value: float
    calibration_reference: str
    calibration_status: str  # "calibrated" | "fallback"


def _percentile_rank(value: float, sorted_refs: list[float]) -> float:
    if not sorted_refs:
        return 50.0
    below = sum(1 for r in sorted_refs if r < value)
    equal = sum(1 for r in sorted_refs if r == value)
    return 100.0 * (below + 0.5 * equal) / len(sorted_refs)


def _lookup_refs(metric_name: str, context: CalibrationContext) -> list[float] | None:
    baseline = lookup_baseline(metric_name, context)
    if baseline and baseline.percentiles:
        return baseline.percentiles
    form_table = _DEFAULT_PERCENTILES.get(context.form_type)
    if not form_table:
        return None
    return form_table.get(metric_name)


def calibrate_metric(
    metric_name: str,
    raw_value: float,
    context: CalibrationContext | None = None,
) -> CalibratedValue:
    ctx = context or CalibrationContext()
    refs = _lookup_refs(metric_name, ctx)
    if refs is None:
        # ponytail: transparent v1-style scaling for ratios in [0,1]
        if 0.0 <= raw_value <= 1.0 and metric_name.endswith("_ratio"):
            calibrated = raw_value * 100.0
        else:
            calibrated = raw_value
        return CalibratedValue(
            raw_value=raw_value,
            calibrated_value=calibrated,
            calibration_reference="identity_fallback",
            calibration_status="fallback",
        )
    ref_key = ctx.form_type
    baseline = lookup_baseline(metric_name, ctx)
    if baseline:
        ref_key = baseline.cohort
    elif ctx.sector:
        ref_key = f"{ctx.sector}:{ctx.form_type}"
    rank = _percentile_rank(raw_value, refs)
    return CalibratedValue(
        raw_value=raw_value,
        calibrated_value=rank,
        calibration_reference=f"builtin_percentiles:{ref_key}:{metric_name}",
        calibration_status="calibrated",
    )


def robust_z_score(value: float, refs: list[float]) -> float:
    if len(refs) < 2:
        return 0.0
    sorted_refs = sorted(refs)
    median = sorted_refs[len(sorted_refs) // 2]
    deviations = sorted(abs(r - median) for r in sorted_refs)
    mad = deviations[len(deviations) // 2] or 1e-9
    return (value - median) / (1.4826 * mad)


def winsorized_min_max(value: float, refs: list[float], *, low_q: float = 0.05, high_q: float = 0.95) -> float:
    if len(refs) < 2:
        return value
    sorted_refs = sorted(refs)
    lo_idx = max(0, int(low_q * (len(sorted_refs) - 1)))
    hi_idx = min(len(sorted_refs) - 1, int(high_q * (len(sorted_refs) - 1)))
    lo, hi = sorted_refs[lo_idx], sorted_refs[hi_idx]
    if hi <= lo:
        return 50.0
    clipped = max(lo, min(hi, value))
    return 100.0 * (clipped - lo) / (hi - lo)


def calibration_provenance(cal: CalibratedValue) -> dict[str, Any]:
    return {
        "raw_value": cal.raw_value,
        "calibrated_value": cal.calibrated_value,
        "calibration_reference": cal.calibration_reference,
        "calibration_status": cal.calibration_status,
    }
