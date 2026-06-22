"""Deterministic filing-level scores from text metrics and diffs only."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from disclosure_alpha.scoring_types import (
    COMPONENT_WEIGHTS,
    AggregateScores,
    ComponentScores,
    MatrixAggregationResult,
    ScoreEvidence,
    aggregate_split_scores,
    blend_evidence,
    blend_scores,
    clamp_score,
    overall_from_components,
)

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


def _section_metrics(
    section_metrics: dict[str, dict[str, float]],
    section_name: str,
) -> dict[str, float] | None:
    metrics = section_metrics.get(section_name)
    if metrics is None:
        return None
    return dict(metrics)


def _metric(metrics: dict[str, float] | None, key: str) -> float | None:
    if metrics is None or key not in metrics:
        return None
    value = metrics[key]
    return float(value) if value is not None else None


def _scaled_metric(metrics: dict[str, float] | None, key: str) -> float | None:
    value = _metric(metrics, key)
    return value * 100 if value is not None else None


def _inverse_metric(metrics: dict[str, float] | None, key: str) -> float | None:
    value = _metric(metrics, key)
    return 100 - value if value is not None else None


def _first_present(values: list[float | None]) -> float | None:
    for value in values:
        if value is not None:
            return value
    return None


def _mdna_metrics(
    section_metrics: dict[str, dict[str, float]],
    section_densities: dict[str, dict[str, float]] | None,
) -> tuple[dict[str, float] | None, str | None]:
    if "item_7_mdna" in section_metrics:
        density_key = "item_7_mdna"
    elif "item_2_mdna" in section_metrics:
        density_key = "item_2_mdna"
    else:
        return None, None
    m_7 = dict(section_metrics[density_key])
    densities = (section_densities or {}).get(density_key, {})
    for key, value in densities.items():
        m_7[key] = value
    return m_7, density_key


def aggregate_deterministic_matrix(
    *,
    section_metrics: dict[str, dict[str, float]],
    section_diffs: dict[str, float | None],
    section_flags: dict[str, dict[str, bool]] | None = None,
    language_deltas: dict[str, dict[str, float]] | None = None,
    section_densities: dict[str, dict[str, float]] | None = None,
) -> DeterministicAggregationResult:
    m_1a = _section_metrics(section_metrics, "item_1a_risk_factors")
    m_7, _mdna_section = _mdna_metrics(section_metrics, section_densities)
    flags = _merged_flags(section_flags)
    provenance: list[DeterministicComponentProvenance] = []

    d_1a = section_diffs.get("item_1a_risk_factors")
    neg_1a = _scaled_metric(m_1a, "negative_word_ratio")
    unc_1a = _scaled_metric(m_1a, "uncertainty_word_ratio")
    risk_factor_intensity = (
        blend_scores(neg_1a, unc_1a, d_1a, weights=[0.375, 0.375, 0.25])
        if m_1a is not None
        else None
    )
    provenance.append(
        DeterministicComponentProvenance(
            score_name="risk_factor_intensity_score",
            value=clamp_score(risk_factor_intensity) if risk_factor_intensity is not None else None,
            inputs={
                "negative_word_ratio": _metric(m_1a, "negative_word_ratio"),
                "uncertainty_word_ratio": _metric(m_1a, "uncertainty_word_ratio"),
                "diff_1a": d_1a,
            },
        )
    )

    d_mdna = _first_present(
        [section_diffs.get("item_7_mdna"), section_diffs.get("item_2_mdna")]
    )
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

    unc_mdna = _scaled_metric(m_7, "uncertainty_word_ratio")
    modal_mdna = _scaled_metric(m_7, "modal_word_ratio")
    mdna_uncertainty = blend_scores(
        unc_mdna,
        modal_mdna,
        _metric(m_7, "readability_score"),
        _metric(m_7, "uncertainty_term_density"),
        _metric(m_7, "demand_softness_density"),
        _metric(m_7, "margin_pressure_density"),
        weights=[0.40, 0.35, 0.25, 0.10, 0.05, 0.05],
    )
    guidance_boost = _flag_boost(flags, ["guidance_withdrawal_flag"])
    mdna_inputs: dict[str, Any] = {
        "uncertainty_word_ratio": _metric(m_7, "uncertainty_word_ratio"),
        "modal_word_ratio": _metric(m_7, "modal_word_ratio"),
        "readability_score": _metric(m_7, "readability_score"),
        "uncertainty_term_density": _metric(m_7, "uncertainty_term_density"),
        "demand_softness_density": _metric(m_7, "demand_softness_density"),
        "margin_pressure_density": _metric(m_7, "margin_pressure_density"),
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

    litigious = _scaled_metric(m_1a, "litigious_word_ratio")
    legal_delta = _language_delta_blend(
        language_deltas,
        [
            "item_1a_risk_factors",
            "item_3_legal_proceedings",
            "item_1_legal_proceedings",
        ],
        key="legal_language_delta",
    )
    legal_regulatory = (
        blend_scores(litigious, legal_delta, weights=[0.70, 0.30])
        if m_1a is not None
        else None
    )
    legal_flag_boost = _flag_boost(
        flags, ["investigation_flag", "material_legal_proceeding_flag"]
    )
    legal_inputs: dict[str, Any] = {
        "litigious_word_ratio": _metric(m_1a, "litigious_word_ratio"),
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

    constraining = _scaled_metric(m_7, "constraining_word_ratio")
    liquidity_stress = blend_scores(
        constraining,
        _metric(m_7, "liquidity_constraint_density"),
        weights=[0.50, 0.35],
    )
    liquidity_flag_boost = _flag_boost(flags, ["going_concern_flag", "covenant_breach_flag"])
    liquidity_inputs: dict[str, Any] = {
        "constraining_word_ratio": _metric(m_7, "constraining_word_ratio"),
        "liquidity_constraint_density": _metric(m_7, "liquidity_constraint_density"),
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

    boilerplate_risk = (
        blend_scores(
            _scaled_metric(m_1a, "boilerplate_phrase_ratio"),
            _inverse_metric(m_1a, "numeric_specificity_score"),
            _inverse_metric(m_1a, "company_specificity_score"),
            weights=[1 / 3, 1 / 3, 1 / 3],
        )
        if m_1a is not None
        else None
    )
    provenance.append(
        DeterministicComponentProvenance(
            score_name="boilerplate_risk_score",
            value=clamp_score(boilerplate_risk) if boilerplate_risk is not None else None,
            inputs={
                "boilerplate_phrase_ratio": _metric(m_1a, "boilerplate_phrase_ratio"),
                "numeric_specificity_score": _metric(m_1a, "numeric_specificity_score"),
                "company_specificity_score": _metric(m_1a, "company_specificity_score"),
            },
        )
    )

    d_controls = _first_present(
        [section_diffs.get("item_9a_controls"), section_diffs.get("item_4_controls")]
    )
    internal_controls = blend_scores(
        d_controls,
        _scaled_metric(m_1a, "constraining_word_ratio"),
        weights=[0.6, 0.4],
    )
    ic_flag_boost = _flag_boost(
        flags,
        ["material_weakness_flag", "restatement_flag", "ineffective_controls_flag"],
    )
    ic_inputs: dict[str, Any] = {
        "diff_controls": d_controls,
        "constraining_word_ratio": _metric(m_1a, "constraining_word_ratio"),
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
        _metric(m_1a, "numeric_specificity_score"),
        _metric(m_1a, "company_specificity_score"),
        weights=[0.5, 0.5],
    )
    provenance.append(
        DeterministicComponentProvenance(
            score_name="specificity_quality_score",
            value=clamp_score(specificity_quality) if specificity_quality is not None else None,
            inputs={
                "numeric_specificity_score": _metric(m_1a, "numeric_specificity_score"),
                "company_specificity_score": _metric(m_1a, "company_specificity_score"),
            },
        )
    )

    tone_negativity = blend_scores(
        neg_1a,
        unc_mdna,
        weights=[0.5, 0.5],
    )
    provenance.append(
        DeterministicComponentProvenance(
            score_name="tone_negativity_score",
            value=clamp_score(tone_negativity) if tone_negativity is not None else None,
            inputs={
                "negative_word_ratio_1a": _metric(m_1a, "negative_word_ratio"),
                "uncertainty_word_ratio_mdna": _metric(m_7, "uncertainty_word_ratio"),
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

    comp_map = {k: v for k, v in components.__dict__.items() if k in COMPONENT_WEIGHTS}
    overall, coverage, missing = overall_from_components(comp_map, COMPONENT_WEIGHTS)

    aggregates = aggregate_split_scores(components)
    if aggregates.disclosure_quality_score is None and components.boilerplate_risk_score is not None:
        aggregates.disclosure_quality_score = clamp_score(100 - components.boilerplate_risk_score)

    return DeterministicAggregationResult(
        overall_disclosure_risk_score=overall,
        score_coverage_ratio=round(coverage, 4),
        confidence_score=0.3,  # ponytail: placeholder; score_deterministic overwrites
        missing_components=missing,
        components=components,
        aggregates=aggregates,
        provenance=provenance,
    )


_FLAG_EVIDENCE_SCORE = 65.0
_SERIOUS_IC_FLAGS = ["material_weakness_flag", "restatement_flag", "ineffective_controls_flag"]
_LEGAL_FLAGS = ["investigation_flag", "material_legal_proceeding_flag"]
_LIQUIDITY_FLAGS = ["going_concern_flag", "covenant_breach_flag"]
_LEGAL_SECTIONS = [
    "item_1a_risk_factors",
    "item_3_legal_proceedings",
    "item_1_legal_proceedings",
]
_CYBER_INCIDENT_SECTIONS = ("item_1_05", "item_8_01", "item_1a_risk_factors")
_EVENT_SECTIONS = (
    "item_1_01",
    "item_1_05",
    "item_2_02",
    "item_5_02",
    "item_8_01",
)


def _flag_section(
    section_flags: dict[str, dict[str, bool]] | None, flag_name: str
) -> str | None:
    if not section_flags:
        return None
    for section, flags in section_flags.items():
        if flags.get(flag_name):
            return section
    return None


def _controls_diff(
    section_diffs: dict[str, float | None],
) -> tuple[str | None, float | None]:
    for name in ("item_9a_controls", "item_4_controls"):
        value = section_diffs.get(name)
        if value is not None:
            return name, value
    return None, None


def _internal_controls_risk_score_v2(
    *,
    section_metrics: dict[str, dict[str, float]],
    section_diffs: dict[str, float | None],
    section_flags: dict[str, dict[str, bool]] | None,
    flags: dict[str, bool],
) -> tuple[float | None, dict[str, Any]]:
    m_1a = _section_metrics(section_metrics, "item_1a_risk_factors")
    evidence: list[ScoreEvidence] = []
    controls_section, d_controls = _controls_diff(section_diffs)
    if d_controls is not None:
        evidence.append(
            ScoreEvidence(
                "diff_controls",
                float(d_controls),
                0.6,
                section=controls_section,
                raw_value=d_controls,
            )
        )
    constraining = _scaled_metric(m_1a, "constraining_word_ratio")
    if constraining is not None:
        evidence.append(
            ScoreEvidence(
                "constraining_word_ratio",
                constraining,
                0.4,
                section="item_1a_risk_factors",
                raw_value=_metric(m_1a, "constraining_word_ratio"),
            )
        )
    for flag in _SERIOUS_IC_FLAGS:
        if flags.get(flag):
            evidence.append(
                ScoreEvidence(
                    flag,
                    _FLAG_EVIDENCE_SCORE,
                    0.5,
                    section=_flag_section(section_flags, flag),
                    raw_value=True,
                    reason="serious_flag",
                )
            )
    score, inputs = blend_evidence(evidence)
    if score is not None:
        score = clamp_score(score)
    return score, inputs


def _legal_regulatory_risk_score_v2(
    *,
    section_metrics: dict[str, dict[str, float]],
    language_deltas: dict[str, dict[str, float]] | None,
    section_flags: dict[str, dict[str, bool]] | None,
    flags: dict[str, bool],
) -> tuple[float | None, dict[str, Any]]:
    evidence: list[ScoreEvidence] = []
    for section in _LEGAL_SECTIONS:
        metrics = _section_metrics(section_metrics, section)
        litigious = _scaled_metric(metrics, "litigious_word_ratio")
        if litigious is not None:
            weight = 0.5 if section == "item_1a_risk_factors" else 0.35
            evidence.append(
                ScoreEvidence(
                    f"litigious_word_ratio_{section}",
                    litigious,
                    weight,
                    section=section,
                    raw_value=_metric(metrics, "litigious_word_ratio"),
                )
            )
    legal_delta = _language_delta_blend(language_deltas, _LEGAL_SECTIONS, key="legal_language_delta")
    if legal_delta is not None:
        evidence.append(
            ScoreEvidence(
                "legal_language_delta",
                legal_delta,
                0.30,
                raw_value=legal_delta,
            )
        )
    for flag in _LEGAL_FLAGS:
        if flags.get(flag):
            evidence.append(
                ScoreEvidence(
                    flag,
                    _FLAG_EVIDENCE_SCORE,
                    0.5,
                    section=_flag_section(section_flags, flag),
                    raw_value=True,
                    reason="serious_flag",
                )
            )
    score, inputs = blend_evidence(evidence)
    if score is not None:
        score = clamp_score(score)
    return score, inputs


def _liquidity_stress_score_v2(
    *,
    section_metrics: dict[str, dict[str, float]],
    section_densities: dict[str, dict[str, float]] | None,
    section_flags: dict[str, dict[str, bool]] | None,
    flags: dict[str, bool],
) -> tuple[float | None, dict[str, Any]]:
    m_7, mdna_section = _mdna_metrics(section_metrics, section_densities)
    m_1a = _section_metrics(section_metrics, "item_1a_risk_factors")
    evidence: list[ScoreEvidence] = []
    constraining_mdna = _scaled_metric(m_7, "constraining_word_ratio")
    if constraining_mdna is not None:
        evidence.append(
            ScoreEvidence(
                "constraining_word_ratio_mdna",
                constraining_mdna,
                0.50,
                section=mdna_section,
                raw_value=_metric(m_7, "constraining_word_ratio"),
            )
        )
    density = _metric(m_7, "liquidity_constraint_density")
    if density is not None:
        evidence.append(
            ScoreEvidence(
                "liquidity_constraint_density",
                density,
                0.35,
                section=mdna_section,
                raw_value=density,
            )
        )
    constraining_1a = _scaled_metric(m_1a, "constraining_word_ratio")
    if constraining_1a is not None:
        evidence.append(
            ScoreEvidence(
                "constraining_word_ratio_1a",
                constraining_1a,
                0.25,
                section="item_1a_risk_factors",
                raw_value=_metric(m_1a, "constraining_word_ratio"),
                reason="liquidity_fallback",
            )
        )
    for flag in _LIQUIDITY_FLAGS:
        if flags.get(flag):
            evidence.append(
                ScoreEvidence(
                    flag,
                    _FLAG_EVIDENCE_SCORE,
                    0.5,
                    section=_flag_section(section_flags, flag),
                    raw_value=True,
                    reason="serious_flag",
                )
            )
    score, inputs = blend_evidence(evidence)
    if score is not None:
        score = clamp_score(score)
    return score, inputs


def _cybersecurity_incident_risk_score_v2(
    *,
    section_flags: dict[str, dict[str, bool]] | None,
    flags: dict[str, bool],
) -> tuple[float | None, dict[str, Any]]:
    evidence: list[ScoreEvidence] = []
    if flags.get("cybersecurity_incident_flag"):
        section = _flag_section(section_flags, "cybersecurity_incident_flag")
        if section in _CYBER_INCIDENT_SECTIONS:
            evidence.append(
                ScoreEvidence(
                    "cybersecurity_incident_flag",
                    _FLAG_EVIDENCE_SCORE,
                    0.7,
                    section=section,
                    raw_value=True,
                    reason="incident_flag",
                )
            )
    score, inputs = blend_evidence(evidence)
    if score is not None:
        score = clamp_score(score)
    return score, inputs


def _event_materiality_score_v2(
    *,
    section_metrics: dict[str, dict[str, float]],
    section_flags: dict[str, dict[str, bool]] | None,
    section_diffs: dict[str, float | None],
    flags: dict[str, bool],
) -> tuple[float | None, dict[str, Any]]:
    evidence: list[ScoreEvidence] = []
    event_flags = [
        "investigation_flag",
        "material_legal_proceeding_flag",
        "going_concern_flag",
        "guidance_withdrawal_flag",
        "cybersecurity_incident_flag",
    ]
    for flag in event_flags:
        if flags.get(flag):
            section = _flag_section(section_flags, flag)
            if section and section in _EVENT_SECTIONS:
                evidence.append(
                    ScoreEvidence(
                        flag,
                        _FLAG_EVIDENCE_SCORE,
                        0.45,
                        section=section,
                        raw_value=True,
                        reason="event_flag",
                    )
                )
    for section in _EVENT_SECTIONS:
        metrics = _section_metrics(section_metrics, section)
        unc = _scaled_metric(metrics, "uncertainty_word_ratio")
        if unc is not None:
            evidence.append(
                ScoreEvidence(
                    f"uncertainty_{section}",
                    unc,
                    0.25,
                    section=section,
                    raw_value=_metric(metrics, "uncertainty_word_ratio"),
                )
            )
        diff = section_diffs.get(section)
        if diff is not None:
            evidence.append(
                ScoreEvidence(
                    f"diff_{section}",
                    float(diff),
                    0.20,
                    section=section,
                    raw_value=diff,
                )
            )
    score, inputs = blend_evidence(evidence)
    if score is not None:
        score = clamp_score(score)
    return score, inputs


def _disclosure_change_from_diffs(
    section_diffs: dict[str, float | None],
    language_deltas: dict[str, dict[str, float]] | None,
) -> tuple[float | None, dict[str, Any]]:
    d_1a = section_diffs.get("item_1a_risk_factors")
    d_mdna = _first_present(
        [section_diffs.get("item_7_mdna"), section_diffs.get("item_2_mdna")]
    )
    disclosure_change = blend_scores(d_1a, d_mdna, weights=[0.6, 0.4])
    unc_delta = _language_delta_blend(
        language_deltas, ["item_1a_risk_factors", "item_7_mdna", "item_2_mdna"]
    )
    disclosure_inputs: dict[str, Any] = {"diff_1a": d_1a, "diff_mdna": d_mdna}
    if disclosure_change is not None and unc_delta is not None:
        disclosure_change = min(100.0, disclosure_change + unc_delta * 0.1)
        disclosure_inputs["uncertainty_language_delta_boost"] = unc_delta * 0.1
    value = clamp_score(disclosure_change) if disclosure_change is not None else None
    return value, disclosure_inputs


def _replace_provenance(
    provenance: list[DeterministicComponentProvenance],
    score_name: str,
    value: float | None,
    inputs: dict[str, Any],
) -> None:
    for i, entry in enumerate(provenance):
        if entry.score_name == score_name:
            provenance[i] = DeterministicComponentProvenance(
                score_name=score_name,
                value=value,
                inputs=inputs,
                source="deterministic_v2",
            )
            return


def aggregate_deterministic_matrix_v2(
    *,
    section_metrics: dict[str, dict[str, float]],
    section_diffs: dict[str, float | None],
    section_flags: dict[str, dict[str, bool]] | None = None,
    language_deltas: dict[str, dict[str, float]] | None = None,
    section_densities: dict[str, dict[str, float]] | None = None,
    calibration_context: Any | None = None,
    section_diffs_v2: dict[str, float | None] | None = None,
) -> DeterministicAggregationResult:
    """Scoring v2: section-specific evidence, flag-only paths, calibrated tone ratios."""
    from disclosure_alpha.calibration import CalibrationContext, calibrate_metric, calibration_provenance

    diffs_for_change = section_diffs_v2 if section_diffs_v2 else section_diffs
    ctx = calibration_context or CalibrationContext()
    base = aggregate_deterministic_matrix(
        section_metrics=section_metrics,
        section_diffs=section_diffs,
        section_flags=section_flags,
        language_deltas=language_deltas,
        section_densities=section_densities,
    )
    flags = _merged_flags(section_flags)
    m_1a = _section_metrics(section_metrics, "item_1a_risk_factors")

    if diffs_for_change is not section_diffs:
        dc_value, dc_inputs = _disclosure_change_from_diffs(diffs_for_change, language_deltas)
        _replace_provenance(base.provenance, "disclosure_change_score", dc_value, dc_inputs)
        base.components.disclosure_change_score = dc_value
        base.aggregates = aggregate_split_scores(base.components)
        if base.aggregates.disclosure_quality_score is None and base.components.boilerplate_risk_score is not None:
            base.aggregates.disclosure_quality_score = clamp_score(
                100 - base.components.boilerplate_risk_score
            )

    # Calibrated tone for risk_factor_intensity when Item 1A present
    if m_1a is not None:
        neg_raw = _metric(m_1a, "negative_word_ratio")
        unc_raw = _metric(m_1a, "uncertainty_word_ratio")
        d_1a = section_diffs.get("item_1a_risk_factors")
        neg_cal = calibrate_metric("negative_word_ratio", neg_raw, ctx) if neg_raw is not None else None
        unc_cal = (
            calibrate_metric("uncertainty_word_ratio", unc_raw, ctx) if unc_raw is not None else None
        )
        neg_1a = neg_cal.calibrated_value if neg_cal else None
        unc_1a = unc_cal.calibrated_value if unc_cal else None
        risk_factor_intensity = blend_scores(neg_1a, unc_1a, d_1a, weights=[0.375, 0.375, 0.25])
        rf_inputs: dict[str, Any] = {"diff_1a": d_1a}
        if neg_cal:
            rf_inputs["negative_word_ratio"] = calibration_provenance(neg_cal)
        if unc_cal:
            rf_inputs["uncertainty_word_ratio"] = calibration_provenance(unc_cal)
        rf_value = clamp_score(risk_factor_intensity) if risk_factor_intensity is not None else None
        _replace_provenance(base.provenance, "risk_factor_intensity_score", rf_value, rf_inputs)
        base.components.risk_factor_intensity_score = rf_value

    legal_score, legal_inputs = _legal_regulatory_risk_score_v2(
        section_metrics=section_metrics,
        language_deltas=language_deltas,
        section_flags=section_flags,
        flags=flags,
    )
    _replace_provenance(base.provenance, "legal_regulatory_risk_score", legal_score, legal_inputs)
    base.components.legal_regulatory_risk_score = legal_score

    liquidity_score, liquidity_inputs = _liquidity_stress_score_v2(
        section_metrics=section_metrics,
        section_densities=section_densities,
        section_flags=section_flags,
        flags=flags,
    )
    _replace_provenance(base.provenance, "liquidity_stress_score", liquidity_score, liquidity_inputs)
    base.components.liquidity_stress_score = liquidity_score

    ic_score, ic_inputs = _internal_controls_risk_score_v2(
        section_metrics=section_metrics,
        section_diffs=section_diffs,
        section_flags=section_flags,
        flags=flags,
    )
    _replace_provenance(base.provenance, "internal_controls_risk_score", ic_score, ic_inputs)
    base.components.internal_controls_risk_score = ic_score

    cyber_score, cyber_inputs = _cybersecurity_incident_risk_score_v2(
        section_flags=section_flags,
        flags=flags,
    )
    base.components.cybersecurity_incident_risk_score = cyber_score
    if cyber_score is not None:
        base.provenance.append(
            DeterministicComponentProvenance(
                score_name="cybersecurity_incident_risk_score",
                value=cyber_score,
                inputs=cyber_inputs,
                source="deterministic_v2",
            )
        )

    event_score, event_inputs = _event_materiality_score_v2(
        section_metrics=section_metrics,
        section_flags=section_flags,
        section_diffs=diffs_for_change,
        flags=flags,
    )
    base.components.event_materiality_score = event_score
    if event_score is not None:
        base.provenance.append(
            DeterministicComponentProvenance(
                score_name="event_materiality_score",
                value=event_score,
                inputs=event_inputs,
                source="deterministic_v2",
            )
        )

    comp_map = {k: v for k, v in base.components.__dict__.items() if k in COMPONENT_WEIGHTS}
    overall, coverage, missing = overall_from_components(comp_map, COMPONENT_WEIGHTS)
    base.overall_disclosure_risk_score = overall
    base.score_coverage_ratio = round(coverage, 4)
    base.missing_components = missing
    base.aggregates = aggregate_split_scores(base.components)
    if base.aggregates.disclosure_quality_score is None and base.components.boilerplate_risk_score is not None:
        base.aggregates.disclosure_quality_score = clamp_score(
            100 - base.components.boilerplate_risk_score
        )
    return base
