"""Committed docs/examples JSON must match generate_docs_examples.py and omit dead keys."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
