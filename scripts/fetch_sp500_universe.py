#!/usr/bin/env python3
"""Refresh data/universe/sp500.csv from Wikipedia S&P 500 constituents."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

import urllib.request

from bs4 import BeautifulSoup

DEFAULT_OUT = Path("data/universe/sp500.csv")
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def fetch_sp500_rows() -> list[dict[str, str]]:
    req = urllib.request.Request(
        WIKI_URL,
        headers={"User-Agent": "disclosure-alpha/0.1 (universe refresh)"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="constituents")
    if table is None:
        raise RuntimeError("Wikipedia constituents table not found")

    rows: list[dict[str, str]] = []
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 7:
            continue
        ticker = tds[0].get_text(strip=True).replace(".", "-").upper()
        name = tds[1].get_text(strip=True)
        cik = tds[6].get_text(strip=True).zfill(10)
        rows.append({"ticker": ticker, "cik": cik, "company_name": name})
    rows.sort(key=lambda r: r["ticker"])
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch S&P 500 universe CSV")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    try:
        rows = fetch_sp500_rows()
    except Exception as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    as_of = date.today().isoformat()
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["ticker", "cik", "company_name", "as_of_date"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "as_of_date": as_of})

    print(f"Wrote {len(rows)} tickers to {args.out}")


if __name__ == "__main__":
    main()
