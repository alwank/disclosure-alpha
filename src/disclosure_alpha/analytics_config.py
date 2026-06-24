"""Pipeline and scoring configuration for the Python SDK."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from typing import Mapping

from disclosure_alpha.baselines import CalibrationContext
from disclosure_alpha.scoring_types import COMPONENT_WEIGHTS
from disclosure_alpha.version import METRICS_ENGINE_VERSION, PARSER_VERSION, SCORING_MODEL_VERSION

_BUILTIN_DEFAULT_ID = "builtin_default"

def _default_component_weights() -> dict[str, float]:
    return dict(COMPONENT_WEIGHTS)


def _validate_component_weights(weights: Mapping[str, float]) -> dict[str, float]:
    expected = set(COMPONENT_WEIGHTS)
    actual = set(weights)
    if actual != expected:
        missing = expected - actual
        extra = actual - expected
        parts: list[str] = []
        if missing:
            parts.append(f"missing keys: {sorted(missing)}")
        if extra:
            parts.append(f"unknown keys: {sorted(extra)}")
        raise ValueError(f"component_weights must match COMPONENT_WEIGHTS exactly ({'; '.join(parts)})")
    normalized = {key: float(weights[key]) for key in COMPONENT_WEIGHTS}
    for key, value in normalized.items():
        if value <= 0:
            raise ValueError(f"component_weights[{key!r}] must be > 0, got {value}")
    return normalized


def _validate_score_range(name: str, value: float) -> None:
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"{name} must be in [0, 100], got {value}")


@dataclass(frozen=True)
class ScoringConfig:
    config_id: str = _BUILTIN_DEFAULT_ID
    component_weights: Mapping[str, float] = field(default_factory=_default_component_weights)
    flag_boost_points: float = 15.0
    flag_evidence_score: float = 65.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "component_weights", _validate_component_weights(self.component_weights))
        _validate_score_range("flag_boost_points", self.flag_boost_points)
        _validate_score_range("flag_evidence_score", self.flag_evidence_score)

    @classmethod
    def default(cls) -> ScoringConfig:
        return cls()

    def resolved_id(self) -> str:
        if self.config_id != _BUILTIN_DEFAULT_ID:
            return self.config_id
        if self == ScoringConfig.default():
            return _BUILTIN_DEFAULT_ID
        payload = {
            "component_weights": dict(self.component_weights),
            "flag_boost_points": self.flag_boost_points,
            "flag_evidence_score": self.flag_evidence_score,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:12]
        return f"custom_{digest}"


@dataclass(frozen=True)
class PipelineConfig:
    scoring: ScoringConfig = field(default_factory=ScoringConfig.default)
    calibration_context: CalibrationContext | None = None
    scoring_model_version: str = SCORING_MODEL_VERSION

    @classmethod
    def default(cls) -> PipelineConfig:
        return cls()

    def resolved_calibration(self, *, form_type: str | None = None) -> CalibrationContext:
        ctx = self.calibration_context or CalibrationContext()
        if form_type is None:
            return ctx
        if ctx.form_type == form_type:
            return ctx
        return replace(ctx, form_type=form_type)

    def version_fields(self) -> dict[str, str]:
        from disclosure_alpha.validation.scoring_version import normalize_scoring_version

        return {
            "analytics_config_id": self.scoring.resolved_id(),
            "scoring_model_version": normalize_scoring_version(self.scoring_model_version),
        }


def resolve_pipeline_config(
    config: PipelineConfig | None,
    *,
    scoring_model_version: str | None = None,
) -> PipelineConfig:
    from disclosure_alpha.validation.scoring_version import normalize_scoring_version

    base = config or PipelineConfig.default()
    if scoring_model_version is None:
        return base
    return replace(
        base,
        scoring_model_version=normalize_scoring_version(scoring_model_version),
    )


def build_versions(config: PipelineConfig | None = None) -> dict[str, str]:
    cfg = config or PipelineConfig.default()
    return {
        "parser_version": PARSER_VERSION,
        "metrics_engine_version": METRICS_ENGINE_VERSION,
        **cfg.version_fields(),
    }
