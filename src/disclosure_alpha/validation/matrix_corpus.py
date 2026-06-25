"""Full-matrix validation corpus loading and quality metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from disclosure_alpha.pipeline import extract_sections_from_html
from disclosure_alpha.text_metrics import tokenize_words

MATRIX_SECTIONS_10K = (
    "item_1a_risk_factors",
    "item_7_mdna",
    "item_7a_market_risk",
    "item_9a_controls",
    "item_3_legal_proceedings",
    "item_1c_cybersecurity",
)

MATRIX_SECTIONS_10Q = (
    "item_1a_risk_factors",
    "item_2_mdna",
    "item_4_controls",
    "item_1_legal_proceedings",
)

MATRIX_SECTIONS_8K = (
    "item_1_01",
    "item_1_05",
    "item_2_02",
    "item_5_02",
    "item_8_01",
)


@dataclass
class SectionQuality:
    section_name: str
    word_count: int
    extraction_confidence: float | None
    warnings: list[str] = field(default_factory=list)
    extraction_method: str | None = None


@dataclass
class MatrixCorpusRow:
    ticker: str
    form_type: str
    fiscal_year: int | None
    sections: dict[str, str]
    prior_sections: dict[str, str] = field(default_factory=dict)
    quality: dict[str, SectionQuality] = field(default_factory=dict)
    accession_number: str | None = None


def sections_for_form(form_type: str) -> tuple[str, ...]:
    form = form_type.upper()
    if form == "10-Q":
        return MATRIX_SECTIONS_10Q
    if form == "8-K":
        return MATRIX_SECTIONS_8K
    return MATRIX_SECTIONS_10K


def _quality_from_section(section) -> SectionQuality:
    warnings = list(section.warnings or [])
    return SectionQuality(
        section_name=section.section_name,
        word_count=int(section.word_count or 0),
        extraction_confidence=float(section.extraction_confidence)
        if section.extraction_confidence is not None
        else None,
        warnings=warnings,
        extraction_method=getattr(section, "extraction_method", None),
    )


def row_from_html_record(raw: dict, *, corpus_path: Path) -> MatrixCorpusRow | None:
    ticker = str(raw.get("ticker", "")).upper().strip()
    if not ticker:
        return None
    form_type = str(raw.get("form_type", "10-K"))
    fiscal_year = raw.get("fiscal_year")

    if raw.get("sections"):
        section_map = {k: str(v) for k, v in raw["sections"].items()}
        prior_map = {k: str(v) for k, v in (raw.get("prior_sections") or {}).items()}
        quality: dict[str, SectionQuality] = {}
        for name, text in section_map.items():
            qmeta = (raw.get("quality") or {}).get(name, {})
            quality[name] = SectionQuality(
                section_name=name,
                word_count=int(qmeta.get("word_count") or len(tokenize_words(text))),
                extraction_confidence=float(qmeta["extraction_confidence"])
                if qmeta.get("extraction_confidence") is not None
                else None,
                warnings=list(qmeta.get("warnings") or []),
                extraction_method=qmeta.get("extraction_method"),
            )
        return MatrixCorpusRow(
            ticker=ticker,
            form_type=form_type,
            fiscal_year=int(fiscal_year) if fiscal_year is not None else None,
            sections=section_map,
            prior_sections=prior_map,
            quality=quality,
            accession_number=raw.get("accession_number"),
        )

    html_path = raw.get("html_path")
    prior_html_path = raw.get("prior_html_path")
    if not html_path:
        return None

    path = Path(html_path)
    if not path.is_absolute():
        path = corpus_path.parent / path
    if not path.exists():
        return None

    html = path.read_text(encoding="utf-8", errors="replace")
    sections = extract_sections_from_html(html, form_type, accession_number=path.name)
    section_map = {s.section_name: s.cleaned_text for s in sections if s.cleaned_text}
    quality = {s.section_name: _quality_from_section(s) for s in sections}

    prior_map: dict[str, str] = {}
    if prior_html_path:
        prior_path = Path(prior_html_path)
        if not prior_path.is_absolute():
            prior_path = corpus_path.parent / prior_path
        if prior_path.exists():
            prior_html = prior_path.read_text(encoding="utf-8", errors="replace")
            prior_sections = extract_sections_from_html(
                prior_html, form_type, accession_number=prior_path.name
            )
            prior_map = {
                s.section_name: s.cleaned_text for s in prior_sections if s.cleaned_text
            }

    if raw.get("prior_sections"):
        prior_map = {k: str(v) for k, v in raw["prior_sections"].items()}

    return MatrixCorpusRow(
        ticker=ticker,
        form_type=form_type,
        fiscal_year=int(fiscal_year) if fiscal_year is not None else None,
        sections=section_map,
        prior_sections=prior_map,
        quality=quality,
        accession_number=raw.get("accession_number"),
    )


def load_matrix_corpus(path: Path) -> tuple[list[MatrixCorpusRow], dict[str, Any]]:
    rows_in: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows_in.append(json.loads(line))

    parsed: list[MatrixCorpusRow] = []
    skipped = 0
    for raw in rows_in:
        row = row_from_html_record(raw, corpus_path=path)
        if row is None:
            skipped += 1
            continue
        parsed.append(row)

    meta = {
        "path": str(path),
        "n_input": len(rows_in),
        "n_loaded": len(parsed),
        "n_skipped": skipped,
    }
    return parsed, meta
