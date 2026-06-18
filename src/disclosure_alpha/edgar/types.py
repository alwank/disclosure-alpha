from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FilingRef:
    cik: str
    ticker: str
    accession_number: str
    form_type: str
    fiscal_year: int
    quarter: str | None
    filing_date: str
    report_date: str | None
    primary_document: str
    html_path: Path | None = None

    @property
    def accession_nodash(self) -> str:
        return self.accession_number.replace("-", "")


class EdgarError(Exception):
    """Base EDGAR error."""


class FilingNotFoundError(EdgarError):
    """No filing matches ticker + fiscal year + form."""


class SecFetchError(EdgarError):
    """SEC HTTP request failed."""
