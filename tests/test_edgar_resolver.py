from __future__ import annotations

from disclosure_alpha.edgar.resolver import (
    _fiscal_year_match_tier,
    _fiscal_year_matches,
    _html_dei_score,
    _score_filing_row,
)


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
