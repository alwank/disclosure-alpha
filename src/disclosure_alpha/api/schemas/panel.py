"""Panel batch response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from disclosure_alpha.version import SCORING_MODEL_VERSION


class PanelRequest(BaseModel):
    tickers: list[str]
    fiscal_year: int
    form_type: str = "10-K"
    quarter: str | None = None
    compare: str = "prior"
    include: str | None = None
    fields: str | None = None
    scoring_model_version: str = Field(
        default=SCORING_MODEL_VERSION,
        description="Scoring model: deterministic_scoring_v2 (default) or deterministic_scoring_v1",
    )


class PanelResult(BaseModel):
    ticker: str
    status: Literal["ok", "error"]
    filing: dict[str, Any] | None = None
    scores: dict[str, Any] | None = None
    error: str | None = None


class PanelResponse(BaseModel):
    results: list[PanelResult]
    summary: dict[str, int]
    versions: dict[str, str]
