#!/usr/bin/env python3
"""Fetch L3 outcome variables for validation cohort rows (vol + earnings surprise)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from disclosure_alpha.validation.openbb_client import DEFAULT_OPENBB_API_URL, OpenBBClient, OpenBBError
from disclosure_alpha.validation.outcomes import fetch_outcomes_for_filing
from disclosure_alpha.validation.universe import DEFAULT_SP500_PATH, load_universe

DEFAULT_CORPUS = Path("data/validation/corpus/sp500_item1a.jsonl")
DEFAULT_OUT = Path("data/validation/outcomes/sp500_outcomes.jsonl")


def _default_out_for_fy(fiscal_year: int | None) -> Path:
    if fiscal_year is None:
        return DEFAULT_OUT
    return Path(f"data/validation/outcomes/sp500_outcomes_fy{fiscal_year}.jsonl")


def _load_corpus_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch L3 outcomes for validation corpus rows")
    parser.add_argument("--corpus", type=Path, default=None, help="JSONL corpus (ticker, fiscal_year, filing_date)")
    parser.add_argument("--universe", type=Path, default=None, help="Universe CSV (use with --fiscal-year)")
    parser.add_argument("--fiscal-year", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--openbb-url", default=None, help=f"default: OPENBB_API_URL or {DEFAULT_OPENBB_API_URL}")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-vol", action="store_true")
    parser.add_argument("--skip-earnings", action="store_true")
    parser.add_argument("--no-edgar-resolve", action="store_true", help="Do not resolve filing_date via EDGAR")
    args = parser.parse_args()

    if args.out is None:
        args.out = _default_out_for_fy(args.fiscal_year)

    if args.universe is not None:
        if args.fiscal_year is None:
            print("--fiscal-year required with --universe", file=sys.stderr)
            sys.exit(1)
        if not args.universe.exists():
            print(f"universe not found: {args.universe}", file=sys.stderr)
            sys.exit(1)
        corpus_rows = [
            {"ticker": e.ticker, "fiscal_year": args.fiscal_year}
            for e in load_universe(args.universe)
        ]
    else:
        corpus_path = args.corpus or DEFAULT_CORPUS
        if not corpus_path.exists():
            print(f"corpus not found: {corpus_path}", file=sys.stderr)
            sys.exit(1)
        corpus_rows = _load_corpus_rows(corpus_path)

    openbb: OpenBBClient | None = None
    if not args.skip_vol:
        openbb = OpenBBClient(args.openbb_url)
        if not openbb.health_check():
            print(
                f"OpenBB API not reachable at {openbb.base_url} "
                f"(start OpenBB Platform API or set OPENBB_API_URL)",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"OpenBB: {openbb.base_url}", flush=True)

    if args.limit is not None:
        corpus_rows = corpus_rows[: args.limit]

    print(f"Fiscal year: {args.fiscal_year or 'from corpus'}", flush=True)
    print(f"Rows: {len(corpus_rows)}", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    vol_ok = 0
    earn_ok = 0

    with args.out.open("w", encoding="utf-8") as out_f:
        for i, raw in enumerate(corpus_rows, start=1):
            ticker = str(raw.get("ticker", "")).upper()
            if not ticker:
                continue
            fiscal_year = raw.get("fiscal_year")
            fy = int(fiscal_year) if fiscal_year is not None else None
            filing_date = raw.get("filing_date")

            try:
                outcome = fetch_outcomes_for_filing(
                    ticker=ticker,
                    fiscal_year=fy,
                    filing_date=filing_date,
                    openbb=openbb,
                    fetch_vol=not args.skip_vol,
                    fetch_earnings=not args.skip_earnings,
                    resolve_filing_from_edgar=not args.no_edgar_resolve,
                )
            except OpenBBError as exc:
                outcome = {
                    "ticker": ticker,
                    "fiscal_year": fy,
                    "filing_date": filing_date,
                    "errors": [str(exc)],
                }
            else:
                outcome = outcome.to_dict()

            if outcome.get("realized_vol_90d") is not None:
                vol_ok += 1
            if outcome.get("earnings_surprise_abs") is not None:
                earn_ok += 1

            out_f.write(json.dumps(outcome) + "\n")
            written += 1
            if i % 25 == 0:
                print(f"progress: {i}/{len(corpus_rows)}", flush=True)

    print(f"Wrote {written} rows -> {args.out}")
    print(f"vol coverage: {vol_ok}/{written}")
    print(f"earnings coverage: {earn_ok}/{written}")


if __name__ == "__main__":
    main()
