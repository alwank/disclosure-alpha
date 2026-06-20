"""Disclosure flags API tests — Track A owns implementation."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from disclosure_alpha.api.routes import app
from disclosure_alpha.edgar.types import FilingNotFoundError
from disclosure_alpha.pipeline import FilingMetricsResult, score_filing_html
from disclosure_alpha.version import (
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)
from html_fixtures import minimal_10k_html

pytest.importorskip("fastapi")

client = TestClient(app)


def _minimal_metrics_result() -> FilingMetricsResult:
    html = minimal_10k_html()
    metrics = score_filing_html(
        html, "10-K", cik="0000320193", accession_number="test"
    ).metrics
    return FilingMetricsResult(
        metrics=metrics,
        filing={
            "ticker": "AAPL",
            "cik": "0000320193",
            "accession_number": "0000320193-25-000079",
            "form_type": "10-K",
            "fiscal_year": 2025,
            "quarter": None,
            "filing_date": "2025-10-31",
            "report_date": "2025-09-27",
            "prior_accession_number": None,
        },
        versions={
            "parser_version": PARSER_VERSION,
            "metrics_engine_version": METRICS_ENGINE_VERSION,
            "scoring_model_version": SCORING_MODEL_VERSION,
        },
    )


@patch("disclosure_alpha.api.endpoints.flags.metrics_filing_ticker")
def test_disclosure_flags_surfaces_investigation_flag(mock_metrics):
    mock_metrics.return_value = _minimal_metrics_result()
    resp = client.get(
        "/v1/company/AAPL/disclosure-flags",
        params={"fiscal_year": 2025, "form_type": "10-K"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["filing"]["ticker"] == "AAPL"
    assert "flags" in body
    assert "active_flags" in body
    item_1a = body["flags"]["item_1a_risk_factors"]
    assert item_1a["investigation_flag"] is True
    active = {(f["section"], f["flag"]) for f in body["active_flags"]}
    assert ("item_1a_risk_factors", "investigation_flag") in active
    assert "section_metrics" not in body
    assert "scores" not in body


@patch("disclosure_alpha.api.endpoints.flags.metrics_filing_ticker")
def test_disclosure_flags_sections_filter(mock_metrics):
    mock_metrics.return_value = _minimal_metrics_result()
    resp = client.get(
        "/v1/company/AAPL/disclosure-flags",
        params={"fiscal_year": 2025, "sections": "item_1a_risk_factors"},
    )
    assert resp.status_code == 200
    assert set(resp.json()["flags"]) == {"item_1a_risk_factors"}


@patch("disclosure_alpha.api.endpoints.flags.metrics_filing_ticker")
def test_disclosure_flags_not_found(mock_metrics):
    mock_metrics.side_effect = FilingNotFoundError("No 10-K for AAPL FY2025")
    resp = client.get(
        "/v1/company/AAPL/disclosure-flags",
        params={"fiscal_year": 2025},
    )
    assert resp.status_code == 404


def test_disclosure_flags_invalid_sections():
    resp = client.get(
        "/v1/company/AAPL/disclosure-flags",
        params={"fiscal_year": 2025, "sections": "not_a_section"},
    )
    assert resp.status_code == 422
