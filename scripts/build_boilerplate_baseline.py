#!/usr/bin/env python3
"""Build committed cross-firm boilerplate 4-gram baseline artifact."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from disclosure_alpha.boilerplate import (  # noqa: E402
    ITEM_1A,
    baseline_artifact_path,
    build_boilerplate_gram_set,
    write_baseline_artifact,
)
from disclosure_alpha.validation.corpus import CorpusLoadConfig, load_corpus  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "validation" / "mini_corpus.jsonl",
        help="Corpus JSONL (default: mini fixture)",
    )
    parser.add_argument("--fiscal-year", type=int, default=2025)
    parser.add_argument("--section", default=ITEM_1A)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--min-doc-freq", type=int, default=10)
    parser.add_argument("--min-doc-frac", type=float, default=0.25)
    parser.add_argument("--min-word-count", type=int, default=200)
    parser.add_argument("--min-confidence", type=float, default=0.75)
    args = parser.parse_args()

    out = args.out or baseline_artifact_path(args.fiscal_year, args.section)
    package_out = (
        ROOT / "src" / "disclosure_alpha" / "baselines_data" / out.name
    )
    rows, meta = load_corpus(
        args.corpus,
        config=CorpusLoadConfig(
            min_word_count=args.min_word_count,
            min_confidence=args.min_confidence,
            section_name=args.section,
        ),
    )
    if len(rows) < 2:
        print(f"error: need at least 2 corpus rows, got {len(rows)}", file=sys.stderr)
        return 1

    bp_min = min(args.min_doc_freq, max(2, len(rows)))
    gram_set = build_boilerplate_gram_set(
        rows,
        min_doc_freq=bp_min,
        min_doc_frac=args.min_doc_frac,
    )
    write_baseline_artifact(
        out,
        fiscal_year=args.fiscal_year,
        section=args.section,
        gram_set=gram_set,
        n_docs=len(rows),
        min_doc_freq=bp_min,
        min_doc_frac=args.min_doc_frac,
    )
    if package_out != out:
        write_baseline_artifact(
            package_out,
            fiscal_year=args.fiscal_year,
            section=args.section,
            gram_set=gram_set,
            n_docs=len(rows),
            min_doc_freq=bp_min,
            min_doc_frac=args.min_doc_frac,
        )
    print(
        f"wrote {out} ({len(gram_set)} grams from n={len(rows)} docs; "
        f"corpus filters: {meta.get('n_input')} -> {meta.get('n_after_filters')})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
