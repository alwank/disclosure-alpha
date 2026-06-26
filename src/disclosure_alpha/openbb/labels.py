"""UI labels and score-band helpers for OpenBB widgets."""

from __future__ import annotations

from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS

DISCLOSURE_ALPHA_HOME_URL = "https://disclosurealpha.com"

HEADLINE_COMPONENT_ORDER: tuple[str, ...] = tuple(COMPONENT_WEIGHTS.keys())

COMPONENT_LABELS: dict[str, str] = {
    "risk_factor_intensity_score": "Risk-factor tone & volatility",
    "disclosure_change_score": "Year-over-year disclosure change",
    "mdna_uncertainty_score": "MD&A uncertainty & demand stress",
    "legal_regulatory_risk_score": "Legal & regulatory risk language",
    "liquidity_stress_score": "Liquidity & covenant stress",
    "boilerplate_risk_score": "Boilerplate & vague risk language",
    "internal_controls_risk_score": "Internal controls weakness signals",
    "event_severity_score": "Material event severity (diff-only)",
    "tone_negativity_score": "Cross-section negative tone",
    "specificity_quality_score": "Specificity quality",
}

COMPONENT_WEIGHTS_PCT: dict[str, int] = {
    key: int(round(weight * 100)) for key, weight in COMPONENT_WEIGHTS.items()
}

SECTION_LABELS: dict[str, str] = {
    "item_1a_risk_factors": "Item 1A Risk Factors",
    "item_7_mdna": "Item 7 MD&A",
    "item_2_mdna": "Item 2 MD&A",
    "item_9a_controls": "Item 9A Controls",
    "item_4_controls": "Item 4 Controls",
    "item_1c_cybersecurity": "Item 1C Cybersecurity",
    "item_3_legal_proceedings": "Item 3 Legal Proceedings",
    "item_1_legal_proceedings": "Item 1 Legal Proceedings",
    "item_7a_market_risk": "Item 7A Market Risk",
}

FLAG_TIERS: dict[str, str] = {
    "restatement_flag": "critical",
    "non_reliance_flag": "critical",
    "material_weakness_flag": "critical",
    "ineffective_controls_flag": "critical",
    "going_concern_flag": "critical",
    "covenant_breach_flag": "critical",
    "investigation_flag": "elevated",
    "cybersecurity_incident_flag": "elevated",
    "auditor_change_flag": "elevated",
    "guidance_withdrawal_flag": "elevated",
}

TIER_SORT_ORDER: dict[str, int] = {"critical": 0, "elevated": 1, "moderate": 2}

TIER_BAND: dict[str, str] = {
    "critical": "high",
    "elevated": "elevated",
    "moderate": "moderate",
}

TIER_COLORS: dict[str, str] = {
    "critical": "#991b1b",
    "elevated": "#dc2626",
    "moderate": "#ea580c",
}

BAND_LABELS: dict[str, str] = {
    "low": "Low concern",
    "moderate": "Moderate",
    "elevated": "Elevated",
    "high": "High",
    "missing": "—",
}


def risk_band(score: float | None, *, inverted: bool = False) -> str:
    if score is None:
        return "missing"
    value = score
    if inverted:
        value = 100.0 - score
    if value <= 25:
        return "low"
    if value <= 50:
        return "moderate"
    if value <= 75:
        return "elevated"
    return "high"


def band_label(band: str) -> str:
    return BAND_LABELS.get(band, band)


def format_score(score: float | None) -> str:
    if score is None:
        return "—"
    return f"{score:.1f}"


def section_label(section_name: str) -> str:
    return SECTION_LABELS.get(section_name, section_name.replace("_", " ").title())


def flag_tier(flag_name: str) -> str:
    return FLAG_TIERS.get(flag_name, "moderate")


def tier_color(tier: str) -> str:
    return TIER_COLORS.get(tier, TIER_COLORS["moderate"])


def section_changes_subtitle(form_type: str = "10-K") -> str:
    if form_type.upper().startswith("10-Q"):
        return "Quarter-over-quarter change by section"
    return "Year-over-year change by section"


DELTA_LABELS: dict[str, str] = {
    "negative_language_delta": "Negative language",
    "uncertainty_language_delta": "Uncertainty language",
    "legal_language_delta": "Legal language",
    "constraining_language_delta": "Constraining language",
}


def delta_label(delta_name: str | None) -> str:
    if not delta_name:
        return ""
    return DELTA_LABELS.get(delta_name, delta_name.removesuffix("_delta").replace("_", " ").title())


def format_delta_value(value: float | None) -> str:
    if value is None:
        return ""
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f} pp"
