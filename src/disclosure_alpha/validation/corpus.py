from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from disclosure_alpha.pipeline import extract_sections_from_html
from disclosure_alpha.text_metrics import tokenize_words
from disclosure_alpha.validation.types import CorpusRow

ITEM_1A = "item_1a_risk_factors"


@dataclass
class CorpusLoadConfig:
    min_word_count: int = 200
    min_confidence: float = 0.75
    section_name: str = ITEM_1A
    holdout_tickers: frozenset[str] = frozenset()


def load_holdout_tickers(path: Path | None) -> frozenset[str]:
    if path is None or not path.exists():
        return frozenset()
    tickers: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        t = line.strip().upper()
        if t and not t.startswith("#"):
            tickers.add(t)
    return frozenset(tickers)


def load_manifest(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_path_for(corpus_path: Path) -> Path:
    return corpus_path.with_suffix(".manifest.json")


def _row_from_dict(raw: dict, *, corpus_path: Path) -> CorpusRow | None:
    ticker = str(raw.get("ticker", "")).upper().strip()
    if not ticker:
        return None

    section_name = str(raw.get("section_name", ITEM_1A))
    cleaned_text = raw.get("cleaned_text")
    html_path = raw.get("html_path")
    form_type = str(raw.get("form_type", "10-K"))

    if not cleaned_text and html_path:
        path = Path(html_path)
        if not path.is_absolute():
            path = corpus_path.parent / path
        html = path.read_text(encoding="utf-8", errors="replace")
        sections = extract_sections_from_html(
            html, form_type, accession_number=path.name
        )
        match = next((s for s in sections if s.section_name == section_name), None)
        if match is None:
            return None
        cleaned_text = match.cleaned_text
        word_count = match.word_count
        confidence = float(match.extraction_confidence or 0.5)
    else:
        cleaned_text = str(cleaned_text or "")
        word_count = int(raw.get("word_count") or len(tokenize_words(cleaned_text)))
        conf_raw = raw.get("extraction_confidence")
        confidence = float(conf_raw) if conf_raw is not None else None

    fiscal_year = raw.get("fiscal_year")
    fy = int(fiscal_year) if fiscal_year is not None else None

    return CorpusRow(
        ticker=ticker,
        fiscal_year=fy,
        section_name=section_name,
        cleaned_text=cleaned_text,
        word_count=word_count,
        extraction_confidence=confidence,
        accession_number=raw.get("accession_number"),
    )


def parse_corpus_row(raw: dict, *, corpus_path: Path) -> CorpusRow | None:
    return _row_from_dict(raw, corpus_path=corpus_path)


def filter_skip_reason(row: CorpusRow, cfg: CorpusLoadConfig) -> str | None:
    if row.section_name != cfg.section_name:
        return "wrong_section"
    if row.word_count < cfg.min_word_count:
        return "short_text"
    if row.extraction_confidence is not None and row.extraction_confidence < cfg.min_confidence:
        return "low_confidence"
    return None


def load_corpus(
    path: Path,
    *,
    config: CorpusLoadConfig | None = None,
    exclude_holdout: bool = True,
) -> tuple[list[CorpusRow], dict]:
    cfg = config or CorpusLoadConfig()
    if cfg.holdout_tickers and exclude_holdout:
        holdout = cfg.holdout_tickers
    else:
        holdout = frozenset()

    rows_in: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows_in.append(json.loads(line))

    parsed: list[CorpusRow] = []
    filter_breakdown: dict[str, int] = {
        "parse_error": 0,
        "holdout": 0,
        "wrong_section": 0,
        "short_text": 0,
        "low_confidence": 0,
    }
    filtered_tickers: list[str] = []

    for raw in rows_in:
        row = _row_from_dict(raw, corpus_path=path)
        if row is None:
            filter_breakdown["parse_error"] += 1
            continue
        if row.ticker in holdout:
            filter_breakdown["holdout"] += 1
            continue
        reason = filter_skip_reason(row, cfg)
        if reason:
            filter_breakdown[reason] += 1
            if len(filtered_tickers) < 50:
                filtered_tickers.append(row.ticker)
            continue
        parsed.append(row)

    fiscal_years = sorted({r.fiscal_year for r in parsed if r.fiscal_year is not None})
    n_skipped = len(rows_in) - len(parsed) - filter_breakdown["holdout"]
    meta = {
        "path": str(path),
        "n_input": len(rows_in),
        "n_after_filters": len(parsed),
        "n_skipped": n_skipped,
        "fiscal_years": fiscal_years,
        "holdout_excluded": sorted(holdout),
        "filter_breakdown": filter_breakdown,
        "filtered_tickers_sample": filtered_tickers,
    }
    return parsed, meta
