from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from disclosure_alpha.api.helpers import (
    parse_compare_param,
    parse_sections_param,
    section_summaries,
)
from disclosure_alpha.api.schemas import ErrorResponse, SectionsResponse
from disclosure_alpha.api.endpoints.deps import parse_form_quarter, run_edgar
from disclosure_alpha.pipeline import filter_sections, sections_filing_ticker

router = APIRouter(tags=["sections"])


@router.get(
    "/v1/company/{ticker}/sections",
    response_model=SectionsResponse,
    response_model_exclude_none=True,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def company_sections(
    ticker: str,
    fiscal_year: int = Query(..., ge=1994, le=2100),
    form_type: str = Query("10-K"),
    quarter: str | None = Query(None),
    compare: str = Query("prior"),
    sections: str | None = Query(None),
    include_text: bool = Query(False),
) -> SectionsResponse:
    base, q = parse_form_quarter(form_type, quarter)
    try:
        compare_prior = parse_compare_param(compare)
        section_filter = parse_sections_param(sections, form_type=base)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    def _fetch() -> SectionsResponse:
        result = sections_filing_ticker(
            ticker,
            fiscal_year,
            form_type=base,
            quarter=q,
            compare_prior=compare_prior,
        )
        extracted = result.sections
        if section_filter:
            extracted = filter_sections(extracted, section_filter)
        return SectionsResponse(
            filing=result.filing,
            sections=section_summaries(extracted, include_text=include_text),
            versions=result.versions,
        )

    return run_edgar(_fetch)
