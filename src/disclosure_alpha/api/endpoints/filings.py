from __future__ import annotations

from fastapi import APIRouter, Query

from disclosure_alpha.api.schemas import ErrorResponse, FilingSummary, FilingsResponse
from disclosure_alpha.api.endpoints.deps import run_edgar
from disclosure_alpha.edgar.resolver import list_filings, normalize_form_type

router = APIRouter(tags=["filings"])


@router.get(
    "/v1/company/{ticker}/filings",
    response_model=FilingsResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def company_filings(
    ticker: str,
    fiscal_year: int = Query(..., ge=1994, le=2100),
    form_type: str | None = Query(None),
) -> FilingsResponse:
    def _fetch() -> FilingsResponse:
        form = normalize_form_type(form_type) if form_type else None
        refs = list_filings(ticker, fiscal_year, form_type=form)
        return FilingsResponse(
            ticker=ticker.upper(),
            fiscal_year=fiscal_year,
            filings=[
                FilingSummary(
                    ticker=r.ticker,
                    cik=r.cik,
                    accession_number=r.accession_number,
                    form_type=r.form_type,
                    fiscal_year=r.fiscal_year,
                    quarter=r.quarter,
                    filing_date=r.filing_date,
                    report_date=r.report_date,
                )
                for r in refs
            ],
        )

    return run_edgar(_fetch)
