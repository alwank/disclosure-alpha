"""Disclosure changes endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from disclosure_alpha.api.endpoints.deps import parse_form_quarter, run_edgar
from disclosure_alpha.api.helpers import parse_compare_param, parse_sections_param
from disclosure_alpha.api.schemas import ChangesResponse, ErrorResponse
from disclosure_alpha.api.shapes import shape_changes_payload
from disclosure_alpha.pipeline import filter_metrics_result, metrics_filing_ticker, score_for_model

router = APIRouter(tags=["changes"])


@router.get(
    "/v1/company/{ticker}/disclosure-changes",
    response_model=ChangesResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
def disclosure_changes(
    ticker: str,
    fiscal_year: int = Query(..., ge=1994, le=2100),
    form_type: str = Query("10-K"),
    quarter: str | None = Query(None),
    compare: str = Query("prior"),
    sections: str | None = Query(None),
) -> ChangesResponse:
    base, q = parse_form_quarter(form_type, quarter)
    try:
        compare_prior = parse_compare_param(compare)
        section_filter = parse_sections_param(sections, form_type=base)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    def _fetch() -> ChangesResponse:
        result = metrics_filing_ticker(
            ticker,
            fiscal_year,
            form_type=base,
            quarter=q,
            compare_prior=compare_prior,
        )
        metrics = result.metrics
        if section_filter:
            metrics = filter_metrics_result(
                metrics,
                section_filter,
                form_type=base,
                sections=result.sections,
            )
        scores = score_for_model(metrics, form_type=base) if compare_prior else None
        shaped = shape_changes_payload(metrics, scores)
        return ChangesResponse(
            filing=result.filing,
            section_diffs=shaped["section_diffs"],
            language_deltas=shaped["language_deltas"],
            change_score=shaped["change_score"],
            versions=result.versions,
        )

    return run_edgar(_fetch)
