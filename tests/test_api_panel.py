"""Panel batch API tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from disclosure_alpha.api.routes import app
from disclosure_alpha.pipeline import (
    PanelBatchResult,
    PanelTickerResult,
    score_filing_html,
)
from disclosure_alpha.version import SCORING_MODEL_VERSION, SCORING_MODEL_VERSION_V2

pytest.importorskip("fastapi")

client = TestClient(app)


def _ok_panel_result(ticker: str) -> PanelTickerResult:
    scored = score_filing_html(
        "<html><body><p>Item 1A. Risk Factors</p><p>Risk text.</p></body></html>",
        "10-K",
    )
    return PanelTickerResult(
        ticker=ticker,
        status="ok",
        filing={"ticker": ticker, "fiscal_year": 2025},
        scores=scored.scores,
    )


@patch("disclosure_alpha.api.endpoints.panel.score_panel_tickers")
def test_panel_mixed_results(mock_score):
    mock_score.return_value = PanelBatchResult(
        results=[
            _ok_panel_result("AAPL"),
            PanelTickerResult(ticker="BAD", status="error", error="No 10-K for BAD FY2025"),
        ],
        summary={"ok": 1, "failed": 1},
        versions={"scoring_model_version": SCORING_MODEL_VERSION},
    )
    resp = client.post(
        "/v1/panel/disclosure-matrix",
        json={
            "tickers": ["AAPL", "BAD"],
            "fiscal_year": 2025,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"] == {"ok": 1, "failed": 1}
    assert len(body["results"]) == 2
    assert body["results"][0]["status"] == "ok"
    assert body["results"][0]["scores"] is not None
    assert body["results"][1]["status"] == "error"
    assert body["results"][1]["error"]


def test_panel_max_tickers_guard():
    resp = client.post(
        "/v1/panel/disclosure-matrix",
        json={
            "tickers": [f"T{i}" for i in range(26)],
            "fiscal_year": 2025,
        },
    )
    assert resp.status_code == 422
    assert "25" in resp.json()["detail"]


@patch("disclosure_alpha.api.endpoints.panel.score_panel_tickers")
def test_panel_passes_compare(mock_score):
    mock_score.return_value = PanelBatchResult(
        results=[_ok_panel_result("AAPL")],
        summary={"ok": 1, "failed": 0},
        versions={"scoring_model_version": SCORING_MODEL_VERSION},
    )
    resp = client.post(
        "/v1/panel/disclosure-matrix",
        json={
            "tickers": ["AAPL"],
            "fiscal_year": 2025,
            "compare": "none",
        },
    )
    assert resp.status_code == 200
    mock_score.assert_called_once()
    assert mock_score.call_args.kwargs["compare_prior"] is False


@patch("disclosure_alpha.api.endpoints.panel.score_panel_tickers")
def test_panel_scoring_model_version_v2(mock_score):
    scored = score_filing_html(
        "<html><body><p>Item 1A. Risk Factors</p><p>Risk text.</p></body></html>",
        "10-K",
    )
    from disclosure_alpha.pipeline import score_deterministic_v2

    v2_scores = score_deterministic_v2(scored.metrics)
    mock_score.return_value = PanelBatchResult(
        results=[
            PanelTickerResult(
                ticker="AAPL",
                status="ok",
                filing={"ticker": "AAPL", "fiscal_year": 2025},
                scores=v2_scores,
            )
        ],
        summary={"ok": 1, "failed": 0},
        versions={"scoring_model_version": SCORING_MODEL_VERSION_V2},
    )
    resp = client.post(
        "/v1/panel/disclosure-matrix",
        json={
            "tickers": ["AAPL"],
            "fiscal_year": 2025,
            "scoring_model_version": "deterministic_scoring_v2",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["versions"]["scoring_model_version"] == SCORING_MODEL_VERSION_V2
    mock_score.assert_called_once()
    assert mock_score.call_args.kwargs["scoring_model_version"] == SCORING_MODEL_VERSION_V2


def test_panel_invalid_scoring_model_version():
    resp = client.post(
        "/v1/panel/disclosure-matrix",
        json={
            "tickers": ["AAPL"],
            "fiscal_year": 2025,
            "scoring_model_version": "deterministic_scoring_v3",
        },
    )
    assert resp.status_code == 422
