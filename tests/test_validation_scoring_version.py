"""Tests for validation scoring version routing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from disclosure_alpha.pipeline import compute_section_metrics, score_deterministic, score_deterministic_v2
from disclosure_alpha.section_extractor import ExtractedSection
from disclosure_alpha.validation.construct import ConstructConfig, run_construct_validation
from disclosure_alpha.validation.matrix_gates import evaluate_matrix_gates, run_matrix_validation
from disclosure_alpha.validation.matrix_corpus import load_matrix_corpus
from disclosure_alpha.validation.outcomes_validation import (
    OutcomesValidationConfig,
    score_item1a_from_corpus_row,
)
from disclosure_alpha.validation.scoring_version import normalize_scoring_version
from disclosure_alpha.version import SCORING_MODEL_VERSION, SCORING_MODEL_VERSION_V2

FIXTURES = Path(__file__).parent / "fixtures" / "validation"
MINI_CORPUS = FIXTURES / "mini_corpus.jsonl"
MATRIX_CORPUS = FIXTURES / "matrix_mini_corpus.jsonl"


def test_normalize_scoring_version():
    assert normalize_scoring_version("v1") == SCORING_MODEL_VERSION
    assert normalize_scoring_version("v2") == SCORING_MODEL_VERSION_V2
    with pytest.raises(ValueError):
        normalize_scoring_version("v3")


def test_construct_report_records_v2_version():
    report = run_construct_validation(
        MINI_CORPUS,
        config=ConstructConfig(min_n=3, boilerplate_min_docs=2, scoring_model_version="v2"),
    )
    assert report.versions["scoring_model_version"] == SCORING_MODEL_VERSION_V2


def test_score_item1a_from_corpus_row_v2_differs_from_v1():
    row = json.loads(MINI_CORPUS.read_text(encoding="utf-8").splitlines()[0])
    v1 = score_item1a_from_corpus_row(row, scoring_model_version="v1")
    v2 = score_item1a_from_corpus_row(row, scoring_model_version="v2")
    assert v1["overall_disclosure_risk_score"] is not None
    assert v2["overall_disclosure_risk_score"] is not None
    assert v1 != v2


def test_matrix_gates_v2_smoke():
    rows, _ = load_matrix_corpus(MATRIX_CORPUS)
    report = evaluate_matrix_gates(
        rows,
        min_extraction_rate=0.3,
        min_median_confidence=0.5,
        min_component_coverage=0.2,
        scoring_model_version="v2",
    )
    assert report.versions["scoring_model_version"] == SCORING_MODEL_VERSION_V2
    assert report.gates["non_empty_corpus"].status == "pass"


def test_run_matrix_validation_records_corpus_path(tmp_path: Path):
    report = run_matrix_validation(
        MATRIX_CORPUS,
        scoring_model_version="v2",
        min_extraction_rate=0.3,
        min_median_confidence=0.5,
        min_component_coverage=0.2,
    )
    assert report.corpus_path == str(MATRIX_CORPUS)
    assert report.versions["scoring_model_version"] == SCORING_MODEL_VERSION_V2


def test_v2_pipeline_entry_point_on_section_metrics():
    section = ExtractedSection(
        "item_1a_risk_factors",
        "We face competition and litigation risk. Revenue may decline materially.",
        "We face competition and litigation risk. Revenue may decline materially.",
        "hash",
        12,
        2,
        0.9,
        "test",
        "fixture",
    )
    metrics = compute_section_metrics([section], prior_sections=None)
    v1 = score_deterministic(metrics)
    v2 = score_deterministic_v2(metrics)
    assert v1.overall_disclosure_risk_score is not None
    assert v2.overall_disclosure_risk_score is not None


def test_outcomes_config_defaults_to_v1():
    cfg = OutcomesValidationConfig()
    assert cfg.scoring_model_version == SCORING_MODEL_VERSION
