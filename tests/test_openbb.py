"""OpenBB HTTP endpoint tests."""

from __future__ import annotations

import importlib
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from disclosure_alpha.api.app_factory import create_app
from disclosure_alpha.pipeline import FilingMetricsResult, score_filing_html
from disclosure_alpha.version import SCORING_MODEL_VERSION
from html_fixtures import minimal_10k_html

pytest.importorskip("fastapi")


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


def _minimal_metrics_result() -> FilingMetricsResult:
    html = minimal_10k_html()
    scored = score_filing_html(html, "10-K", cik="0000320193", accession_number="test")
    return FilingMetricsResult(
        metrics=scored.metrics,
        filing={
            "ticker": "AAPL",
            "cik": "0000320193",
            "accession_number": "0000320193-25-000079",
            "form_type": "10-K",
            "fiscal_year": 2025,
            "quarter": None,
        },
        versions={"scoring_model_version": SCORING_MODEL_VERSION},
    )


def test_widgets_json_company_only(client):
    resp = client.get("/widgets.json")
    assert resp.status_code == 200
    body = resp.json()
    assert list(body.keys()) == ["disclosure_company"]
    widget = body["disclosure_company"]
    assert widget["mcp_tool"]["mcp_server"] == "Disclosure Alpha Analyst"
    assert widget["mcp_tool"]["tool_id"] == "score_company_filing_tool"
    assert widget["subCategory"] == "SEC Filings"
    quarter = next(p for p in widget["params"] if p.get("paramName") == "quarter")
    assert quarter["label"] == "Quarter (10-Q only)"
    assert {o["value"] for o in quarter["options"]} == {"", "Q1", "Q2", "Q3"}


def test_apps_json_company_tab_only(client):
    resp = client.get("/apps.json")
    assert resp.status_code == 200
    apps = resp.json()
    assert isinstance(apps, list)
    assert apps[0]["name"] == "Disclosure Alpha"
    assert apps[0]["img"].startswith("https://")
    assert list(apps[0]["tabs"].keys()) == ["company"]
    layout = apps[0]["tabs"]["company"]["layout"]
    assert len(layout) == 1
    assert layout[0]["i"] == "disclosure_company"


def test_apps_json_has_prompts_and_mcp_servers(client):
    apps = client.get("/apps.json").json()
    assert len(apps[0]["prompts"]) >= 4
    assert apps[0]["mcp_servers"][0]["name"] == "Disclosure Alpha Analyst"


def test_apps_json_resolves_mcp_url(client):
    apps = client.get("/apps.json").json()
    url = apps[0]["mcp_servers"][0]["url"]
    assert url.endswith("/mcp")
    assert url.startswith("http")


def test_legacy_openbb_routes_removed(client):
    for path in (
        "/openbb/disclosure-score-card",
        "/openbb/panel-screener",
        "/openbb/active-flags",
        "/openbb/section-changes",
    ):
        assert client.get(path).status_code == 404


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Disclosure Alpha"
    assert body["widgets"] == "/widgets.json"
    assert body["agents"] == "/agents.json"


def test_openbb_private_network_access_preflight(client):
    resp = client.options(
        "/widgets.json",
        headers={
            "Origin": "https://pro.openbb.co",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Private-Network": "true",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-private-network") == "true"
    assert resp.headers.get("access-control-allow-origin") == "https://pro.openbb.co"


def test_openbb_discovery_stubs(client):
    for path in ("/agents.json", "/prompts.json", "/templates.json"):
        resp = client.get(path)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
    assert client.get("/agents.json").json() == {}
    prompts = client.get("/prompts.json").json()
    assert isinstance(prompts, list)
    assert len(prompts) >= 4
    assert client.get("/templates.json").json() == []


def test_prompts_json_non_empty(client):
    prompts = client.get("/prompts.json").json()
    assert all(isinstance(p, str) and p for p in prompts)


def test_openbb_mcp_mount_available(client):
    resp = client.get("/mcp")
    assert resp.status_code != 404


def test_openbb_mcp_cors_exposes_session_header(client):
    resp = client.get("/health", headers={"Origin": "https://pro.openbb.co"})
    assert resp.status_code == 200
    exposed = resp.headers.get("access-control-expose-headers", "")
    assert "mcp-session-id" in exposed.lower()


def test_openbb_validate_widgets_default_params(client):
    """Workspace 'Validate widgets' sends every widgets.json param."""
    resp = client.get(
        "/openbb/company",
        params={
            "ticker": "AAPL",
            "fiscal_year": 2025,
            "form_type": "10-K",
            "demo": "1",
        },
    )
    assert resp.status_code == 200
    assert "DEMO DATA" in resp.text


def test_company_probe_without_query_returns_demo(client):
    resp = client.get("/openbb/company")
    assert resp.status_code == 200
    assert "DEMO DATA" in resp.text
    assert 'data-marker="active-flags"' in resp.text


def test_company_demo_html(client):
    resp = client.get("/openbb/company", params={"demo": "1"})
    assert resp.status_code == 200
    text = resp.text
    assert "DEMO DATA" in text
    assert 'data-marker="active-flags"' in text
    assert 'data-marker="section-changes"' in text
    assert 'class="comp-row"' in text
    assert 'class="flag-summary"' in text
    assert 'class="flag-section"' in text
    assert 'class="company-panels"' in text
    assert "Item 1A Risk Factors" in text
    assert "Phrase-pattern hits" in text
    flags_section = text.split('data-marker="active-flags"')[1].split("section-changes")[0]
    assert 'class="data"' not in flags_section
    assert "item_1a_risk_factors" not in flags_section
    assert "Uncertainty language" in text
    assert ".hero-score" in text
    assert 'class="card"' in text
    assert "score_coverage_ratio" in text
    assert "Nine headline" in text or "NINE HEADLINE" in text.upper()
    assert "Powered by" in text
    assert 'href="https://disclosurealpha.com"' in text
    assert 'class="company-footer-brand"' in text
    assert "Not investment advice" not in text
    assert "Artifact versions" not in text
    assert "specificity_quality" not in text
    assert "Corpus median" not in text
    assert "S&amp;P 500" not in text and "S&P 500" not in text


def test_company_demo_uses_requested_ticker_label(client):
    resp = client.get("/openbb/company", params={"ticker": "AGG", "demo": "1"})
    assert resp.status_code == 200
    assert "AGG" in resp.text


def test_company_escapes_ticker_in_demo(client):
    resp = client.get("/openbb/company", params={"ticker": "<script>", "demo": "1"})
    assert resp.status_code == 200
    assert "<script>" not in resp.text


@patch("disclosure_alpha.openbb.router.metrics_filing_ticker")
def test_company_live_single_pipeline_call(mock_metrics, client):
    mock_metrics.return_value = _minimal_metrics_result()
    resp = client.get(
        "/openbb/company",
        params={"ticker": "AAPL", "fiscal_year": 2025, "form_type": "10-K"},
    )
    assert resp.status_code == 200
    assert mock_metrics.call_count == 1
    assert mock_metrics.call_args.kwargs.get("compare_prior") is True
    assert 'data-marker="active-flags"' in resp.text
    assert 'data-marker="section-changes"' in resp.text


@patch("disclosure_alpha.openbb.router.metrics_filing_ticker")
def test_company_404_html(mock_metrics, client):
    from disclosure_alpha.edgar.types import FilingNotFoundError

    mock_metrics.side_effect = FilingNotFoundError("No 10-K for BAD FY2025")
    resp = client.get(
        "/openbb/company",
        params={"ticker": "BAD", "fiscal_year": 2025},
    )
    assert resp.status_code == 404
    assert "text/html" in resp.headers["content-type"]


def test_company_10q_requires_quarter(client):
    resp = client.get(
        "/openbb/company",
        params={"ticker": "AAPL", "fiscal_year": 2025, "form_type": "10-Q"},
    )
    assert resp.status_code == 422
    assert "quarter is required" in resp.json()["detail"]


@patch("disclosure_alpha.openbb.router.metrics_filing_ticker")
def test_company_10q_passes_quarter(mock_metrics, client):
    mock_metrics.return_value = _minimal_metrics_result()
    resp = client.get(
        "/openbb/company",
        params={
            "ticker": "AAPL",
            "fiscal_year": 2025,
            "form_type": "10-Q",
            "quarter": "Q2",
        },
    )
    assert resp.status_code == 200
    assert mock_metrics.call_args.kwargs["form_type"] == "10-Q"
    assert mock_metrics.call_args.kwargs["quarter"] == "Q2"


def test_app_factory_defaults_embedding_backend_tfidf(monkeypatch):
    monkeypatch.delenv("EMBEDDING_BACKEND", raising=False)
    import disclosure_alpha.api.app_factory as app_factory

    importlib.reload(app_factory)
    assert os.environ.get("EMBEDDING_BACKEND") == "tfidf"


def test_tfidf_default_skips_sentence_transformers(monkeypatch):
    monkeypatch.setenv("EMBEDDING_BACKEND", "tfidf")
    import builtins

    from disclosure_alpha.embedding_service import _get_sentence_model

    _get_sentence_model.cache_clear()
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise AssertionError("sentence_transformers should not load")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=guarded_import):
        assert _get_sentence_model() is None
