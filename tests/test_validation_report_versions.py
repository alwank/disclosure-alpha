"""Tests for committed validation report version hygiene."""

from __future__ import annotations

from pathlib import Path

from disclosure_alpha.validation import report_versions
from disclosure_alpha.validation.report_versions import check_report_versions


def test_no_in_repo_validation_reports_required():
    repo = Path(__file__).resolve().parents[1]
    assert report_versions.COMMITTED_REPORTS == {}
    assert check_report_versions(repo) == []
