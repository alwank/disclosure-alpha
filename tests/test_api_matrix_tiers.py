"""Matrix tier preset tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from disclosure_alpha.api.routes import app
from disclosure_alpha.pipeline import FilingMetricsResult, MetricsResult, score_filing_html
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


def _dual_section_metrics_result() -> FilingMetricsResult:
    """Metrics with both Item 1A and MD&A so section filter changes scores."""
    metrics = MetricsResult(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.1,
                "uncertainty_word_ratio": 0.1,
                "litigious_word_ratio": 0.05,
                "boilerplate_phrase_ratio": 0.1,
                "numeric_specificity_score": 20,
                "company_specificity_score": 30,
                "constraining_word_ratio": 0.02,
            },
            "item_7_mdna": {
                "uncertainty_word_ratio": 0.08,
                "modal_word_ratio": 0.05,
                "readability_score": 40,
                "constraining_word_ratio": 0.02,
            },
        },
        section_diffs={"item_1a_risk_factors": 55, "item_7_mdna": 45},
        section_flags={},
        section_densities={
            "item_7_mdna": {"liquidity_constraint_density": 3.0},
        },
        language_deltas={},
        extraction_confs=[0.9, 0.85],
        diff_confs=[0.8, 0.75],
    )
    return FilingMetricsResult(
        metrics=metrics,
        filing={"ticker": "AAPL", "fiscal_year": 2025},
        versions={"scoring_model_version": SCORING_MODEL_VERSION},
    )


@patch("disclosure_alpha.api.endpoints.matrix.metrics_filing_ticker")
def test_matrix_sections_filter_scores_from_filtered_metrics(mock_metrics):
    mock_metrics.return_value = _dual_section_metrics_result()
    full = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "tier": "standard"},
    )
    filtered = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={
            "fiscal_year": 2025,
            "tier": "standard",
            "sections": "item_1a_risk_factors",
        },
    )
    assert full.status_code == 200
    assert filtered.status_code == 200
    full_body = full.json()
    filtered_body = filtered.json()
    assert set(full_body["metrics"]["section_metrics"]) == {
        "item_1a_risk_factors",
        "item_7_mdna",
    }
    assert set(filtered_body["metrics"]["section_metrics"]) == {"item_1a_risk_factors"}
    full_components = full_body["scores"]["components"]
    filtered_components = filtered_body["scores"]["components"]
    assert full_components["mdna_uncertainty_score"] is not None
    assert filtered_components["mdna_uncertainty_score"] is None
    assert full_components["liquidity_stress_score"] is not None
    assert filtered_components["liquidity_stress_score"] is None
    assert (
        filtered_components["risk_factor_intensity_score"]
        == full_components["risk_factor_intensity_score"]
    )


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
