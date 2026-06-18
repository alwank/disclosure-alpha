"""MCP server for Disclosure Alpha deterministic analytics."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from disclosure_alpha.diff_engine import compute_section_diff
from disclosure_alpha.pipeline import (
    compute_section_metrics,
    extract_sections_from_html,
    score_deterministic,
    score_filing_html,
)
from disclosure_alpha.deterministic_scoring import DETERMINISTIC_COMPONENT_WEIGHTS
from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS
from disclosure_alpha.version import (
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "MCP extras required: pip install disclosure-alpha[mcp]"
    ) from exc

mcp = FastMCP("disclosure-alpha")


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


@mcp.tool()
def extract_sections(html: str, form_type: str) -> str:
    """Extract SEC filing sections from HTML for a form type (10-K, 10-Q, 8-K)."""
    sections = extract_sections_from_html(html, form_type)
    return json.dumps(
        {
            "parser_version": PARSER_VERSION,
            "sections": _section_dicts(sections),
        },
        indent=2,
    )


@mcp.tool()
def compute_section_metrics_tool(
    sections_json: str,
    prior_sections_json: str | None = None,
) -> str:
    """Compute deterministic text metrics and diffs from extracted section payloads."""
    from disclosure_alpha.section_extractor import ExtractedSection

    sections = [ExtractedSection(**item) for item in json.loads(sections_json)]
    prior = None
    if prior_sections_json:
        prior = [ExtractedSection(**item) for item in json.loads(prior_sections_json)]
    metrics = compute_section_metrics(sections, prior)
    return json.dumps(asdict(metrics), indent=2, default=str)


@mcp.tool()
def diff_sections(current_text: str, prior_text: str, section_name: str = "section") -> str:
    """Diff two section texts and return change score + language deltas."""
    diff = compute_section_diff(
        current_text=current_text,
        prior_text=prior_text,
        current_section_id=section_name,
        prior_section_id=f"prior_{section_name}",
    )
    return json.dumps(asdict(diff), indent=2, default=str)


@mcp.tool()
def score_deterministic_tool(metrics_json: str) -> str:
    """Aggregate deterministic component scores from a metrics payload."""
    from disclosure_alpha.pipeline import MetricsResult

    metrics = MetricsResult(**json.loads(metrics_json))
    scores = score_deterministic(metrics)
    return json.dumps(
        {
            "overall_disclosure_risk_score": scores.overall_disclosure_risk_score,
            "score_coverage_ratio": scores.score_coverage_ratio,
            "confidence_score": scores.confidence_score,
            "missing_components": scores.missing_components,
            "components": asdict(scores.components),
            "provenance": [p.to_dict() for p in scores.provenance],
            "scoring_model_version": SCORING_MODEL_VERSION,
        },
        indent=2,
    )


@mcp.tool()
def score_filing_html_tool(
    html: str,
    form_type: str,
    prior_html: str | None = None,
) -> str:
    """Run full deterministic pipeline on filing HTML (optional prior HTML for diffs)."""
    result = score_filing_html(html, form_type, prior_html=prior_html)
    return json.dumps(result.to_dict(), indent=2, default=str)


@mcp.tool()
def score_company_filing(
    ticker: str,
    fiscal_year: int,
    form_type: str = "10-K",
    quarter: str | None = None,
) -> str:
    """Score a company filing by ticker and fiscal year (10-K or 10-Q with quarter)."""
    from disclosure_alpha.pipeline import score_filing_ticker

    result = score_filing_ticker(
        ticker, fiscal_year, form_type=form_type, quarter=quarter
    )
    return json.dumps(result.to_dict(), indent=2, default=str)


@mcp.tool()
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


@mcp.resource("disclosure://taxonomy/v1")
def taxonomy() -> str:
    """Score taxonomy: component weights and version strings."""
    return json.dumps(
        {
            "parser_version": PARSER_VERSION,
            "metrics_engine_version": METRICS_ENGINE_VERSION,
            "scoring_model_version": SCORING_MODEL_VERSION,
            "component_weights": DETERMINISTIC_COMPONENT_WEIGHTS,
            "all_component_weights": COMPONENT_WEIGHTS,
        },
        indent=2,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
