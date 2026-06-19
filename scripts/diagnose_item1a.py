#!/usr/bin/env python3
"""Diagnose Item 1A extraction for tickers (uses cached EDGAR HTML when available)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from disclosure_alpha.edgar import cache
from disclosure_alpha.section_extractor import (
    FilingDocument,
    _extract_item1a_from_clean_html,
    _extract_sections_fallback,
    _find_heading_positions,
    _parse_blocks,
    extract_sections,
)
from disclosure_alpha.dictionaries import sections_for_form_type
from disclosure_alpha.text_cleaner import clean_html_text
from disclosure_alpha.validation.corpus import manifest_path_for
from disclosure_alpha.validation.universe import DEFAULT_SP500_PATH, load_universe

ITEM_1A = "item_1a_risk_factors"
DEFAULT_CORPUS = Path("data/validation/corpus/sp500_item1a.jsonl")


def _corpus_row_by_ticker(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out[str(row.get("ticker", "")).upper()] = row
    return out


def _diagnose_ticker(
    ticker: str,
    *,
    corpus_path: Path,
    fiscal_year: int,
) -> None:
    corpus = _corpus_row_by_ticker(corpus_path).get(ticker.upper())
    print(f"\n=== {ticker} ===")
    if corpus:
        print(f"corpus: wc={corpus.get('word_count')} conf={corpus.get('extraction_confidence')}")
        cik = corpus.get("cik")
        acc = corpus.get("accession_number")
    else:
        print("corpus: not present")
        cik = acc = None

    if not cik or not acc:
        print("cache: no cik/accession (not in corpus)")
        return

    html = cache.read_cached_html(cache.default_cache_dir(), cik, acc)
    if not html:
        print("cache: HTML not cached")
        return

    doc = FilingDocument(cik=cik, accession_number=acc, form_type="10-K", html=html)
    blocks = _parse_blocks(html)
    print(f"sec_parser blocks: {len(blocks)}")

    section_map = sections_for_form_type("10-K")
    cleaned_positions = _find_heading_positions(clean_html_text(html), section_map)
    item1a_positions = [p for p in cleaned_positions if p[1] == ITEM_1A]
    print(f"fallback Item 1A heading hits: {len(item1a_positions)}")

    sections = extract_sections(doc)
    sec = next((s for s in sections if s.section_name == ITEM_1A), None)
    if sec:
        preview = sec.cleaned_text[:200].replace("\n", " ")
        print(
            f"extract_sections: wc={sec.word_count} conf={sec.extraction_confidence} "
            f"method={sec.extraction_method} warnings={sec.warnings}"
        )
        print(f"preview: {preview!r}")
    else:
        print("extract_sections: no Item 1A")
        last = _extract_item1a_from_clean_html(doc, "diagnostic")
        if last:
            print(f"last_resort: wc={last.word_count} preview={last.cleaned_text[:120]!r}")
        fb = _extract_sections_fallback(doc, "diagnostic")
        fb_sec = next((s for s in fb if s.section_name == ITEM_1A), None)
        if fb_sec:
            print(f"fallback only: wc={fb_sec.word_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose Item 1A extraction")
    parser.add_argument("--tickers", nargs="*", default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--fiscal-year", type=int, default=2025)
    parser.add_argument("--universe", type=Path, default=DEFAULT_SP500_PATH)
    args = parser.parse_args()

    tickers: list[str] = []
    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        manifest = args.manifest or manifest_path_for(args.corpus)
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            tickers = [
                f["ticker"].upper()
                for f in data.get("failures", [])
                if f.get("reason") == "no_item_1a"
            ]
        if not tickers and args.universe.exists():
            tickers = [e.ticker for e in load_universe(args.universe)[:5]]

    if not tickers:
        print("no tickers to diagnose", file=sys.stderr)
        sys.exit(1)

    for ticker in tickers:
        _diagnose_ticker(ticker, corpus_path=args.corpus, fiscal_year=args.fiscal_year)


if __name__ == "__main__":
    main()
