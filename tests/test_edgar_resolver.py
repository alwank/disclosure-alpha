from __future__ import annotations

from unittest.mock import patch

import pytest

from disclosure_alpha.edgar.cache import write_cache
from disclosure_alpha.edgar.resolver import (
    _fiscal_year_match_tier,
    _fiscal_year_matches,
    _html_dei_score,
    _score_filing_row,
    list_filings,
    normalize_form_type,
)
from disclosure_alpha.edgar.types import FilingRef


def test_fiscal_year_tier_dei_exact():
    assert _fiscal_year_match_tier(2025, fiscal_year_html=2025, report_date=None) == 3


def test_fiscal_year_tier_report_date():
    assert _fiscal_year_match_tier(2025, fiscal_year_html=None, report_date="2025-12-31") == 2


def test_fiscal_year_tier_filing_date():
    assert (
        _fiscal_year_match_tier(
            2025,
            fiscal_year_html=None,
            report_date=None,
            filing_date="2025-02-15",
        )
        == 1
    )


def test_fiscal_year_matches_any_tier():
    assert _fiscal_year_matches(
        2025,
        fiscal_year_html=None,
        report_date=None,
        filing_date="2025-01-10",
    )


def test_score_filing_row_prefers_dei_over_filing_date():
    row = {"form": "10-K", "filingDate": "2025-03-01", "reportDate": "2024-12-31"}
    dei_score = _score_filing_row(
        row,
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        fiscal_year_html=2025,
        period_html="FY",
    )
    filing_score = _score_filing_row(
        row,
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        fiscal_year_html=None,
        period_html="FY",
    )
    assert dei_score is not None
    assert filing_score is not None
    assert dei_score > filing_score


def test_html_dei_score_when_metadata_mismatch():
    html = (
        '<span name="dei:DocumentFiscalYearFocus">2025</span>'
        '<span name="dei:DocumentFiscalPeriodFocus">FY</span>'
        "<p>Item 1A risk factors</p>"
    )
    row = {"form": "10-K", "filingDate": "2026-01-15", "reportDate": "2026-01-01"}
    score = _html_dei_score(
        row,
        html,
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
    )
    assert score is not None
    assert score >= 500_000_000


def test_normalize_form_type_rejects_8k():
    with pytest.raises(ValueError, match="Unsupported form_type"):
        normalize_form_type("8-K")


_HTML_10K = (
    '<span name="dei:DocumentFiscalYearFocus">2025</span>'
    '<span name="dei:DocumentFiscalPeriodFocus">FY</span>'
    "<p>Item 1A risk factors</p>"
)
_HTML_10Q = (
    '<span name="dei:DocumentFiscalYearFocus">2025</span>'
    '<span name="dei:DocumentFiscalPeriodFocus">Q1</span>'
    "<p>Item 2 financials</p>"
)


@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_list_filings_filters_form_and_year(mock_tickers, mock_submissions, tmp_path):
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = {
        "filings": {
            "recent": {
                "accessionNumber": ["acc-10k", "acc-8k", "acc-10q"],
                "form": ["10-K", "8-K", "10-Q"],
                "filingDate": ["2025-02-01", "2025-02-02", "2025-05-01"],
                "reportDate": ["2024-12-31", "2025-01-15", "2025-03-31"],
                "primaryDocument": ["a.htm", "b.htm", "c.htm"],
            }
        }
    }

    def fake_fetch_text(url: str) -> str:
        if "a.htm" in url:
            return _HTML_10K
        if "c.htm" in url:
            return _HTML_10Q
        raise AssertionError(f"unexpected fetch: {url}")

    with patch("disclosure_alpha.edgar.resolver.client.fetch_text", fake_fetch_text):
        filings = list_filings("AAPL", 2025, use_cache=False, cache_dir=tmp_path)

    assert {f.form_type for f in filings} == {"10-K", "10-Q"}
    assert all(f.fiscal_year == 2025 for f in filings)


@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_list_filings_uses_cache_without_fetch(mock_tickers, mock_submissions, tmp_path):
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = {
        "filings": {
            "recent": {
                "accessionNumber": ["acc-10k"],
                "form": ["10-K"],
                "filingDate": ["2025-02-01"],
                "reportDate": ["2024-12-31"],
                "primaryDocument": ["a.htm"],
            }
        }
    }
    ref = FilingRef(
        cik="0000320193",
        ticker="AAPL",
        accession_number="acc-10k",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-02-01",
        report_date="2024-12-31",
        primary_document="a.htm",
    )
    write_cache(tmp_path, ref, _HTML_10K)

    with patch("disclosure_alpha.edgar.resolver.client.fetch_text") as mock_fetch_text:
        filings = list_filings("AAPL", 2025, use_cache=True, cache_dir=tmp_path)

    mock_fetch_text.assert_not_called()
    assert len(filings) == 1
    assert filings[0].form_type == "10-K"
