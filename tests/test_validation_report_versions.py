"""Tests for committed validation report version hygiene."""

from __future__ import annotations

from pathlib import Path

from disclosure_alpha.validation.report_versions import COMMITTED_REPORTS, check_report_versions


def test_committed_reports_registered():
    assert "data/validation/reports/l3_outcomes_report_fy2025_v2.json" in COMMITTED_REPORTS


def test_check_report_versions_matches_runtime():
    repo = Path(__file__).resolve().parents[1]
    assert check_report_versions(repo) == []


def test_check_report_versions_detects_stale_scoring_version():
    repo = Path(__file__).resolve().parents[1]
    rel = "data/validation/reports/l3_outcomes_report_fy2025_v2.json"
    stale = {rel: {"scoring_model_version": "deterministic_scoring_v1"}}
    errors = check_report_versions(repo, reports=stale)
    assert any("stale scoring_model_version" in err for err in errors)
