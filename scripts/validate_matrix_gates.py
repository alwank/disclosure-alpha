#!/usr/bin/env python3
"""Run full-matrix validation gates on a JSONL corpus."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from disclosure_alpha.validation.matrix_gates import run_matrix_validation, write_matrix_validation_report
from disclosure_alpha.validation.scoring_version import SCORING_VERSION_CHOICES, normalize_scoring_version
from disclosure_alpha.version import SCORING_MODEL_VERSION, SCORING_MODEL_VERSION_V2

DEFAULT_CORPUS = Path("tests/fixtures/validation/matrix_mini_corpus.jsonl")


def _default_report_path(scoring_version: str) -> Path:
    model = normalize_scoring_version(scoring_version)
    if model == SCORING_MODEL_VERSION_V2:
        return Path("data/validation/reports/matrix_validation_report_v2.json")
    return Path("data/validation/reports/matrix_validation_report.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Full-matrix validation gates")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS, help="Matrix JSONL corpus path")
    parser.add_argument("--out", type=Path, default=None, help="Report JSON path")
    parser.add_argument(
        "--scoring-version",
        choices=SCORING_VERSION_CHOICES,
        default="v1",
        help="Scoring model for matrix aggregation (default: v1)",
    )
    parser.add_argument("--min-extraction-rate", type=float, default=0.5)
    parser.add_argument("--min-median-confidence", type=float, default=0.6)
    parser.add_argument("--min-component-coverage", type=float, default=0.4)
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
    print(f"Scoring version: {args.scoring_version}", flush=True)
    print(f"Output: {out_path}", flush=True)

    report = run_matrix_validation(
        args.corpus,
        scoring_model_version=args.scoring_version,
        min_extraction_rate=args.min_extraction_rate,
        min_median_confidence=args.min_median_confidence,
        min_component_coverage=args.min_component_coverage,
    )
    write_matrix_validation_report(report, out_path)

    print(f"Wrote {out_path}")
    for name, gate in report.gates.items():
        val = gate.value
        vs = f"{val:.4f}" if isinstance(val, float) else val
        print(f"  {name}: {gate.status} (value={vs}, threshold={gate.threshold})")
    print(f"overall_pass: {report.overall_pass}")
    sys.exit(0 if report.overall_pass else 1)


if __name__ == "__main__":
    main()
