"""Tests for full-matrix validation corpus and gates."""

from __future__ import annotations

import json
from pathlib import Path

from disclosure_alpha.edgar.types import FilingRef
from disclosure_alpha.pipeline import FilingBundle
from disclosure_alpha.validation.edgar_build import build_matrix_row
from disclosure_alpha.validation.matrix_corpus import load_matrix_corpus, sections_for_form
from disclosure_alpha.validation.matrix_gates import evaluate_matrix_gates
from html_fixtures import minimal_10k_html, minimal_prior_html

FIXTURE = Path(__file__).parent / "fixtures" / "validation" / "matrix_mini_corpus.jsonl"

def _demo_bundle(*, with_prior: bool = True) -> FilingBundle:
    ref = FilingRef(
        cik="0000000001",
        ticker="DEMO",
        accession_number="0000000001-25-000001",
        form_type="10-K",
        fiscal_year=2025,
        quarter=None,
        filing_date="2025-10-31",
        report_date="2025-09-30",
        primary_document="demo.htm",
    )
    return FilingBundle(
        ref=ref,
        html=minimal_10k_html(),
        prior_html=minimal_prior_html() if with_prior else None,
        prior_accession="0000000001-24-000001" if with_prior else None,
    )


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
        scoring_model_version="v1",
    )
    assert report.n_filings == 2
    assert report.gates["non_empty_corpus"].status == "pass"
    assert report.component_coverage
    assert report.versions["scoring_model_version"] == "deterministic_scoring_v1"


def test_sections_for_form():
    assert "item_7_mdna" in sections_for_form("10-K")
    assert "item_7a_market_risk" in sections_for_form("10-K")
    assert "item_2_mdna" in sections_for_form("10-Q")
    assert "item_1_05" in sections_for_form("8-K")


def test_edgar_matrix_row_from_bundle(monkeypatch):
    def fake_load(*_a, **kwargs):
        return _demo_bundle(with_prior=kwargs.get("compare_prior", True))

    monkeypatch.setattr(
        "disclosure_alpha.validation.edgar_build.load_filing_bundle",
        fake_load,
    )
    row, err = build_matrix_row("DEMO", 2025, form_type="10-K")
    assert err is None
    assert row is not None
    assert row["ticker"] == "DEMO"
    assert "item_1a_risk_factors" in row["sections"]
    assert "item_7_mdna" in row["sections"]
    assert "item_1a_risk_factors" in row["prior_sections"]
    assert row["quality"]["item_1a_risk_factors"]["extraction_confidence"] is not None


def test_edgar_matrix_row_writes_jsonl(tmp_path, monkeypatch):
    def fake_load(*_a, **kwargs):
        return _demo_bundle(with_prior=kwargs.get("compare_prior", True))

    monkeypatch.setattr(
        "disclosure_alpha.validation.edgar_build.load_filing_bundle",
        fake_load,
    )
    out = tmp_path / "matrix.jsonl"
    row, err = build_matrix_row("DEMO", 2025, form_type="10-K")
    assert err is None
    out.write_text(json.dumps(row) + "\n", encoding="utf-8")
    rows, meta = load_matrix_corpus(out)
    assert meta["n_loaded"] == 1
    assert rows[0].ticker == "DEMO"
    assert rows[0].prior_sections
