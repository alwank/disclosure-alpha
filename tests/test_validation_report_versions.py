"""Tests for committed validation report version hygiene."""

from __future__ import annotations

from pathlib import Path

from disclosure_alpha.validation.report_versions import check_report_versions


def test_committed_validation_reports_match_runtime_versions():
    repo = Path(__file__).resolve().parents[1]
    errors = check_report_versions(repo)
    assert errors == [], "\n".join(errors)
