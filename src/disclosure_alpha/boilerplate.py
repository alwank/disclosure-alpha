"""Cross-firm boilerplate metrics (Lang & Stice-Lawrence style 4-grams)."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from disclosure_alpha.text_matching import tokenize_words

if TYPE_CHECKING:
    from disclosure_alpha.validation.types import CorpusRow

DEFAULT_BLEND_WEIGHTS = (0.4, 0.6)  # phrase, cross_firm
ITEM_1A = "item_1a_risk_factors"
_BASELINE_SEARCH_DIRS = (
    Path(__file__).resolve().parent / "baselines_data",
    Path(__file__).resolve().parents[2] / "data" / "baselines",
)
_BASELINE_FILE_PATTERN = re.compile(
    r"^(?P<section>.+)_boilerplate_4grams_fy(?P<year>\d{4})\.json$"
)


def four_grams(words: list[str]) -> set[tuple[str, ...]]:
    if len(words) < 4:
        return set()
    return {tuple(words[i : i + 4]) for i in range(len(words) - 3)}


def build_boilerplate_gram_set_from_texts(
    texts: list[str],
    *,
    min_doc_freq: int = 10,
    min_doc_frac: float = 0.25,
) -> frozenset[tuple[str, ...]]:
    """Build cross-firm boilerplate 4-gram set from section texts."""
    n = len(texts)
    if n == 0:
        return frozenset()

    threshold = max(min_doc_freq, math.ceil(min_doc_frac * n))
    gram_doc_freq: Counter[tuple[str, ...]] = Counter()
    for text in texts:
        words = tokenize_words(text)
        for gram in four_grams(words):
            gram_doc_freq[gram] += 1
    return frozenset(g for g, count in gram_doc_freq.items() if count >= threshold)


def build_boilerplate_gram_set(
    rows: list[CorpusRow],
    *,
    min_doc_freq: int = 10,
    min_doc_frac: float = 0.25,
) -> frozenset[tuple[str, ...]]:
    return build_boilerplate_gram_set_from_texts(
        [row.cleaned_text for row in rows],
        min_doc_freq=min_doc_freq,
        min_doc_frac=min_doc_frac,
    )


def boilerplate_cross_firm_word_ratio(
    text: str,
    gram_set: frozenset[tuple[str, ...]],
) -> float:
    """Fraction of words falling in committed cross-firm boilerplate 4-grams."""
    words = tokenize_words(text)
    if not words or not gram_set:
        return 0.0
    boilerplate_word_idxs: set[int] = set()
    for i in range(len(words) - 3):
        gram = tuple(words[i : i + 4])
        if gram in gram_set:
            boilerplate_word_idxs.update(range(i, i + 4))
    return len(boilerplate_word_idxs) / len(words)


def blend_boilerplate_ratios(
    phrase_ratio: float,
    cross_firm_ratio: float,
    *,
    weights: tuple[float, float] = DEFAULT_BLEND_WEIGHTS,
) -> float:
    wp, wx = weights
    return min(1.0, max(0.0, wp * phrase_ratio + wx * cross_firm_ratio))


def _baselines_dir() -> Path | None:
    for directory in _BASELINE_SEARCH_DIRS:
        if directory.is_dir():
            return directory
    return None


def baseline_artifact_path(fiscal_year: int, section: str = ITEM_1A) -> Path:
    base = _baselines_dir() or _BASELINE_SEARCH_DIRS[0]
    return base / f"{section}_boilerplate_4grams_fy{fiscal_year}.json"


def _grams_from_artifact(data: dict) -> frozenset[tuple[str, ...]]:
    raw = data.get("grams")
    if not isinstance(raw, list):
        return frozenset()
    out: set[tuple[str, ...]] = set()
    for item in raw:
        if isinstance(item, list) and len(item) == 4:
            out.add(tuple(str(t).lower() for t in item))
    return frozenset(out)


def _available_baseline_years(section: str) -> list[int]:
    years: list[int] = []
    prefix = f"{section}_boilerplate_4grams_fy"
    for directory in _BASELINE_SEARCH_DIRS:
        if not directory.is_dir():
            continue
        for path in directory.glob(f"{prefix}*.json"):
            match = _BASELINE_FILE_PATTERN.match(path.name)
            if match and match.group("section") == section:
                years.append(int(match.group("year")))
    return sorted(set(years))


@lru_cache(maxsize=8)
def load_boilerplate_gram_set(
    fiscal_year: int | None = None,
    section: str = ITEM_1A,
) -> frozenset[tuple[str, ...]] | None:
    """Load committed boilerplate grams; fall back to latest fiscal year for section."""
    years = _available_baseline_years(section)
    if not years:
        return None
    year = fiscal_year if fiscal_year in years else years[-1]
    path = baseline_artifact_path(year, section)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    grams = _grams_from_artifact(data)
    return grams if grams else None


def write_baseline_artifact(
    path: Path,
    *,
    fiscal_year: int,
    section: str,
    gram_set: frozenset[tuple[str, ...]],
    n_docs: int,
    min_doc_freq: int,
    min_doc_frac: float,
) -> Path:
    payload = {
        "fiscal_year": fiscal_year,
        "section": section,
        "min_doc_freq": min_doc_freq,
        "min_doc_frac": min_doc_frac,
        "n_docs": n_docs,
        "gram_count": len(gram_set),
        "grams": [list(g) for g in sorted(gram_set)],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    load_boilerplate_gram_set.cache_clear()
    return path


def compute_ls_boilerplate_ratios(
    rows: list[CorpusRow],
    *,
    min_doc_freq: int = 10,
    min_doc_frac: float = 0.25,
) -> dict[str, float]:
    """Per-ticker fraction of words in cross-firm boilerplate 4-grams (L2 reference)."""
    n = len(rows)
    if n == 0:
        return {}

    gram_set = build_boilerplate_gram_set(
        rows, min_doc_freq=min_doc_freq, min_doc_frac=min_doc_frac
    )
    out: dict[str, float] = {}
    for row in rows:
        out[row.ticker] = boilerplate_cross_firm_word_ratio(row.cleaned_text, gram_set)
    return out
