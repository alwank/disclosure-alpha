from dataclasses import dataclass, field

COMPONENT_WEIGHTS = {
    "risk_factor_intensity_score": 0.20,
    "disclosure_change_score": 0.15,
    "mdna_uncertainty_score": 0.15,
    "legal_regulatory_risk_score": 0.10,
    "liquidity_stress_score": 0.10,
    "boilerplate_risk_score": 0.10,
    "internal_controls_risk_score": 0.05,
    "event_severity_score": 0.05,
    "tone_negativity_score": 0.05,
}


@dataclass
class ComponentScores:
    risk_factor_intensity_score: float | None = None
    disclosure_change_score: float | None = None
    mdna_uncertainty_score: float | None = None
    legal_regulatory_risk_score: float | None = None
    liquidity_stress_score: float | None = None
    boilerplate_risk_score: float | None = None
    internal_controls_risk_score: float | None = None
    event_severity_score: float | None = None
    specificity_quality_score: float | None = None
    tone_negativity_score: float | None = None


@dataclass
class AggregateScores:
    disclosure_quality_score: float | None = None
    disclosure_deterioration_score: float | None = None


@dataclass
class MatrixAggregationResult:
    overall_disclosure_risk_score: float | None
    score_coverage_ratio: float
    confidence_score: float
    missing_components: list[str] = field(default_factory=list)
    components: ComponentScores = field(default_factory=ComponentScores)
    aggregates: AggregateScores = field(default_factory=AggregateScores)


def clamp_score(score: float) -> float:
    return max(0.0, min(100.0, score))


def blend_scores(*values: float | None, weights: list[float] | None = None) -> float | None:
    pairs = [(v, w) for v, w in zip(values, weights or [1.0] * len(values)) if v is not None]
    if not pairs:
        return None
    total_w = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / total_w


def overall_from_components(
    comp_map: dict[str, float | None],
    weights: dict[str, float],
) -> tuple[float | None, float, list[str]]:
    present = {k: v for k, v in comp_map.items() if k in weights and v is not None}
    missing = [k for k in weights if comp_map.get(k) is None]
    coverage = len(present) / len(weights) if weights else 0.0
    overall = None
    if present:
        total_w = sum(weights[k] for k in present)
        overall = clamp_score(sum(comp_map[k] * weights[k] for k in present) / total_w)
    return overall, coverage, missing
