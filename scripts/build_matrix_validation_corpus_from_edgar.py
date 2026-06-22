#!/usr/bin/env python3
"""Build full-matrix validation JSONL corpus from S&P 500 tickers via EDGAR."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from disclosure_alpha.edgar.types import FilingNotFoundError, SecFetchError
from disclosure_alpha.pipeline import extract_sections_from_html, load_filing_bundle
from disclosure_alpha.validation.corpus import load_manifest, manifest_path_for
from disclosure_alpha.validation.matrix_corpus import sections_for_form
from disclosure_alpha.validation.universe import DEFAULT_SP500_PATH, load_universe


def _default_out_for_fiscal_year(fiscal_year: int) -> Path:
    return Path(f"data/validation/corpus/sp500_matrix_fy{fiscal_year}.jsonl")


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


def matrix_row_from_bundle(
    bundle,
    *,
    form_type: str = "10-K",
) -> dict | None:
    """Build a matrix corpus JSON object from a filing bundle."""
    ticker = bundle.ref.ticker.upper()
    required = sections_for_form(form_type)
    sections = extract_sections_from_html(
        bundle.html,
        form_type,
        cik=bundle.ref.cik,
        accession_number=bundle.ref.accession_number,
    )
    section_map = {
        s.section_name: s.cleaned_text
        for s in sections
        if s.section_name in required and s.cleaned_text
    }
    if not section_map:
        return None

    prior_map: dict[str, str] = {}
    if bundle.prior_html:
        prior_sections = extract_sections_from_html(
            bundle.prior_html,
            form_type,
            cik=bundle.ref.cik,
            accession_number=bundle.prior_accession or "prior",
        )
        prior_map = {
            s.section_name: s.cleaned_text
            for s in prior_sections
            if s.section_name in required and s.cleaned_text
        }

    quality: dict[str, dict] = {}
    for s in sections:
        if s.section_name in section_map:
            quality[s.section_name] = {
                "word_count": s.word_count,
                "extraction_confidence": s.extraction_confidence,
                "warnings": list(s.warnings or []),
                "extraction_method": getattr(s, "extraction_method", None),
            }

    return {
        "ticker": ticker,
        "fiscal_year": bundle.ref.fiscal_year,
        "form_type": form_type,
        "sections": section_map,
        "prior_sections": prior_map,
        "quality": quality,
        "accession_number": bundle.ref.accession_number,
        "cik": bundle.ref.cik,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build S&P 500 full-matrix validation corpus from EDGAR"
    )
    parser.add_argument("--universe", type=Path, default=DEFAULT_SP500_PATH)
    parser.add_argument("--fiscal-year", type=int, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--form", default="10-K")
    parser.add_argument("--resume", action="store_true", help="Skip tickers already in output")
    parser.add_argument(
        "--no-prior",
        action="store_true",
        help="Skip prior-year filing fetch for prior_sections",
    )
    parser.add_argument("--limit", type=int, default=None, help="Process first N tickers (debug)")
    args = parser.parse_args()

    out = args.out or _default_out_for_fiscal_year(args.fiscal_year)

    if not args.universe.exists():
        print(f"universe not found: {args.universe}", file=sys.stderr)
        print("Run: python scripts/fetch_sp500_universe.py", file=sys.stderr)
        sys.exit(1)

    entries = load_universe(args.universe)
    if args.limit is not None:
        entries = entries[: args.limit]

    existing = _load_existing_tickers(out) if args.resume else set()
    if args.resume and not out.exists():
        existing = set()
    if args.limit is None and not args.resume:
        existing = set()

    out.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.resume and out.exists() else "w"
    written = 0
    skipped = 0
    failures: list[dict[str, str]] = []
    succeeded_retry: set[str] = set()

    with out.open(mode, encoding="utf-8") as out_f:
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
                    compare_prior=not args.no_prior,
                )
                row = matrix_row_from_bundle(bundle, form_type=args.form)
                if row is None:
                    failures.append({"ticker": entry.ticker, "reason": "no_matrix_sections"})
                    print(f"skip {entry.ticker}: no matrix sections", file=sys.stderr)
                    continue
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

    manifest_path = manifest_path_for(out)
    n_in_corpus = len(_load_existing_tickers(out))
    manifest = {
        "fiscal_year": args.fiscal_year,
        "form": args.form,
        "universe": str(args.universe),
        "corpus": str(out),
        "compare_prior": not args.no_prior,
        "n_written": n_in_corpus,
        "n_new": written,
        "n_skipped_existing": skipped,
        "failures": failures,
    }
    if manifest_path.exists() and args.resume:
        prior = load_manifest(manifest_path) or {}
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
        f"Wrote {written} rows to {out} "
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
