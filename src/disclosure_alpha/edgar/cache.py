from __future__ import annotations

import json
import os
from pathlib import Path

from disclosure_alpha.edgar.types import FilingRef


def default_cache_dir() -> Path:
    return Path(os.environ.get("DISCLOSURE_ALPHA_CACHE_DIR", "data/cache/sec_filings"))


def _cik_dir(cache_dir: Path, cik: str) -> Path:
    return cache_dir / cik.lstrip("0")


def html_path(cache_dir: Path, cik: str, accession_number: str) -> Path:
    return _cik_dir(cache_dir, cik) / f"{accession_number}.html"


def meta_path(cache_dir: Path, cik: str, accession_number: str) -> Path:
    return _cik_dir(cache_dir, cik) / f"{accession_number}.json"


def read_cached_html(cache_dir: Path, cik: str, accession_number: str) -> str | None:
    path = html_path(cache_dir, cik, accession_number)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return None


def write_cache(cache_dir: Path, ref: FilingRef, html: str) -> Path:
    path = html_path(cache_dir, ref.cik, ref.accession_number)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    meta_path(cache_dir, ref.cik, ref.accession_number).write_text(
        json.dumps(
            {
                "cik": ref.cik,
                "ticker": ref.ticker,
                "accession_number": ref.accession_number,
                "form_type": ref.form_type,
                "fiscal_year": ref.fiscal_year,
                "quarter": ref.quarter,
                "filing_date": ref.filing_date,
                "report_date": ref.report_date,
                "primary_document": ref.primary_document,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path
