"""Tests for full-matrix validation corpus and gates."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from disclosure_alpha.edgar.types import FilingRef
from disclosure_alpha.pipeline import FilingBundle
from disclosure_alpha.validation.matrix_corpus import load_matrix_corpus, sections_for_form
from disclosure_alpha.validation.matrix_gates import evaluate_matrix_gates
from html_fixtures import minimal_10k_html, minimal_prior_html

FIXTURE = Path(__file__).parent / "fixtures" / "validation" / "matrix_mini_corpus.jsonl"
BUILDER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_matrix_validation_corpus_from_edgar.py"


def _load_edgar_matrix_builder():
    spec = importlib.util.spec_from_file_location("build_matrix_edgar", BUILDER_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


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
    assert "item_2_mdna" in sections_for_form("10-Q")
    assert "item_1_05" in sections_for_form("8-K")


def test_edgar_matrix_row_from_bundle():
    builder = _load_edgar_matrix_builder()
    row = builder.matrix_row_from_bundle(_demo_bundle(), form_type="10-K")
    assert row is not None
    assert row["ticker"] == "DEMO"
    assert "item_1a_risk_factors" in row["sections"]
    assert "item_7_mdna" in row["sections"]
    assert "item_1a_risk_factors" in row["prior_sections"]
    assert row["quality"]["item_1a_risk_factors"]["extraction_confidence"] is not None


def test_edgar_matrix_builder_smoke(tmp_path, monkeypatch):
    builder = _load_edgar_matrix_builder()
    universe = tmp_path / "universe.csv"
    universe.write_text("ticker,cik\nDEMO,0000000001\n", encoding="utf-8")
    out = tmp_path / "matrix.jsonl"
    manifest = tmp_path / "matrix.manifest.json"

    def fake_load(*_a, **kwargs):
        return _demo_bundle(with_prior=kwargs.get("compare_prior", True))

    monkeypatch.setattr(builder, "load_filing_bundle", fake_load)
    monkeypatch.setattr(builder, "manifest_path_for", lambda p: manifest)

    argv = [
        "build_matrix_validation_corpus_from_edgar.py",
        "--fiscal-year",
        "2025",
        "--universe",
        str(universe),
        "--out",
        str(out),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    builder.main()

    rows, meta = load_matrix_corpus(out)
    assert meta["n_loaded"] == 1
    assert rows[0].ticker == "DEMO"
    assert rows[0].prior_sections
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["n_new"] == 1
    assert manifest_data["compare_prior"] is True
