from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MatrixResponse(BaseModel):
    filing: dict[str, Any]
    metrics: dict[str, Any] | None = None
    scores: dict[str, Any]
    versions: dict[str, str]
    view: str = Field(default="deterministic")
