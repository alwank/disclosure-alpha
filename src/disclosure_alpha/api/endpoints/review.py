"""One response for the score dashboard and its exact filing evidence."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from disclosure_alpha.api.endpoints.deps import parse_form_quarter, run_edgar, scores_dict
from disclosure_alpha.api.helpers import parse_compare_param, parse_scoring_model_version
from disclosure_alpha.api.schemas import ErrorResponse
from disclosure_alpha.api.schemas.review import FilingReviewResponse
from disclosure_alpha.api.shapes import shape_changes_payload, shape_flags_payload
from disclosure_alpha.openbb.adapters import change_rows, flag_display_from_active, score_card_context
from disclosure_alpha.openbb.labels import section_label
from disclosure_alpha.pipeline import metrics_filing_ticker, score_for_model
from disclosure_alpha.text_metrics import detect_section_flags_with_evidence
from disclosure_alpha.version import SCORING_MODEL_VERSION

router = APIRouter(tags=["review"])


@router.get(
    "/v1/company/{ticker}/filing-review",
    response_model=FilingReviewResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def filing_review(
    ticker: str,
    fiscal_year: int = Query(..., ge=1994, le=2100),
    form_type: str = Query("10-K"),
    quarter: str | None = Query(None),
    compare: str = Query("prior"),
    scoring_model_version: str = Query(SCORING_MODEL_VERSION),
) -> FilingReviewResponse:
    base, q = parse_form_quarter(form_type, quarter)
    try:
        compare_prior = parse_compare_param(compare)
        scoring_version = parse_scoring_model_version(scoring_model_version)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    def _fetch() -> FilingReviewResponse:
        result = metrics_filing_ticker(
            ticker, fiscal_year, form_type=base, quarter=q, compare_prior=compare_prior
        )
        scores = score_for_model(result.metrics, scoring_version, form_type=base)
        sections = []
        evidence = []
        for section in result.sections:
            sections.append(
                {
                    "section_name": section.section_name,
                    "cleaned_text": section.cleaned_text,
                    "word_count": section.word_count,
                    "extraction_confidence": section.extraction_confidence,
                    "parser_version": section.parser_version,
                    "warnings": list(section.warnings),
                    "reading_blocks": section.reading_blocks,
                }
            )
            _, matches = detect_section_flags_with_evidence(
                section.cleaned_text, section.section_name
            )
            for match in matches:
                flag = str(match["flag"])
                match["id"] = f"{section.section_name}:{flag}:{match['start']}-{match['end']}"
                match["label"] = flag.removesuffix("_flag").replace("_", " ").title()
                evidence.append(match)
        versions = dict(result.versions)
        versions["scoring_model_version"] = scoring_version
        scores_payload = scores_dict(scores)
        active_flags = shape_flags_payload(result.metrics)["active_flags"]
        card = score_card_context(result.filing, scores_payload, versions)
        return FilingReviewResponse(
            filing=result.filing,
            scores=scores_payload,
            sections=sections,
            active_flags=active_flags,
            evidence=evidence,
            changes=shape_changes_payload(result.metrics, scores if compare_prior else None),
            display={
                "headline_rows": card["headline_rows"],
                "section_labels": {
                    section.section_name: section_label(section.section_name)
                    for section in result.sections
                },
                "flag_summary": flag_display_from_active(active_flags)["summary"],
                "change_rows": change_rows(result.metrics, scores) if compare_prior else [],
            },
            versions=versions,
        )

    return run_edgar(_fetch)
