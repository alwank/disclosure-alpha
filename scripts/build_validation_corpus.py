#!/usr/bin/env python3
"""Build L2 validation JSONL corpus from local 10-K HTML files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from disclosure_alpha.pipeline import extract_sections_from_html
from disclosure_alpha.validation.universe import load_universe

ITEM_1A = "item_1a_risk_factors"
DEFAULT_OUT = Path("data/validation/corpus/sp500_item1a.jsonl")


def _ticker_from_name(path: Path) -> str:
    stem = path.stem
    if "_" in stem:
        return stem.split("_")[0].upper()
    return stem.upper()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build validation corpus JSONL from HTML")
    parser.add_argument("--html-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--universe", type=Path, default=None, help="Optional ticker CSV filter")
    parser.add_argument("--form", default="10-K")
    parser.add_argument("--fiscal-year", type=int, default=None)
    args = parser.parse_args()

    if not args.html_dir.is_dir():
        print(f"html-dir not found: {args.html_dir}", file=sys.stderr)
        sys.exit(1)

    html_files = sorted(args.html_dir.glob("*.html"))
    if not html_files:
        print(f"no HTML files in {args.html_dir}", file=sys.stderr)
        sys.exit(1)

    allowed: set[str] | None = None
    if args.universe:
        if not args.universe.exists():
            print(f"universe not found: {args.universe}", file=sys.stderr)
            sys.exit(1)
        allowed = {e.ticker for e in load_universe(args.universe)}

    rows: list[dict] = []
    for path in html_files:
        ticker = _ticker_from_name(path)
        if allowed is not None and ticker not in allowed:
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        sections = extract_sections_from_html(
            html, args.form, accession_number=path.name
        )
        sec = next((s for s in sections if s.section_name == ITEM_1A), None)
        if sec is None:
            print(f"skip {path.name}: no Item 1A", file=sys.stderr)
            continue
        rows.append(
            {
                "ticker": ticker,
                "fiscal_year": args.fiscal_year,
                "section_name": sec.section_name,
                "cleaned_text": sec.cleaned_text,
                "word_count": sec.word_count,
                "extraction_confidence": sec.extraction_confidence,
                "accession_number": path.name,
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
