"""Tests for OpenBB core helpers."""

from __future__ import annotations

from disclosure_alpha.openbb.adapters import flag_section_groups, flag_summary, score_card_context
from disclosure_alpha.openbb.corpus import corpus_context
from disclosure_alpha.openbb.labels import format_score, risk_band, section_changes_subtitle
from disclosure_alpha.openbb.demo import is_demo


def test_risk_band_boundaries():
    assert risk_band(24.9) == "low"
    assert risk_band(25.0) == "low"
    assert risk_band(26.0) == "moderate"
    assert risk_band(50.0) == "moderate"
    assert risk_band(51.0) == "elevated"
    assert risk_band(None) == "missing"


def test_risk_band_inverted_specificity():
    assert risk_band(80.0, inverted=True) == "low"


def test_format_score_none():
    assert format_score(None) == "—"


def test_is_demo():
    assert is_demo("1")
    assert is_demo("true")
    assert not is_demo(None)
    assert not is_demo("0")


def test_corpus_context_aapl():
    ctx = corpus_context("AAPL", 20.7, 2025, "10-K")
    assert ctx is not None
    assert ctx["n"] == 502
    assert ctx["median"] == 19.4
    assert 0 <= ctx["percentile_rank"] <= 100


def test_corpus_context_wrong_year():
    assert corpus_context("AAPL", 20.7, 2024, "10-K") is None


def test_score_card_context_shape():
    ctx = score_card_context(
        {"ticker": "AAPL", "fiscal_year": 2025, "form_type": "10-K"},
        {
            "overall_disclosure_risk_score": 20.0,
            "score_coverage_ratio": 1.0,
            "confidence_score": 0.9,
            "missing_components": [],
            "components": {"risk_factor_intensity_score": 10.0},
        },
        {"parser_version": "section_extractor_v1"},
    )
    assert ctx["overall"] == 20.0
    assert len(ctx["headline_rows"]) == 9


def test_flag_summary_groups_multi_section():
    active = [
        {"section": "item_1a_risk_factors", "flag": "investigation_flag", "label": "Investigation"},
        {"section": "item_3_legal_proceedings", "flag": "investigation_flag", "label": "Investigation"},
        {"section": "item_9a_controls", "flag": "restatement_flag", "label": "Restatement"},
    ]
    summary = flag_summary(active)
    assert len(summary) == 2
    inv = next(r for r in summary if r["flag"] == "investigation_flag")
    assert inv["section_count"] == 2
    assert inv["tier"] == "elevated"

    groups = flag_section_groups(active)
    assert len(groups) == 3
    assert groups[0]["section"] == "item_1a_risk_factors"
    assert groups[0]["section_label"] == "Item 1A Risk Factors"


def test_flag_summary_empty():
    assert flag_summary([]) == []
    assert flag_section_groups([]) == []


def test_section_changes_subtitle_by_form():
    assert "Year-over-year" in section_changes_subtitle("10-K")
    assert "Quarter-over-quarter" in section_changes_subtitle("10-Q")
