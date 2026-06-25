"""Tests for cross-firm boilerplate metrics."""

from __future__ import annotations

import json
from pathlib import Path

from disclosure_alpha.boilerplate import (
    DEFAULT_BLEND_WEIGHTS,
    baseline_artifact_path,
    blend_boilerplate_ratios,
    boilerplate_cross_firm_word_ratio,
    build_boilerplate_gram_set_from_texts,
    load_boilerplate_gram_set,
    write_baseline_artifact,
)
from disclosure_alpha.validation.types import CorpusRow

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data" / "baselines" / "item_1a_risk_factors_boilerplate_4grams_fy2025.json"


def test_four_gram_set_flags_shared_language():
    shared = "alpha beta gamma delta epsilon zeta eta theta iota kappa "
    unique = "unique words only here " * 30
    gram_set = build_boilerplate_gram_set_from_texts(
        [shared * 5, shared * 5, unique],
        min_doc_freq=2,
        min_doc_frac=0.25,
    )
    assert gram_set
    assert boilerplate_cross_firm_word_ratio(shared * 5, gram_set) > boilerplate_cross_firm_word_ratio(
        unique, gram_set
    )


def test_blend_boilerplate_ratios_respects_weights():
    combined = blend_boilerplate_ratios(0.2, 0.8, weights=(0.4, 0.6))
    assert combined == 0.56
    assert blend_boilerplate_ratios(1.5, 1.5) == 1.0


def test_baseline_artifact_write_payload(tmp_path: Path):
    gram_set = frozenset({("alpha", "beta", "gamma", "delta")})
    path = tmp_path / "item_1a_risk_factors_boilerplate_4grams_fy2025.json"
    write_baseline_artifact(
        path,
        fiscal_year=2025,
        section="item_1a_risk_factors",
        gram_set=gram_set,
        n_docs=3,
        min_doc_freq=2,
        min_doc_frac=0.25,
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["gram_count"] == 1
    assert data["grams"][0] == ["alpha", "beta", "gamma", "delta"]


def test_committed_fy2025_baseline_loads():
    assert BASELINE.is_file()
    grams = load_boilerplate_gram_set(2025)
    assert grams is not None
    assert len(grams) > 0


def test_compute_ls_style_ratio_from_rows():
    from disclosure_alpha.boilerplate import compute_ls_boilerplate_ratios

    shared = "alpha beta gamma delta epsilon zeta eta theta iota kappa "
    rows = [
        CorpusRow("A", 2025, "item_1a_risk_factors", shared * 5, 200, 0.9),
        CorpusRow("B", 2025, "item_1a_risk_factors", shared * 5, 200, 0.9),
        CorpusRow("C", 2025, "item_1a_risk_factors", "unique words only here " * 30, 200, 0.9),
    ]
    ratios = compute_ls_boilerplate_ratios(rows, min_doc_freq=2, min_doc_frac=0.25)
    assert ratios["A"] > ratios["C"]
    assert ratios["B"] > ratios["C"]


def test_default_blend_weights():
    assert DEFAULT_BLEND_WEIGHTS == (0.4, 0.6)


def test_baseline_artifact_path():
    assert baseline_artifact_path(2025).name == "item_1a_risk_factors_boilerplate_4grams_fy2025.json"
