"""Cross-firm 4-gram boilerplate reference (Lang & Stice-Lawrence style)."""

from __future__ import annotations

import math
from collections import Counter

from disclosure_alpha.text_metrics import tokenize_words
from disclosure_alpha.validation.types import CorpusRow


def _four_grams(words: list[str]) -> set[tuple[str, ...]]:
    if len(words) < 4:
        return set()
    return {tuple(words[i : i + 4]) for i in range(len(words) - 3)}


def compute_ls_boilerplate_ratios(
    rows: list[CorpusRow],
    *,
    min_doc_freq: int = 10,
    min_doc_frac: float = 0.25,
) -> dict[str, float]:
    """Per-ticker fraction of words falling in cross-firm boilerplate 4-grams."""
    n = len(rows)
    if n == 0:
        return {}

    threshold = max(min_doc_freq, math.ceil(min_doc_frac * n))
    ticker_words: dict[str, list[str]] = {}
    gram_doc_freq: Counter[tuple[str, ...]] = Counter()

    for row in rows:
        words = tokenize_words(row.cleaned_text)
        ticker_words[row.ticker] = words
        for g in _four_grams(words):
            gram_doc_freq[g] += 1

    boilerplate_grams = {g for g, c in gram_doc_freq.items() if c >= threshold}
    out: dict[str, float] = {}
    for ticker, words in ticker_words.items():
        if not words:
            out[ticker] = 0.0
            continue
        if not boilerplate_grams:
            out[ticker] = 0.0
            continue
        boilerplate_word_idxs: set[int] = set()
        for i in range(len(words) - 3):
            g = tuple(words[i : i + 4])
            if g in boilerplate_grams:
                boilerplate_word_idxs.update(range(i, i + 4))
        out[ticker] = len(boilerplate_word_idxs) / len(words)
    return out
