from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from typing import Any, TypeVar

from fastapi import HTTPException

from disclosure_alpha.edgar.resolver import normalize_form_type, normalize_quarter
from disclosure_alpha.edgar.types import EdgarError, FilingNotFoundError, SecFetchError

T = TypeVar("T")


def parse_form_quarter(form_type: str, quarter: str | None) -> tuple[str, str | None]:
    try:
        base = normalize_form_type(form_type)
        q = normalize_quarter(quarter)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if base == "10-Q" and q is None:
        raise HTTPException(status_code=422, detail="quarter is required for 10-Q (Q1, Q2, or Q3)")
    return base, q


def run_edgar(fn: Callable[[], T]) -> T:
    try:
        return fn()
    except FilingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SecFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except EdgarError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def scores_dict(scores) -> dict[str, Any]:
    return {
        "overall_disclosure_risk_score": scores.overall_disclosure_risk_score,
        "score_coverage_ratio": scores.score_coverage_ratio,
        "confidence_score": scores.confidence_score,
        "missing_components": scores.missing_components,
        "components": asdict(scores.components),
        "aggregates": asdict(scores.aggregates),
        "provenance": [p.to_dict() for p in scores.provenance],
    }
