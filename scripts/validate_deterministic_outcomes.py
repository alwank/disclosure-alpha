#!/usr/bin/env python3
"""Run L3 predictive monotonicity validation (quintile gates on fetched outcomes)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from disclosure_alpha.validation.outcomes_validation import (
    OutcomesValidationConfig,
    run_outcomes_validation,
    write_outcomes_report,
)
from disclosure_alpha.validation.scoring_version import SCORING_VERSION_CHOICES, normalize_scoring_version
from disclosure_alpha.version import SCORING_MODEL_VERSION_V2

DEFAULT_OUTCOMES = Path("data/validation/outcomes/sp500_outcomes.jsonl")
DEFAULT_CORPUS = Path("data/validation/corpus/sp500_item1a.jsonl")


def _paths_for_fy(fiscal_year: int | None, scoring_version: str) -> tuple[Path, Path]:
    v2 = normalize_scoring_version(scoring_version) == SCORING_MODEL_VERSION_V2
    suffix = "_v2" if v2 else ""
    if fiscal_year is None:
        return (
            DEFAULT_OUTCOMES,
            Path(f"data/validation/reports/l3_outcomes_report{suffix}.json"),
        )
    return (
        Path(f"data/validation/outcomes/sp500_outcomes_fy{fiscal_year}.jsonl"),
        Path(f"data/validation/reports/l3_outcomes_report_fy{fiscal_year}{suffix}.json"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="L3 outcome monotonicity validation")
    parser.add_argument("--outcomes", type=Path, default=None)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--fiscal-year", type=int, default=None, help="FY cohort (sets default outcomes/report paths)")
    parser.add_argument(
        "--score-mode",
        choices=("corpus", "edgar"),
        default="corpus",
        help="corpus=Item 1A-only (fast); edgar=full 10-K+prior (slow, enables change-score gate)",
    )
    parser.add_argument(
        "--scoring-version",
        choices=SCORING_VERSION_CHOICES,
        default="v1",
        help="Scoring model for corpus/edgar scoring (default: v1)",
    )
    parser.add_argument("--min-n", type=int, default=50)
    parser.add_argument("--limit", type=int, default=None, help="Score first N outcome rows only")
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

    default_outcomes, default_report = _paths_for_fy(args.fiscal_year, args.scoring_version)
    if args.outcomes is None:
        args.outcomes = default_outcomes
    if args.out is None:
        args.out = default_report
    if args.corpus is None and args.score_mode == "corpus":
        args.corpus = DEFAULT_CORPUS if args.fiscal_year is None else Path(
            f"data/validation/corpus/sp500_item1a_fy{args.fiscal_year}.jsonl"
        )

    if not args.outcomes.exists():
        print(f"outcomes not found: {args.outcomes}", file=sys.stderr)
        print("Run: python scripts/fetch_validation_outcomes.py", file=sys.stderr)
        sys.exit(1)

    if args.score_mode == "corpus" and not args.corpus.exists():
        print(f"corpus not found: {args.corpus}", file=sys.stderr)
        sys.exit(1)

    print(f"Outcomes: {args.outcomes}", flush=True)
    print(f"Score mode: {args.score_mode}", flush=True)
    print(f"Scoring version: {args.scoring_version}", flush=True)

    report = run_outcomes_validation(
        args.outcomes,
        corpus_path=args.corpus if args.score_mode == "corpus" else None,
        score_mode=args.score_mode,
        config=OutcomesValidationConfig(
            min_n=args.min_n,
            scoring_model_version=args.scoring_version,
        ),
        limit=args.limit,
    )
    out_path = args.out
    if args.score_mode == "edgar" and args.out == default_report:
        suffix = f"_fy{args.fiscal_year}" if args.fiscal_year else ""
        out_path = Path(f"data/validation/reports/l3_outcomes_report_edgar{suffix}.json")
    write_outcomes_report(report, out_path)

    print(f"Wrote {out_path}")
    for name, gate in report.gates.items():
        q1 = f"{gate.q1_mean:.4f}" if gate.q1_mean is not None else "n/a"
        q5 = f"{gate.q5_mean:.4f}" if gate.q5_mean is not None else "n/a"
        ratio = f"{gate.q5_q1_ratio:.4f}" if gate.q5_q1_ratio is not None else "n/a"
        print(f"  {name}: {gate.status} (n={gate.n}, Q1={q1}, Q5={q5}, ratio={ratio})")
        if gate.message:
            print(f"    {gate.message}")
    print(f"monotonicity_pass: {report.monotonicity_pass}")
    print(f"overall_l3_pass: {report.overall_l3_pass}")
    if report.notes:
        for note in report.notes:
            print(f"note: {note}")
    sys.exit(0 if report.overall_l3_pass else 1)


if __name__ == "__main__":
    main()
