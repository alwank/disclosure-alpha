"""MCP tool smoke tests — call tool functions directly, no MCP process."""

from __future__ import annotations

import json
from dataclasses import asdict
from unittest.mock import patch

import pytest

pytest.importorskip("mcp")

from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS
from disclosure_alpha.mcp.tools import (
    compute_section_metrics_tool,
    diff_sections,
    extract_sections,
    list_company_filings,
    score_company_filing,
    score_deterministic_tool,
    score_filing_html_tool,
    taxonomy_payload,
)
from disclosure_alpha.pipeline import extract_sections_from_html, score_filing_html
from disclosure_alpha.version import PARSER_VERSION, SCORING_MODEL_VERSION, SCORING_MODEL_VERSION_V2
from html_fixtures import minimal_10k_html, minimal_prior_html


def _sections_json(html: str) -> str:
    sections = extract_sections_from_html(html, "10-K")
    return json.dumps([asdict(s) for s in sections])


def test_mcp_extract_sections():
    payload = json.loads(extract_sections(minimal_10k_html(), "10-K"))
    assert payload["parser_version"] == PARSER_VERSION
    assert payload["sections"]
    assert payload["sections"][0]["section_name"]


def test_mcp_compute_section_metrics_tool():
    metrics = json.loads(
        compute_section_metrics_tool(
            _sections_json(minimal_10k_html()),
            _sections_json(minimal_prior_html()),
        )
    )
    assert "section_metrics" in metrics
    assert "section_diffs" in metrics


def test_mcp_diff_sections():
    payload = json.loads(
        diff_sections(
            "We may face litigation and regulatory investigation.",
            "Stable operations continue.",
            "item_1a_risk_factors",
        )
    )
    assert isinstance(payload["disclosure_change_score"], float)


def test_mcp_score_deterministic_tool():
    metrics = json.loads(
        compute_section_metrics_tool(_sections_json(minimal_10k_html()))
    )
    payload = json.loads(score_deterministic_tool(json.dumps(metrics)))
    assert payload["overall_disclosure_risk_score"] is not None
    assert "aggregates" in payload
    assert payload["scoring_model_version"] == SCORING_MODEL_VERSION


def test_mcp_score_deterministic_tool_v2():
    metrics = json.loads(
        compute_section_metrics_tool(_sections_json(minimal_10k_html()))
    )
    payload = json.loads(
        score_deterministic_tool(
            json.dumps(metrics),
            scoring_model_version="deterministic_scoring_v2",
        )
    )
    assert payload["scoring_model_version"] == SCORING_MODEL_VERSION_V2
    assert payload["aggregates"]["static_disclosure_risk_score"] is not None


def test_mcp_score_filing_html_tool_v2():
    payload = json.loads(
        score_filing_html_tool(
            minimal_10k_html(),
            "10-K",
            scoring_model_version="deterministic_scoring_v2",
        )
    )
    assert payload["versions"]["scoring_model_version"] == SCORING_MODEL_VERSION_V2


def test_mcp_score_deterministic_tool_invalid_version():
    metrics = json.loads(
        compute_section_metrics_tool(_sections_json(minimal_10k_html()))
    )
    with pytest.raises(ValueError, match="unsupported scoring version"):
        score_deterministic_tool(
            json.dumps(metrics),
            scoring_model_version="deterministic_scoring_v3",
        )


def test_mcp_score_filing_html_tool():
    payload = json.loads(score_filing_html_tool(minimal_10k_html(), "10-K"))
    assert "scores" in payload
    assert "metrics" in payload
    assert "versions" in payload


@patch("disclosure_alpha.mcp.tools.score_for_model")
@patch("disclosure_alpha.mcp.tools.score_filing_html")
def test_mcp_score_filing_html_tool_10q_passes_form_type(mock_score_html, mock_score_model):
    scored = score_filing_html(minimal_10k_html(), "10-K")
    mock_score_html.return_value = scored
    mock_score_model.return_value = scored.scores
    score_filing_html_tool(minimal_10k_html(), "10-Q")
    mock_score_model.assert_called_once()
    assert mock_score_model.call_args.kwargs["form_type"] == "10-Q"


@patch("disclosure_alpha.pipeline.score_filing_ticker")
def test_mcp_score_company_filing(mock_score):
    scored = score_filing_html(minimal_10k_html(), "10-K")
    scored.filing = {"ticker": "AAPL"}
    mock_score.return_value = scored
    payload = json.loads(score_company_filing("AAPL", 2025))
    assert payload["filing"]["ticker"] == "AAPL"


@patch("disclosure_alpha.edgar.resolver.list_filings")
def test_mcp_list_company_filings(mock_list):
    from disclosure_alpha.edgar.types import FilingRef

    mock_list.return_value = [
        FilingRef(
            cik="0000320193",
            ticker="AAPL",
            accession_number="0000320193-25-000079",
            form_type="10-K",
            fiscal_year=2025,
            quarter=None,
            filing_date="2025-10-31",
            report_date="2025-09-27",
            primary_document="aapl.htm",
        )
    ]
    payload = json.loads(list_company_filings("AAPL", 2025))
    assert payload[0]["ticker"] == "AAPL"
    assert payload[0]["accession_number"]


def test_mcp_taxonomy_resource():
    payload = json.loads(taxonomy_payload())
    assert set(payload["component_weights"]) == set(COMPONENT_WEIGHTS)
    assert payload["analytics_config_id"] == "builtin_default"
