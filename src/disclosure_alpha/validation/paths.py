"""Path helpers for FY-scoped validation artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from disclosure_alpha.validation.scoring_version import normalize_scoring_version
from disclosure_alpha.version import SCORING_MODEL_VERSION_V2


def corpus_path(fiscal_year: int | None, *, kind: Literal["item1a", "matrix"]) -> Path:
    fy = fiscal_year or 2025
    if kind == "item1a":
        if fy == 2025:
            return Path("data/validation/corpus/sp500_item1a.jsonl")
        return Path(f"data/validation/corpus/sp500_item1a_fy{fy}.jsonl")
    if kind == "matrix":
        return Path(f"data/validation/corpus/sp500_matrix_fy{fy}.jsonl")
    raise ValueError(f"unsupported corpus kind: {kind}")


def outcomes_path(fiscal_year: int | None) -> Path:
    if fiscal_year is None or fiscal_year == 2025:
        return Path("data/validation/outcomes/sp500_outcomes.jsonl")
    return Path(f"data/validation/outcomes/sp500_outcomes_fy{fiscal_year}.jsonl")


def report_path(
    level: Literal["l2", "l3"],
    fiscal_year: int | None,
    scoring_version: str,
) -> Path:
    fy = fiscal_year or 2025
    is_v2 = normalize_scoring_version(scoring_version) == SCORING_MODEL_VERSION_V2
    suffix = "_v2" if is_v2 else ""
    if level == "l2":
        if fy == 2025:
            return Path(f"data/validation/reports/deterministic_validation_report{suffix}.json")
        return Path(f"data/validation/reports/deterministic_validation_report_fy{fy}{suffix}.json")
    if level == "l3":
        if fy == 2025:
            return Path(f"data/validation/reports/l3_outcomes_report{suffix}.json")
        return Path(f"data/validation/reports/l3_outcomes_report_fy{fy}{suffix}.json")
    raise ValueError(f"unsupported report level: {level}")
