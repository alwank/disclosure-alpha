"""Sector/form-aware baseline statistics for calibration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationContext:
    form_type: str = "10-K"
    sector: str | None = None
    fiscal_year: int | None = None


# ponytail: committed defaults; expand from validation corpus over time
_BASELINES: dict[str, dict[str, list[float]]] = {
    "10-K": {
        "negative_word_ratio": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15],
        "uncertainty_word_ratio": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.09, 0.11, 0.14],
        "boilerplate_phrase_ratio": [0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.22],
        "readability_score": [20.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 75.0],
    },
    "10-Q": {
        "negative_word_ratio": [0.008, 0.015, 0.025, 0.035, 0.045, 0.055, 0.07, 0.09, 0.11, 0.13],
        "uncertainty_word_ratio": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15],
    },
}

_SECTOR_OVERRIDES: dict[str, dict[str, dict[str, list[float]]]] = {
    "financials": {
        "10-K": {
            "negative_word_ratio": [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.09, 0.11, 0.13, 0.16],
        }
    },
    "healthcare": {
        "10-K": {
            "uncertainty_word_ratio": [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.14, 0.18],
        }
    },
}


@dataclass(frozen=True)
class BaselineStats:
    metric_name: str
    cohort: str
    sample_size: int
    fallback_level: str
    percentiles: list[float] | None = None
    mean: float | None = None
    std: float | None = None


def _cohort_stats(percentiles: list[float]) -> tuple[float | None, float | None]:
    if not percentiles:
        return None, None
    mean = sum(percentiles) / len(percentiles)
    if len(percentiles) < 2:
        return mean, None
    var = sum((p - mean) ** 2 for p in percentiles) / (len(percentiles) - 1)
    return mean, var**0.5


def lookup_baseline(
    metric_name: str,
    context: CalibrationContext | None = None,
) -> BaselineStats | None:
    """Resolve baseline with fallback: sector+form+year → sector+form → form+year → form → none."""
    ctx = context or CalibrationContext()
    form = ctx.form_type or "10-K"
    sector = (ctx.sector or "").lower().strip() or None
    year = ctx.fiscal_year

    candidates: list[tuple[str, list[float] | None]] = []
    if sector and year:
        sector_form = _SECTOR_OVERRIDES.get(sector, {}).get(form, {})
        refs = sector_form.get(metric_name)
        if refs:
            candidates.append((f"{sector}:{form}:{year}", refs))
    if sector:
        sector_form = _SECTOR_OVERRIDES.get(sector, {}).get(form, {})
        refs = sector_form.get(metric_name)
        if refs:
            candidates.append((f"{sector}:{form}", refs))
    form_table = _BASELINES.get(form, {})
    refs = form_table.get(metric_name)
    if refs and year:
        candidates.append((f"{form}:{year}", refs))
    if refs:
        candidates.append((form, refs))

    for cohort, percentiles in candidates:
        if percentiles:
            mean, std = _cohort_stats(percentiles)
            return BaselineStats(
                metric_name=metric_name,
                cohort=cohort,
                sample_size=len(percentiles),
                fallback_level=cohort,
                percentiles=list(percentiles),
                mean=mean,
                std=std,
            )
    return None
