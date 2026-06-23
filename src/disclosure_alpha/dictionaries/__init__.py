"""Built-in word lists for deterministic text metrics. Replaceable with licensed dictionaries."""

from disclosure_alpha.dictionaries.base import (
    MVP_FORM_TYPES,
    REQUIRED_SECTIONS,
    SECTION_DISPLAY_NAMES,
    SUPPORTED_SECTIONS,
    SUPPORTED_SECTIONS_10K,
    SUPPORTED_SECTIONS_10Q,
    SUPPORTED_SECTIONS_8K,
    TERM_PACK_METADATA,
    sections_for_form_type,
)
from disclosure_alpha.dictionaries.flags import (
    FLAG_PATTERNS,
    FLAG_SECTION_SCOPE,
    FLAG_SUPPRESSIONS,
)
from disclosure_alpha.dictionaries.phrases import (
    BOILERPLATE_PHRASES,
    GEOGRAPHY_TERMS,
    LEGAL_REGULATORY_PHRASES,
    MDNA_DENSITY_TERMS,
    MDNA_SECTIONS,
    SEGMENT_TERMS,
)
from disclosure_alpha.dictionaries.sentiment import (
    CONSTRAINING_WORDS,
    LITIGIOUS_WORDS,
    MODAL_WORDS,
    MODERATE_MODAL_WORDS,
    NEGATIVE_WORDS,
    STRONG_MODAL_WORDS,
    UNCERTAINTY_WORDS,
    WEAK_MODAL_WORDS,
)
from disclosure_alpha.dictionaries.topics import SEVERITY_WORDS, TOPIC_KEYWORDS

__all__ = [
    "TERM_PACK_METADATA",
    "NEGATIVE_WORDS",
    "UNCERTAINTY_WORDS",
    "LITIGIOUS_WORDS",
    "CONSTRAINING_WORDS",
    "WEAK_MODAL_WORDS",
    "MODERATE_MODAL_WORDS",
    "STRONG_MODAL_WORDS",
    "MODAL_WORDS",
    "BOILERPLATE_PHRASES",
    "LEGAL_REGULATORY_PHRASES",
    "GEOGRAPHY_TERMS",
    "SEGMENT_TERMS",
    "TOPIC_KEYWORDS",
    "SEVERITY_WORDS",
    "SUPPORTED_SECTIONS_10K",
    "SUPPORTED_SECTIONS_10Q",
    "SUPPORTED_SECTIONS_8K",
    "SUPPORTED_SECTIONS",
    "REQUIRED_SECTIONS",
    "sections_for_form_type",
    "SECTION_DISPLAY_NAMES",
    "MVP_FORM_TYPES",
    "FLAG_PATTERNS",
    "FLAG_SECTION_SCOPE",
    "FLAG_SUPPRESSIONS",
    "MDNA_DENSITY_TERMS",
    "MDNA_SECTIONS",
]
