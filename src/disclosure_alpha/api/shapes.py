"""Response shaping helpers shared across product endpoints."""

from __future__ import annotations

from typing import Any

from disclosure_alpha.deterministic_scoring import DeterministicAggregationResult
from disclosure_alpha.pipeline import MetricsResult

TIER_PRESETS: dict[str, dict[str, Any]] = {
    "lite": {"include": "", "fields": "overall"},
    "standard": {"include": "metrics", "fields": "overall,components"},
    "analyst": {"include": "metrics,provenance", "fields": None},
}


def _flag_label(flag_name: str) -> str:
    base = flag_name.removesuffix("_flag") if flag_name.endswith("_flag") else flag_name
    return base.replace("_", " ").title()


def shape_flags_payload(metrics: MetricsResult) -> dict[str, Any]:
    """Boolean risk flags only."""
    flags = metrics.section_flags
    active_flags: list[dict[str, str]] = []
    for section, section_flags in flags.items():
        for flag_name, is_active in section_flags.items():
            if is_active:
                active_flags.append(
                    {
                        "section": section,
                        "flag": flag_name,
                        "label": _flag_label(flag_name),
                    }
                )
    return {"flags": flags, "active_flags": active_flags}


def shape_changes_payload(
    metrics: MetricsResult,
    scores: DeterministicAggregationResult | None,
) -> dict[str, Any]:
    """Section diffs and change score without full rescore noise."""
    change_value: float | None = None
    missing_reason: str | None = None
    if scores is None:
        missing_reason = "compare=none"
    else:
        change_value = scores.components.disclosure_change_score
        if change_value is None:
            missing_reason = "no prior filing comparison available"
    return {
        "section_diffs": metrics.section_diffs,
        "section_diffs_v2": metrics.section_diffs_v2,
        "language_deltas": metrics.language_deltas,
        "change_score": {"value": change_value, "missing_reason": missing_reason},
    }


def apply_tier_preset(
    tier: str,
    *,
    include: str | None,
    fields: str | None,
) -> tuple[str | None, str | None]:
    """Map tier=lite|standard|analyst to include/fields overrides."""
    if tier not in TIER_PRESETS:
        valid = ", ".join(sorted(TIER_PRESETS))
        raise ValueError(f"tier must be one of: {valid}")
    preset = TIER_PRESETS[tier]
    return preset.get("include"), preset.get("fields")
