"""Disclosure flags response models — Track A owns implementation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ActiveFlag(BaseModel):
    section: str
    flag: str
    label: str


class FlagsResponse(BaseModel):
    filing: dict[str, Any]
    flags: dict[str, dict[str, bool]]
    active_flags: list[ActiveFlag] = Field(default_factory=list)
    versions: dict[str, str]
