from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from disclosure_alpha.api.endpoints.deps import parse_form_quarter, run_edgar, scores_dict
from disclosure_alpha.api.helpers import (
    parse_compare_param,
    parse_fields_param,
    parse_include_param,
    parse_sections_param,
    shape_matrix_scores,
)
from disclosure_alpha.api.schemas import ErrorResponse, MatrixResponse
from disclosure_alpha.api.shapes import apply_tier_preset
from disclosure_alpha.pipeline import filter_metrics_result, metrics_filing_ticker, score_deterministic
from disclosure_alpha.version import SCORING_MODEL_VERSION

router = APIRouter(tags=["matrix"])

_PRO_VIEWS = frozenset({"composite", "full"})


def _pro_stub_response(view: str) -> JSONResponse:
    return JSONResponse(
        status_code=402,
        content={
            "detail": (
                f"view={view} requires Disclosure Alpha Pro "
                "(composite LLM scoring not available in open-source API)"
            ),
            "available_views": ["deterministic"],
            "pro_required": True,
            "scoring_model_version": SCORING_MODEL_VERSION,
        },
    )


@router.get(
    "/v1/company/{ticker}/disclosure-matrix",
    response_model=MatrixResponse,
    responses={
        402: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
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
    tier: str | None = Query(
        None,
        description="Response tier preset (lite|standard|analyst); overrides include/fields when set",
    ),
) -> MatrixResponse | JSONResponse:
    if view in _PRO_VIEWS:
        return _pro_stub_response(view)
    if view != "deterministic":
        raise HTTPException(status_code=422, detail="view must be deterministic, composite, or full")
    base, q = parse_form_quarter(form_type, quarter)
    try:
        compare_prior = parse_compare_param(compare)
        section_filter = parse_sections_param(sections, form_type=base)
        if tier is not None:
            include, fields = apply_tier_preset(tier, include=include, fields=fields)
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
            scores_dict(scores),
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

    return run_edgar(_fetch)
