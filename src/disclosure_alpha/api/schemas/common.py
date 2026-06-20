from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FilingSummary(BaseModel):
    ticker: str
    cik: str
    accession_number: str
    form_type: str
    fiscal_year: int
    quarter: str | None = None
    filing_date: str
    report_date: str | None = None


class FilingsResponse(BaseModel):
    ticker: str
    fiscal_year: int
    filings: list[FilingSummary]


class ErrorResponse(BaseModel):
    detail: str


class MetricsResponse(BaseModel):
    filing: dict[str, Any]
    metrics: dict[str, Any]
    versions: dict[str, str]


class SectionSummary(BaseModel):
    section_name: str
    word_count: int
    extraction_confidence: float
    parser_version: str
    warnings: list[str] = Field(default_factory=list)
    cleaned_text: str | None = None


class SectionsResponse(BaseModel):
    filing: dict[str, Any]
    sections: list[SectionSummary]
    versions: dict[str, str]
