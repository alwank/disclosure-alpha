"""Shared MCP tool implementations (no FastMCP registration)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from disclosure_alpha.diff_engine import compute_section_diff
from disclosure_alpha.pipeline import (
    compute_section_metrics,
    extract_sections_from_html,
    score_for_model,
    score_filing_html,
)
from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS
from disclosure_alpha.validation.scoring_version import normalize_scoring_version
from disclosure_alpha.version import (
    DICTIONARY_VERSION,
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)


def _section_dicts(sections) -> list[dict[str, Any]]:
    return [
        {
            "section_name": s.section_name,
            "cleaned_text": s.cleaned_text,
            "word_count": s.word_count,
            "extraction_confidence": s.extraction_confidence,
            "parser_version": s.parser_version,
        }
        for s in sections
    ]


def extract_sections(html: str, form_type: str) -> str:
    """Extract SEC filing sections from HTML (10-K, 10-Q, or 8-K; 8-K: local HTML only)."""
    sections = extract_sections_from_html(html, form_type)
    return json.dumps(
        {
            "parser_version": PARSER_VERSION,
            "sections": _section_dicts(sections),
        },
        indent=2,
    )


def compute_section_metrics_tool(
    sections_json: str,
    prior_sections_json: str | None = None,
    form_type: str = "10-K",
) -> str:
    """Compute deterministic text metrics and diffs from extracted section payloads."""
    from disclosure_alpha.section_extractor import ExtractedSection

    sections = [ExtractedSection(**item) for item in json.loads(sections_json)]
    prior = None
    if prior_sections_json:
        prior = [ExtractedSection(**item) for item in json.loads(prior_sections_json)]
    metrics = compute_section_metrics(sections, prior, form_type=form_type)
    return json.dumps(asdict(metrics), indent=2, default=str)


def diff_sections(current_text: str, prior_text: str, section_name: str = "section") -> str:
    """Diff two section texts and return change score + language deltas."""
    diff = compute_section_diff(
        current_text=current_text,
        prior_text=prior_text,
        current_section_id=section_name,
        prior_section_id=f"prior_{section_name}",
    )
    return json.dumps(asdict(diff), indent=2, default=str)


def score_deterministic_tool(
    metrics_json: str,
    scoring_model_version: str = SCORING_MODEL_VERSION,
    form_type: str = "10-K",
) -> str:
    """Aggregate deterministic component scores from a metrics payload."""
    from disclosure_alpha.pipeline import MetricsResult

    version = normalize_scoring_version(scoring_model_version)
    metrics = MetricsResult(**json.loads(metrics_json))
    scores = score_for_model(metrics, version, form_type=form_type)
    return json.dumps(
        {
            "overall_disclosure_risk_score": scores.overall_disclosure_risk_score,
            "score_coverage_ratio": scores.score_coverage_ratio,
            "confidence_score": scores.confidence_score,
            "missing_components": scores.missing_components,
            "components": asdict(scores.components),
            "aggregates": asdict(scores.aggregates),
            "provenance": [p.to_dict() for p in scores.provenance],
            "scoring_model_version": version,
        },
        indent=2,
    )


def score_filing_html_tool(
    html: str,
    form_type: str,
    prior_html: str | None = None,
    scoring_model_version: str = SCORING_MODEL_VERSION,
) -> str:
    """Run full pipeline on filing HTML (10-K, 10-Q, or 8-K; 8-K: local HTML only)."""
    version = normalize_scoring_version(scoring_model_version)
    result = score_filing_html(html, form_type, prior_html=prior_html)
    result.scores = score_for_model(result.metrics, version, form_type=form_type)
    result.versions = dict(result.versions)
    result.versions["scoring_model_version"] = version
    return json.dumps(result.to_dict(), indent=2, default=str)


def score_company_filing(
    ticker: str,
    fiscal_year: int,
    form_type: str = "10-K",
    quarter: str | None = None,
    scoring_model_version: str = SCORING_MODEL_VERSION,
) -> str:
    """Score a company filing by ticker and fiscal year (10-K or 10-Q with quarter)."""
    from disclosure_alpha.pipeline import score_filing_ticker

    version = normalize_scoring_version(scoring_model_version)
    result = score_filing_ticker(
        ticker, fiscal_year, form_type=form_type, quarter=quarter
    )
    result.scores = score_for_model(result.metrics, version, form_type=form_type)
    result.versions = dict(result.versions)
    result.versions["scoring_model_version"] = version
    return json.dumps(result.to_dict(), indent=2, default=str)


def list_company_filings(
    ticker: str,
    fiscal_year: int,
    form_type: str | None = None,
) -> str:
    """List available 10-K / 10-Q filings for a ticker and fiscal year."""
    from disclosure_alpha.edgar.resolver import list_filings

    refs = list_filings(ticker, fiscal_year, form_type=form_type)
    return json.dumps(
        [
            {
                "ticker": r.ticker,
                "cik": r.cik,
                "accession_number": r.accession_number,
                "form_type": r.form_type,
                "fiscal_year": r.fiscal_year,
                "quarter": r.quarter,
                "filing_date": r.filing_date,
                "report_date": r.report_date,
            }
            for r in refs
        ],
        indent=2,
    )


def taxonomy_payload() -> str:
    """Score taxonomy: component weights and version strings."""
    return json.dumps(
        {
            "parser_version": PARSER_VERSION,
            "metrics_engine_version": METRICS_ENGINE_VERSION,
            "dictionary_version": DICTIONARY_VERSION,
            "scoring_model_version": SCORING_MODEL_VERSION,
            "analytics_config_id": "builtin_default",
            "component_weights": COMPONENT_WEIGHTS,
        },
        indent=2,
    )
