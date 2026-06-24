import pytest

from disclosure_alpha.analytics_config import (
    PipelineConfig,
    ScoringConfig,
    build_versions,
    resolve_pipeline_config,
)
from disclosure_alpha.baselines import CalibrationContext
from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS
from disclosure_alpha.version import SCORING_MODEL_VERSION


def test_scoring_config_default_matches_builtin():
    cfg = ScoringConfig.default()
    assert dict(cfg.component_weights) == COMPONENT_WEIGHTS
    assert cfg.flag_boost_points == 15.0
    assert cfg.flag_evidence_score == 65.0
    assert cfg.resolved_id() == "builtin_default"


def test_scoring_config_explicit_id():
    cfg = ScoringConfig(config_id="my_screen_v1", component_weights=dict(COMPONENT_WEIGHTS))
    assert cfg.resolved_id() == "my_screen_v1"


def test_scoring_config_custom_hash_id():
    weights = dict(COMPONENT_WEIGHTS)
    weights["disclosure_change_score"] = 0.25
    weights["risk_factor_intensity_score"] = 0.10
    cfg = ScoringConfig(component_weights=weights)
    assert cfg.resolved_id().startswith("custom_")
    assert ScoringConfig(component_weights=weights).resolved_id() == cfg.resolved_id()


def test_scoring_config_rejects_invalid_keys():
    with pytest.raises(ValueError, match="component_weights"):
        ScoringConfig(component_weights={"risk_factor_intensity_score": 1.0})


def test_scoring_config_rejects_non_positive_weights():
    bad = dict(COMPONENT_WEIGHTS)
    bad["tone_negativity_score"] = 0.0
    with pytest.raises(ValueError, match="must be > 0"):
        ScoringConfig(component_weights=bad)


def test_pipeline_config_resolved_calibration_fills_form_type():
    cfg = PipelineConfig()
    ctx = cfg.resolved_calibration(form_type="10-Q")
    assert ctx.form_type == "10-Q"

    partial = PipelineConfig(calibration_context=CalibrationContext(sector="financials"))
    ctx2 = partial.resolved_calibration(form_type="10-K")
    assert ctx2.form_type == "10-K"
    assert ctx2.sector == "financials"


def test_resolve_pipeline_config_scoring_version_override():
    base = PipelineConfig(scoring=ScoringConfig(config_id="x", component_weights=dict(COMPONENT_WEIGHTS)))
    resolved = resolve_pipeline_config(base, scoring_model_version="deterministic_scoring_v1")
    assert resolved.scoring_model_version == "deterministic_scoring_v1"
    assert resolved.scoring.resolved_id() == "x"


def test_build_versions_includes_analytics_config_id():
    versions = build_versions(PipelineConfig.default())
    assert versions["analytics_config_id"] == "builtin_default"
    assert versions["scoring_model_version"] == SCORING_MODEL_VERSION
    assert "parser_version" in versions
    assert "metrics_engine_version" in versions
