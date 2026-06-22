"""Tests for full-matrix validation corpus and gates."""

from __future__ import annotations

from pathlib import Path

from disclosure_alpha.validation.matrix_corpus import load_matrix_corpus, sections_for_form
from disclosure_alpha.validation.matrix_gates import evaluate_matrix_gates

FIXTURE = Path(__file__).parent / "fixtures" / "validation" / "matrix_mini_corpus.jsonl"


def test_matrix_corpus_loads_fixture():
    rows, meta = load_matrix_corpus(FIXTURE)
    assert meta["n_loaded"] == 2
    assert rows[0].ticker == "DEMO1"
    assert "item_1a_risk_factors" in rows[0].sections


def test_matrix_gates_smoke():
    rows, _ = load_matrix_corpus(FIXTURE)
    report = evaluate_matrix_gates(
        rows,
        min_extraction_rate=0.3,
        min_median_confidence=0.5,
        min_component_coverage=0.2,
    )
    assert report.n_filings == 2
    assert report.gates["non_empty_corpus"].status == "pass"
    assert report.component_coverage


def test_sections_for_form():
    assert "item_7_mdna" in sections_for_form("10-K")
    assert "item_2_mdna" in sections_for_form("10-Q")
    assert "item_1_05" in sections_for_form("8-K")
