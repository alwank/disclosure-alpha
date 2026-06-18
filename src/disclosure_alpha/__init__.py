"""Deterministic SEC filing analytics — parse, metrics, diff, score."""

from disclosure_alpha.deterministic_scoring import (
    DeterministicAggregationResult,
    aggregate_deterministic_matrix,
)
from disclosure_alpha.pipeline import (
    FilingScoreResult,
    MetricsResult,
    compute_section_metrics,
    extract_sections_from_html,
    score_deterministic,
    score_filing_html,
    score_filing_ticker,
)
from disclosure_alpha.section_extractor import (
    ExtractedSection,
    FilingDocument,
    extract_sections,
    required_sections_present,
)
from disclosure_alpha.version import (
    DICTIONARY_VERSION,
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)

__all__ = [
    "DICTIONARY_VERSION",
    "DeterministicAggregationResult",
    "ExtractedSection",
    "FilingDocument",
    "FilingScoreResult",
    "METRICS_ENGINE_VERSION",
    "MetricsResult",
    "PARSER_VERSION",
    "SCORING_MODEL_VERSION",
    "aggregate_deterministic_matrix",
    "compute_section_metrics",
    "extract_sections",
    "extract_sections_from_html",
    "required_sections_present",
    "score_deterministic",
    "score_filing_html",
    "score_filing_ticker",
]

__version__ = "0.1.0"
