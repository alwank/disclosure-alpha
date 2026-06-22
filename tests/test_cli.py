"""CLI entry-point smoke tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from html_fixtures import minimal_10k_html, minimal_prior_html, write_temp_html

from disclosure_alpha.version import PARSER_VERSION


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "disclosure_alpha.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_extract(tmp_path: Path):
    html_path = write_temp_html(tmp_path, minimal_10k_html())
    result = _run_cli("extract", "--html", str(html_path), "--form", "10-K")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert payload[0]["section_name"]
    assert payload[0]["parser_version"] == PARSER_VERSION


def test_cli_metrics_with_prior(tmp_path: Path):
    current = write_temp_html(tmp_path, minimal_10k_html(), "current.html")
    prior = write_temp_html(tmp_path, minimal_prior_html(), "prior.html")
    result = _run_cli(
        "metrics",
        "--html",
        str(current),
        "--form",
        "10-K",
        "--prior-html",
        str(prior),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "section_metrics" in payload
    assert "section_diffs" in payload


def test_cli_score_html(tmp_path: Path):
    html_path = write_temp_html(tmp_path, minimal_10k_html())
    result = _run_cli("score", "--html", str(html_path), "--form", "10-K")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["scores"]["overall_disclosure_risk_score"] is not None


def test_cli_score_ticker_requires_fiscal_year():
    result = _run_cli("score", "--ticker", "AAPL", "--form", "10-K")
    assert result.returncode != 0


def test_cli_score_ticker_rejects_unsupported_form():
    result = _run_cli(
        "score", "--ticker", "AAPL", "--fiscal-year", "2025", "--form", "8-K"
    )
    assert result.returncode != 0
    assert "Unsupported form_type" in result.stderr


def test_cli_extract_bad_html_path():
    result = _run_cli("extract", "--html", "/nonexistent/filing.html", "--form", "10-K")
    assert result.returncode != 0
    assert "No such file or directory" in result.stderr


def test_cli_score_html_stdin():
    result = subprocess.run(
        [sys.executable, "-m", "disclosure_alpha.cli", "score", "--html", "-", "--form", "10-K"],
        input=minimal_10k_html(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "scores" in payload


def test_cli_score_ticker_mocked(monkeypatch, capsys):
    from disclosure_alpha.pipeline import score_filing_html

    scored = score_filing_html(minimal_10k_html(), "10-K")
    scored.filing = {"ticker": "AAPL", "fiscal_year": 2025}

    monkeypatch.setattr(
        "disclosure_alpha.cli.score_filing_ticker",
        lambda *a, **k: scored,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["disclosure-alpha", "score", "--ticker", "AAPL", "--fiscal-year", "2025"],
    )

    from disclosure_alpha.cli import main

    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["filing"]["ticker"] == "AAPL"
