from __future__ import annotations

from unittest.mock import patch

import pytest

from disclosure_alpha.edgar.cache import write_cache
from disclosure_alpha.edgar.resolver import (
    FilingTarget,
    _fiscal_year_match_tier,
    _fiscal_year_matches,
    _html_dei_score,
    _score_filing_row,
    list_filings,
    normalize_form_type,
    resolve_filing,
    resolve_filing_targets,
    resolve_filing_with_prior,
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


def _submissions_10k_rows(*rows: dict[str, str]) -> dict:
    return {
        "filings": {
            "recent": {
                "accessionNumber": [r["accessionNumber"] for r in rows],
                "form": [r["form"] for r in rows],
                "filingDate": [r["filingDate"] for r in rows],
                "reportDate": [r["reportDate"] for r in rows],
                "primaryDocument": [r["primaryDocument"] for r in rows],
            }
        }
    }


@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_resolve_filing_targets_single_submissions_fetch(mock_tickers, mock_submissions):
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = _submissions_10k_rows(
        {
            "accessionNumber": "acc-2025",
            "form": "10-K",
            "filingDate": "2025-10-31",
            "reportDate": "2025-09-27",
            "primaryDocument": "a.htm",
        },
        {
            "accessionNumber": "acc-2024",
            "form": "10-K",
            "filingDate": "2024-10-31",
            "reportDate": "2024-09-27",
            "primaryDocument": "b.htm",
        },
    )

    resolved = resolve_filing_targets(
        "AAPL",
        [FilingTarget(2025, "10-K"), FilingTarget(2024, "10-K")],
        use_cache=False,
    )

    assert mock_submissions.call_count == 1
    assert resolved[FilingTarget(2025, "10-K")].accession_number == "acc-2025"
    assert resolved[FilingTarget(2024, "10-K")].accession_number == "acc-2024"


@patch("disclosure_alpha.edgar.resolver.client.fetch_text_prefix")
@patch("disclosure_alpha.edgar.resolver.client.fetch_text")
@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_metadata_first_skips_probe_downloads(
    mock_tickers, mock_submissions, mock_fetch_text, mock_fetch_prefix
):
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = _submissions_10k_rows(
        {
            "accessionNumber": "acc-noise-2024",
            "form": "10-K",
            "filingDate": "2024-06-01",
            "reportDate": "2024-05-31",
            "primaryDocument": "noise.htm",
        },
        {
            "accessionNumber": "acc-2025",
            "form": "10-K",
            "filingDate": "2025-02-01",
            "reportDate": "2024-12-31",
            "primaryDocument": "winner.htm",
        },
    )

    resolved = resolve_filing_targets(
        "AAPL",
        [FilingTarget(2025, "10-K")],
        use_cache=False,
    )

    mock_fetch_text.assert_not_called()
    mock_fetch_prefix.assert_not_called()
    assert resolved[FilingTarget(2025, "10-K")].accession_number == "acc-2025"


@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_resolve_filing_with_prior_single_submissions_fetch(mock_tickers, mock_submissions):
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = _submissions_10k_rows(
        {
            "accessionNumber": "acc-2025",
            "form": "10-K",
            "filingDate": "2025-10-31",
            "reportDate": "2025-09-27",
            "primaryDocument": "a.htm",
        },
        {
            "accessionNumber": "acc-2024",
            "form": "10-K",
            "filingDate": "2024-10-31",
            "reportDate": "2024-09-27",
            "primaryDocument": "b.htm",
        },
    )

    current, prior = resolve_filing_with_prior("AAPL", 2025, "10-K", compare_prior=True, use_cache=False)

    assert mock_submissions.call_count == 1
    assert current.accession_number == "acc-2025"
    assert prior is not None
    assert prior.accession_number == "acc-2024"


@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_resolve_filing_targets_prior_10q_chain(mock_tickers, mock_submissions, tmp_path):
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = {
        "filings": {
            "recent": {
                "accessionNumber": ["acc-q1", "acc-prior-q3"],
                "form": ["10-Q", "10-Q"],
                "filingDate": ["2025-05-01", "2024-11-01"],
                "reportDate": ["2025-03-31", "2024-09-30"],
                "primaryDocument": ["q1.htm", "q3.htm"],
            }
        }
    }
    cik = "0000320193"
    write_cache(
        tmp_path,
        FilingRef(
            cik=cik,
            ticker="AAPL",
            accession_number="acc-q1",
            form_type="10-Q",
            fiscal_year=2025,
            quarter="Q1",
            filing_date="2025-05-01",
            report_date="2025-03-31",
            primary_document="q1.htm",
        ),
        _HTML_10Q,
    )
    write_cache(
        tmp_path,
        FilingRef(
            cik=cik,
            ticker="AAPL",
            accession_number="acc-prior-q3",
            form_type="10-Q",
            fiscal_year=2024,
            quarter="Q3",
            filing_date="2024-11-01",
            report_date="2024-09-30",
            primary_document="q3.htm",
        ),
        _HTML_10Q.replace("Q1", "Q3"),
    )

    resolved = resolve_filing_targets(
        "AAPL",
        [FilingTarget(2025, "10-Q", "Q1"), FilingTarget(2024, "10-Q", "Q3")],
        use_cache=True,
        cache_dir=tmp_path,
    )

    assert resolved[FilingTarget(2025, "10-Q", "Q1")].accession_number == "acc-q1"
    assert resolved[FilingTarget(2024, "10-Q", "Q3")].accession_number == "acc-prior-q3"


@patch("disclosure_alpha.edgar.resolver.client.fetch_text_prefix")
@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_disambiguation_prefers_year_near_target(mock_tickers, mock_submissions, mock_fetch_prefix):
    """10-Q quarter lives in DEI tags; cap of 3 HTML fetches must try FY-near rows first."""
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = {
        "filings": {
            "recent": {
                "accessionNumber": [
                    "acc-new-1",
                    "acc-new-2",
                    "acc-new-3",
                    "acc-q2",
                    "acc-q3",
                ],
                "form": ["10-Q"] * 5,
                "filingDate": [
                    "2026-01-30",
                    "2025-08-01",
                    "2025-05-02",
                    "2024-05-03",
                    "2024-08-02",
                ],
                "reportDate": [
                    "2025-12-27",
                    "2025-06-28",
                    "2025-03-29",
                    "2024-03-30",
                    "2024-06-29",
                ],
                "primaryDocument": ["n1.htm", "n2.htm", "n3.htm", "q2.htm", "q3.htm"],
            }
        }
    }

    def fake_prefix(url: str, max_bytes: int = 131_072) -> str:
        if "q3.htm" in url:
            return (
                '<span name="dei:DocumentFiscalYearFocus">2024</span>'
                '<span name="dei:DocumentFiscalPeriodFocus">Q3</span>'
            )
        return (
            '<span name="dei:DocumentFiscalYearFocus">2025</span>'
            '<span name="dei:DocumentFiscalPeriodFocus">Q2</span>'
        )

    mock_fetch_prefix.side_effect = fake_prefix

    ref = resolve_filing("AAPL", 2024, "10-Q", "Q3", use_cache=False)

    assert ref.accession_number == "acc-q3"
    assert mock_fetch_prefix.call_count <= 3


@patch("disclosure_alpha.edgar.resolver.client.fetch_text_prefix")
@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_resolve_fy2025_q1_with_prior_chain(mock_tickers, mock_submissions, mock_fetch_prefix):
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = {
        "filings": {
            "recent": {
                "accessionNumber": [
                    "acc-new-1",
                    "acc-new-2",
                    "acc-new-3",
                    "acc-q1",
                    "acc-q3",
                ],
                "form": ["10-Q"] * 5,
                "filingDate": [
                    "2026-01-30",
                    "2025-08-01",
                    "2025-05-02",
                    "2025-01-31",
                    "2024-08-02",
                ],
                "reportDate": [
                    "2025-12-27",
                    "2025-06-28",
                    "2025-03-29",
                    "2024-12-28",
                    "2024-06-29",
                ],
                "primaryDocument": ["n1.htm", "n2.htm", "n3.htm", "q1.htm", "q3.htm"],
            }
        }
    }

    def fake_prefix(url: str, max_bytes: int = 131_072) -> str:
        if "q1.htm" in url:
            return (
                '<span name="dei:DocumentFiscalYearFocus">2025</span>'
                '<span name="dei:DocumentFiscalPeriodFocus">Q1</span>'
            )
        if "q3.htm" in url:
            return (
                '<span name="dei:DocumentFiscalYearFocus">2024</span>'
                '<span name="dei:DocumentFiscalPeriodFocus">Q3</span>'
            )
        return (
            '<span name="dei:DocumentFiscalYearFocus">2025</span>'
            '<span name="dei:DocumentFiscalPeriodFocus">Q2</span>'
        )

    mock_fetch_prefix.side_effect = fake_prefix

    current, prior = resolve_filing_with_prior(
        "AAPL",
        2025,
        "10-Q",
        "Q1",
        compare_prior=True,
        use_cache=False,
    )

    assert current.accession_number == "acc-q1"
    assert prior is not None
    assert prior.accession_number == "acc-q3"


@patch("disclosure_alpha.edgar.resolver.client.fetch_text_prefix")
@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_disambiguation_fetches_only_tied_candidates(
    mock_tickers, mock_submissions, mock_fetch_prefix
):
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = _submissions_10k_rows(
        {
            "accessionNumber": "acc-a",
            "form": "10-K",
            "filingDate": "2025-02-01",
            "reportDate": "2024-12-31",
            "primaryDocument": "a.htm",
        },
        {
            "accessionNumber": "acc-b",
            "form": "10-K",
            "filingDate": "2025-02-01",
            "reportDate": "2024-12-31",
            "primaryDocument": "b.htm",
        },
    )

    def fake_prefix(url: str, max_bytes: int = 131_072) -> str:
        if "a.htm" in url:
            return (
                '<span name="dei:DocumentFiscalYearFocus">2025</span>'
                '<span name="dei:DocumentFiscalPeriodFocus">FY</span>'
            )
        return (
            '<span name="dei:DocumentFiscalYearFocus">2024</span>'
            '<span name="dei:DocumentFiscalPeriodFocus">FY</span>'
        )

    mock_fetch_prefix.side_effect = fake_prefix

    resolved = resolve_filing_targets(
        "AAPL",
        [FilingTarget(2025, "10-K")],
        use_cache=False,
    )

    assert mock_fetch_prefix.call_count <= 3
    assert resolved[FilingTarget(2025, "10-K")].accession_number == "acc-a"


@patch("disclosure_alpha.edgar.resolver.client.fetch_submissions")
@patch("disclosure_alpha.edgar.resolver.client.fetch_company_tickers")
def test_resolve_filing_backward_compat(mock_tickers, mock_submissions):
    mock_tickers.return_value = {"AAPL": ("0000320193", "Apple Inc.")}
    mock_submissions.return_value = _submissions_10k_rows(
        {
            "accessionNumber": "acc-2025",
            "form": "10-K",
            "filingDate": "2025-02-01",
            "reportDate": "2024-12-31",
            "primaryDocument": "a.htm",
        },
    )

    ref = resolve_filing("AAPL", 2025, "10-K", use_cache=False)

    assert ref.accession_number == "acc-2025"
    assert ref.fiscal_year == 2025
