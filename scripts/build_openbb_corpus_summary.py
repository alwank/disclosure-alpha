#!/usr/bin/env python3
"""Regenerate OpenBB corpus summary JSON from validation score cache."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/validation/cache/scores_sp500_matrix_fy2025_v2.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("src/disclosure_alpha/openbb/data/sp500_overall_fy2025.json"),
    )
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    overalls = [r["overall_disclosure_risk_score"] for r in rows]
    payload = {
        "cohort_label": "S&P 500 FY2025 10-K",
        "fiscal_year": 2025,
        "form_type": "10-K",
        "n": len(rows),
        "median_overall": round(median(overalls), 1),
        "sorted_overalls": sorted(overalls),
        "by_ticker": {r["ticker"]: r["overall_disclosure_risk_score"] for r in rows},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} (n={payload['n']}, median={payload['median_overall']})")


if __name__ == "__main__":
    main()
