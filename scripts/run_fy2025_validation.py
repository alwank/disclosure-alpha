#!/usr/bin/env python3
"""Run FY2025 L2 construct + L3 outcomes validation and write reports.

Requires local gitignored artifacts:
  data/validation/corpus/sp500_item1a.jsonl
  data/validation/outcomes/sp500_outcomes.jsonl
  data/validation/cache/scores_sp500_matrix_fy2025_v2.jsonl

Usage:
  python scripts/run_fy2025_validation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from disclosure_alpha.validation.construct import (  # noqa: E402
    ConstructConfig,
    run_construct_validation,
    write_validation_report,
)
from disclosure_alpha.validation.outcomes_validation import (  # noqa: E402
    OutcomesValidationConfig,
    run_outcomes_validation,
    write_outcomes_report,
)

CORPUS = ROOT / "data/validation/corpus/sp500_item1a.jsonl"
OUTCOMES = ROOT / "data/validation/outcomes/sp500_outcomes.jsonl"
SCORE_CACHE = ROOT / "data/validation/cache/scores_sp500_matrix_fy2025_v2.jsonl"
REPORTS = ROOT / "data/validation/reports"


def _require(path: Path, label: str) -> None:
    if not path.exists():
        print(f"ERROR: missing {label}: {path}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    for path, label in [
        (CORPUS, "Item 1A corpus"),
        (OUTCOMES, "outcomes"),
        (SCORE_CACHE, "matrix score cache"),
    ]:
        _require(path, label)

    REPORTS.mkdir(parents=True, exist_ok=True)

    print("L2 construct validation...")
    l2 = run_construct_validation(CORPUS, config=ConstructConfig(use_ner_cache=True))
    l2_path = REPORTS / "deterministic_validation_report_fy2025_v2.json"
    write_validation_report(l2, l2_path)
    for name, pair in l2.pairs.items():
        print(f"  {name}: rho={pair.spearman_rho:.4f} n={pair.n} {pair.status}")
    legacy = l2.diagnostics.get("boilerplate_phrase_vs_ls4gram", {})
    print(f"  phrase-only: rho={legacy.get('spearman_rho')}")

    print("L3 outcomes validation (cache mode)...")
    l3 = run_outcomes_validation(
        OUTCOMES,
        score_cache_path=SCORE_CACHE,
        score_mode="cache",
        config=OutcomesValidationConfig(scoring_model_version="deterministic_scoring_v2"),
    )
    l3_path = REPORTS / "l3_outcomes_report_fy2025_v2.json"
    write_outcomes_report(l3, l3_path)
    vol = l3.gates["volatility_vs_overall"]
    print(f"  volatility_vs_overall: n={vol.n} Q5/Q1={vol.q5_q1_ratio} {vol.status}")
    earn = l3.gates["earnings_surprise_vs_change"]
    print(f"  earnings_surprise_vs_change: {earn.status}")

    summary = {
        "specificity_rho": l2.pairs["specificity_vs_ner"].spearman_rho,
        "boilerplate_combined_rho": l2.pairs["boilerplate_vs_ls4gram"].spearman_rho,
        "boilerplate_phrase_rho": legacy.get("spearman_rho"),
        "n_construct": l2.pairs["specificity_vs_ner"].n,
        "vol_n": vol.n,
        "vol_q5_q1": vol.q5_q1_ratio,
    }
    summary_path = REPORTS / "fy2025_validation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {l2_path.name}, {l3_path.name}, {summary_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
