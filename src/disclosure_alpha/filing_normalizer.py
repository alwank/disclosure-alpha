"""Filing metadata normalization per Doc 02."""

from __future__ import annotations

import re

# ponytail: SIC→sector lookup is a static subset; upgrade path is full SEC SIC table
SIC_SECTOR_MAP: dict[str, str] = {
    "3571": "Technology",
    "7370": "Technology",
    "7372": "Technology",
    "2834": "Healthcare",
    "6021": "Financials",
    "1311": "Energy",
    "3674": "Technology",
}


def parse_filing_type(form: str) -> tuple[str, bool]:
    """Return (base_filing_type, is_amendment)."""
    form = form.strip().upper()
    is_amendment = form.endswith("/A") or form.endswith("-A")
    base = re.sub(r"[-/]A$", "", form, flags=re.IGNORECASE)
    return base, is_amendment


def sic_to_sector(sic: str | None) -> str | None:
    if not sic:
        return None
    return SIC_SECTOR_MAP.get(sic[:4], SIC_SECTOR_MAP.get(sic, "Other"))
