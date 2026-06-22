"""Validation gates for full-matrix scoring coverage."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from disclosure_alpha.deterministic_scoring import (
    aggregate_deterministic_matrix,
    aggregate_deterministic_matrix_v2,
)
from disclosure_alpha.pipeline import compute_section_metrics
from disclosure_alpha.section_extractor import ExtractedSection
from disclosure_alpha.validation.matrix_corpus import MatrixCorpusRow, sections_for_form
from disclosure_alpha.validation.scoring_version import normalize_scoring_version
from disclosure_alpha.version import (
    DICTIONARY_VERSION,
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
    SCORING_MODEL_VERSION_V2,
)

COMPONENT_FIELDS = (
    "risk_factor_intensity_score",
    "disclosure_change_score",
    "mdna_uncertainty_score",
    "legal_regulatory_risk_score",
    "liquidity_stress_score",
    "boilerplate_risk_score",
    "internal_controls_risk_score",
    "event_severity_score",
    "tone_negativity_score",
)


@dataclass
class MatrixGateResult:
    name: str
    status: str  # pass | fail | skipped
    value: float | None = None
    threshold: float | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MatrixValidationReport:
    validation_level: str = "matrix"
    generated_at: str = ""
    versions: dict[str, str] = field(default_factory=dict)
    corpus_path: str = ""
    n_filings: int = 0
    gates: dict[str, MatrixGateResult] = field(default_factory=dict)
    component_coverage: dict[str, float] = field(default_factory=dict)
    overall_pass: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_level": self.validation_level,
            "generated_at": self.generated_at,
            "versions": self.versions,
            "corpus": {"path": self.corpus_path, "n_filings": self.n_filings},
            "gates": {k: v.to_dict() for k, v in self.gates.items()},
            "component_coverage": self.component_coverage,
            "overall_pass": self.overall_pass,
        }


def _make_section(name: str, text: str, confidence: float = 0.8) -> ExtractedSection:
    cleaned = text.strip()
    return ExtractedSection(
        section_name=name,
        raw_text=cleaned,
        cleaned_text=cleaned,
        text_hash=hashlib.sha256(cleaned.encode()).hexdigest()[:16],
        word_count=len(cleaned.split()),
        sentence_count=max(1, cleaned.count(".") + cleaned.count("!") + cleaned.count("?")),
        extraction_confidence=confidence,
        extraction_method="corpus_fixture",
        parser_version="fixture",
    )


def _sections_from_row(row: MatrixCorpusRow) -> tuple[list[ExtractedSection], list[ExtractedSection] | None]:
    current = [
        _make_section(
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
            _make_section(name, text)
            for name, text in row.prior_sections.items()
            if text.strip()
        ]
    return current, prior


def _aggregate_scores(metrics, *, scoring_model_version: str):
    if scoring_model_version == SCORING_MODEL_VERSION_V2:
        return aggregate_deterministic_matrix_v2(
            section_metrics=metrics.section_metrics,
            section_diffs=metrics.section_diffs,
            section_flags=metrics.section_flags,
            language_deltas=metrics.language_deltas,
            section_densities=metrics.section_densities,
            section_diffs_v2=metrics.section_diffs_v2,
        )
    return aggregate_deterministic_matrix(
        section_metrics=metrics.section_metrics,
        section_diffs=metrics.section_diffs,
        section_flags=metrics.section_flags,
        language_deltas=metrics.language_deltas,
        section_densities=metrics.section_densities,
    )


def evaluate_matrix_gates(
    rows: list[MatrixCorpusRow],
    *,
    min_extraction_rate: float = 0.5,
    min_median_confidence: float = 0.6,
    min_component_coverage: float = 0.4,
    scoring_model_version: str = SCORING_MODEL_VERSION,
) -> MatrixValidationReport:
    scoring_model_version = normalize_scoring_version(scoring_model_version)
    if not rows:
        return MatrixValidationReport(
            n_filings=0,
            gates={
                "non_empty_corpus": MatrixGateResult(
                    "non_empty_corpus", "fail", message="no corpus rows"
                )
            },
            component_coverage={},
            overall_pass=False,
        )

    required_hits = 0
    required_total = 0
    confidences: list[float] = []
    component_hits = {name: 0 for name in COMPONENT_FIELDS}

    for row in rows:
        required = sections_for_form(row.form_type)
        for section in required:
            required_total += 1
            if section in row.sections and row.sections[section].strip():
                required_hits += 1
                q = row.quality.get(section)
                if q and q.extraction_confidence is not None:
                    confidences.append(q.extraction_confidence)

        current, prior = _sections_from_row(row)
        metrics = compute_section_metrics(current, prior)
        scores = _aggregate_scores(metrics, scoring_model_version=scoring_model_version)
        for name in COMPONENT_FIELDS:
            if getattr(scores.components, name) is not None:
                component_hits[name] += 1

    extraction_rate = required_hits / required_total if required_total else 0.0
    confidences.sort()
    median_conf = confidences[len(confidences) // 2] if confidences else 0.0
    component_coverage = {k: v / len(rows) for k, v in component_hits.items()}
    avg_component_coverage = sum(component_coverage.values()) / len(component_coverage)

    gates = {
        "non_empty_corpus": MatrixGateResult("non_empty_corpus", "pass", value=float(len(rows))),
        "required_section_extraction_rate": MatrixGateResult(
            "required_section_extraction_rate",
            "pass" if extraction_rate >= min_extraction_rate else "fail",
            value=round(extraction_rate, 4),
            threshold=min_extraction_rate,
        ),
        "median_extraction_confidence": MatrixGateResult(
            "median_extraction_confidence",
            "pass" if median_conf >= min_median_confidence else "fail",
            value=round(median_conf, 4),
            threshold=min_median_confidence,
        ),
        "component_coverage": MatrixGateResult(
            "component_coverage",
            "pass" if avg_component_coverage >= min_component_coverage else "fail",
            value=round(avg_component_coverage, 4),
            threshold=min_component_coverage,
        ),
    }
    overall = all(g.status == "pass" for g in gates.values())
    return MatrixValidationReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        versions={
            "parser_version": PARSER_VERSION,
            "metrics_engine_version": METRICS_ENGINE_VERSION,
            "scoring_model_version": scoring_model_version,
            "dictionary_version": DICTIONARY_VERSION,
        },
        n_filings=len(rows),
        gates=gates,
        component_coverage={k: round(v, 4) for k, v in component_coverage.items()},
        overall_pass=overall,
    )


def run_matrix_validation(
    corpus_path: Path,
    *,
    scoring_model_version: str = SCORING_MODEL_VERSION,
    min_extraction_rate: float = 0.5,
    min_median_confidence: float = 0.6,
    min_component_coverage: float = 0.4,
) -> MatrixValidationReport:
    from disclosure_alpha.validation.matrix_corpus import load_matrix_corpus

    rows, _ = load_matrix_corpus(corpus_path)
    report = evaluate_matrix_gates(
        rows,
        min_extraction_rate=min_extraction_rate,
        min_median_confidence=min_median_confidence,
        min_component_coverage=min_component_coverage,
        scoring_model_version=scoring_model_version,
    )
    report.corpus_path = str(corpus_path)
    return report


def write_matrix_validation_report(report: MatrixValidationReport, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out_path
