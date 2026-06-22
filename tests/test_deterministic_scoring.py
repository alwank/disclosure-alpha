from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix
from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS


_BASE_METRICS = {
    "item_1a_risk_factors": {
        "negative_word_ratio": 0.1,
        "uncertainty_word_ratio": 0.1,
        "litigious_word_ratio": 0.05,
        "boilerplate_phrase_ratio": 0.1,
        "numeric_specificity_score": 20,
        "company_specificity_score": 30,
        "constraining_word_ratio": 0.02,
    },
    "item_7_mdna": {
        "uncertainty_word_ratio": 0.08,
        "modal_word_ratio": 0.05,
        "readability_score": 40,
        "constraining_word_ratio": 0.02,
    },
}

_BASE_DIFFS = {"item_1a_risk_factors": 55, "item_7_mdna": 45}


def test_deterministic_without_llm():
    agg = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
    )
    assert agg.overall_disclosure_risk_score is not None
    assert agg.components.disclosure_change_score is not None
    assert agg.components.specificity_quality_score is not None
    assert len(agg.provenance) == 10
    assert agg.provenance[0].score_name == "risk_factor_intensity_score"


def test_deterministic_replay_identical():
    kwargs = {
        "section_metrics": _BASE_METRICS,
        "section_diffs": _BASE_DIFFS,
        "section_flags": {"item_7_mdna": {"going_concern_flag": False}},
        "section_densities": {
            "item_7_mdna": {
                "uncertainty_term_density": 5.0,
                "liquidity_constraint_density": 3.0,
            }
        },
    }
    first = aggregate_deterministic_matrix(**kwargs)
    second = aggregate_deterministic_matrix(**kwargs)
    assert first.overall_disclosure_risk_score == second.overall_disclosure_risk_score
    assert first.components.__dict__ == second.components.__dict__


def test_missing_diff_null_not_zero():
    agg = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs={},
    )
    assert agg.components.disclosure_change_score is None


def test_empty_metrics_have_no_weighted_coverage():
    agg = aggregate_deterministic_matrix(section_metrics={}, section_diffs={})

    assert agg.overall_disclosure_risk_score is None
    assert agg.score_coverage_ratio == 0.0
    assert set(agg.missing_components) == set(COMPONENT_WEIGHTS)


def test_missing_item_1a_does_not_synthesize_item_1a_scores():
    agg = aggregate_deterministic_matrix(
        section_metrics={
            "item_7_mdna": {
                "uncertainty_word_ratio": 0.05,
                "modal_word_ratio": 0.03,
                "readability_score": 35,
                "constraining_word_ratio": 0.02,
            }
        },
        section_diffs={"item_1a_risk_factors": 50, "item_7_mdna": 20},
        language_deltas={"item_1a_risk_factors": {"legal_language_delta": 10.0}},
    )

    assert agg.components.risk_factor_intensity_score is None
    assert agg.components.legal_regulatory_risk_score is None
    assert agg.components.boilerplate_risk_score is None
    assert "risk_factor_intensity_score" in agg.missing_components
    assert "legal_regulatory_risk_score" in agg.missing_components
    assert "boilerplate_risk_score" in agg.missing_components


def test_missing_mdna_does_not_synthesize_mdna_scores():
    agg = aggregate_deterministic_matrix(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.01,
                "uncertainty_word_ratio": 0.01,
                "litigious_word_ratio": 0.01,
                "boilerplate_phrase_ratio": 0.01,
                "numeric_specificity_score": 10,
                "company_specificity_score": 10,
            }
        },
        section_diffs={},
        section_densities={"item_7_mdna": {"liquidity_constraint_density": 50.0}},
    )

    assert agg.components.mdna_uncertainty_score is None
    assert agg.components.liquidity_stress_score is None
    assert "mdna_uncertainty_score" in agg.missing_components
    assert "liquidity_stress_score" in agg.missing_components


def test_explicit_zero_metric_values_count_as_present_evidence():
    agg = aggregate_deterministic_matrix(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.0,
                "uncertainty_word_ratio": 0.0,
                "litigious_word_ratio": 0.0,
                "boilerplate_phrase_ratio": 0.0,
                "numeric_specificity_score": 0.0,
                "company_specificity_score": 0.0,
                "constraining_word_ratio": 0.0,
            },
            "item_7_mdna": {
                "uncertainty_word_ratio": 0.0,
                "modal_word_ratio": 0.0,
                "readability_score": 0.0,
                "constraining_word_ratio": 0.0,
            },
        },
        section_diffs={"item_1a_risk_factors": 0.0, "item_7_mdna": 0.0},
    )

    assert agg.components.risk_factor_intensity_score == 0.0
    assert agg.components.mdna_uncertainty_score == 0.0
    assert agg.components.liquidity_stress_score == 0.0
    assert agg.components.legal_regulatory_risk_score == 0.0
    assert agg.components.disclosure_change_score == 0.0
    assert agg.components.event_severity_score == 0.0
    assert agg.components.boilerplate_risk_score is not None
    assert abs(agg.components.boilerplate_risk_score - 66.66666666666667) < 1e-12
    assert agg.score_coverage_ratio == 1.0


def test_flag_boost_cap_at_100():
    agg = aggregate_deterministic_matrix(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.5,
                "uncertainty_word_ratio": 0.5,
                "litigious_word_ratio": 0.5,
                "boilerplate_phrase_ratio": 0.1,
                "numeric_specificity_score": 5,
                "company_specificity_score": 5,
                "constraining_word_ratio": 0.5,
            },
            "item_7_mdna": {
                "uncertainty_word_ratio": 0.5,
                "modal_word_ratio": 0.5,
                "constraining_word_ratio": 0.5,
                "readability_score": 90,
            },
        },
        section_diffs={"item_1a_risk_factors": 95, "item_7_mdna": 95},
        section_flags={
            "item_7_mdna": {"going_concern_flag": True, "covenant_breach_flag": True},
            "item_1a_risk_factors": {
                "investigation_flag": True,
                "material_legal_proceeding_flag": True,
            },
        },
    )
    assert agg.components.liquidity_stress_score is not None
    assert agg.components.liquidity_stress_score <= 100
    assert agg.components.legal_regulatory_risk_score is not None
    assert agg.components.legal_regulatory_risk_score <= 100


def test_coverage_math_partial_components():
    agg = aggregate_deterministic_matrix(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.01,
                "uncertainty_word_ratio": 0.01,
                "litigious_word_ratio": 0.01,
                "boilerplate_phrase_ratio": 0.01,
                "numeric_specificity_score": 10,
                "company_specificity_score": 10,
            }
        },
        section_diffs={},
    )
    assert agg.missing_components
    expected_coverage = (9 - len(agg.missing_components)) / 9
    assert abs(agg.score_coverage_ratio - expected_coverage) < 0.01


def test_deterministic_coverage_partial_without_mdna():
    agg = aggregate_deterministic_matrix(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.01,
                "uncertainty_word_ratio": 0.01,
                "litigious_word_ratio": 0.01,
                "boilerplate_phrase_ratio": 0.01,
                "numeric_specificity_score": 10,
                "company_specificity_score": 10,
            }
        },
        section_diffs={},
    )
    assert agg.missing_components
    assert agg.score_coverage_ratio < 1.0


def test_mdna_densities_raise_uncertainty():
    base = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
    )
    with_density = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
        section_densities={
            "item_7_mdna": {
                "uncertainty_term_density": 40.0,
                "demand_softness_density": 30.0,
                "margin_pressure_density": 25.0,
            }
        },
    )
    assert with_density.components.mdna_uncertainty_score is not None
    assert base.components.mdna_uncertainty_score is not None
    assert with_density.components.mdna_uncertainty_score > base.components.mdna_uncertainty_score


def test_liquidity_density_wired():
    base = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
    )
    with_density = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
        section_densities={"item_7_mdna": {"liquidity_constraint_density": 50.0}},
    )
    assert with_density.components.liquidity_stress_score is not None
    assert base.components.liquidity_stress_score is not None
    assert with_density.components.liquidity_stress_score > base.components.liquidity_stress_score


def test_legal_language_delta_blend():
    base = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
    )
    with_delta = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
        language_deltas={
            "item_1a_risk_factors": {"legal_language_delta": 20.0},
        },
    )
    assert with_delta.components.legal_regulatory_risk_score is not None
    assert base.components.legal_regulatory_risk_score is not None
    assert with_delta.components.legal_regulatory_risk_score > base.components.legal_regulatory_risk_score


def test_flag_boost_raises_liquidity_not_wildly():
    base = aggregate_deterministic_matrix(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.05,
                "uncertainty_word_ratio": 0.05,
                "litigious_word_ratio": 0.02,
                "boilerplate_phrase_ratio": 0.05,
                "numeric_specificity_score": 30,
                "company_specificity_score": 30,
                "constraining_word_ratio": 0.02,
            },
            "item_7_mdna": {
                "uncertainty_word_ratio": 0.05,
                "modal_word_ratio": 0.03,
                "constraining_word_ratio": 0.02,
                "readability_score": 35,
            },
        },
        section_diffs={"item_1a_risk_factors": 40, "item_7_mdna": 35},
    )
    boosted = aggregate_deterministic_matrix(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.05,
                "uncertainty_word_ratio": 0.05,
                "litigious_word_ratio": 0.02,
                "boilerplate_phrase_ratio": 0.05,
                "numeric_specificity_score": 30,
                "company_specificity_score": 30,
                "constraining_word_ratio": 0.02,
            },
            "item_7_mdna": {
                "uncertainty_word_ratio": 0.05,
                "modal_word_ratio": 0.03,
                "constraining_word_ratio": 0.02,
                "readability_score": 35,
            },
        },
        section_diffs={"item_1a_risk_factors": 40, "item_7_mdna": 35},
        section_flags={"item_7_mdna": {"going_concern_flag": True}},
    )
    assert boosted.components.liquidity_stress_score is not None
    assert base.components.liquidity_stress_score is not None
    delta = boosted.components.liquidity_stress_score - base.components.liquidity_stress_score
    assert 0 < delta <= 15
    assert abs(boosted.overall_disclosure_risk_score - base.overall_disclosure_risk_score) < 5


def test_10q_mdna_section_used():
    agg = aggregate_deterministic_matrix(
        section_metrics={
            "item_1a_risk_factors": _BASE_METRICS["item_1a_risk_factors"],
            "item_2_mdna": _BASE_METRICS["item_7_mdna"],
        },
        section_diffs={"item_1a_risk_factors": 10, "item_2_mdna": 20},
    )
    assert agg.components.mdna_uncertainty_score is not None
    assert agg.components.liquidity_stress_score is not None


def test_guidance_withdrawal_flag_boosts_mdna():
    base = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
    )
    flagged = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
        section_flags={"item_7_mdna": {"guidance_withdrawal_flag": True}},
    )
    assert flagged.components.mdna_uncertainty_score is not None
    assert base.components.mdna_uncertainty_score is not None
    assert flagged.components.mdna_uncertainty_score > base.components.mdna_uncertainty_score


def test_disclosure_quality_score_zero_boilerplate():
    agg = aggregate_deterministic_matrix(
        section_metrics={
            "item_1a_risk_factors": {
                "boilerplate_phrase_ratio": 0.0,
                "numeric_specificity_score": 100.0,
                "company_specificity_score": 100.0,
            },
        },
        section_diffs={},
    )

    assert agg.components.boilerplate_risk_score == 0.0
    assert agg.aggregates.disclosure_quality_score == 100.0


def test_disclosure_quality_aggregate():
    agg = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
    )
    assert agg.aggregates.disclosure_quality_score is not None
    assert agg.aggregates.disclosure_deterioration_score is not None


def test_confidence_bounds():
    from disclosure_alpha.pipeline import MetricsResult, score_deterministic

    empty = score_deterministic(
        MetricsResult(
            section_metrics={},
            section_diffs={},
            section_flags={},
            section_densities={},
            language_deltas={},
        )
    )
    full = score_deterministic(
        MetricsResult(
            section_metrics=_BASE_METRICS,
            section_diffs=_BASE_DIFFS,
            section_flags={},
            section_densities={},
            language_deltas={},
            extraction_confs=[0.85, 0.9],
            diff_confs=[0.8, 0.75],
        )
    )
    assert 0.0 <= empty.confidence_score <= 1.0
    assert 0.0 <= full.confidence_score <= 1.0
    assert full.confidence_score > empty.confidence_score


def test_blend_evidence_weighted_average():
    from disclosure_alpha.scoring_types import ScoreEvidence, blend_evidence

    score, inputs = blend_evidence(
        [
            ScoreEvidence("a", 40.0, 0.5, section="s1", raw_value=0.4),
            ScoreEvidence("b", 80.0, 0.5, section="s2", raw_value=0.8),
        ]
    )
    assert score == 60.0
    assert "a" in inputs and inputs["a"]["section"] == "s1"


def test_v2_material_weakness_without_item_1a():
    from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix_v2

    agg = aggregate_deterministic_matrix_v2(
        section_metrics={},
        section_diffs={},
        section_flags={"item_9a_controls": {"material_weakness_flag": True}},
    )
    assert agg.components.internal_controls_risk_score is not None
    assert "internal_controls_risk_score" not in agg.missing_components


def test_v2_legal_flag_without_item_1a():
    from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix_v2

    agg = aggregate_deterministic_matrix_v2(
        section_metrics={},
        section_diffs={},
        section_flags={"item_3_legal_proceedings": {"investigation_flag": True}},
    )
    assert agg.components.legal_regulatory_risk_score is not None


def test_v2_going_concern_without_mdna():
    from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix_v2

    agg = aggregate_deterministic_matrix_v2(
        section_metrics={},
        section_diffs={},
        section_flags={"item_7_mdna": {"going_concern_flag": True}},
    )
    assert agg.components.liquidity_stress_score is not None


def test_v1_unchanged_flag_without_base_stays_null():
    agg = aggregate_deterministic_matrix(
        section_metrics={},
        section_diffs={},
        section_flags={"item_9a_controls": {"material_weakness_flag": True}},
    )
    assert agg.components.internal_controls_risk_score is None


def test_aggregate_split_scores():
    agg = aggregate_deterministic_matrix(
        section_metrics=_BASE_METRICS,
        section_diffs=_BASE_DIFFS,
    )
    assert agg.aggregates.static_disclosure_risk_score is not None
    assert agg.aggregates.disclosure_change_risk_score is not None
    assert agg.aggregates.static_disclosure_quality_score is not None
    assert agg.overall_disclosure_risk_score is not None


def test_v2_cyber_incident_score_item_105():
    from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix_v2

    agg = aggregate_deterministic_matrix_v2(
        section_metrics={},
        section_diffs={},
        section_flags={"item_1_05": {"cybersecurity_incident_flag": True}},
    )
    assert agg.components.cybersecurity_incident_risk_score is not None
    # item_1c is governance-only scope; incident flag there must not score
    agg_gov = aggregate_deterministic_matrix_v2(
        section_metrics={},
        section_diffs={},
        section_flags={"item_1c_cybersecurity": {"cybersecurity_incident_flag": True}},
    )
    assert agg_gov.components.cybersecurity_incident_risk_score is None


def test_v2_cyber_governance_item_1c_no_incident_score():
    from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix_v2

    agg = aggregate_deterministic_matrix_v2(
        section_metrics={
            "item_1c_cybersecurity": {
                "negative_word_ratio": 0.01,
                "uncertainty_word_ratio": 0.01,
            }
        },
        section_diffs={},
        section_flags={"item_1c_cybersecurity": {"cybersecurity_incident_flag": False}},
    )
    assert agg.components.cybersecurity_incident_risk_score is None


def test_v2_event_materiality_8k():
    from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix_v2

    agg = aggregate_deterministic_matrix_v2(
        section_metrics={
            "item_8_01": {
                "uncertainty_word_ratio": 0.08,
                "negative_word_ratio": 0.05,
            }
        },
        section_diffs={},
        section_flags={"item_8_01": {"investigation_flag": True}},
    )
    assert agg.components.event_materiality_score is not None
