"""L2 construct validity: Spearman comparisons vs reference constructs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from disclosure_alpha.text_metrics import SectionTextInput, compute_text_metrics
from disclosure_alpha.validation.corpus import (
    CorpusLoadConfig,
    load_corpus,
    load_holdout_tickers,
    load_manifest,
    manifest_path_for,
)
from disclosure_alpha.validation.edgar_gates import EdgarGatesConfig, evaluate_edgar_gates
from disclosure_alpha.validation.references.boilerplate import compute_ls_boilerplate_ratios
from disclosure_alpha.validation.references.ner import compute_ner_densities
from disclosure_alpha.validation.universe import load_universe
from disclosure_alpha.validation.types import ConstructPairResult, CorpusRow, ValidationReport
from disclosure_alpha.validation.scoring_version import normalize_scoring_version
from disclosure_alpha.version import (
    DICTIONARY_VERSION,
    METRICS_ENGINE_VERSION,
    PARSER_VERSION,
    SCORING_MODEL_VERSION,
)


@dataclass
class ConstructConfig:
    min_n: int = 80
    boilerplate_min_docs: int = 10
    boilerplate_min_doc_frac: float = 0.25
    min_confidence: float = 0.75
    min_word_count: int = 200
    holdout_path: Path | None = None
    universe_path: Path | None = None
    manifest_path: Path | None = None
    edgar_gates: EdgarGatesConfig | None = None
    scoring_model_version: str = SCORING_MODEL_VERSION
    use_ner_cache: bool = True
    refresh_ner_cache: bool = False


def spearman_rho(x: list[float], y: list[float]) -> float | None:
    if len(x) < 2 or len(x) != len(y):
        return None
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    corr = np.corrcoef(rx, ry)[0, 1]
    if np.isnan(corr):
        return None
    return float(corr)


def _discordant_tickers(
    rows: list[CorpusRow],
    ours: list[float],
    refs: list[float],
    *,
    top_k: int = 20,
) -> list[str]:
    if len(rows) != len(ours):
        return []
    rx = np.argsort(np.argsort(ours))
    ry = np.argsort(np.argsort(refs))
    gaps = [(abs(int(a) - int(b)), row.ticker) for row, a, b in zip(rows, rx, ry)]
    gaps.sort(reverse=True)
    return [t for _, t in gaps[:top_k]]


def _compute_ours(rows: list[CorpusRow], *, progress_every: int = 25) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    total = len(rows)
    for i, row in enumerate(rows, start=1):
        m = compute_text_metrics(
            SectionTextInput(row.section_name, row.cleaned_text)
        )
        out[row.ticker] = {
            "company_specificity_per_word": m.company_specificity_score / 100.0,
            "boilerplate_phrase_ratio": m.boilerplate_phrase_ratio,
            "boilerplate_phrase_ratio_per_word": m.boilerplate_phrase_ratio / max(
                1, m.word_count
            ),
        }
        if progress_every and i % progress_every == 0:
            print(f"  metrics progress: {i}/{total}", flush=True)
    if total and progress_every and total % progress_every != 0:
        print(f"  metrics progress: {total}/{total}", flush=True)
    return out


def _pair_result(
    name: str,
    rows: list[CorpusRow],
    ours_map: dict[str, dict[str, float]],
    ref_map: dict[str, float] | None,
    *,
    ours_field: str,
    ref_field: str,
    threshold: float,
    skip_message: str = "",
) -> tuple[ConstructPairResult, list[str]]:
    if ref_map is None:
        return (
            ConstructPairResult(
                name=name,
                status="skipped",
                spearman_rho=None,
                threshold=threshold,
                n=0,
                ours_field=ours_field,
                ref_field=ref_field,
                message=skip_message,
            ),
            [],
        )

    paired_rows: list[CorpusRow] = []
    xs: list[float] = []
    ys: list[float] = []
    for row in rows:
        if row.ticker not in ref_map or row.ticker not in ours_map:
            continue
        paired_rows.append(row)
        xs.append(ours_map[row.ticker][ours_field])
        ys.append(ref_map[row.ticker])

    n = len(xs)
    if n < 2:
        return (
            ConstructPairResult(
                name=name,
                status="skipped",
                spearman_rho=None,
                threshold=threshold,
                n=n,
                ours_field=ours_field,
                ref_field=ref_field,
                message="insufficient paired rows",
            ),
            [],
        )

    rho = spearman_rho(xs, ys)
    status = "pass" if rho is not None and rho >= threshold else "fail"
    discordant = _discordant_tickers(paired_rows, xs, ys) if rho is not None else []
    return (
        ConstructPairResult(
            name=name,
            status=status,
            spearman_rho=rho,
            threshold=threshold,
            n=n,
            ours_field=ours_field,
            ref_field=ref_field,
        ),
        discordant,
    )


def run_construct_validation(
    corpus_path: Path,
    *,
    config: ConstructConfig | None = None,
) -> ValidationReport:
    cfg = config or ConstructConfig()
    scoring_model_version = normalize_scoring_version(cfg.scoring_model_version)
    holdout = load_holdout_tickers(cfg.holdout_path)
    load_cfg = CorpusLoadConfig(
        min_word_count=cfg.min_word_count,
        min_confidence=cfg.min_confidence,
        holdout_tickers=holdout,
    )
    rows, corpus_meta = load_corpus(corpus_path, config=load_cfg)
    print(
        f"Loaded corpus: {corpus_meta['n_input']} rows, "
        f"{corpus_meta['n_after_filters']} after filters",
        flush=True,
    )

    manifest_file = cfg.manifest_path or manifest_path_for(corpus_path)
    manifest = load_manifest(manifest_file)

    if cfg.universe_path and cfg.universe_path.exists():
        expected = {e.ticker for e in load_universe(cfg.universe_path)}
        present = {r.ticker for r in rows}
        corpus_meta["universe_path"] = str(cfg.universe_path)
        corpus_meta["universe_expected"] = len(expected)
        corpus_meta["universe_present"] = len(present & expected)
        corpus_meta["universe_missing"] = sorted(expected - present)[:50]
        if len(expected - present) > 50:
            corpus_meta["universe_missing_truncated"] = len(expected - present) - 50
        print(f"Universe coverage: {len(present & expected)}/{len(expected)}", flush=True)

    print(f"Computing text metrics for {len(rows)} firms...", flush=True)
    ours = _compute_ours(rows)
    diagnostics: dict[str, Any] = {"specificity_compare": "company_specificity_per_word vs ner_entity_density"}

    print("Running spaCy NER (slowest step)...", flush=True)
    ner_by_ticker, ner_msg = compute_ner_densities(
        rows,
        use_cache=cfg.use_ner_cache,
        refresh_cache=cfg.refresh_ner_cache,
    )
    if ner_msg:
        print(f"  NER skipped: {ner_msg}", flush=True)

    print("Computing cross-firm boilerplate reference...", flush=True)
    bp_min = min(cfg.boilerplate_min_docs, max(2, len(rows))) if rows else cfg.boilerplate_min_docs
    ls_bp = (
        compute_ls_boilerplate_ratios(
            rows,
            min_doc_freq=bp_min,
            min_doc_frac=cfg.boilerplate_min_doc_frac,
        )
        if len(rows) >= 2
        else None
    )

    pairs: dict[str, ConstructPairResult] = {}
    discordant: dict[str, list[str]] = {}

    pr, disc = _pair_result(
        "specificity_vs_ner",
        rows,
        ours,
        ner_by_ticker,
        ours_field="company_specificity_per_word",
        ref_field="ner_entity_density",
        threshold=0.60,
        skip_message=ner_msg,
    )
    pairs["specificity_vs_ner"] = pr
    discordant["specificity_vs_ner"] = disc

    bp_skip = ""
    if ls_bp is None:
        bp_skip = "cohort too small for cross-firm 4-gram reference"
    pr, disc = _pair_result(
        "boilerplate_vs_ls4gram",
        rows,
        ours,
        ls_bp,
        ours_field="boilerplate_phrase_ratio",
        ref_field="ls_boilerplate_word_ratio",
        threshold=0.50,
        skip_message=bp_skip,
    )
    pairs["boilerplate_vs_ls4gram"] = pr
    discordant["boilerplate_vs_ls4gram"] = disc

    if len(rows) < cfg.min_n:
        diagnostics["warning"] = f"n={len(rows)} below recommended min_n={cfg.min_n}"

    construct_pass = all(p.status == "pass" for p in pairs.values())

    gate_results, edgar_pass, gate_extras = evaluate_edgar_gates(
        corpus_meta,
        rows,
        config=cfg.edgar_gates,
        manifest=manifest,
    )
    if gate_extras:
        diagnostics["edgar"] = gate_extras
    if manifest:
        corpus_meta["manifest_path"] = str(manifest_file)

    edgar_gates_dict = {k: v.to_dict() for k, v in gate_results.items()}

    return ValidationReport(
        validation_level="L2",
        generated_at=datetime.now(timezone.utc).isoformat(),
        versions={
            "parser_version": PARSER_VERSION,
            "metrics_engine_version": METRICS_ENGINE_VERSION,
            "scoring_model_version": scoring_model_version,
            "dictionary_version": DICTIONARY_VERSION,
        },
        corpus=corpus_meta,
        pairs=pairs,
        edgar_gates=edgar_gates_dict,
        edgar_pass=edgar_pass,
        construct_pass=construct_pass,
        overall_l2_pass=edgar_pass and construct_pass,
        discordant_tickers=discordant,
        diagnostics=diagnostics,
    )


def write_validation_report(report: ValidationReport, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out_path
