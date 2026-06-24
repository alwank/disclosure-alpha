from unittest.mock import patch

import pytest

from disclosure_alpha.analytics_config import PipelineConfig, ScoringConfig
from disclosure_alpha.baselines import CalibrationContext
from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix_v2
from disclosure_alpha.pipeline import (
    MetricsResult,
    score_filing_html,
    score_for_model,
    score_panel_tickers,
)
from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS
from disclosure_alpha.validation.scoring_version import SCORING_MODEL_VERSION_V1

_MINIMAL_HTML = """
<html><body>
<p>Item 1A. Risk Factors</p>
<p>We may face litigation and regulatory investigation. Results could be uncertain.</p>
<p>Item 7. Management's Discussion and Analysis</p>
<p>Revenue may decline amid margin pressure and liquidity constraints.</p>
</body></html>
"""


def test_default_config_parity_and_analytics_config_id():
    baseline = score_filing_html(_MINIMAL_HTML, "10-K")
    explicit = score_filing_html(_MINIMAL_HTML, "10-K", config=PipelineConfig.default())
    assert baseline.scores.overall_disclosure_risk_score == explicit.scores.overall_disclosure_risk_score
    assert baseline.versions["analytics_config_id"] == "builtin_default"
    assert explicit.versions["analytics_config_id"] == "builtin_default"


def test_weight_override_changes_overall_score():
    weights = dict(COMPONENT_WEIGHTS)
    weights["disclosure_change_score"] = 0.25
    weights["risk_factor_intensity_score"] = 0.10
    config = PipelineConfig(
        scoring=ScoringConfig(
            config_id="change_heavy_v1",
            component_weights=weights,
        )
    )
    baseline = score_filing_html(_MINIMAL_HTML, "10-K")
    custom = score_filing_html(_MINIMAL_HTML, "10-K", config=config)
    assert custom.versions["analytics_config_id"] == "change_heavy_v1"
    if baseline.scores.components.disclosure_change_score is not None:
        assert custom.scores.overall_disclosure_risk_score != baseline.scores.overall_disclosure_risk_score


def test_calibration_context_changes_v2_risk_factor_intensity():
    metrics = MetricsResult(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.11,
                "uncertainty_word_ratio": 0.09,
                "litigious_word_ratio": 0.05,
                "boilerplate_phrase_ratio": 0.1,
                "numeric_specificity_score": 20,
                "company_specificity_score": 30,
                "constraining_word_ratio": 0.02,
            }
        },
        section_diffs={"item_1a_risk_factors": 50.0},
        section_flags={},
        section_densities={},
        language_deltas={},
    )
    default = aggregate_deterministic_matrix_v2(
        section_metrics=metrics.section_metrics,
        section_diffs=metrics.section_diffs,
        section_flags=metrics.section_flags,
        language_deltas=metrics.language_deltas,
        section_densities=metrics.section_densities,
        calibration_context=CalibrationContext(form_type="10-K"),
    )
    financials = aggregate_deterministic_matrix_v2(
        section_metrics=metrics.section_metrics,
        section_diffs=metrics.section_diffs,
        section_flags=metrics.section_flags,
        language_deltas=metrics.language_deltas,
        section_densities=metrics.section_densities,
        calibration_context=CalibrationContext(form_type="10-K", sector="financials"),
    )
    assert default.components.risk_factor_intensity_score is not None
    assert financials.components.risk_factor_intensity_score is not None
    assert (
        default.components.risk_factor_intensity_score
        != financials.components.risk_factor_intensity_score
    )


def test_score_for_model_v1_with_custom_config_id():
    metrics = MetricsResult(
        section_metrics={
            "item_1a_risk_factors": {
                "negative_word_ratio": 0.1,
                "uncertainty_word_ratio": 0.1,
                "litigious_word_ratio": 0.05,
                "boilerplate_phrase_ratio": 0.1,
                "numeric_specificity_score": 20,
                "company_specificity_score": 30,
                "constraining_word_ratio": 0.02,
            }
        },
        section_diffs={"item_1a_risk_factors": 55.0},
        section_flags={},
        section_densities={},
        language_deltas={},
    )
    config = PipelineConfig(
        scoring=ScoringConfig(config_id="legacy_weights_v1", component_weights=dict(COMPONENT_WEIGHTS))
    )
    scores = score_for_model(metrics, SCORING_MODEL_VERSION_V1, config=config)
    assert scores.overall_disclosure_risk_score is not None


@patch("disclosure_alpha.pipeline.score_filing_ticker")
def test_panel_batch_versions_include_analytics_config_id(mock_score_ticker):
    from disclosure_alpha.pipeline import FilingScoreResult
    from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix

    metrics = MetricsResult(
        section_metrics={},
        section_diffs={},
        section_flags={},
        section_densities={},
        language_deltas={},
    )
    mock_score_ticker.return_value = FilingScoreResult(
        sections=[],
        metrics=metrics,
        scores=aggregate_deterministic_matrix(section_metrics={}, section_diffs={}),
        versions={},
        filing={"form_type": "10-K", "ticker": "AAPL"},
    )
    config = PipelineConfig(
        scoring=ScoringConfig(config_id="panel_test_v1", component_weights=dict(COMPONENT_WEIGHTS))
    )
    batch = score_panel_tickers(["AAPL"], 2025, config=config)
    assert batch.versions["analytics_config_id"] == "panel_test_v1"
