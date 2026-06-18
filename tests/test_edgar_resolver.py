from pathlib import Path

import pytest

from disclosure_alpha.edgar.resolver import (
    normalize_form_type,
    normalize_quarter,
    parse_fiscal_tags,
    resolve_filing,
    resolve_prior_filing,
)
from disclosure_alpha.edgar.types import FilingNotFoundError, FilingRef

GOLD_HTML = (
    Path(__file__).resolve().parents[1]
    / "data/parser_eval/gold_set/0000320193-25-000079/0000320193-25-000079.html"
)


def test_parse_fiscal_tags_from_aapl_10k():
    html = GOLD_HTML.read_text(encoding="utf-8", errors="replace")
    fy, period = parse_fiscal_tags(html)
    assert fy == 2025
    assert period == "FY"


def test_normalize_form_and_quarter():
    assert normalize_form_type("10-K/A") == "10-K"
    assert normalize_quarter("q2") == "Q2"
    with pytest.raises(ValueError):
        normalize_quarter("Q4")


def test_resolve_filing_mocked(monkeypatch, tmp_path):
    html = GOLD_HTML.read_text(encoding="utf-8", errors="replace")
    submissions = {
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-25-000079", "0000320193-24-000123"],
                "form": ["10-K", "10-K"],
                "filingDate": ["2025-10-31", "2024-11-01"],
                "reportDate": ["2025-09-27", "2024-09-28"],
                "primaryDocument": ["aapl-20250927.htm", "aapl-20240928.htm"],
            },
            "files": [],
        }
    }

    monkeypatch.setenv("SEC_USER_AGENT", "Test test@example.com")
    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.client.fetch_company_tickers",
        lambda: {"AAPL": ("0000320193", "Apple Inc.")},
    )
    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.client.fetch_submissions",
        lambda cik: submissions,
    )
    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.client.fetch_text",
        lambda url: html,
    )
    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.cache.default_cache_dir",
        lambda: tmp_path,
    )

    ref = resolve_filing("AAPL", 2025, "10-K", use_cache=True, cache_dir=tmp_path)
    assert ref.accession_number == "0000320193-25-000079"
    assert ref.fiscal_year == 2025
    assert ref.form_type == "10-K"


def test_resolve_filing_not_found(monkeypatch, tmp_path):
    submissions = {
        "filings": {
            "recent": {
                "accessionNumber": [],
                "form": [],
                "filingDate": [],
                "reportDate": [],
                "primaryDocument": [],
            },
            "files": [],
        }
    }
    monkeypatch.setenv("SEC_USER_AGENT", "Test test@example.com")
    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.client.fetch_company_tickers",
        lambda: {"ZZZZ": ("0000000001", "Fake")},
    )
    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.client.fetch_submissions",
        lambda cik: submissions,
    )
    monkeypatch.setattr(
        "disclosure_alpha.edgar.resolver.cache.default_cache_dir",
        lambda: tmp_path,
    )
    with pytest.raises(FilingNotFoundError):
        resolve_filing("ZZZZ", 2025, "10-K", cache_dir=tmp_path)


def test_candidate_score_skips_insider_forms():
    from disclosure_alpha.edgar.resolver import _candidate_score

    row = {"form": "4", "reportDate": "2025-01-01", "filingDate": "2025-01-02"}
    assert _candidate_score(
        row,
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        fiscal_year_html=None,
        period_html=None,
    ) is None


def test_resolve_prior_10k(monkeypatch, tmp_path):
    monkeypatch.setenv("SEC_USER_AGENT", "Test test@example.com")

    def fake_resolve(ticker, fiscal_year, form_type, quarter=None, **kwargs):
        return FilingRef(
            cik="0000320193",
            ticker="AAPL",
            accession_number=f"acc-{fiscal_year}",
            form_type=form_type,
            fiscal_year=fiscal_year,
            quarter=quarter,
            filing_date=f"{fiscal_year}-10-31",
            report_date=None,
            primary_document="doc.htm",
        )

    monkeypatch.setattr("disclosure_alpha.edgar.resolver.resolve_filing", fake_resolve)
    current = fake_resolve("AAPL", 2025, "10-K")
    prior = resolve_prior_filing(current, cache_dir=tmp_path)
    assert prior is not None
    assert prior.fiscal_year == 2024

    current_q2 = fake_resolve("AAPL", 2025, "10-Q", quarter="Q2")
    prior_q = resolve_prior_filing(current_q2, cache_dir=tmp_path)
    assert prior_q is not None
    assert prior_q.quarter == "Q1"
