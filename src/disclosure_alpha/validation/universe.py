"""Universe ticker lists for validation cohorts."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SP500_PATH = Path("data/universe/sp500.csv")


@dataclass(frozen=True)
class UniverseEntry:
    ticker: str
    cik: str | None = None
    company_name: str | None = None


def load_universe(path: Path) -> list[UniverseEntry]:
    entries: list[UniverseEntry] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"empty universe file: {path}")
        ticker_col = next(
            (c for c in reader.fieldnames if c.lower() in ("ticker", "symbol")),
            reader.fieldnames[0],
        )
        cik_col = next((c for c in reader.fieldnames if c.lower() == "cik"), None)
        name_col = next(
            (c for c in reader.fieldnames if c.lower() in ("company_name", "name", "security")),
            None,
        )
        for row in reader:
            ticker = (row.get(ticker_col) or "").strip().upper()
            if not ticker or ticker.startswith("#"):
                continue
            cik_raw = (row.get(cik_col) or "").strip() if cik_col else ""
            cik = cik_raw.zfill(10) if cik_raw else None
            name = (row.get(name_col) or "").strip() if name_col else None
            entries.append(UniverseEntry(ticker=ticker, cik=cik, company_name=name))
    return entries


def universe_tickers(path: Path) -> frozenset[str]:
    return frozenset(e.ticker for e in load_universe(path))
