#!/usr/bin/env python3
"""Diagnose boilerplate blend weights vs LS 4-gram reference on a corpus."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from disclosure_alpha.boilerplate import (  # noqa: E402
    DEFAULT_BLEND_WEIGHTS,
    blend_boilerplate_ratios,
    load_boilerplate_gram_set,
)
from disclosure_alpha.text_metrics import SectionTextInput, compute_text_metrics  # noqa: E402
from disclosure_alpha.validation.construct import (  # noqa: E402
    ConstructConfig,
    _discordant_tickers,
    spearman_rho,
)
from disclosure_alpha.validation.corpus import CorpusLoadConfig, load_corpus  # noqa: E402
from disclosure_alpha.validation.references.boilerplate import (  # noqa: E402
    compute_ls_boilerplate_ratios,
)


def _correlations(
    rows,
    ls_bp: dict[str, float],
    *,
    weights: tuple[float, float],
    fiscal_year: int | None,
) -> tuple[float | None, list[str]]:
    paired_rows = []
    xs: list[float] = []
    ys: list[float] = []
    for row in rows:
        if row.ticker not in ls_bp:
            continue
        m = compute_text_metrics(
            SectionTextInput(row.section_name, row.cleaned_text, fiscal_year=fiscal_year)
        )
        combined = blend_boilerplate_ratios(
            m.boilerplate_phrase_ratio,
            m.boilerplate_cross_firm_ratio,
            weights=weights,
        )
        paired_rows.append(row)
        xs.append(combined)
        ys.append(ls_bp[row.ticker])
    rho = spearman_rho(xs, ys) if len(xs) >= 2 else None
    discordant = _discordant_tickers(paired_rows, xs, ys) if rho is not None else []
    return rho, discordant


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "validation" / "mini_corpus.jsonl",
    )
    parser.add_argument("--fiscal-year", type=int, default=2025)
    parser.add_argument("--min-word-count", type=int, default=200)
    parser.add_argument("--min-confidence", type=float, default=0.75)
    args = parser.parse_args()

    rows, meta = load_corpus(
        args.corpus,
        config=CorpusLoadConfig(
            min_word_count=args.min_word_count,
            min_confidence=args.min_confidence,
        ),
    )
    if len(rows) < 2:
        print(f"error: need at least 2 rows, got {len(rows)}", file=sys.stderr)
        return 1

    cfg = ConstructConfig()
    bp_min = min(cfg.boilerplate_min_docs, max(2, len(rows)))
    ls_bp = compute_ls_boilerplate_ratios(
        rows,
        min_doc_freq=bp_min,
        min_doc_frac=cfg.boilerplate_min_doc_frac,
    )

    phrase_only: list[float] = []
    ls_vals: list[float] = []
    for row in rows:
        if row.ticker not in ls_bp:
            continue
        m = compute_text_metrics(
            SectionTextInput(row.section_name, row.cleaned_text, fiscal_year=args.fiscal_year)
        )
        phrase_only.append(m.boilerplate_phrase_ratio)
        ls_vals.append(ls_bp[row.ticker])

    print(f"corpus: {args.corpus}")
    print(f"rows after filters: {meta.get('n_after_filters')} (paired n={len(phrase_only)})")
    gram_set = load_boilerplate_gram_set(args.fiscal_year)
    print(f"baseline grams loaded: {len(gram_set) if gram_set else 0}")

    rho_phrase = spearman_rho(phrase_only, ls_vals)
    print(f"phrase_only vs LS: rho={rho_phrase}")

    best_weights = DEFAULT_BLEND_WEIGHTS
    best_rho = -1.0
    for wx in (0.5, 0.6, 0.7):
        wp = 1.0 - wx
        rho, _ = _correlations(rows, ls_bp, weights=(wp, wx), fiscal_year=args.fiscal_year)
        print(f"blend w_p={wp:.1f} w_x={wx:.1f}: rho={rho}")
        if rho is not None and rho > best_rho:
            best_rho = rho
            best_weights = (wp, wx)

    rho, discordant = _correlations(
        rows, ls_bp, weights=best_weights, fiscal_year=args.fiscal_year
    )
    print(f"recommended weights: w_p={best_weights[0]}, w_x={best_weights[1]} (rho={rho})")
    if discordant:
        print(f"discordant tickers (top): {', '.join(discordant[:20])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
