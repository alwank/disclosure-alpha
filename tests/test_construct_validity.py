from __future__ import annotations

import json
from pathlib import Path

import pytest

from disclosure_alpha.validation.construct import (
    ConstructConfig,
    run_construct_validation,
    spearman_rho,
)
from disclosure_alpha.validation.corpus import CorpusLoadConfig, load_corpus
from disclosure_alpha.validation.edgar_gates import EdgarGatesConfig, evaluate_edgar_gates
from disclosure_alpha.validation.references.boilerplate import compute_ls_boilerplate_ratios
from disclosure_alpha.validation.types import CorpusRow
from disclosure_alpha.validation.universe import load_universe

FIXTURES = Path(__file__).parent / "fixtures" / "validation"
MINI_CORPUS = FIXTURES / "mini_corpus.jsonl"


def test_sp500_universe_loads():
    path = Path(__file__).resolve().parents[1] / "data" / "universe" / "sp500.csv"
    if not path.exists():
        pytest.skip("sp500.csv not present")
    entries = load_universe(path)
    assert len(entries) >= 500
    assert entries[0].ticker
    assert "AAPL" in {e.ticker for e in entries}


def test_universe_coverage_in_report():
    path = Path(__file__).resolve().parents[1] / "data" / "universe" / "sp500.csv"
    if not path.exists():
        pytest.skip("sp500.csv not present")
    report = run_construct_validation(
        MINI_CORPUS,
        config=ConstructConfig(
            min_n=3,
            boilerplate_min_docs=2,
            universe_path=path,
        ),
    )
    assert report.corpus["universe_expected"] >= 500
    assert report.corpus["universe_present"] == 3


def test_corpus_loader_filters(tmp_path: Path):
    rows = [
        {
            "ticker": "GOOD",
            "section_name": "item_1a_risk_factors",
            "cleaned_text": "word " * 250,
            "extraction_confidence": 0.9,
        },
        {
            "ticker": "SHORT",
            "section_name": "item_1a_risk_factors",
            "cleaned_text": "too short",
            "extraction_confidence": 0.9,
        },
        {
            "ticker": "LOWCONF",
            "section_name": "item_1a_risk_factors",
            "cleaned_text": "word " * 250,
            "extraction_confidence": 0.5,
        },
    ]
    path = tmp_path / "corpus.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    loaded, meta = load_corpus(
        path,
        config=CorpusLoadConfig(min_word_count=200, min_confidence=0.75),
    )
    assert meta["n_input"] == 3
    assert meta["n_after_filters"] == 1
    assert loaded[0].ticker == "GOOD"


def test_filter_breakdown(tmp_path: Path):
    rows = [
        {
            "ticker": "GOOD",
            "section_name": "item_1a_risk_factors",
            "cleaned_text": "word " * 250,
            "extraction_confidence": 0.9,
        },
        {
            "ticker": "SHORT",
            "section_name": "item_1a_risk_factors",
            "cleaned_text": "too short",
            "extraction_confidence": 0.9,
        },
        {
            "ticker": "LOWCONF",
            "section_name": "item_1a_risk_factors",
            "cleaned_text": "word " * 250,
            "extraction_confidence": 0.5,
        },
        {
            "ticker": "WRONG",
            "section_name": "item_7_mdna",
            "cleaned_text": "word " * 250,
            "extraction_confidence": 0.9,
        },
    ]
    path = tmp_path / "corpus.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    _, meta = load_corpus(path)
    breakdown = meta["filter_breakdown"]
    assert breakdown["short_text"] == 1
    assert breakdown["low_confidence"] == 1
    assert breakdown["wrong_section"] == 1
    assert "SHORT" in meta["filtered_tickers_sample"]
    assert "LOWCONF" in meta["filtered_tickers_sample"]


def test_boilerplate_reference_monotonic():
    shared = "alpha beta gamma delta epsilon zeta eta theta iota kappa "
    rows = [
        CorpusRow("A", 2025, "item_1a_risk_factors", shared * 5, 200, 0.9),
        CorpusRow("B", 2025, "item_1a_risk_factors", shared * 5, 200, 0.9),
        CorpusRow("C", 2025, "item_1a_risk_factors", "unique words only here " * 30, 200, 0.9),
    ]
    ratios = compute_ls_boilerplate_ratios(rows, min_doc_freq=2, min_doc_frac=0.25)
    assert ratios["A"] > ratios["C"]
    assert ratios["B"] > ratios["C"]


def test_construct_report_shape():
    report = run_construct_validation(
        MINI_CORPUS,
        config=ConstructConfig(min_n=3, boilerplate_min_docs=2),
    )
    d = report.to_dict()
    assert d["validation_level"] == "L2"
    assert set(d["pairs"]) == {
        "specificity_vs_ner",
        "boilerplate_vs_ls4gram",
    }
    assert "edgar_gates" in d
    assert "edgar_pass" in d
    assert "construct_pass" in d
    assert d["overall_l2_pass"] == (d["edgar_pass"] and d["construct_pass"])
    assert d["corpus"]["n_after_filters"] == 3


def test_edgar_gates_pass_fail():
    rows = [
        CorpusRow("A", 2025, "item_1a_risk_factors", "word " * 250, 250, 0.9),
        CorpusRow("B", 2025, "item_1a_risk_factors", "word " * 250, 250, 0.85),
    ]
    meta = {
        "universe_expected": 2,
        "n_input": 2,
        "n_after_filters": 2,
    }
    gates, edgar_pass, _ = evaluate_edgar_gates(
        meta,
        rows,
        config=EdgarGatesConfig(min_analysis_n=2),
    )
    assert edgar_pass
    assert gates["E2_analysis_rate"].status == "pass"
    assert gates["E4_median_confidence"].status == "pass"

    bad_meta = {
        "universe_expected": 100,
        "n_input": 50,
        "n_after_filters": 40,
    }
    _, edgar_fail, _ = evaluate_edgar_gates(bad_meta, rows)
    assert not edgar_fail
    assert gates["E1_fetch_rate"].threshold == 0.90


def test_spearman_perfect_correlation():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert spearman_rho(xs, xs) == pytest.approx(1.0)


def test_ner_pair_runs_when_spacy_available():
    pytest.importorskip("spacy")
    report = run_construct_validation(
        MINI_CORPUS,
        config=ConstructConfig(min_n=3, boilerplate_min_docs=2),
    )
    pair = report.pairs["specificity_vs_ner"]
    if pair.status == "skipped" and pair.message:
        if "not installed" in pair.message or "not found" in pair.message:
            pytest.skip(pair.message)
    assert pair.status in ("pass", "fail")
