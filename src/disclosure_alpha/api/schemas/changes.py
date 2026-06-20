"""Disclosure changes response models — Track B owns implementation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChangeScore(BaseModel):
    value: float | None = None
    missing_reason: str | None = None


class ChangesResponse(BaseModel):
    filing: dict[str, Any]
    section_diffs: dict[str, float | None] = Field(default_factory=dict)
    language_deltas: dict[str, dict[str, float]] = Field(default_factory=dict)
    change_score: ChangeScore
    versions: dict[str, str]
