import re
from dataclasses import dataclass

from disclosure_alpha.dictionaries import (
    BOILERPLATE_PHRASES,
    CONSTRAINING_WORDS,
    FLAG_PATTERNS,
    FLAG_SECTION_SCOPE,
    FLAG_SUPPRESSIONS,
    GEOGRAPHY_TERMS,
    LEGAL_REGULATORY_PHRASES,
    LITIGIOUS_WORDS,
    MDNA_DENSITY_TERMS,
    MDNA_SECTIONS,
    MODAL_WORDS,
    MODERATE_MODAL_WORDS,
    NEGATIVE_WORDS,
    SEGMENT_TERMS,
    STRONG_MODAL_WORDS,
    UNCERTAINTY_WORDS,
    WEAK_MODAL_WORDS,
)
from disclosure_alpha.boilerplate import (
    DEFAULT_BLEND_WEIGHTS,
    blend_boilerplate_ratios,
    boilerplate_cross_firm_word_ratio,
    load_boilerplate_gram_set,
)
from disclosure_alpha.text_matching import (
    boilerplate_hits,
    phrase_count,
    phrase_matches,
    split_sentences,
    tokenize_words,
)

__all__ = [
    "SectionTextInput",
    "TextMetricResult",
    "METRIC_FAMILIES",
    "tokenize_words",
    "compute_text_metrics",
    "compute_metric_families",
    "detect_section_flags",
    "compute_density_metrics",
]


@dataclass
class SectionTextInput:
    section_name: str
    cleaned_text: str
    fiscal_year: int | None = None


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
    weak_modal_word_ratio: float
    moderate_modal_word_ratio: float
    strong_modal_word_ratio: float
    legal_regulatory_phrase_ratio: float
    numeric_specificity_score: float
    company_specificity_score: float
    boilerplate_phrase_ratio: float
    boilerplate_cross_firm_ratio: float
    boilerplate_combined_ratio: float


def _tokenize(text: str) -> list[str]:
    return tokenize_words(text)


def _count_sentences(text: str) -> int:
    sentences = split_sentences(text)
    return max(1, len(sentences)) if sentences else 0


def _word_ratio(words: list[str], vocab: frozenset[str]) -> float:
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in vocab)
    return hits / len(words)


def _phrase_ratio(lower: str, phrases: list[str], word_count: int) -> float:
    if not word_count:
        return 0.0
    hits = sum(phrase_count(lower, phrase) for phrase in phrases)
    return hits / word_count


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
    geo_hits = sum(1 for g in GEOGRAPHY_TERMS if phrase_matches(lower, g))
    segment_hits = sum(1 for s in SEGMENT_TERMS if phrase_matches(lower, s))
    company_specificity = min(
        100.0,
        ((capitalized + numeric_tokens + geo_hits + segment_hits) / word_count * 100)
        if word_count
        else 0.0,
    )

    bp_hits = boilerplate_hits(text, BOILERPLATE_PHRASES)
    boilerplate_ratio = min(1.0, bp_hits / max(1, sentence_count))

    gram_set = load_boilerplate_gram_set(inp.fiscal_year)
    cross_firm_ratio = (
        boilerplate_cross_firm_word_ratio(text, gram_set) if gram_set is not None else 0.0
    )
    combined_ratio = blend_boilerplate_ratios(
        boilerplate_ratio,
        cross_firm_ratio,
        weights=DEFAULT_BLEND_WEIGHTS,
    )

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
        weak_modal_word_ratio=round(_word_ratio(words, WEAK_MODAL_WORDS), 6),
        moderate_modal_word_ratio=round(_word_ratio(words, MODERATE_MODAL_WORDS), 6),
        strong_modal_word_ratio=round(_word_ratio(words, STRONG_MODAL_WORDS), 6),
        legal_regulatory_phrase_ratio=round(
            _phrase_ratio(lower, LEGAL_REGULATORY_PHRASES, word_count), 6
        ),
        numeric_specificity_score=round(numeric_specificity, 4),
        company_specificity_score=round(company_specificity, 4),
        boilerplate_phrase_ratio=round(boilerplate_ratio, 6),
        boilerplate_cross_firm_ratio=round(cross_firm_ratio, 6),
        boilerplate_combined_ratio=round(combined_ratio, 6),
    )


METRIC_FAMILIES = ("tone", "specificity", "boilerplate", "liquidity", "internal_controls")


def compute_metric_families(inp: SectionTextInput) -> list[dict[str, float | str]]:
    """Return metric family rows (tone, specificity, boilerplate, liquidity, internal_controls) with raw and normalized values."""
    base = compute_text_metrics(inp)
    return [
        {"metric_family": "tone", "metric_name": "negative_word_ratio", "raw_value": base.negative_word_ratio, "normalized_value": base.negative_word_ratio * 100},
        {"metric_family": "tone", "metric_name": "uncertainty_word_ratio", "raw_value": base.uncertainty_word_ratio, "normalized_value": base.uncertainty_word_ratio * 100},
        {"metric_family": "specificity", "metric_name": "numeric_specificity_score", "raw_value": base.numeric_specificity_score, "normalized_value": base.numeric_specificity_score},
        {"metric_family": "specificity", "metric_name": "company_specificity_score", "raw_value": base.company_specificity_score, "normalized_value": base.company_specificity_score},
        {"metric_family": "boilerplate", "metric_name": "boilerplate_phrase_ratio", "raw_value": base.boilerplate_phrase_ratio, "normalized_value": base.boilerplate_phrase_ratio * 100},
        {"metric_family": "boilerplate", "metric_name": "boilerplate_cross_firm_ratio", "raw_value": base.boilerplate_cross_firm_ratio, "normalized_value": base.boilerplate_cross_firm_ratio * 100},
        {"metric_family": "boilerplate", "metric_name": "boilerplate_combined_ratio", "raw_value": base.boilerplate_combined_ratio, "normalized_value": base.boilerplate_combined_ratio * 100},
        {"metric_family": "liquidity", "metric_name": "constraining_word_ratio", "raw_value": base.constraining_word_ratio, "normalized_value": base.constraining_word_ratio * 100},
        {"metric_family": "internal_controls", "metric_name": "modal_word_ratio", "raw_value": base.modal_word_ratio, "normalized_value": base.modal_word_ratio * 100},
    ]


def detect_section_flags(text: str, section_name: str) -> dict[str, bool]:
    """Return all v1 boolean flags for a section (False when out of scope)."""
    sentences = split_sentences(text or "")
    flags: dict[str, bool] = {}
    for flag_name, phrases in FLAG_PATTERNS.items():
        scope = FLAG_SECTION_SCOPE.get(flag_name, frozenset())
        if section_name not in scope:
            flags[flag_name] = False
            continue
        suppressions = FLAG_SUPPRESSIONS.get(flag_name, [])
        matched = False
        for sent in sentences:
            lower = sent.lower()
            if not any(phrase_matches(lower, phrase) for phrase in phrases):
                continue
            if suppressions and any(phrase_matches(lower, sup) for sup in suppressions):
                continue
            matched = True
            break
        flags[flag_name] = matched
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
        hits = sum(phrase_count(lower, term) for term in terms)
        raw = hits / word_count * 1000
        densities[name] = round(min(100.0, raw), 4)
    return densities
