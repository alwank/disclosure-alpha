"""Composite/full matrix view and tier preset tests — Track D owns implementation."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from disclosure_alpha.api.routes import app
from disclosure_alpha.pipeline import FilingMetricsResult, score_filing_html
from disclosure_alpha.version import SCORING_MODEL_VERSION
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
        filing={"ticker": "AAPL", "fiscal_year": 2025},
        versions={"scoring_model_version": SCORING_MODEL_VERSION},
    )


def test_composite_view_returns_402_unsupported():
    resp = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "view": "composite"},
    )
    assert resp.status_code == 402
    body = resp.json()
    assert body["available_views"] == ["deterministic"]
    assert body["scoring_model_version"] == SCORING_MODEL_VERSION
    assert "composite" in body["detail"]
    assert "open-source" in body["detail"]
    assert "Pro" not in body["detail"]


def test_full_view_returns_402_unsupported():
    resp = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "view": "full"},
    )
    assert resp.status_code == 402
    body = resp.json()
    assert body["available_views"] == ["deterministic"]
    assert "open-source" in body["detail"]
    assert "Pro" not in body["detail"]


@patch("disclosure_alpha.api.endpoints.matrix.metrics_filing_ticker")
@patch("disclosure_alpha.api.endpoints.matrix.score_deterministic")
def test_tier_lite_slims_response(mock_score, mock_metrics):
    mock_metrics.return_value = _minimal_metrics_result()
    mock_score.return_value = score_filing_html(minimal_10k_html(), "10-K").scores
    resp = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "tier": "lite"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["metrics"] is None
    scores = body["scores"]
    assert set(scores) == {"overall_disclosure_risk_score"}
    assert "provenance" not in scores
    assert "components" not in scores


@patch("disclosure_alpha.api.endpoints.matrix.metrics_filing_ticker")
@patch("disclosure_alpha.api.endpoints.matrix.score_deterministic")
def test_tier_standard_includes_metrics_and_components(mock_score, mock_metrics):
    mock_metrics.return_value = _minimal_metrics_result()
    mock_score.return_value = score_filing_html(minimal_10k_html(), "10-K").scores
    resp = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "tier": "standard"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["metrics"] is not None
    scores = body["scores"]
    assert "overall_disclosure_risk_score" in scores
    assert "components" in scores
    assert "provenance" not in scores


def test_invalid_tier_param():
    resp = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "tier": "enterprise"},
    )
    assert resp.status_code == 422
