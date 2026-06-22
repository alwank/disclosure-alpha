#!/usr/bin/env python3
"""Regenerate committed docs/examples/*.json from html_fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from disclosure_alpha.pipeline import score_filing_html
from disclosure_alpha.version import SCORING_MODEL_VERSION
from html_fixtures import minimal_10k_html, minimal_prior_html

EXAMPLES = ROOT / "docs" / "examples"

DEAD_COMPONENT_KEYS = frozenset(
    {"business_model_fragility_score", "cybersecurity_risk_score"}
)
DEAD_AGGREGATE_KEYS = frozenset({"hidden_risk_score"})
DEAD_TOP_LEVEL = frozenset({"top_hidden_risks", "evidence"})


def _scores_block(result) -> dict[str, Any]:
    scores = result.scores
    return {
        "overall_disclosure_risk_score": scores.overall_disclosure_risk_score,
        "score_coverage_ratio": scores.score_coverage_ratio,
        "confidence_score": scores.confidence_score,
        "missing_components": scores.missing_components,
        "components": scores.components.__dict__,
        "aggregates": scores.aggregates.__dict__,
    }


def _assert_no_dead_keys(obj: Any, *, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in DEAD_COMPONENT_KEYS | DEAD_AGGREGATE_KEYS | DEAD_TOP_LEVEL:
                raise ValueError(f"dead key at {path}.{key}" if path else f"dead key: {key}")
            _assert_no_dead_keys(value, path=f"{path}.{key}" if path else key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _assert_no_dead_keys(item, path=f"{path}[{i}]")


def _panel_snippet() -> dict[str, Any]:
    ok = score_filing_html(minimal_10k_html(), "10-K")
    scores = _scores_block(ok)
    return {
        "results": [
            {
                "ticker": "AAPL",
                "status": "ok",
                "filing": {"ticker": "AAPL", "fiscal_year": 2025, "form_type": "10-K"},
                "scores": {
                    k: scores[k]
                    for k in (
                        "overall_disclosure_risk_score",
                        "score_coverage_ratio",
                        "confidence_score",
                        "missing_components",
                        "components",
                    )
                },
            },
            {"ticker": "BAD", "status": "error", "error": "No 10-K for BAD FY2025"},
        ],
        "summary": {"ok": 1, "failed": 1},
        "versions": {"scoring_model_version": SCORING_MODEL_VERSION},
    }


def generate() -> dict[str, str]:
    minimal = score_filing_html(minimal_10k_html(), "10-K")
    with_prior = score_filing_html(
        minimal_10k_html(), "10-K", prior_html=minimal_prior_html()
    )
    full_coverage = with_prior

    outputs = {
        "score-minimal-10k.json": json.dumps(minimal.to_dict(), indent=2) + "\n",
        "score-with-prior-snippet.json": json.dumps(_scores_block(with_prior), indent=2) + "\n",
        "score-full-coverage-snippet.json": json.dumps(
            _scores_block(full_coverage), indent=2
        )
        + "\n",
        "panel-response-snippet.json": json.dumps(_panel_snippet(), indent=2) + "\n",
    }
    for name, text in outputs.items():
        _assert_no_dead_keys(json.loads(text))
        EXAMPLES.joinpath(name).write_text(text, encoding="utf-8")
    return {name: str(EXAMPLES / name) for name in outputs}


def check() -> None:
    before = {p.name: p.read_text(encoding="utf-8") for p in sorted(EXAMPLES.glob("*.json"))}
    generate()
    drift = [name for name, text in before.items() if EXAMPLES.joinpath(name).read_text() != text]
    if drift:
        names = ", ".join(sorted(drift))
        raise SystemExit(f"docs/examples drift: {names} (run without --check to refresh)")
    print("docs/examples OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate in memory and fail if committed files differ",
    )
    args = parser.parse_args()
    if args.check:
        check()
        return
    paths = generate()
    for path in paths.values():
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
