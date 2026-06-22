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

`overall_l2_pass` is false because EDGAR gates failed, not because construct pairs failed. Full multi-section matrix validation at SP500 scale is **not** complete — see scope note below.

## v2 smoke validation (opt-in, not production-grade)

An experimental **`deterministic_scoring_v2`** (`score_deterministic_v2`) has a **committed smoke pass** on local CI fixtures only. This is **not** the same evidence level as the v1 SP500 cohort above.

| Check | Fixture | Result | Source |
|-------|---------|--------|--------|
| L2 construct pairs | 3-firm mini corpus | **fail** (n=3; below thresholds) | `data/validation/reports/deterministic_validation_report_v2.json` |
| Matrix component gates | 2-filing mini corpus | **pass** (relaxed CI thresholds) | `data/validation/reports/matrix_validation_report_v2.json` |

**v2 artifact versions:** same parser/metrics/dictionary as v1; `scoring_model_version` = `deterministic_scoring_v2`.

Reproduce locally (no network):

```bash
python3 scripts/validate_deterministic_construct.py \
  --corpus tests/fixtures/validation/mini_corpus.jsonl \
  --scoring-version v2 --min-n 3 --boilerplate-min-docs 2

python3 scripts/validate_matrix_gates.py \
  --corpus tests/fixtures/validation/matrix_mini_corpus.jsonl \
  --scoring-version v2 \
  --min-extraction-rate 0.3 --min-median-confidence 0.5 --min-component-coverage 0.2
```

**Do not** cite v2 numeric levels or claim SP500-scale construct/outcome validity until v2 is re-run on the full validation corpus. v2 is **not** wired to HTTP/MCP defaults.

## Limitations

```{admonition} Not supported
:class: warning

- Buy/sell signals or return prediction
- Earnings-surprise outcome validation (FY2024 gate did not pass)
- Full S&P 500 validation coverage (corpus fetch rate ~84%, not 100%)
- Full multi-section matrix validation at SP500 scale (Item 1A construct + limited volatility association only)
- v2 SP500-scale construct or outcome validation (smoke fixtures only)
```

**Scope note:** validation runs used **Item 1A text** for corpus scoring, not the full multi-section matrix. Missing filing sections reduce score coverage and confidence.

**Disclaimer:** Output is for research and integration testing. Read the underlying SEC filings before making decisions.

## Score versioning

Artifact version strings and pinning guidance: {doc}`../reference/versioning` (includes v1 → v2 migration notes).

Corpus layout and reproduction scripts: `data/validation/README.md` in the repository.

Stale committed reports are detected offline via:

```bash
python3 scripts/validate_deterministic_construct.py --check-versions
```

v1 reports are checked against `deterministic_scoring_v1`; committed v2 smoke reports are checked against `deterministic_scoring_v2`.
