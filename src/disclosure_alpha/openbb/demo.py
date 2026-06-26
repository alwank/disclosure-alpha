"""Demo fixtures for OpenBB widgets (no EDGAR)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from disclosure_alpha.openbb.adapters import score_card_context
from disclosure_alpha.version import (
    DICTIONARY_VERSION,
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def is_demo(demo: str | None) -> bool:
    return (demo or "").strip().lower() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def _load_example(name: str) -> dict[str, Any]:
    path = _REPO_ROOT / "docs" / "examples" / name
    return json.loads(path.read_text(encoding="utf-8"))


def demo_score_card_context(ticker: str = "AAPL") -> dict[str, Any]:
    scores = _load_example("score-full-coverage-snippet.json")
    sym = ticker.strip().upper() or "AAPL"
    filing = {
        "ticker": sym,
        "fiscal_year": 2025,
        "form_type": "10-K",
        "quarter": None,
    }
    versions = {
        "parser_version": PARSER_VERSION,
        "metrics_engine_version": METRICS_ENGINE_VERSION,
        "scoring_model_version": SCORING_MODEL_VERSION,
        "dictionary_version": DICTIONARY_VERSION,
    }
    return score_card_context(filing, scores, versions, demo=True)


def demo_flag_rows() -> list[dict[str, str]]:
    payload = _load_example("score-minimal-10k.json")
    flags = payload["metrics"]["section_flags"]["item_1a_risk_factors"]
    rows: list[dict[str, str]] = []
    for flag_name, active in flags.items():
        if not active:
            continue
        label = flag_name.removesuffix("_flag").replace("_", " ").title()
        rows.append(
            {
                "section": "item_1a_risk_factors",
                "flag": flag_name,
                "label": label,
            }
        )
    if any(r["flag"] == "investigation_flag" for r in rows):
        rows.append(
            {
                "section": "item_3_legal_proceedings",
                "flag": "investigation_flag",
                "label": "Investigation",
            }
        )
    return rows


def demo_change_rows() -> list[dict[str, Any]]:
    payload = _load_example("score-full-coverage-snippet.json")
    minimal = _load_example("score-minimal-10k.json")
    metrics = minimal["metrics"]
    from disclosure_alpha.pipeline import MetricsResult
    from disclosure_alpha.pipeline import score_for_model

    mr = MetricsResult(
        section_metrics=metrics["section_metrics"],
        section_diffs=metrics.get("section_diffs") or {},
        section_flags=metrics["section_flags"],
        section_densities=metrics.get("section_densities") or {},
        language_deltas=metrics.get("language_deltas") or {},
        extraction_confs=metrics.get("extraction_confs") or {},
        diff_confs=metrics.get("diff_confs") or [],
        section_diffs_v2=metrics.get("section_diffs_v2") or {},
    )
    scores = score_for_model(mr, SCORING_MODEL_VERSION, form_type="10-K")
    from disclosure_alpha.openbb.adapters import change_rows

    rows = change_rows(mr, scores)
    if rows:
        return rows
    # score-full-coverage has prior diffs in scores but minimal fixture may be empty;
    # synthesize one row for demo layout.
    return [
        {
            "section": "item_1a_risk_factors",
            "section_label": "Item 1A Risk Factors",
            "change_score": 38.1,
            "section_diff": 42.5,
            "section_diff_v2": 38.1,
            "top_delta_name": "uncertainty_language_delta",
            "top_delta_value": 12.3,
        },
        {
            "section": "item_7_mdna",
            "section_label": "Item 7 MD&A",
            "change_score": 18.5,
            "section_diff": 20.0,
            "section_diff_v2": 18.5,
            "top_delta_name": "legal_language_delta",
            "top_delta_value": 5.0,
        },
    ]
