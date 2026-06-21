#!/usr/bin/env python3
"""Compare dictionary-driven metrics and scores against a frozen baseline corpus snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

from disclosure_alpha.deterministic_scoring import aggregate_deterministic_matrix
from disclosure_alpha.text_metrics import (
    SectionTextInput,
    compute_text_metrics,
    detect_section_flags,
)
from disclosure_alpha.validation.corpus import CorpusLoadConfig, load_corpus
from disclosure_alpha.version import DICTIONARY_VERSION, METRICS_ENGINE_VERSION

DEFAULT_CORPUS = Path("data/validation/corpus/sp500_item1a.jsonl")
DEFAULT_BASELINE = Path("data/validation/baselines/dictionary_shift_baseline.json")

METRIC_FIELDS = (
    "negative_word_ratio",
    "uncertainty_word_ratio",
    "litigious_word_ratio",
    "constraining_word_ratio",
    "modal_word_ratio",
    "boilerplate_phrase_ratio",
    "company_specificity_score",
    "numeric_specificity_score",
)

SCORE_FIELDS = (
    "risk_factor_intensity_score",
    "legal_regulatory_risk_score",
    "boilerplate_risk_score",
    "tone_negativity_score",
    "specificity_quality_score",
)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    return float(np.percentile(values, pct))


def compute_corpus_snapshot(corpus_path: Path) -> dict:
    rows, _meta = load_corpus(
        corpus_path,
        config=CorpusLoadConfig(min_word_count=200, min_confidence=0.75),
    )
    per_ticker: dict[str, dict] = {}
    for row in rows:
        metrics = compute_text_metrics(
            SectionTextInput(row.section_name, row.cleaned_text)
        )
        flags = detect_section_flags(row.cleaned_text, row.section_name)
        section_metrics = {row.section_name: asdict(metrics)}
        agg = aggregate_deterministic_matrix(
            section_metrics=section_metrics,
            section_diffs={row.section_name: None},
            section_flags={row.section_name: flags},
            language_deltas={},
            section_densities={},
        )
        scores = {p.score_name: p.value for p in agg.provenance if p.value is not None}
        per_ticker[row.ticker] = {
            "metrics": {k: getattr(metrics, k) for k in METRIC_FIELDS},
            "scores": {k: scores.get(k) for k in SCORE_FIELDS if k in scores},
            "flags": {k: v for k, v in flags.items() if v},
        }

    summary: dict[str, dict] = {"metrics": {}, "scores": {}}
    for field in METRIC_FIELDS:
        vals = [t["metrics"][field] for t in per_ticker.values()]
        summary["metrics"][field] = {
            "mean": float(np.mean(vals)),
            "p95": _percentile(vals, 95),
        }
    for field in SCORE_FIELDS:
        vals = [t["scores"][field] for t in per_ticker.values() if t["scores"].get(field) is not None]
        if vals:
            summary["scores"][field] = {
                "mean": float(np.mean(vals)),
                "p95": _percentile(vals, 95),
            }
    return {
        "dictionary_version": DICTIONARY_VERSION,
        "metrics_engine_version": METRICS_ENGINE_VERSION,
        "corpus_path": str(corpus_path),
        "n": len(per_ticker),
        "summary": summary,
        "per_ticker": per_ticker,
    }


def compare_snapshots(current: dict, baseline: dict, *, score_delta_threshold: float, max_frac: float) -> dict:
    base_tickers = baseline["per_ticker"]
    cur_tickers = current["per_ticker"]
    shared = sorted(set(base_tickers) & set(cur_tickers))
    metric_deltas: dict[str, list[float]] = {f: [] for f in METRIC_FIELDS}
    score_deltas: dict[str, list[float]] = {f: [] for f in SCORE_FIELDS}
    large_score_shifts: list[dict] = []

    for ticker in shared:
        b = base_tickers[ticker]
        c = cur_tickers[ticker]
        for field in METRIC_FIELDS:
            metric_deltas[field].append(abs(c["metrics"][field] - b["metrics"][field]))
        for field in SCORE_FIELDS:
            bv = b["scores"].get(field)
            cv = c["scores"].get(field)
            if bv is None or cv is None:
                continue
            delta = abs(cv - bv)
            score_deltas[field].append(delta)
            if delta > score_delta_threshold:
                large_score_shifts.append(
                    {"ticker": ticker, "score": field, "baseline": bv, "current": cv, "delta": delta}
                )

    n = len(shared)
    frac_large = len(large_score_shifts) / n if n else 0.0
    report = {
        "n_compared": n,
        "metric_mean_abs_delta": {
            f: float(np.mean(metric_deltas[f])) if metric_deltas[f] else 0.0 for f in METRIC_FIELDS
        },
        "score_mean_abs_delta": {
            f: float(np.mean(score_deltas[f])) if score_deltas[f] else 0.0 for f in SCORE_FIELDS
        },
        "large_score_shifts": large_score_shifts[:50],
        "large_score_shift_count": len(large_score_shifts),
        "large_score_shift_frac": round(frac_large, 4),
        "gate_pass": frac_large <= max_frac,
        "gate_threshold_frac": max_frac,
        "gate_threshold_points": score_delta_threshold,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Dictionary distribution shift validation")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--write-baseline", action="store_true", help="Write current snapshot as baseline")
    parser.add_argument("--out", type=Path, default=Path("data/validation/reports/dictionary_shift_report.json"))
    parser.add_argument("--score-delta-threshold", type=float, default=5.0)
    parser.add_argument("--max-frac", type=float, default=0.05)
    parser.add_argument("--allow-fail", action="store_true", help="Exit 0 even if gate fails")
    args = parser.parse_args()

    if not args.corpus.exists():
        print(f"skip: corpus not found: {args.corpus}", file=sys.stderr)
        sys.exit(0)

    current = compute_corpus_snapshot(args.corpus)
    if args.write_baseline:
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"Wrote baseline {args.baseline} (n={current['n']})")
        sys.exit(0)

    if not args.baseline.exists():
        print(f"baseline not found: {args.baseline} (run with --write-baseline first)", file=sys.stderr)
        sys.exit(1)

    baseline = json.loads(args.baseline.read_text())
    comparison = compare_snapshots(
        current,
        baseline,
        score_delta_threshold=args.score_delta_threshold,
        max_frac=args.max_frac,
    )
    report = {
        "current": {
            "dictionary_version": current["dictionary_version"],
            "metrics_engine_version": current["metrics_engine_version"],
            "n": current["n"],
        },
        "baseline": {
            "dictionary_version": baseline.get("dictionary_version"),
            "metrics_engine_version": baseline.get("metrics_engine_version"),
            "n": baseline.get("n"),
        },
        "comparison": comparison,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {args.out}")
    print(f"large_score_shift_frac={comparison['large_score_shift_frac']} gate_pass={comparison['gate_pass']}")
    if not comparison["gate_pass"] and not args.allow_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
