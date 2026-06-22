"""Deterministic SEC filing analytics — parse, metrics, diff, score."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

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

try:
    __version__ = _pkg_version("disclosure-alpha")
except PackageNotFoundError:
    __version__ = "1.1.0"  # editable install fallback
