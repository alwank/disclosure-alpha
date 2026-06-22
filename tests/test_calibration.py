"""Tests for calibration transforms."""

from __future__ import annotations

from disclosure_alpha.calibration import (
    CalibrationContext,
    calibrate_metric,
    robust_z_score,
    winsorized_min_max,
)
from disclosure_alpha.baselines import lookup_baseline


def test_calibrate_metric_percentile_rank():
    cal = calibrate_metric("negative_word_ratio", 0.05, CalibrationContext(form_type="10-K"))
    assert cal.calibration_status == "calibrated"
    assert 0.0 <= cal.calibrated_value <= 100.0
    assert cal.raw_value == 0.05


def test_calibrate_metric_fallback_unknown_metric():
    cal = calibrate_metric("unknown_metric_xyz", 0.03, CalibrationContext())
    assert cal.calibration_status == "fallback"
    assert cal.calibrated_value == 0.03


def test_calibrate_metric_ratio_fallback_scaling():
    cal = calibrate_metric("custom_ratio", 0.04, CalibrationContext(form_type="8-K"))
    assert cal.calibration_status == "fallback"
    assert cal.calibrated_value == 4.0


def test_robust_z_score_centered():
    refs = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert abs(robust_z_score(3.0, refs)) < 0.01


def test_winsorized_min_max_bounds():
    refs = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    mid = winsorized_min_max(5.0, refs)
    assert 40.0 <= mid <= 60.0
    assert 0.0 <= winsorized_min_max(-5.0, refs) <= 100.0
    assert 0.0 <= winsorized_min_max(50.0, refs) <= 100.0


def test_lookup_baseline_form_fallback():
    stats = lookup_baseline("negative_word_ratio", CalibrationContext(form_type="10-K"))
    assert stats is not None
    assert stats.sample_size >= 5
    assert stats.percentiles


def test_lookup_baseline_sector_override():
    stats = lookup_baseline(
        "negative_word_ratio",
        CalibrationContext(form_type="10-K", sector="financials"),
    )
    assert stats is not None
    assert "financials" in stats.cohort


def test_lookup_baseline_unknown_form_returns_none():
    stats = lookup_baseline("negative_word_ratio", CalibrationContext(form_type="UNKNOWN-FORM"))
    assert stats is None
