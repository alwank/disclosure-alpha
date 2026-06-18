from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from disclosure_alpha.api.routes import app
from disclosure_alpha.edgar.types import FilingRef
from disclosure_alpha.pipeline import (
    FilingMetricsResult,
    FilingSectionsResult,
    score_filing_html,
)

pytest.importorskip("fastapi")

client = TestClient(app)


def _minimal_html() -> str:
    return """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>We may face litigation and regulatory investigation.</p>
    <p>Item 7. Management's Discussion and Analysis</p>
    <p>Revenue may decline amid margin pressure.</p>
    </body></html>
    """


def _minimal_metrics_result() -> FilingMetricsResult:
    html = _minimal_html()
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
            "parser_version": "section_extractor_v1",
            "metrics_engine_version": "text_metrics_v1.2",
            "scoring_model_version": "deterministic_scoring_v2",
        },
    )


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@patch("disclosure_alpha.api.routes.metrics_filing_ticker")
@patch("disclosure_alpha.api.routes.score_deterministic")
def test_disclosure_matrix(mock_score, mock_metrics):
    mock_metrics.return_value = _minimal_metrics_result()
    mock_score.return_value = score_filing_html(_minimal_html(), "10-K").scores
    resp = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "form_type": "10-K", "view": "deterministic"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["view"] == "deterministic"
    assert body["filing"]["ticker"] == "AAPL"
    assert "scores" in body
    assert "metrics" in body
    mock_score.assert_called_once()


@patch("disclosure_alpha.api.routes.metrics_filing_ticker")
@patch("disclosure_alpha.api.routes.score_deterministic")
def test_disclosure_metrics_skips_scoring(mock_score, mock_metrics):
    mock_metrics.return_value = _minimal_metrics_result()
    resp = client.get(
        "/v1/company/AAPL/disclosure-metrics",
        params={"fiscal_year": 2025},
    )
    assert resp.status_code == 200
    assert "metrics" in resp.json()
    mock_score.assert_not_called()


@patch("disclosure_alpha.api.routes.sections_filing_ticker")
def test_company_sections(mock_sections):
    html = _minimal_html()
    from disclosure_alpha.pipeline import extract_sections_from_html

    sections = extract_sections_from_html(html, "10-K")
    mock_sections.return_value = FilingSectionsResult(
        sections=sections,
        filing=_minimal_metrics_result().filing,
        versions=_minimal_metrics_result().versions,
    )
    resp = client.get(
        "/v1/company/AAPL/sections",
        params={"fiscal_year": 2025, "form_type": "10-K"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "sections" in body
    assert body["sections"][0]["section_name"]
    assert "cleaned_text" not in body["sections"][0]


@patch("disclosure_alpha.api.routes.sections_filing_ticker")
def test_company_sections_include_text(mock_sections):
    from disclosure_alpha.pipeline import extract_sections_from_html

    sections = extract_sections_from_html(_minimal_html(), "10-K")
    mock_sections.return_value = FilingSectionsResult(
        sections=sections,
        filing=_minimal_metrics_result().filing,
        versions=_minimal_metrics_result().versions,
    )
    resp = client.get(
        "/v1/company/AAPL/sections",
        params={"fiscal_year": 2025, "include_text": True},
    )
    assert resp.status_code == 200
    assert "cleaned_text" in resp.json()["sections"][0]


@patch("disclosure_alpha.api.routes.metrics_filing_ticker")
@patch("disclosure_alpha.api.routes.score_deterministic")
def test_disclosure_matrix_slim_include(mock_score, mock_metrics):
    mock_metrics.return_value = _minimal_metrics_result()
    mock_score.return_value = score_filing_html(_minimal_html(), "10-K").scores
    resp = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "include": ""},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["metrics"] is None
    assert "provenance" not in body["scores"]


@patch("disclosure_alpha.api.routes.metrics_filing_ticker")
@patch("disclosure_alpha.api.routes.score_deterministic")
def test_disclosure_matrix_fields(mock_score, mock_metrics):
    mock_metrics.return_value = _minimal_metrics_result()
    mock_score.return_value = score_filing_html(_minimal_html(), "10-K").scores
    resp = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "fields": "overall,components"},
    )
    assert resp.status_code == 200
    scores = resp.json()["scores"]
    assert "overall_disclosure_risk_score" in scores
    assert "components" in scores
    assert "provenance" not in scores


@patch("disclosure_alpha.api.routes.metrics_filing_ticker")
def test_disclosure_metrics_compare_none(mock_metrics):
    mock_metrics.return_value = _minimal_metrics_result()
    resp = client.get(
        "/v1/company/AAPL/disclosure-metrics",
        params={"fiscal_year": 2025, "compare": "none"},
    )
    assert resp.status_code == 200
    mock_metrics.assert_called_once()
    assert mock_metrics.call_args.kwargs["compare_prior"] is False


def test_invalid_sections_param():
    resp = client.get(
        "/v1/company/AAPL/disclosure-metrics",
        params={"fiscal_year": 2025, "sections": "not_a_section"},
    )
    assert resp.status_code == 422


def test_10q_requires_quarter():
    resp = client.get(
        "/v1/company/AAPL/disclosure-matrix",
        params={"fiscal_year": 2025, "form_type": "10-Q"},
    )
    assert resp.status_code == 422


@patch("disclosure_alpha.api.routes.list_filings")
def test_company_filings(mock_list):
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
    resp = client.get("/v1/company/AAPL/filings", params={"fiscal_year": 2025})
    assert resp.status_code == 200
    assert len(resp.json()["filings"]) == 1
