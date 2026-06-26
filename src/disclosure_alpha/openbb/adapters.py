"""Flatten pipeline outputs into OpenBB widget row shapes."""

from __future__ import annotations

from typing import Any

from disclosure_alpha.deterministic_scoring import DeterministicAggregationResult
from disclosure_alpha.openbb.labels import (
    COMPONENT_LABELS,
    COMPONENT_WEIGHTS_PCT,
    HEADLINE_COMPONENT_ORDER,
    TIER_SORT_ORDER,
    flag_tier,
    section_label,
)
from disclosure_alpha.pipeline import MetricsResult
from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS


def _components_dict(scores: dict[str, Any]) -> dict[str, float | None]:
    raw = scores.get("components") or {}
    return {key: raw.get(key) for key in COMPONENT_WEIGHTS}


def score_card_context(
    filing: dict[str, Any],
    scores: dict[str, Any],
    versions: dict[str, str],
    *,
    demo: bool = False,
    corpus: dict[str, Any] | None = None,
) -> dict[str, Any]:
    components = _components_dict(scores)
    missing = list(scores.get("missing_components") or [])
    headline_present = sum(
        1 for key in HEADLINE_COMPONENT_ORDER if components.get(key) is not None
    )
    headline_rows = []
    for key in HEADLINE_COMPONENT_ORDER:
        headline_rows.append(
            {
                "key": key,
                "label": COMPONENT_LABELS[key],
                "weight_pct": COMPONENT_WEIGHTS_PCT[key],
                "score": components.get(key),
            }
        )
    specificity = components.get("specificity_quality_score")
    return {
        "demo": demo,
        "filing": filing,
        "versions": versions,
        "overall": scores.get("overall_disclosure_risk_score"),
        "score_coverage_ratio": scores.get("score_coverage_ratio"),
        "confidence_score": scores.get("confidence_score"),
        "components_present": f"{headline_present} / {len(HEADLINE_COMPONENT_ORDER)}",
        "missing_components": missing,
        "headline_rows": headline_rows,
        "specificity": {
            "key": "specificity_quality_score",
            "label": COMPONENT_LABELS["specificity_quality_score"],
            "score": specificity,
        },
        "corpus": corpus,
    }


def flag_rows(active_flags: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "section": item["section"],
            "flag": item["flag"],
            "label": item["label"],
        }
        for item in active_flags
    ]


_SECTION_ORDER: tuple[str, ...] = (
    "item_1a_risk_factors",
    "item_7_mdna",
    "item_2_mdna",
    "item_9a_controls",
    "item_4_controls",
    "item_3_legal_proceedings",
    "item_1_legal_proceedings",
    "item_1c_cybersecurity",
    "item_7a_market_risk",
)


def _section_sort_key(section: str, section_label_text: str) -> tuple[int, str]:
    try:
        return (_SECTION_ORDER.index(section), section_label_text)
    except ValueError:
        return (len(_SECTION_ORDER), section_label_text)


def _flag_sort_key(flag: dict[str, Any]) -> tuple[int, str]:
    tier = flag.get("tier") or "moderate"
    return (TIER_SORT_ORDER.get(tier, 99), str(flag.get("label") or ""))


def flag_summary(active_flags: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_flag: dict[str, dict[str, Any]] = {}
    for item in active_flags:
        flag_name = item["flag"]
        entry = by_flag.get(flag_name)
        if entry is None:
            entry = {
                "flag": flag_name,
                "label": item["label"],
                "tier": flag_tier(flag_name),
                "sections": [],
            }
            by_flag[flag_name] = entry
        section = item["section"]
        if section not in entry["sections"]:
            entry["sections"].append(section)
    rows = list(by_flag.values())
    for row in rows:
        row["section_count"] = len(row["sections"])
    rows.sort(key=lambda r: (_flag_sort_key(r), r["flag"]))
    return rows


def flag_section_groups(active_flags: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_section: dict[str, dict[str, Any]] = {}
    for item in active_flags:
        section = item["section"]
        group = by_section.get(section)
        if group is None:
            label = section_label(section)
            group = {
                "section": section,
                "section_label": label,
                "flags": [],
            }
            by_section[section] = group
        flag_name = item["flag"]
        if any(f["flag"] == flag_name for f in group["flags"]):
            continue
        group["flags"].append(
            {
                "flag": flag_name,
                "label": item["label"],
                "tier": flag_tier(flag_name),
            }
        )
    groups = list(by_section.values())
    for group in groups:
        group["flags"].sort(key=_flag_sort_key)
    groups.sort(
        key=lambda g: _section_sort_key(g["section"], g["section_label"]),
    )
    return groups


def flag_display_from_active(active_flags: list[dict[str, str]]) -> dict[str, Any]:
    flat = flag_rows(active_flags)
    return {
        "summary": flag_summary(flat),
        "section_groups": flag_section_groups(flat),
        "hit_count": len(flat),
    }


def change_rows(
    metrics: MetricsResult,
    scores: DeterministicAggregationResult | None,
) -> list[dict[str, Any]]:
    from disclosure_alpha.api.shapes import shape_changes_payload

    payload = shape_changes_payload(metrics, scores)
    rows: list[dict[str, Any]] = []
    sections = set(payload.get("section_diffs", {})) | set(payload.get("section_diffs_v2", {}))
    for section in sections:
        deltas = payload.get("language_deltas", {}).get(section, {})
        top_name: str | None = None
        top_value: float | None = None
        if deltas:
            top_name, top_value = max(deltas.items(), key=lambda kv: abs(kv[1]))
        v2 = payload.get("section_diffs_v2", {}).get(section)
        v1 = payload.get("section_diffs", {}).get(section)
        rows.append(
            {
                "section": section,
                "section_label": section_label(section),
                "change_score": v2 if v2 is not None else v1,
                "section_diff": v1,
                "section_diff_v2": v2,
                "top_delta_name": top_name,
                "top_delta_value": top_value,
            }
        )
    rows.sort(
        key=lambda row: (row.get("change_score") is not None, row.get("change_score") or 0.0),
        reverse=True,
    )
    return rows


