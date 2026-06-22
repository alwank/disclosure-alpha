#!/usr/bin/env python3
"""Build full-matrix validation JSONL corpus from local HTML filings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from disclosure_alpha.pipeline import extract_sections_from_html
from disclosure_alpha.validation.matrix_corpus import sections_for_form
from disclosure_alpha.validation.universe import load_universe

DEFAULT_OUT = Path("data/validation/corpus/matrix_mini.jsonl")


def _ticker_from_name(path: Path) -> str:
    stem = path.stem
    if "_" in stem:
        return stem.split("_")[0].upper()
    return stem.upper()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build full-matrix validation corpus JSONL")
    parser.add_argument("--html-dir", type=Path, default=None)
    parser.add_argument("--prior-html-dir", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--universe", type=Path, default=None)
    parser.add_argument("--form", default="10-K")
    parser.add_argument("--fiscal-year", type=int, default=None)
    args = parser.parse_args()

    if args.html_dir is None:
        print("Provide --html-dir with local filing HTML files.", file=sys.stderr)
        sys.exit(1)
    if not args.html_dir.is_dir():
        print(f"html-dir not found: {args.html_dir}", file=sys.stderr)
        sys.exit(1)

    html_files = sorted(args.html_dir.glob("*.html"))
    if not html_files:
        print(f"no HTML files in {args.html_dir}", file=sys.stderr)
        sys.exit(1)

    allowed: set[str] | None = None
    if args.universe and args.universe.exists():
        allowed = {e.ticker for e in load_universe(args.universe)}

    required = sections_for_form(args.form)
    rows: list[dict] = []
    for path in html_files:
        ticker = _ticker_from_name(path)
        if allowed is not None and ticker not in allowed:
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        sections = extract_sections_from_html(html, args.form, accession_number=path.name)
        section_map = {
            s.section_name: s.cleaned_text
            for s in sections
            if s.section_name in required and s.cleaned_text
        }
        if not section_map:
            print(f"skip {path.name}: no matrix sections", file=sys.stderr)
            continue

        prior_map: dict[str, str] = {}
        if args.prior_html_dir and args.prior_html_dir.is_dir():
            prior_candidates = list(args.prior_html_dir.glob(f"{ticker}*.html"))
            if prior_candidates:
                prior_html = prior_candidates[0].read_text(encoding="utf-8", errors="replace")
                prior_sections = extract_sections_from_html(
                    prior_html, args.form, accession_number=prior_candidates[0].name
                )
                prior_map = {
                    s.section_name: s.cleaned_text
                    for s in prior_sections
                    if s.section_name in required and s.cleaned_text
                }

        quality = {}
        for s in sections:
            if s.section_name in section_map:
                quality[s.section_name] = {
                    "word_count": s.word_count,
                    "extraction_confidence": s.extraction_confidence,
                    "warnings": list(s.warnings or []),
                    "extraction_method": getattr(s, "extraction_method", None),
                }

        rows.append(
            {
                "ticker": ticker,
                "fiscal_year": args.fiscal_year,
                "form_type": args.form,
                "sections": section_map,
                "prior_sections": prior_map,
                "quality": quality,
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
