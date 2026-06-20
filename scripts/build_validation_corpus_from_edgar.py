#!/usr/bin/env python3
"""Build L2 validation JSONL corpus from S&P 500 tickers via EDGAR."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from disclosure_alpha.edgar.types import FilingNotFoundError, SecFetchError
from disclosure_alpha.pipeline import extract_sections_from_html, load_filing_bundle
from disclosure_alpha.validation.corpus import (
    CorpusLoadConfig,
    filter_skip_reason,
    load_manifest,
    manifest_path_for,
    parse_corpus_row,
)
from disclosure_alpha.validation.universe import DEFAULT_SP500_PATH, load_universe

ITEM_1A = "item_1a_risk_factors"
DEFAULT_OUT = Path("data/validation/corpus/sp500_item1a.jsonl")
DEFAULT_MIN_CONFIDENCE = 0.75
DEFAULT_MIN_WORD_COUNT = 200


def _load_existing_tickers(path: Path) -> set[str]:
    if not path.exists():
        return set()
    tickers: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            ticker = str(row.get("ticker", "")).upper()
            if ticker:
                tickers.add(ticker)
    return tickers


def _filter_drop_tickers(
    corpus_path: Path,
    *,
    min_confidence: float,
    min_word_count: int,
) -> set[str]:
    if not corpus_path.exists():
        return set()
    cfg = CorpusLoadConfig(min_confidence=min_confidence, min_word_count=min_word_count)
    dropped: set[str] = set()
    with corpus_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            raw = json.loads(line)
            row = parse_corpus_row(raw, corpus_path=corpus_path)
            if row is None:
                continue
            if filter_skip_reason(row, cfg):
                dropped.add(row.ticker)
    return dropped


def _retry_ticker_set(
    *,
    corpus_path: Path,
    manifest_path: Path,
    validation_report: Path | None,
    min_confidence: float,
    min_word_count: int,
) -> set[str]:
    tickers: set[str] = set()
    manifest = load_manifest(manifest_path)
    if manifest:
        for failure in manifest.get("failures") or []:
            t = str(failure.get("ticker", "")).upper()
            if t:
                tickers.add(t)
    tickers |= _filter_drop_tickers(
        corpus_path,
        min_confidence=min_confidence,
        min_word_count=min_word_count,
    )
    if validation_report and validation_report.exists():
        report = json.loads(validation_report.read_text(encoding="utf-8"))
        sample = report.get("corpus", {}).get("filtered_tickers_sample") or []
        tickers |= {str(t).upper() for t in sample}
    return tickers


def _rewrite_corpus_without(path: Path, exclude: set[str]) -> int:
    if not path.exists():
        return 0
    kept: list[str] = []
    removed = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            ticker = str(row.get("ticker", "")).upper()
            if ticker in exclude:
                removed += 1
                continue
            kept.append(line.rstrip("\n"))
    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    return removed


def _quality_tier(sec, *, min_confidence: float, min_word_count: int) -> str:
    if sec.word_count >= min_word_count and sec.extraction_confidence >= min_confidence:
        return "analysis"
    return "extracted"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build S&P 500 Item 1A validation corpus from EDGAR"
    )
    parser.add_argument("--universe", type=Path, default=DEFAULT_SP500_PATH)
    parser.add_argument("--fiscal-year", type=int, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--form", default="10-K")
    parser.add_argument("--resume", action="store_true", help="Skip tickers already in output")
    parser.add_argument(
        "--retry-failures",
        action="store_true",
        help="Re-fetch manifest failures and filter-drop tickers",
    )
    parser.add_argument(
        "--validation-report",
        type=Path,
        default=Path("data/validation/reports/deterministic_validation_report.json"),
    )
    parser.add_argument("--min-confidence", type=float, default=DEFAULT_MIN_CONFIDENCE)
    parser.add_argument("--min-word-count", type=int, default=DEFAULT_MIN_WORD_COUNT)
    parser.add_argument("--limit", type=int, default=None, help="Process first N tickers (debug)")
    args = parser.parse_args()

    if not args.universe.exists():
        print(f"universe not found: {args.universe}", file=sys.stderr)
        print("Run: python scripts/fetch_sp500_universe.py", file=sys.stderr)
        sys.exit(1)

    entries = load_universe(args.universe)
    if args.limit is not None:
        entries = entries[: args.limit]

    manifest_path = manifest_path_for(args.out)
    retry_tickers: set[str] = set()
    if args.retry_failures:
        retry_tickers = _retry_ticker_set(
            corpus_path=args.out,
            manifest_path=manifest_path,
            validation_report=args.validation_report,
            min_confidence=args.min_confidence,
            min_word_count=args.min_word_count,
        )
        removed = _rewrite_corpus_without(args.out, retry_tickers)
        print(f"retry-failures: {len(retry_tickers)} tickers, removed {removed} from corpus")

    existing = _load_existing_tickers(args.out) if args.resume and not args.retry_failures else set()
    if args.resume and not args.out.exists():
        existing = set()

    if args.retry_failures:
        entries = [e for e in entries if e.ticker in retry_tickers]
    elif args.limit is None and not args.resume:
        existing = set()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if (args.resume or args.retry_failures) and args.out.exists() else "w"
    written = 0
    skipped = 0
    failures: list[dict[str, str]] = []
    succeeded_retry: set[str] = set()

    with args.out.open(mode, encoding="utf-8") as out_f:
        for entry in entries:
            if entry.ticker in existing:
                skipped += 1
                continue
            try:
                bundle = load_filing_bundle(
                    entry.ticker,
                    args.fiscal_year,
                    form_type=args.form,
                    use_cache=True,
                    compare_prior=False,
                )
                sections = extract_sections_from_html(
                    bundle.html,
                    bundle.ref.form_type,
                    cik=bundle.ref.cik,
                    accession_number=bundle.ref.accession_number,
                )
                sec = next((s for s in sections if s.section_name == ITEM_1A), None)
                if sec is None:
                    failures.append({"ticker": entry.ticker, "reason": "no_item_1a"})
                    print(f"skip {entry.ticker}: no Item 1A", file=sys.stderr)
                    continue
                tier = _quality_tier(
                    sec,
                    min_confidence=args.min_confidence,
                    min_word_count=args.min_word_count,
                )
                row = {
                    "ticker": entry.ticker,
                    "fiscal_year": bundle.ref.fiscal_year,
                    "filing_date": bundle.ref.filing_date,
                    "section_name": sec.section_name,
                    "cleaned_text": sec.cleaned_text,
                    "word_count": sec.word_count,
                    "extraction_confidence": sec.extraction_confidence,
                    "extraction_method": sec.extraction_method,
                    "warnings": sec.warnings,
                    "quality_tier": tier,
                    "accession_number": bundle.ref.accession_number,
                    "cik": bundle.ref.cik,
                }
                out_f.write(json.dumps(row) + "\n")
                written += 1
                succeeded_retry.add(entry.ticker)
                if written % 25 == 0:
                    print(f"progress: {written} written", file=sys.stderr)
            except FilingNotFoundError as exc:
                failures.append({"ticker": entry.ticker, "reason": "filing_not_found"})
                print(f"skip {entry.ticker}: {exc}", file=sys.stderr)
            except SecFetchError as exc:
                failures.append({"ticker": entry.ticker, "reason": "sec_fetch_error"})
                print(f"skip {entry.ticker}: {exc}", file=sys.stderr)
            except ValueError as exc:
                failures.append({"ticker": entry.ticker, "reason": "value_error"})
                print(f"skip {entry.ticker}: {exc}", file=sys.stderr)

    n_in_corpus = len(_load_existing_tickers(args.out))
    manifest = {
        "fiscal_year": args.fiscal_year,
        "form": args.form,
        "universe": str(args.universe),
        "corpus": str(args.out),
        "n_written": n_in_corpus,
        "n_new": written,
        "n_skipped_existing": skipped,
        "failures": failures,
    }
    if manifest_path.exists() and (args.resume or args.retry_failures):
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        prior_failures = [
            f
            for f in (prior.get("failures") or [])
            if f.get("ticker") not in succeeded_retry
        ]
        prior_tickers = {f["ticker"] for f in prior_failures}
        merged_failures = list(prior_failures)
        for f in failures:
            if f["ticker"] not in prior_tickers:
                merged_failures.append(f)
        manifest["failures"] = merged_failures
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(
        f"Wrote {written} rows to {args.out} "
        f"(skipped {skipped} existing, {len(failures)} failed)"
    )
    print(f"Wrote manifest to {manifest_path}")
    if failures:
        print(
            f"failed tickers ({len(failures)}): {', '.join(f['ticker'] for f in failures[:20])}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
