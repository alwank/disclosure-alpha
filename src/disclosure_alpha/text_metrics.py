import re
from dataclasses import dataclass

from disclosure_alpha.dictionaries import (
    BOILERPLATE_PHRASES,
    CONSTRAINING_WORDS,
    FLAG_PATTERNS,
    FLAG_SECTION_SCOPE,
    GEOGRAPHY_TERMS,
    LITIGIOUS_WORDS,
    MDNA_DENSITY_TERMS,
    MDNA_SECTIONS,
    MODAL_WORDS,
    NEGATIVE_WORDS,
    SEGMENT_TERMS,
    UNCERTAINTY_WORDS,
)


@dataclass
class SectionTextInput:
    section_name: str
    cleaned_text: str


@dataclass
class TextMetricResult:
    word_count: int
    sentence_count: int
    average_sentence_length: float
    readability_score: float | None
    negative_word_ratio: float
    uncertainty_word_ratio: float
    litigious_word_ratio: float
    constraining_word_ratio: float
    modal_word_ratio: float
    numeric_specificity_score: float
    company_specificity_score: float
    boilerplate_phrase_ratio: float


def tokenize_words(text: str) -> list[str]:
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())


def _tokenize(text: str) -> list[str]:
    return tokenize_words(text)


def _count_sentences(text: str) -> int:
    if not text.strip():
        return 0
    parts = re.split(r"[.!?]+\s+", text.strip())
    return max(1, len([p for p in parts if p.strip()]))


def _word_ratio(words: list[str], vocab: frozenset[str]) -> float:
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in vocab)
    return hits / len(words)


def _phrase_pattern(phrase: str) -> str:
    parts = [re.escape(part) for part in re.split(r"[\s-]+", phrase.lower()) if part]
    body = r"[\s-]+".join(parts)
    return rf"(?<![a-z0-9]){body}(?![a-z0-9])"


def _phrase_count(lower: str, phrase: str) -> int:
    return len(re.findall(_phrase_pattern(phrase), lower))


def compute_text_metrics(inp: SectionTextInput) -> TextMetricResult:
    text = inp.cleaned_text or ""
    words = _tokenize(text)
    word_count = len(words)
    sentence_count = _count_sentences(text)
    avg_sentence_len = word_count / sentence_count if sentence_count else 0.0
    long_words = sum(1 for w in words if len(w) > 6)
    long_word_pct = (long_words / word_count) if word_count else 0.0
    readability = min(100.0, avg_sentence_len * 2 + long_word_pct * 100)

    numeric_tokens = len(re.findall(r"\b\d+(?:[.,]\d+)?%?\b", text))
    numeric_specificity = min(100.0, (numeric_tokens / word_count * 1000) if word_count else 0.0)

    lower = text.lower()
    capitalized = len(re.findall(r"\b[A-Z][a-z]+\b", text))
    geo_hits = sum(1 for g in GEOGRAPHY_TERMS if g in lower)
    segment_hits = sum(1 for s in SEGMENT_TERMS if s in lower)
    company_specificity = min(
        100.0,
        ((capitalized + numeric_tokens + geo_hits + segment_hits) / word_count * 100)
        if word_count
        else 0.0,
    )

    boilerplate_hits = sum(_phrase_count(lower, p) for p in BOILERPLATE_PHRASES)
    boilerplate_ratio = min(1.0, boilerplate_hits / max(1, sentence_count))

    return TextMetricResult(
        word_count=word_count,
        sentence_count=sentence_count,
        average_sentence_length=round(avg_sentence_len, 4),
        readability_score=round(readability, 4),
        negative_word_ratio=round(_word_ratio(words, NEGATIVE_WORDS), 6),
        uncertainty_word_ratio=round(_word_ratio(words, UNCERTAINTY_WORDS), 6),
        litigious_word_ratio=round(_word_ratio(words, LITIGIOUS_WORDS), 6),
        constraining_word_ratio=round(_word_ratio(words, CONSTRAINING_WORDS), 6),
        modal_word_ratio=round(_word_ratio(words, MODAL_WORDS), 6),
        numeric_specificity_score=round(numeric_specificity, 4),
        company_specificity_score=round(company_specificity, 4),
        boilerplate_phrase_ratio=round(boilerplate_ratio, 6),
    )


METRIC_FAMILIES = ("tone", "specificity", "boilerplate", "liquidity", "internal_controls")


def compute_metric_families(inp: SectionTextInput) -> list[dict[str, float | str]]:
    """Return normalized metric family rows per Doc 04."""
    base = compute_text_metrics(inp)
    return [
        {"metric_family": "tone", "metric_name": "negative_word_ratio", "raw_value": base.negative_word_ratio, "normalized_value": base.negative_word_ratio * 100},
        {"metric_family": "tone", "metric_name": "uncertainty_word_ratio", "raw_value": base.uncertainty_word_ratio, "normalized_value": base.uncertainty_word_ratio * 100},
        {"metric_family": "specificity", "metric_name": "numeric_specificity_score", "raw_value": base.numeric_specificity_score, "normalized_value": base.numeric_specificity_score},
        {"metric_family": "specificity", "metric_name": "company_specificity_score", "raw_value": base.company_specificity_score, "normalized_value": base.company_specificity_score},
        {"metric_family": "boilerplate", "metric_name": "boilerplate_phrase_ratio", "raw_value": base.boilerplate_phrase_ratio, "normalized_value": base.boilerplate_phrase_ratio * 100},
        {"metric_family": "liquidity", "metric_name": "constraining_word_ratio", "raw_value": base.constraining_word_ratio, "normalized_value": base.constraining_word_ratio * 100},
        {"metric_family": "internal_controls", "metric_name": "modal_word_ratio", "raw_value": base.modal_word_ratio, "normalized_value": base.modal_word_ratio * 100},
    ]


def _phrase_matches(lower: str, phrase: str) -> bool:
    """Word-boundary phrase match with whitespace/hyphen separator tolerance."""
    return bool(re.search(_phrase_pattern(phrase), lower))


def detect_section_flags(text: str, section_name: str) -> dict[str, bool]:
    """Return all v1 boolean flags for a section (False when out of scope)."""
    lower = (text or "").lower()
    flags: dict[str, bool] = {}
    for flag_name, phrases in FLAG_PATTERNS.items():
        scope = FLAG_SECTION_SCOPE.get(flag_name, frozenset())
        if section_name not in scope:
            flags[flag_name] = False
            continue
        flags[flag_name] = any(_phrase_matches(lower, phrase) for phrase in phrases)
    return flags


def compute_density_metrics(text: str, section_name: str) -> dict[str, float]:
    """MD&A keyword density: hits per 1000 words, capped 0–100."""
    if section_name not in MDNA_SECTIONS:
        return {name: 0.0 for name in MDNA_DENSITY_TERMS}
    words = _tokenize(text or "")
    word_count = max(1, len(words))
    lower = (text or "").lower()
    densities: dict[str, float] = {}
    for name, terms in MDNA_DENSITY_TERMS.items():
        hits = sum(_phrase_count(lower, term) for term in terms)
        raw = hits / word_count * 1000
        densities[name] = round(min(100.0, raw), 4)
    return densities
