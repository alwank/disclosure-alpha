"""L3 validation: join scores with outcomes and evaluate monotonicity gates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from disclosure_alpha.pipeline import compute_section_metrics, score_deterministic
from disclosure_alpha.section_extractor import ExtractedSection
from disclosure_alpha.validation.monotonicity import (
    MonotonicityGateResult,
    evaluate_quintile_monotonicity,
    overall_l3_pass,
)
from disclosure_alpha.version import (
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)


@dataclass
class OutcomesValidationConfig:
    min_n: int = 50
    min_per_quintile: int = 5
    min_l3_pass_count: int = 1  # ponytail: 2-of-4 when flag gates exist; 1-of-2 for vol+earnings only


@dataclass
class OutcomesValidationReport:
    validation_level: str
    generated_at: str
    versions: dict[str, str]
    inputs: dict[str, Any]
    gates: dict[str, MonotonicityGateResult]
    monotonicity_pass: bool
    overall_l3_pass: bool
    notes: list[str] = field(default_factory=list)
    outcome_gates_pass: bool | None = None

    def __post_init__(self) -> None:
        if self.outcome_gates_pass is None:
            self.outcome_gates_pass = self.monotonicity_pass

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_level": self.validation_level,
            "generated_at": self.generated_at,
            "versions": self.versions,
            "inputs": self.inputs,
            "gates": {k: v.to_dict() for k, v in self.gates.items()},
            "monotonicity_pass": self.monotonicity_pass,
            "outcome_gates_pass": self.outcome_gates_pass,
            "overall_l3_pass": self.overall_l3_pass,
            "notes": self.notes,
        }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_corpus_by_ticker(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(path):
        ticker = str(row.get("ticker", "")).upper()
        if ticker:
            out[ticker] = row
    return out


def score_item1a_from_corpus_row(row: dict[str, Any]) -> dict[str, float | None]:
    text = str(row.get("cleaned_text") or "")
    word_count = int(row.get("word_count") or len(text.split()))
    section = ExtractedSection(
        "item_1a_risk_factors",
        text,
        text,
        "corpus",
        word_count,
        max(1, word_count // 20),
        float(row.get("extraction_confidence") or 0.5),
        str(row.get("extraction_method") or "corpus"),
        PARSER_VERSION,
        warnings=[],
    )
    metrics = compute_section_metrics([section], prior_sections=None)
    scores = score_deterministic(metrics)
    return {
        "overall_disclosure_risk_score": scores.overall_disclosure_risk_score,
        "disclosure_change_score": scores.components.disclosure_change_score,
        "risk_factor_intensity_score": scores.components.risk_factor_intensity_score,
        "score_coverage_ratio": scores.score_coverage_ratio,
    }


def score_from_edgar(ticker: str, fiscal_year: int) -> dict[str, float | None]:
    from disclosure_alpha.pipeline import score_filing_ticker

    result = score_filing_ticker(
        ticker,
        fiscal_year,
        form_type="10-K",
        use_cache=True,
        compare_prior=True,
    )
    return {
        "overall_disclosure_risk_score": result.scores.overall_disclosure_risk_score,
        "disclosure_change_score": result.scores.components.disclosure_change_score,
        "risk_factor_intensity_score": result.scores.components.risk_factor_intensity_score,
        "score_coverage_ratio": result.scores.score_coverage_ratio,
    }


def run_outcomes_validation(
    outcomes_path: Path,
    *,
    corpus_path: Path | None = None,
    score_mode: str = "corpus",
    config: OutcomesValidationConfig | None = None,
    limit: int | None = None,
) -> OutcomesValidationReport:
    cfg = config or OutcomesValidationConfig()
    outcomes = load_jsonl(outcomes_path)
    if limit is not None:
        outcomes = outcomes[:limit]
    corpus = load_corpus_by_ticker(corpus_path) if corpus_path else {}

    notes: list[str] = []
    if score_mode == "corpus":
        notes.append(
            "corpus mode: Item 1A-only scores; disclosure_change_score null without prior filing"
        )
    elif score_mode == "edgar":
        notes.append("edgar mode: full 10-K + prior via score_filing_ticker (requires SEC cache)")

    joined: list[dict[str, Any]] = []
    total = len(outcomes)
    for i, out in enumerate(outcomes, start=1):
        ticker = str(out.get("ticker", "")).upper()
        fy = out.get("fiscal_year")
        fiscal_year = int(fy) if fy is not None else None

        score_fields: dict[str, float | None] = {
            "overall_disclosure_risk_score": None,
            "disclosure_change_score": None,
        }
        if score_mode == "edgar" and fiscal_year is not None:
            try:
                score_fields = score_from_edgar(ticker, fiscal_year)
            except Exception as exc:
                out = {**out, "score_error": str(exc)}
            if score_mode == "edgar" and i % 25 == 0:
                print(f"  score progress: {i}/{total}", flush=True)
        elif ticker in corpus:
            score_fields = score_item1a_from_corpus_row(corpus[ticker])

        joined.append({**out, **score_fields})
    if score_mode == "edgar" and total:
        print(f"  score progress: {total}/{total}", flush=True)

    vol_scores: list[float] = []
    vol_outcomes: list[float] = []
    change_scores: list[float] = []
    earn_outcomes: list[float] = []

    for row in joined:
        overall = row.get("overall_disclosure_risk_score")
        vol = row.get("realized_vol_90d")
        if overall is not None and vol is not None:
            vol_scores.append(float(overall))
            vol_outcomes.append(float(vol))

        change = row.get("disclosure_change_score")
        surprise = row.get("earnings_surprise_abs")
        if change is not None and surprise is not None:
            change_scores.append(float(change))
            earn_outcomes.append(float(surprise))

    gates: dict[str, MonotonicityGateResult] = {}

    gates["volatility_vs_overall"] = evaluate_quintile_monotonicity(
        vol_scores,
        vol_outcomes,
        name="volatility_vs_overall",
        score_field="overall_disclosure_risk_score",
        outcome_field="realized_vol_90d",
        min_n=cfg.min_n,
        min_per_quintile=cfg.min_per_quintile,
    )

    if change_scores:
        gates["earnings_surprise_vs_change"] = evaluate_quintile_monotonicity(
            change_scores,
            earn_outcomes,
            name="earnings_surprise_vs_change",
            score_field="disclosure_change_score",
            outcome_field="earnings_surprise_abs",
            min_n=cfg.min_n,
            min_per_quintile=cfg.min_per_quintile,
        )
    else:
        gates["earnings_surprise_vs_change"] = MonotonicityGateResult(
            name="earnings_surprise_vs_change",
            status="skipped",
            score_field="disclosure_change_score",
            outcome_field="earnings_surprise_abs",
            n=0,
            q1_mean=None,
            q5_mean=None,
            q5_q1_ratio=None,
            threshold_direction="Q5 > Q1",
            message="no disclosure_change_score (use --score-mode edgar for prior-year diffs)",
        )

    mono_pass = any(g.status == "pass" for g in gates.values())
    l3_pass = overall_l3_pass(
        list(gates.values()),
        min_pass=cfg.min_l3_pass_count,
    )

    return OutcomesValidationReport(
        validation_level="L3",
        generated_at=datetime.now(timezone.utc).isoformat(),
        versions={
            "parser_version": PARSER_VERSION,
            "metrics_engine_version": METRICS_ENGINE_VERSION,
            "scoring_model_version": SCORING_MODEL_VERSION,
        },
        inputs={
            "outcomes_path": str(outcomes_path),
            "corpus_path": str(corpus_path) if corpus_path else None,
            "score_mode": score_mode,
            "n_outcomes": len(outcomes),
            "n_vol_pairs": len(vol_scores),
            "n_change_pairs": len(change_scores),
        },
        gates=gates,
        monotonicity_pass=mono_pass,
        overall_l3_pass=l3_pass,
        notes=notes,
    )


def write_outcomes_report(report: OutcomesValidationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
