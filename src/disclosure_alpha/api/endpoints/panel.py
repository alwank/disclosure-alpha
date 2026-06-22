"""Panel batch endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from disclosure_alpha.api.endpoints.deps import parse_form_quarter, scores_dict
from disclosure_alpha.api.helpers import (
    parse_compare_param,
    parse_fields_param,
    parse_include_param,
    parse_scoring_model_version,
    shape_matrix_scores,
)
from disclosure_alpha.api.schemas import ErrorResponse, PanelRequest, PanelResponse, PanelResult
from disclosure_alpha.pipeline import score_panel_tickers

router = APIRouter(tags=["panel"])

MAX_PANEL_TICKERS = 25


@router.post(
    "/v1/panel/disclosure-matrix",
    response_model=PanelResponse,
    responses={422: {"model": ErrorResponse}},
)
def panel_disclosure_matrix(body: PanelRequest) -> PanelResponse:
    if len(body.tickers) > MAX_PANEL_TICKERS:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum {MAX_PANEL_TICKERS} tickers per request",
        )
    try:
        compare_prior = parse_compare_param(body.compare)
        scoring_version = parse_scoring_model_version(body.scoring_model_version)
        include_set = parse_include_param(body.include)
        field_set = parse_fields_param(body.fields)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    base, q = parse_form_quarter(body.form_type, body.quarter)
    batch = score_panel_tickers(
        body.tickers,
        body.fiscal_year,
        form_type=base,
        quarter=q,
        compare_prior=compare_prior,
        scoring_model_version=scoring_version,
    )
    results: list[PanelResult] = []
    for item in batch.results:
        if item.status == "ok":
            scores_payload = None
            if item.scores is not None:
                scores_payload = shape_matrix_scores(
                    scores_dict(item.scores),
                    include_provenance="provenance" in include_set,
                    fields=field_set,
                )
            results.append(
                PanelResult(
                    ticker=item.ticker,
                    status="ok",
                    filing=item.filing,
                    scores=scores_payload,
                )
            )
        else:
            results.append(
                PanelResult(
                    ticker=item.ticker,
                    status="error",
                    error=item.error,
                )
            )
    return PanelResponse(
        results=results,
        summary=batch.summary,
        versions=batch.versions,
    )
