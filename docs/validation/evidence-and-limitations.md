# Evidence & Limitations

Canonical validation source for public claims. Other docs link here for cohort counts and supported limits.

See also {doc}`../getting-started/scope-and-claims` for product scope in plain language.

## What is supported today

Deterministic Item 1A analytics on **428 S&P 500 FY2025 10-Ks** (analysis cohort after quality filters; ~84% of index universe in manifest audits):

| Check | Result | Source |
|-------|--------|--------|
| Construct validity (boilerplate proxy) | Spearman ρ ≈ 0.69 vs literature measure (n=428) | `data/validation/reports/deterministic_validation_report.json` |
| Construct validity (specificity proxy) | Spearman ρ ≈ 0.84 vs NER-based specificity (n=428) | same |
| Post-filing volatility association | Q5/Q1 ≈ 1.11 on **435**-firm cohort (90-day window) | `data/validation/reports/l3_outcomes_report.json` |

**Last validated:** 2026-06-22. Package artifact versions in those reports: `section_extractor_v1`, `text_metrics_v2`, `deterministic_scoring_v1`, `built_in_dictionaries_v2`.

Scores use the deterministic engine (`deterministic_scoring_v1`). An experimental **`deterministic_scoring_v2`** exists in Python (`score_deterministic_v2`) but has **no committed validation pass** — do not cite v2 levels with the same evidence claims as v1.

### Gate status (read separately)

| Gate family | Status | Notes |
|-------------|--------|-------|
| Construct pairs (`construct_pairs_pass`) | **pass** | Both Item 1A boilerplate and specificity proxies meet Spearman thresholds |
| EDGAR gates (`edgar_gates_pass`) | **fail** | E1/E2 fetch and analysis rates missing from manifest; not a construct contradiction |
| Outcome gates (`outcome_gates_pass`) | **pass** | Volatility monotonicity on overall score; earnings-surprise vs change skipped in corpus mode |

`overall_l2_pass` is false because EDGAR gates failed, not because construct pairs failed. Full multi-section matrix validation is **not** complete — see scope note below.

## Limitations

```{admonition} Not supported
:class: warning

- Buy/sell signals or return prediction
- Earnings-surprise outcome validation (FY2024 gate did not pass)
- Full S&P 500 validation coverage (corpus fetch rate ~84%, not 100%)
- Full multi-section matrix validation (Item 1A construct + limited volatility association only)
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

Reports are checked against **v1** runtime constants (`deterministic_scoring_v1`). Opt-in v2 is outside the committed validation gate until reports are regenerated with v2.
