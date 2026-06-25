"""Shared scoring helpers for validation pipelines."""

from __future__ import annotations

import hashlib
from typing import Any

from disclosure_alpha.deterministic_scoring import (
    aggregate_deterministic_matrix,
    aggregate_deterministic_matrix_v2,
)
from disclosure_alpha.pipeline import compute_section_metrics, score_for_model
from disclosure_alpha.section_extractor import ExtractedSection
from disclosure_alpha.validation.matrix_corpus import MatrixCorpusRow
from disclosure_alpha.validation.scoring_version import is_v1_scoring, normalize_scoring_version
from disclosure_alpha.version import PARSER_VERSION, SCORING_MODEL_VERSION


def score_item1a_from_corpus_row(
    row: dict[str, Any],
    *,
    scoring_model_version: str = SCORING_MODEL_VERSION,
) -> dict[str, float | None]:
    text = str(row.get("cleaned_text") or "")
    word_count = int(row.get("word_count") or len(text.split()))
    section = ExtractedSection(
        "item_1a_risk_factors",
        text,
        text,
        "corpus",
        word_count,
        max(1, word_count // 20),
        float(row.get("extraction_confidence") or 0.5),
        str(row.get("extraction_method") or "corpus"),
        PARSER_VERSION,
        warnings=[],
    )
    version = normalize_scoring_version(scoring_model_version)
    metrics = compute_section_metrics(
        [section],
        prior_sections=None,
        form_type="10-K",
        fiscal_year=int(row["fiscal_year"]) if row.get("fiscal_year") is not None else None,
    )
    scores = score_for_model(metrics, version)
    return {
        "overall_disclosure_risk_score": scores.overall_disclosure_risk_score,
        "disclosure_change_score": scores.components.disclosure_change_score,
        "risk_factor_intensity_score": scores.components.risk_factor_intensity_score,
        "score_coverage_ratio": scores.score_coverage_ratio,
    }


def _matrix_section(name: str, text: str, confidence: float = 0.8) -> ExtractedSection:
    cleaned = text.strip()
    return ExtractedSection(
        section_name=name,
        raw_text=cleaned,
        cleaned_text=cleaned,
        text_hash=hashlib.sha256(cleaned.encode()).hexdigest()[:16],
        word_count=len(cleaned.split()),
        sentence_count=max(1, cleaned.count(".") + cleaned.count("!") + cleaned.count("?")),
        extraction_confidence=confidence,
        extraction_method="validation_matrix",
        parser_version="validation_matrix",
    )


def score_matrix_corpus_row(
    row: MatrixCorpusRow,
    *,
    scoring_model_version: str = SCORING_MODEL_VERSION,
) -> dict[str, float | None]:
    current = [
        _matrix_section(
            name,
            text,
            confidence=(row.quality.get(name).extraction_confidence if name in row.quality else 0.8) or 0.8,
        )
        for name, text in row.sections.items()
        if text.strip()
    ]
    prior = None
    if row.prior_sections:
        prior = [
            _matrix_section(name, text)
            for name, text in row.prior_sections.items()
            if text.strip()
        ]
    metrics = compute_section_metrics(
        current,
        prior,
        form_type=row.form_type,
        fiscal_year=row.fiscal_year,
    )
    version = normalize_scoring_version(scoring_model_version)
    if is_v1_scoring(version):
        scores = aggregate_deterministic_matrix(
            section_metrics=metrics.section_metrics,
            section_diffs=metrics.section_diffs,
            section_flags=metrics.section_flags,
            language_deltas=metrics.language_deltas,
            section_densities=metrics.section_densities,
        )
    else:
        scores = aggregate_deterministic_matrix_v2(
            section_metrics=metrics.section_metrics,
            section_diffs=metrics.section_diffs,
            section_flags=metrics.section_flags,
            language_deltas=metrics.language_deltas,
            section_densities=metrics.section_densities,
            section_diffs_v2=metrics.section_diffs_v2,
        )
    return {
        "overall_disclosure_risk_score": scores.overall_disclosure_risk_score,
        "disclosure_change_score": scores.components.disclosure_change_score,
        "risk_factor_intensity_score": scores.components.risk_factor_intensity_score,
        "score_coverage_ratio": scores.score_coverage_ratio,
    }
