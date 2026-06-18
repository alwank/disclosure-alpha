from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from typing import Any, TypeVar

from fastapi import FastAPI, HTTPException, Query

from disclosure_alpha.api.helpers import (
    parse_compare_param,
    parse_fields_param,
    parse_include_param,
    parse_sections_param,
    section_summaries,
    shape_matrix_scores,
)
from disclosure_alpha.api.schemas import (
    ErrorResponse,
    FilingSummary,
    FilingsResponse,
    MatrixResponse,
    MetricsResponse,
    SectionsResponse,
)
from disclosure_alpha.edgar.resolver import list_filings, normalize_form_type, normalize_quarter
from disclosure_alpha.edgar.types import EdgarError, FilingNotFoundError, SecFetchError
from disclosure_alpha.pipeline import (
    filter_metrics_result,
    filter_sections,
    metrics_filing_ticker,
    score_deterministic,
    sections_filing_ticker,
)

app = FastAPI(
    title="Disclosure Alpha API",
    description="Self-hosted deterministic SEC filing analytics",
    version="0.1.0",
)

T = TypeVar("T")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _parse_form_quarter(form_type: str, quarter: str | None) -> tuple[str, str | None]:
    try:
        base = normalize_form_type(form_type)
        q = normalize_quarter(quarter)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if base == "10-Q" and q is None:
        raise HTTPException(status_code=422, detail="quarter is required for 10-Q (Q1, Q2, or Q3)")
    return base, q


def _run_edgar(fn: Callable[[], T]) -> T:
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


def _scores_dict(scores) -> dict[str, Any]:
    return {
        "overall_disclosure_risk_score": scores.overall_disclosure_risk_score,
        "score_coverage_ratio": scores.score_coverage_ratio,
        "confidence_score": scores.confidence_score,
        "missing_components": scores.missing_components,
        "components": asdict(scores.components),
        "aggregates": asdict(scores.aggregates),
        "provenance": [p.to_dict() for p in scores.provenance],
    }


@app.get(
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

    return _run_edgar(_fetch)


@app.get(
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
    base, q = _parse_form_quarter(form_type, quarter)
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

    return _run_edgar(_fetch)


@app.get(
    "/v1/company/{ticker}/disclosure-metrics",
    response_model=MetricsResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def disclosure_metrics(
    ticker: str,
    fiscal_year: int = Query(..., ge=1994, le=2100),
    form_type: str = Query("10-K"),
    quarter: str | None = Query(None),
    compare: str = Query("prior"),
    sections: str | None = Query(None),
) -> MetricsResponse:
    base, q = _parse_form_quarter(form_type, quarter)
    try:
        compare_prior = parse_compare_param(compare)
        section_filter = parse_sections_param(sections, form_type=base)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    def _fetch() -> MetricsResponse:
        result = metrics_filing_ticker(
            ticker,
            fiscal_year,
            form_type=base,
            quarter=q,
            compare_prior=compare_prior,
        )
        metrics = result.metrics
        if section_filter:
            metrics = filter_metrics_result(metrics, section_filter)
        return MetricsResponse(
            filing=result.filing,
            metrics=asdict(metrics),
            versions=result.versions,
        )

    return _run_edgar(_fetch)


@app.get(
    "/v1/company/{ticker}/disclosure-matrix",
    response_model=MatrixResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def disclosure_matrix(
    ticker: str,
    fiscal_year: int = Query(..., ge=1994, le=2100),
    form_type: str = Query("10-K"),
    quarter: str | None = Query(None),
    view: str = Query("deterministic"),
    compare: str = Query("prior"),
    sections: str | None = Query(None),
    include: str | None = Query("metrics,provenance"),
    fields: str | None = Query(None),
) -> MatrixResponse:
    if view != "deterministic":
        raise HTTPException(
            status_code=422,
            detail="Only view=deterministic is supported in self-hosted open-source API",
        )
    base, q = _parse_form_quarter(form_type, quarter)
    try:
        compare_prior = parse_compare_param(compare)
        section_filter = parse_sections_param(sections, form_type=base)
        include_set = parse_include_param(include)
        field_set = parse_fields_param(fields)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    def _fetch() -> MatrixResponse:
        result = metrics_filing_ticker(
            ticker,
            fiscal_year,
            form_type=base,
            quarter=q,
            compare_prior=compare_prior,
        )
        scores = score_deterministic(result.metrics)
        scores_payload = shape_matrix_scores(
            _scores_dict(scores),
            include_provenance="provenance" in include_set,
            fields=field_set,
        )
        metrics_payload = None
        if "metrics" in include_set:
            metrics = result.metrics
            if section_filter:
                metrics = filter_metrics_result(metrics, section_filter)
            metrics_payload = asdict(metrics)
        return MatrixResponse(
            filing=result.filing,
            metrics=metrics_payload,
            scores=scores_payload,
            versions=result.versions,
            view=view,
        )

    return _run_edgar(_fetch)
