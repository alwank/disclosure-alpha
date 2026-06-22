"""Check committed validation reports against runtime artifact versions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from disclosure_alpha.version import (
    DICTIONARY_VERSION,
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)

RUNTIME_VERSIONS: dict[str, str] = {
    "parser_version": PARSER_VERSION,
    "metrics_engine_version": METRICS_ENGINE_VERSION,
    "scoring_model_version": SCORING_MODEL_VERSION,
    "dictionary_version": DICTIONARY_VERSION,
}

# ponytail: only reports that ship in-repo and claim artifact versions
COMMITTED_REPORTS: dict[str, list[str]] = {
    "data/validation/reports/deterministic_validation_report.json": [
        "parser_version",
        "metrics_engine_version",
        "scoring_model_version",
        "dictionary_version",
    ],
    "data/validation/reports/l3_outcomes_report.json": [
        "parser_version",
        "metrics_engine_version",
        "scoring_model_version",
    ],
    "data/validation/reports/l3_outcomes_report_edgar.json": [
        "parser_version",
        "metrics_engine_version",
        "scoring_model_version",
    ],
    "data/validation/reports/l3_outcomes_report_edgar_fy2024.json": [
        "parser_version",
        "metrics_engine_version",
        "scoring_model_version",
    ],
}


def _load_report_versions(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    versions = data.get("versions")
    if not isinstance(versions, dict):
        raise ValueError(f"{path}: missing versions object")
    return {k: str(v) for k, v in versions.items()}


def check_report_versions(
    repo_root: Path | None = None,
    *,
    reports: dict[str, list[str]] | None = None,
) -> list[str]:
    """Return human-readable errors for stale or missing committed reports."""
    root = repo_root or Path(__file__).resolve().parents[3]
    errors: list[str] = []
    for rel_path, keys in (reports or COMMITTED_REPORTS).items():
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing committed report: {rel_path}")
            continue
        try:
            reported = _load_report_versions(path)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{rel_path}: {exc}")
            continue
        for key in keys:
            expected = RUNTIME_VERSIONS.get(key)
            if expected is None:
                continue
            actual = reported.get(key)
            if actual is None:
                errors.append(f"{rel_path}: missing {key}")
            elif actual != expected:
                errors.append(
                    f"{rel_path}: stale {key} (report={actual}, runtime={expected})"
                )
    return errors


def check_report_versions_or_raise(repo_root: Path | None = None) -> None:
    errors = check_report_versions(repo_root)
    if errors:
        raise SystemExit("\n".join(errors))
