# Evidence & Limitations

Canonical validation source for public claims. Other docs link here for cohort counts and supported limits.

See also {doc}`../getting-started/scope-and-claims` for product scope in plain language.

## What is supported today (v1 — default)

Deterministic Item 1A analytics on **428 S&P 500 FY2025 10-Ks** (analysis cohort after quality filters; ~84% of index universe in manifest audits):

| Check | Result | Source |
|-------|--------|--------|
| Construct validity (boilerplate proxy) | Spearman ρ ≈ 0.69 vs literature measure (n=428) | `data/validation/reports/deterministic_validation_report.json` |
| Construct validity (specificity proxy) | Spearman ρ ≈ 0.84 vs NER-based specificity (n=428) | same |
| Post-filing volatility association | Q5/Q1 ≈ 1.11 on **435**-firm cohort (90-day window) | `data/validation/reports/l3_outcomes_report.json` |

**Last validated:** 2026-06-22. Package artifact versions in those reports: `section_extractor_v1`, `text_metrics_v2`, `deterministic_scoring_v1`, `built_in_dictionaries_v2`.

CLI, HTTP, MCP, and `score_deterministic()` all use **`deterministic_scoring_v1`** by default.

### Gate status — v1 (read separately)

| Gate family | Status | Notes |
|-------------|--------|-------|
| Construct pairs (`construct_pairs_pass`) | **pass** | Both Item 1A boilerplate and specificity proxies meet Spearman thresholds |
| EDGAR gates (`edgar_gates_pass`) | **fail** | E1/E2 fetch and analysis rates missing from manifest; not a construct contradiction |
| Outcome gates (`outcome_gates_pass`) | **pass** | Volatility monotonicity on overall score; earnings-surprise vs change skipped in corpus mode |

`overall_l2_pass` is false because EDGAR gates failed, not because construct pairs failed. v1 validation used Item 1A text only; see v2 matrix evidence for partial multi-section gates.

## v2 FY2025 evidence (opt-in; not the default)

**`deterministic_scoring_v2`** (`score_deterministic_v2`) was re-run on the same FY2025 S&P 500 Item 1A corpus as v1 (n=428 analysis rows) plus a **partial** EDGAR full-matrix cohort (330 filings; ingestion incomplete vs ~503 index names). v2 score **levels are not comparable** to v1 — see {doc}`../reference/versioning`.

| Check | Result | Source |
|-------|--------|--------|
| Construct validity (boilerplate proxy) | Spearman ρ ≈ 0.69 (n=428) | `data/validation/reports/deterministic_validation_report_v2.json` |
| Construct validity (specificity proxy) | Spearman ρ ≈ 0.84 (n=428) | same |
| Full-matrix component gates (production thresholds) | **pass** (median confidence 0.85; component coverage ≈ 0.99) | `data/validation/reports/matrix_validation_report_v2.json` |
| Post-filing volatility association (v2 overall) | Q5/Q1 ≈ 1.05 (n=435; corpus mode) | `data/validation/reports/l3_outcomes_report_v2.json` |

**Last validated:** 2026-06-23. Artifact versions: `section_extractor_v1`, `text_metrics_v2`, `deterministic_scoring_v2`, `built_in_dictionaries_v2`.

### Gate status — v2 (read separately)

| Gate family | Status | Notes |
|-------------|--------|-------|
| Construct pairs (`construct_pairs_pass`) | **pass** | Same Item 1A proxies as v1 at n=428 |
| EDGAR gates (`edgar_gates_pass`) | **fail** | E1 fetch rate 0.87 vs 0.90 threshold (same corpus as v1) |
| Matrix `overall_pass` | **pass** | n=330 matrix filings; not full index coverage |
| Outcome gates (`outcome_gates_pass`) | **pass** | Volatility monotonicity; earnings-surprise vs change skipped in corpus mode |

`overall_l2_pass` is false because EDGAR E1 failed, not because construct pairs failed.

Reproduce FY2025 v2 reports (local corpora under `data/validation/corpus/`, gitignored):

```bash
python3 scripts/validate_deterministic_construct.py \
  --corpus data/validation/corpus/sp500_item1a.jsonl \
  --universe data/universe/sp500.csv \
  --manifest data/validation/corpus/sp500_item1a.manifest.json \
  --scoring-version v2

python3 scripts/validate_matrix_gates.py \
  --corpus data/validation/corpus/sp500_matrix_fy2025.jsonl \
  --scoring-version v2

python3 scripts/validate_deterministic_outcomes.py --scoring-version v2
```

CI still runs **fixture smoke** thresholds via `tests/test_matrix_validation.py`; committed SP500 matrix results use **production** defaults in `validate_matrix_gates.py`.

**Opt-in v2 on HTTP/MCP:** pass `scoring_model_version=deterministic_scoring_v2` on matrix GET, panel POST body, or MCP scoring tools (`score_company_filing_tool`, `score_deterministic_tool_wrapper`, `score_filing_html_tool_wrapper`). Defaults remain v1.

## FY2024 robustness (secondary cohort)

**FY2025 remains the canonical primary evidence.** FY2024 is an out-of-sample robustness check on the same S&P 500 universe with FY2024 10-K Item 1A text. Corpus fetch is **partial** until EDGAR ingestion completes (~238/~503 tickers in the committed manifest snapshot; target ≥430 for parity with FY2025 analysis cohort).

| Check | FY2025 (canonical) | FY2024 (robustness) | Source |
|-------|-------------------|---------------------|--------|
| E1 fetch rate | 0.87 (fail vs 0.90) | 0.47 (fail; partial corpus) | `deterministic_validation_report.json` vs `deterministic_validation_report_fy2024.json` |
| Construct: specificity vs NER (ρ) | 0.84 (pass, n≈428) | 0.92 (pass, n=232) | same reports |
| Construct: boilerplate vs LS4gram (ρ) | 0.69 (pass) | −0.46 (fail; likely partial-cohort artifact) | same reports |
| L3 volatility Q5/Q1 (v2, corpus mode) | 1.05 (n=435) | 1.24 (n=230) | `l3_outcomes_report_v2.json` vs `l3_outcomes_report_fy2024_v2.json` |

**v2 FY2024 L2:** `deterministic_validation_report_fy2024_v2.json` (regenerated when corpus completes). **Matrix gates:** not run at FY2024 SP500 scale (no `sp500_matrix_fy2024.jsonl` yet).

Do **not** cite FY2024 construct levels as production claims until the FY2024 corpus meets E1/E2 thresholds. No earnings-surprise outcome claims for FY2024 v2 (corpus mode skips change-score gate).

## Limitations

```{admonition} Not supported
:class: warning

- Buy/sell signals or return prediction
- Earnings-surprise outcome validation (FY2024 gate did not pass)
- Full S&P 500 validation coverage (corpus fetch rate ~84%, not 100%)
- Full S&P 500 **matrix** corpus (330/~503 tickers in the FY2025 EDGAR matrix build at last run)
- Comparable v1 vs v2 headline levels on the same filing (different score scales)
```

**Scope note:** L2/L3 corpus mode scores **Item 1A text** only. Matrix gates use multi-section EDGAR HTML on the partial matrix cohort above; missing sections reduce coverage and confidence.

**Disclaimer:** Output is for research and integration testing. Read the underlying SEC filings before making decisions.

## Score versioning

Artifact version strings and pinning guidance: {doc}`../reference/versioning` (includes v1 → v2 migration notes).

Corpus layout and reproduction scripts: `data/validation/README.md` in the repository.

Stale committed reports are detected offline via:

```bash
python3 scripts/validate_deterministic_construct.py --check-versions
```

v1 reports are checked against `deterministic_scoring_v1`; committed v2 reports are checked against `deterministic_scoring_v2`.
