#!/usr/bin/env python3
"""Run L2 construct validity validation on a user-supplied corpus."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from disclosure_alpha.validation.construct import ConstructConfig, run_construct_validation, write_validation_report
from disclosure_alpha.validation.edgar_gates import EdgarGatesConfig
from disclosure_alpha.validation.scoring_version import SCORING_VERSION_CHOICES, normalize_scoring_version
from disclosure_alpha.version import SCORING_MODEL_VERSION_V2

DEFAULT_CORPUS = Path("data/validation/corpus/sp500_item1a.jsonl")


def _default_report_path(scoring_version: str) -> Path:
    if normalize_scoring_version(scoring_version) == SCORING_MODEL_VERSION_V2:
        return Path("data/validation/reports/deterministic_validation_report_v2.json")
    return Path("data/validation/reports/deterministic_validation_report.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="L2 construct validity validation")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS, help="JSONL corpus path")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--scoring-version",
        choices=SCORING_VERSION_CHOICES,
        default="v1",
        help="Scoring model recorded in report (default: v1)",
    )
    parser.add_argument("--universe", type=Path, default=None, help="Report coverage vs universe CSV")
    parser.add_argument("--manifest", type=Path, default=None, help="EDGAR build manifest JSON")
    parser.add_argument("--min-n", type=int, default=80)
    parser.add_argument("--min-confidence", type=float, default=0.75)
    parser.add_argument("--min-word-count", type=int, default=200)
    parser.add_argument("--boilerplate-min-docs", type=int, default=10)
    parser.add_argument("--boilerplate-min-doc-frac", type=float, default=0.25)
    parser.add_argument("--holdout", type=Path, default=None)
    parser.add_argument(
        "--check-versions",
        action="store_true",
        help="Exit 1 if committed validation reports have stale artifact versions",
    )
    args = parser.parse_args()

    if args.check_versions:
        from disclosure_alpha.validation.report_versions import check_report_versions

        errors = check_report_versions()
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            sys.exit(1)
        print("validation report versions OK")
        sys.exit(0)

    if not args.corpus.exists():
        print(f"corpus not found: {args.corpus}", file=sys.stderr)
        sys.exit(1)

    out_path = args.out or _default_report_path(args.scoring_version)
    print(f"Corpus: {args.corpus}", flush=True)
    if args.universe:
        print(f"Universe: {args.universe}", flush=True)
    print(f"Scoring version: {args.scoring_version}", flush=True)
    print(f"Output: {out_path}", flush=True)

    report = run_construct_validation(
        args.corpus,
        config=ConstructConfig(
            min_n=args.min_n,
            boilerplate_min_docs=args.boilerplate_min_docs,
            boilerplate_min_doc_frac=args.boilerplate_min_doc_frac,
            min_confidence=args.min_confidence,
            min_word_count=args.min_word_count,
            holdout_path=args.holdout,
            universe_path=args.universe if args.universe and args.universe.exists() else None,
            manifest_path=args.manifest,
            edgar_gates=EdgarGatesConfig(),
            scoring_model_version=args.scoring_version,
        ),
    )
    print("Writing report...", flush=True)
    write_validation_report(report, out_path)

    print(f"Wrote {out_path}")
    print("EDGAR gates:")
    for name, gate in report.edgar_gates.items():
        val = gate.get("value")
        vs = f"{val:.4f}" if isinstance(val, float) else val
        print(f"  {name}: {gate['status']} (value={vs}, threshold={gate['threshold']})")
    print(f"edgar_pass: {report.edgar_pass}")
    print("Construct pairs:")
    for name, pair in report.pairs.items():
        rho = f"{pair.spearman_rho:.4f}" if pair.spearman_rho is not None else "n/a"
        print(f"  {name}: {pair.status} (rho={rho}, n={pair.n})")
    print(f"construct_pass: {report.construct_pass}")
    print(f"overall_l2_pass: {report.overall_l2_pass}")
    sys.exit(0 if report.overall_l2_pass else 1)


if __name__ == "__main__":
    main()
