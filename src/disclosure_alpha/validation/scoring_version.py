"""Resolve validation scoring model version labels."""

from __future__ import annotations

from disclosure_alpha.version import SCORING_MODEL_VERSION, SCORING_MODEL_VERSION_V2

SCORING_VERSION_CHOICES = ("v1", "v2")


def normalize_scoring_version(version: str) -> str:
    """Return artifact id (`deterministic_scoring_v1` or `deterministic_scoring_v2`)."""
    key = version.strip().lower()
    if key in ("v1", "1", SCORING_MODEL_VERSION):
        return SCORING_MODEL_VERSION
    if key in ("v2", "2", SCORING_MODEL_VERSION_V2):
        return SCORING_MODEL_VERSION_V2
    raise ValueError(f"unsupported scoring version: {version!r} (use v1 or v2)")
