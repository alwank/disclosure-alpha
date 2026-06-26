"""Precomputed S&P 500 FY2025 overall score distribution for score-card footer."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any


@lru_cache(maxsize=1)
def _load_corpus() -> dict[str, Any]:
    raw = resources.files("disclosure_alpha.openbb.data").joinpath("sp500_overall_fy2025.json").read_text(
        encoding="utf-8"
    )
    return json.loads(raw)


def _percentile_rank(value: float, sorted_values: list[float]) -> int:
    if not sorted_values:
        return 0
    below = sum(1 for v in sorted_values if v < value)
    return int(round(100 * below / len(sorted_values)))


def corpus_context(
    ticker: str,
    overall: float | None,
    fiscal_year: int,
    form_type: str,
) -> dict[str, Any] | None:
    if overall is None:
        return None
    data = _load_corpus()
    if fiscal_year != data.get("fiscal_year") or form_type != data.get("form_type"):
        return None
    sorted_overalls: list[float] = data["sorted_overalls"]
    return {
        "cohort_label": data["cohort_label"],
        "median": data["median_overall"],
        "n": data["n"],
        "percentile_rank": _percentile_rank(overall, sorted_overalls),
        "ticker_overall": data.get("by_ticker", {}).get(ticker.upper()),
    }
