"""Committed docs/examples JSON must match generate_docs_examples.py and omit dead keys."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from disclosure_alpha.pipeline import score_filing_html
from html_fixtures import full_coverage_10k_html, full_coverage_prior_html, minimal_10k_html

EXAMPLES = ROOT / "docs" / "examples"

DEAD_KEYS = frozenset(
    {
        "business_model_fragility_score",
        "cybersecurity_risk_score",
        "hidden_risk_score",
        "top_hidden_risks",
        "evidence",
    }
)


def _walk(obj, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            full = f"{path}.{key}" if path else key
            if key in DEAD_KEYS:
                hits.append(full)
            hits.extend(_walk(value, full))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            hits.extend(_walk(item, f"{path}[{i}]"))
    return hits


def test_docs_examples_no_dead_keys():
    for path in sorted(EXAMPLES.glob("*.json")):
        dead = _walk(json.loads(path.read_text(encoding="utf-8")))
        assert not dead, f"{path.name}: dead keys {dead}"


def test_docs_examples_match_generator():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_docs_examples.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_minimal_without_prior_leaves_change_score_null():
    result = score_filing_html(minimal_10k_html(), "10-K")
    assert result.scores.components.disclosure_change_score is None


def test_full_coverage_10k_populates_cyber_not_event_materiality():
    result = score_filing_html(
        full_coverage_10k_html(), "10-K", prior_html=full_coverage_prior_html()
    )
    components = result.scores.components
    assert components.cybersecurity_incident_risk_score is not None
    assert components.event_materiality_score is None
    assert components.event_severity_score is None
    assert result.scores.score_coverage_ratio == pytest.approx(8 / 9, rel=1e-3)
    assert result.scores.missing_components == ["event_severity_score"]
