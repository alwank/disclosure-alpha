#!/usr/bin/env python3
"""Audit validation corpus: filter drops, word counts, extraction methods."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from disclosure_alpha.validation.corpus import (
    CorpusLoadConfig,
    filter_skip_reason,
    load_corpus,
    parse_corpus_row,
)

DEFAULT_CORPUS = Path("data/validation/corpus/sp500_item1a.jsonl")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit validation corpus quality")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--min-confidence", type=float, default=0.75)
    parser.add_argument("--min-word-count", type=int, default=200)
    args = parser.parse_args()

    if not args.corpus.exists():
        raise SystemExit(f"corpus not found: {args.corpus}")

    cfg = CorpusLoadConfig(
        min_confidence=args.min_confidence,
        min_word_count=args.min_word_count,
    )
    _, meta = load_corpus(args.corpus, config=cfg)

    methods: Counter[str] = Counter()
    conf_buckets: Counter[str] = Counter()
    wc_buckets: Counter[str] = Counter()
    by_reason: dict[str, list[str]] = {}

    with args.corpus.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            raw = json.loads(line)
            ticker = str(raw.get("ticker", "")).upper()
            row = parse_corpus_row(raw, corpus_path=args.corpus)
            if row is None:
                continue

            method = str(raw.get("extraction_method", "unknown"))
            methods[method] += 1

            wc = row.word_count
            if wc < 50:
                wc_buckets["<50"] += 1
            elif wc < 200:
                wc_buckets["50-199"] += 1
            else:
                wc_buckets["200+"] += 1

            conf = row.extraction_confidence or 0.0
            if conf < 0.5:
                conf_buckets["<0.5"] += 1
            elif conf < 0.75:
                conf_buckets["0.5-0.74"] += 1
            else:
                conf_buckets["0.75+"] += 1

            reason = filter_skip_reason(row, cfg)
            if reason:
                by_reason.setdefault(reason, []).append(ticker)

    print(f"Corpus: {args.corpus}")
    print(f"n_input={meta['n_input']} n_after_filters={meta['n_after_filters']}")
    print(f"filter_breakdown: {meta.get('filter_breakdown')}")
    print(f"extraction_method: {dict(methods)}")
    print(f"word_count buckets: {dict(wc_buckets)}")
    print(f"confidence buckets: {dict(conf_buckets)}")
    print("filter drops by reason:")
    for reason, tickers in sorted(by_reason.items()):
        print(f"  {reason}: {len(tickers)} e.g. {', '.join(tickers[:12])}")


if __name__ == "__main__":
    main()
