"""Filing review response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ReadingBlock(BaseModel):
    start: int
    end: int
    kind: Literal["paragraph", "heading"]


class ReviewSection(BaseModel):
    section_name: str
    cleaned_text: str
    word_count: int
    extraction_confidence: float
    parser_version: str
    warnings: list[str] = Field(default_factory=list)
    reading_blocks: list[ReadingBlock] = Field(default_factory=list)


class ReviewEvidence(BaseModel):
    id: str
    section: str
    flag: str
    label: str
    pattern: str
    matched_text: str
    start: int
    end: int
    sentence_start: int | None = None
    sentence_end: int | None = None
    sentence: str


class FilingReviewResponse(BaseModel):
    filing: dict[str, Any]
    scores: dict[str, Any]
    sections: list[ReviewSection]
    active_flags: list[dict[str, str]]
    evidence: list[ReviewEvidence]
    changes: dict[str, Any]
    display: dict[str, Any]
    versions: dict[str, str]
