"""Disclosure changes API tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from disclosure_alpha.api.routes import app
from disclosure_alpha.pipeline import FilingMetricsResult, score_filing_html
from disclosure_alpha.version import (
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)
from html_fixtures import minimal_10k_html, minimal_prior_html

pytest.importorskip("fastapi")

client = TestClient(app)


def _metrics_with_prior() -> FilingMetricsResult:
    html = minimal_10k_html()
    prior = minimal_prior_html()
    metrics = score_filing_html(
        html,
        "10-K",
        prior_html=prior,
        cik="0000320193",
        accession_number="test",
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
            "prior_accession_number": "0000320193-24-000001",
        },
        versions={
            "parser_version": PARSER_VERSION,
            "metrics_engine_version": METRICS_ENGINE_VERSION,
            "scoring_model_version": SCORING_MODEL_VERSION,
        },
    )


def _metrics_no_prior() -> FilingMetricsResult:
    html = minimal_10k_html()
    metrics = score_filing_html(html, "10-K", cik="0000320193", accession_number="test").metrics
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


@patch("disclosure_alpha.api.endpoints.changes.score_for_model")
@patch("disclosure_alpha.api.endpoints.changes.metrics_filing_ticker")
def test_disclosure_changes_with_prior(mock_metrics, mock_score):
    result = _metrics_with_prior()
    mock_metrics.return_value = result
    scored = score_filing_html(minimal_10k_html(), "10-K", prior_html=minimal_prior_html())
    mock_score.return_value = scored.scores
    resp = client.get(
        "/v1/company/AAPL/disclosure-changes",
        params={"fiscal_year": 2025, "compare": "prior"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "section_diffs" in body
    assert "language_deltas" in body
    change_score = body["change_score"]
    assert change_score["value"] is not None or change_score["missing_reason"] is not None
    assert "scores" not in body
    mock_score.assert_called_once()


@patch("disclosure_alpha.api.endpoints.changes.metrics_filing_ticker")
def test_disclosure_changes_compare_none(mock_metrics):
    mock_metrics.return_value = _metrics_no_prior()
    resp = client.get(
        "/v1/company/AAPL/disclosure-changes",
        params={"fiscal_year": 2025, "compare": "none"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["change_score"]["value"] is None
    assert body["change_score"]["missing_reason"] == "compare=none"


@patch("disclosure_alpha.api.endpoints.changes.score_for_model")
@patch("disclosure_alpha.api.endpoints.changes.metrics_filing_ticker")
def test_disclosure_changes_null_change_score(mock_metrics, mock_score):
    mock_metrics.return_value = _metrics_no_prior()
    scored = score_filing_html(minimal_10k_html(), "10-K")
    mock_score.return_value = scored.scores
    resp = client.get(
        "/v1/company/AAPL/disclosure-changes",
        params={"fiscal_year": 2025, "compare": "prior"},
    )
    assert resp.status_code == 200
    assert resp.json()["change_score"]["missing_reason"] == "no prior filing comparison available"
