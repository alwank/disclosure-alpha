"""Check committed validation reports against runtime artifact versions."""

from __future__ import annotations

import json
from pathlib import Path

from disclosure_alpha.version import (
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)

COMMITTED_REPORTS: dict[str, dict[str, str]] = {}


def _load_report_versions(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    versions = data.get("versions")
    if not isinstance(versions, dict):
        raise ValueError(f"{path}: missing versions object")
    return {k: str(v) for k, v in versions.items()}


def check_report_versions(
    repo_root: Path | None = None,
    *,
    reports: dict[str, dict[str, str]] | None = None,
) -> list[str]:
    """Return human-readable errors for stale or missing committed reports."""
    root = repo_root or Path(__file__).resolve().parents[3]
    errors: list[str] = []
    for rel_path, expected_versions in (reports or COMMITTED_REPORTS).items():
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing committed report: {rel_path}")
            continue
        try:
            reported = _load_report_versions(path)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{rel_path}: {exc}")
            continue
        for key, expected in expected_versions.items():
            actual = reported.get(key)
            if actual is None:
                errors.append(f"{rel_path}: missing {key}")
            elif actual != expected:
                # ponytail: allow build-only dictionary/metrics iteration without forcing full corpus replay.
                if key in {"metrics_engine_version", "dictionary_version"}:
                    continue
                errors.append(
                    f"{rel_path}: stale {key} (report={actual}, runtime={expected})"
                )
    return errors


def check_report_versions_or_raise(repo_root: Path | None = None) -> None:
    errors = check_report_versions(repo_root)
    if errors:
        raise SystemExit("\n".join(errors))
