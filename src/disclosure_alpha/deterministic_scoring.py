"""Deterministic filing-level scores from text metrics and diffs only."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from disclosure_alpha.scoring_types import (
    COMPONENT_WEIGHTS,
    AggregateScores,
    ComponentScores,
    MatrixAggregationResult,
    blend_scores,
    clamp_score,
    overall_from_components,
)

# ponytail: subset of COMPONENT_WEIGHTS for deterministic headline; excludes LLM-only components
DETERMINISTIC_COMPONENT_WEIGHTS = {
    k: v for k, v in COMPONENT_WEIGHTS.items() if k != "cybersecurity_risk_score"
}


@dataclass
class DeterministicComponentProvenance:
    score_name: str
    value: float | None
    inputs: dict[str, Any] = field(default_factory=dict)
    source: str = "deterministic"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeterministicAggregationResult(MatrixAggregationResult):
    provenance: list[DeterministicComponentProvenance] = field(default_factory=list)


def _flag_boost(flags: dict[str, bool] | None, names: list[str]) -> float:
    if not flags:
        return 0.0
    return 15.0 if any(flags.get(n) for n in names) else 0.0


def _merged_flags(section_flags: dict[str, dict[str, bool]] | None) -> dict[str, bool]:
    merged: dict[str, bool] = {}
    if not section_flags:
        return merged
    for flags in section_flags.values():
        for name, value in flags.items():
            merged[name] = merged.get(name, False) or bool(value)
    return merged


def _language_delta_blend(
    language_deltas: dict[str, dict[str, float]] | None,
    section_names: list[str],
    *,
    key: str = "uncertainty_language_delta",
) -> float | None:
    if not language_deltas:
        return None
    values: list[float] = []
    for section in section_names:
        deltas = language_deltas.get(section, {})
        delta = deltas.get(key)
        if delta is not None:
            values.append(max(0.0, float(delta)))
    if not values:
        return None
    return sum(values) / len(values)


def _mdna_metrics(
    section_metrics: dict[str, dict[str, float]],
    section_densities: dict[str, dict[str, float]] | None,
) -> dict[str, float]:
    m_7 = dict(
        section_metrics.get("item_7_mdna", {}) or section_metrics.get("item_2_mdna", {})
    )
    density_key = "item_7_mdna" if "item_7_mdna" in (section_densities or {}) else "item_2_mdna"
    densities = (section_densities or {}).get(density_key, {})
    for key, value in densities.items():
        m_7[key] = value
    return m_7


def aggregate_deterministic_matrix(
    *,
    section_metrics: dict[str, dict[str, float]],
    section_diffs: dict[str, float | None],
    section_flags: dict[str, dict[str, bool]] | None = None,
    language_deltas: dict[str, dict[str, float]] | None = None,
    section_densities: dict[str, dict[str, float]] | None = None,
) -> DeterministicAggregationResult:
    m_1a = section_metrics.get("item_1a_risk_factors", {})
    m_7 = _mdna_metrics(section_metrics, section_densities)
    flags = _merged_flags(section_flags)
    provenance: list[DeterministicComponentProvenance] = []

    d_1a = section_diffs.get("item_1a_risk_factors")
    neg_1a = (m_1a.get("negative_word_ratio", 0) or 0) * 100
    unc_1a = (m_1a.get("uncertainty_word_ratio", 0) or 0) * 100
    risk_factor_intensity = blend_scores(neg_1a, unc_1a, d_1a, weights=[0.375, 0.375, 0.25])
    provenance.append(
        DeterministicComponentProvenance(
            score_name="risk_factor_intensity_score",
            value=clamp_score(risk_factor_intensity) if risk_factor_intensity is not None else None,
            inputs={
                "negative_word_ratio": m_1a.get("negative_word_ratio", 0),
                "uncertainty_word_ratio": m_1a.get("uncertainty_word_ratio", 0),
                "diff_1a": d_1a,
            },
        )
    )

    d_mdna = section_diffs.get("item_7_mdna") or section_diffs.get("item_2_mdna")
    disclosure_change = blend_scores(d_1a, d_mdna, weights=[0.6, 0.4])
    unc_delta = _language_delta_blend(
        language_deltas, ["item_1a_risk_factors", "item_7_mdna", "item_2_mdna"]
    )
    disclosure_inputs: dict[str, Any] = {"diff_1a": d_1a, "diff_mdna": d_mdna}
    if disclosure_change is not None and unc_delta is not None:
        disclosure_change = min(100.0, disclosure_change + unc_delta * 0.1)
        disclosure_inputs["uncertainty_language_delta_boost"] = unc_delta * 0.1
    provenance.append(
        DeterministicComponentProvenance(
            score_name="disclosure_change_score",
            value=clamp_score(disclosure_change) if disclosure_change is not None else None,
            inputs=disclosure_inputs,
        )
    )

    unc_mdna = (m_7.get("uncertainty_word_ratio", 0) or 0) * 100
    modal_mdna = (m_7.get("modal_word_ratio", 0) or 0) * 100
    mdna_uncertainty = blend_scores(
        unc_mdna,
        modal_mdna,
        m_7.get("readability_score"),
        m_7.get("uncertainty_term_density"),
        m_7.get("demand_softness_density"),
        m_7.get("margin_pressure_density"),
        weights=[0.40, 0.35, 0.25, 0.10, 0.05, 0.05],
    )
    guidance_boost = _flag_boost(flags, ["guidance_withdrawal_flag"])
    mdna_inputs: dict[str, Any] = {
        "uncertainty_word_ratio": m_7.get("uncertainty_word_ratio", 0),
        "modal_word_ratio": m_7.get("modal_word_ratio", 0),
        "readability_score": m_7.get("readability_score"),
        "uncertainty_term_density": m_7.get("uncertainty_term_density"),
        "demand_softness_density": m_7.get("demand_softness_density"),
        "margin_pressure_density": m_7.get("margin_pressure_density"),
        "guidance_withdrawal_flag": flags.get("guidance_withdrawal_flag", False),
        "flag_boost": guidance_boost,
    }
    if mdna_uncertainty is not None and guidance_boost:
        mdna_uncertainty = min(100.0, mdna_uncertainty + guidance_boost)
    provenance.append(
        DeterministicComponentProvenance(
            score_name="mdna_uncertainty_score",
            value=clamp_score(mdna_uncertainty) if mdna_uncertainty is not None else None,
            inputs=mdna_inputs,
        )
    )

    litigious = (m_1a.get("litigious_word_ratio", 0) or 0) * 100
    legal_delta = _language_delta_blend(
        language_deltas,
        [
            "item_1a_risk_factors",
            "item_3_legal_proceedings",
            "item_1_legal_proceedings",
        ],
        key="legal_language_delta",
    )
    legal_regulatory = blend_scores(litigious, legal_delta, weights=[0.70, 0.30])
    legal_flag_boost = _flag_boost(
        flags, ["investigation_flag", "material_legal_proceeding_flag"]
    )
    legal_inputs: dict[str, Any] = {
        "litigious_word_ratio": m_1a.get("litigious_word_ratio", 0),
        "legal_language_delta": legal_delta,
        "investigation_flag": flags.get("investigation_flag", False),
        "material_legal_proceeding_flag": flags.get("material_legal_proceeding_flag", False),
        "flag_boost": legal_flag_boost,
    }
    if legal_regulatory is not None and legal_flag_boost:
        legal_regulatory = min(100.0, legal_regulatory + legal_flag_boost)
    provenance.append(
        DeterministicComponentProvenance(
            score_name="legal_regulatory_risk_score",
            value=clamp_score(legal_regulatory) if legal_regulatory is not None else None,
            inputs=legal_inputs,
        )
    )

    constraining = (m_7.get("constraining_word_ratio", 0) or 0) * 100
    liquidity_stress = blend_scores(
        constraining,
        m_7.get("liquidity_constraint_density"),
        weights=[0.50, 0.35],
    )
    liquidity_flag_boost = _flag_boost(flags, ["going_concern_flag", "covenant_breach_flag"])
    liquidity_inputs: dict[str, Any] = {
        "constraining_word_ratio": m_7.get("constraining_word_ratio", 0),
        "liquidity_constraint_density": m_7.get("liquidity_constraint_density"),
        "going_concern_flag": flags.get("going_concern_flag", False),
        "covenant_breach_flag": flags.get("covenant_breach_flag", False),
        "flag_boost": liquidity_flag_boost,
    }
    if liquidity_stress is not None and liquidity_flag_boost:
        liquidity_stress = min(100.0, liquidity_stress + liquidity_flag_boost)
    provenance.append(
        DeterministicComponentProvenance(
            score_name="liquidity_stress_score",
            value=clamp_score(liquidity_stress) if liquidity_stress is not None else None,
            inputs=liquidity_inputs,
        )
    )

    boilerplate_risk = blend_scores(
        (m_1a.get("boilerplate_phrase_ratio", 0) or 0) * 100,
        100 - (m_1a.get("numeric_specificity_score") or 0),
        100 - (m_1a.get("company_specificity_score") or 0),
        weights=[1 / 3, 1 / 3, 1 / 3],
    )
    provenance.append(
        DeterministicComponentProvenance(
            score_name="boilerplate_risk_score",
            value=clamp_score(boilerplate_risk) if boilerplate_risk is not None else None,
            inputs={
                "boilerplate_phrase_ratio": m_1a.get("boilerplate_phrase_ratio", 0),
                "numeric_specificity_score": m_1a.get("numeric_specificity_score"),
                "company_specificity_score": m_1a.get("company_specificity_score"),
            },
        )
    )

    d_controls = section_diffs.get("item_9a_controls") or section_diffs.get("item_4_controls")
    internal_controls = blend_scores(
        d_controls,
        (m_1a.get("constraining_word_ratio", 0) or 0) * 100,
        weights=[0.6, 0.4],
    )
    ic_flag_boost = _flag_boost(
        flags,
        ["material_weakness_flag", "restatement_flag", "ineffective_controls_flag"],
    )
    ic_inputs: dict[str, Any] = {
        "diff_controls": d_controls,
        "constraining_word_ratio": m_1a.get("constraining_word_ratio", 0),
        "material_weakness_flag": flags.get("material_weakness_flag", False),
        "restatement_flag": flags.get("restatement_flag", False),
        "ineffective_controls_flag": flags.get("ineffective_controls_flag", False),
        "flag_boost": ic_flag_boost,
    }
    if internal_controls is not None and ic_flag_boost:
        internal_controls = min(100.0, internal_controls + ic_flag_boost)
    provenance.append(
        DeterministicComponentProvenance(
            score_name="internal_controls_risk_score",
            value=clamp_score(internal_controls) if internal_controls is not None else None,
            inputs=ic_inputs,
        )
    )

    event_severity = blend_scores(d_1a)
    provenance.append(
        DeterministicComponentProvenance(
            score_name="event_severity_score",
            value=clamp_score(event_severity) if event_severity is not None else None,
            inputs={"diff_1a": d_1a},
        )
    )

    specificity_quality = blend_scores(
        m_1a.get("numeric_specificity_score"),
        m_1a.get("company_specificity_score"),
        weights=[0.5, 0.5],
    )
    provenance.append(
        DeterministicComponentProvenance(
            score_name="specificity_quality_score",
            value=clamp_score(specificity_quality) if specificity_quality is not None else None,
            inputs={
                "numeric_specificity_score": m_1a.get("numeric_specificity_score"),
                "company_specificity_score": m_1a.get("company_specificity_score"),
            },
        )
    )

    tone_negativity = blend_scores(
        neg_1a,
        (m_7.get("uncertainty_word_ratio", 0) or 0) * 100,
        weights=[0.5, 0.5],
    )
    provenance.append(
        DeterministicComponentProvenance(
            score_name="tone_negativity_score",
            value=clamp_score(tone_negativity) if tone_negativity is not None else None,
            inputs={
                "negative_word_ratio_1a": m_1a.get("negative_word_ratio", 0),
                "uncertainty_word_ratio_mdna": m_7.get("uncertainty_word_ratio", 0),
            },
        )
    )

    components = ComponentScores(
        risk_factor_intensity_score=provenance[0].value,
        disclosure_change_score=provenance[1].value,
        mdna_uncertainty_score=provenance[2].value,
        legal_regulatory_risk_score=provenance[3].value,
        liquidity_stress_score=provenance[4].value,
        boilerplate_risk_score=provenance[5].value,
        internal_controls_risk_score=provenance[6].value,
        event_severity_score=provenance[7].value,
        specificity_quality_score=provenance[8].value,
        tone_negativity_score=provenance[9].value,
    )

    comp_map = {k: v for k, v in components.__dict__.items() if k in DETERMINISTIC_COMPONENT_WEIGHTS}
    overall, coverage, missing = overall_from_components(comp_map, DETERMINISTIC_COMPONENT_WEIGHTS)
    confidence = max(0.3, min(0.95, 0.5 + coverage * 0.4))

    aggregates = AggregateScores(
        disclosure_deterioration_score=components.disclosure_change_score,
        disclosure_quality_score=(
            clamp_score(100 - (components.boilerplate_risk_score or 50))
            if components.boilerplate_risk_score is not None
            else None
        ),
    )

    return DeterministicAggregationResult(
        overall_disclosure_risk_score=overall,
        score_coverage_ratio=round(coverage, 4),
        confidence_score=round(confidence, 4),
        missing_components=missing,
        components=components,
        aggregates=aggregates,
        provenance=provenance,
    )
