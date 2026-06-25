# Evidence and Validation

**Audience:** Readers evaluating whether to trust Disclosure Alpha scores.
**Before you start:** Skim {doc}`scope-and-claims` for product scope and unsupported claims.

## Summary

Deterministic scoring (**`deterministic_scoring_v2`**) was checked on S&P 500 FY2025 **Item 1A** risk-factor text. The table below is the public evidence record — construct checks against independent references, plus one descriptive post-filing volatility association.

**Last updated:** 2026-06-23.

| Check | Result |
|-------|--------|
| **Analysis cohort** | **478** firms (FY2025 Item 1A, S&P 500 universe n=503) |
| **Specificity construct validity** | Spearman **ρ ≈ 0.87** vs NER entity density (n=478) |
| **Boilerplate construct validity** | Spearman **ρ ≈ 0.74** vs cross-firm 4-gram boilerplate proxy (n=478) |
| **Post-filing volatility association** | Q5/Q1 **≈ 1.15** on 90-day realized vol (n=435) |

Construct rows show our metrics track external references. The volatility row is a **descriptive association only** — not return prediction, alpha, or investment advice.

## Cohort

| Field | Value |
|-------|------:|
| Universe | S&P 500 (`data/universe/sp500.csv`, **503** names) |
| Fiscal year | **2025** |
| Section | **Item 1A** risk factors (`item_1a_risk_factors`) |
| Rows after quality filters | **478** |
| Rows skipped (short text) | 19 |
| Scoring model | `deterministic_scoring_v2` |
| Parser / metrics / dictionary | `section_extractor_v1`, `text_metrics_v3`, `built_in_dictionaries_v3` |

The analysis cohort is post-filter extractions with sufficient word count and extraction confidence. It does **not** imply 100% index coverage — some tickers are missing from the corpus or fail extraction.

The volatility association uses **435** tickers with valid 90-day realized-vol outcomes — a separate pairing cohort from the 478-firm construct sample.

## Validation scopes

Headline numbers on this page come from **different validation runs** with different cohorts. Do not assume one sample size applies to every row.

| Claim on this page | Cohort | Score source |
|--------------------|--------|--------------|
| Specificity / boilerplate (n=478) | Item 1A extract quality filters | Per-section metrics on `item_1a_risk_factors` |
| Vol Q5/Q1 (n=435) | Outcome pairing subset | `overall_disclosure_risk_score` v2 |
| L3 outcome gates (n=497) | Full-matrix cache run | Committed L3 report (see below) |

The committed L3 outcomes report (`data/validation/reports/l3_outcomes_report_fy2025_v2.json`) uses **full-matrix cache mode** (`score_mode: cache`) over **497** tickers with valid outcomes. Its volatility quintile ratio (**≈ 1.12**, Q5/Q1) is a different scope from the Item 1A construct table and the n=435 vol row above.

## Specificity construct validity

| | |
|--|--|
| **Our metric** | `company_specificity_per_word` (from `company_specificity_score` / word count) |
| **Reference** | spaCy NER entity density (`ner_entity_density`) — independent of our dictionaries |
| **Association** | Spearman **ρ ≈ 0.87** |
| **n** | 478 |

**Interpretation:** Filings that score higher on company-specific language also tend to have higher named-entity density in risk-factor text. This is the strongest construct check in the current release.

## Boilerplate construct validity

| | |
|--|--|
| **Our metric** | `boilerplate_phrase_ratio` (section-level phrase hit rate) |
| **Reference** | Lang & Stice-Lawrence-style cross-firm 4-gram boilerplate proxy (`ls_boilerplate_word_ratio`) |
| **Association** | Spearman **ρ ≈ 0.74** |
| **n** | 478 |

**Interpretation:** Our boilerplate measure moves with a literature boilerplate proxy. It is **not** a full replication of the LS4-gram paper measure — see {doc}`../methodology/research-foundation` for how the built-in metric differs.

## Post-filing volatility association

| | |
|--|--|
| **Score** | `overall_disclosure_risk_score` (v2) |
| **Outcome** | `realized_vol_90d` (90-day realized volatility post-filing) |
| **Quintile ratio** | Q5 mean / Q1 mean **≈ 1.15** |
| **n** | 435 |
| **Direction** | Highest-risk quintile shows higher realized vol than lowest |

**Interpretation:** Firms in the highest overall-risk quintile had roughly **15%** higher average 90-day realized volatility than the lowest quintile in this sample. The effect is modest. Do **not** treat this as a tradeable signal or validated alpha.

```{admonition} Not claimed
:class: warning

We do **not** claim earnings-surprise prediction (change-score vs surprise did not show the expected monotonic pattern in v2 cache-mode runs). See {doc}`scope-and-claims`.
```

## What this does not prove

- Buy/sell signals or expected returns
- Full S&P 500 coverage on every ticker and fiscal year
- That headline risk scores are "correct" in an absolute sense — only that components relate to chosen external references and one vol outcome in-sample
- Comparable numeric levels between `deterministic_scoring_v1` and v2 (different scales — see {doc}`../reference/versioning`)

## Reproducing checks (contributors)

The public `main` branch does not ship validation scripts or report JSON. Maintainers refresh evidence on the git branch **`internal`** — see `INTERNAL_VALIDATION.md` in the repository. After a re-run, update the table on this page if headline numbers change.

## Related

- {doc}`scope-and-claims` — supported vs unsupported product claims
- {doc}`../methodology/research-foundation` — literature motivation for metrics
- {doc}`../reference/versioning` — artifact versions and v1 legacy opt-in
- {doc}`../legal` — not investment advice
