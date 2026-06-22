# What This Does and Does Not Claim

Canonical scope statement for public docs. Other pages link here instead of repeating full disclaimers.

## Supported product claims

Disclosure Alpha **does**:

- Parse **10-K, 10-Q, and 8-K** HTML and extract named sections (Item 1A, MD&A, controls, etc.)
- Compute **deterministic** text metrics, boolean flags, and section diffs — **no LLM required**
- Produce reproducible **0–100 disclosure risk scores** with versioned artifact strings in every response
- Expose the same pipeline via **CLI, Python SDK, HTTP API, and MCP**

Scores summarize **language and change signals** in filings. They are research and integration tools, not trading signals.

## Unsupported claims

Disclosure Alpha **does not**:

- Provide buy/sell signals or return prediction
- Replace reading the underlying SEC filing
- Guarantee full S&P 500 corpus coverage (see validation cohort below)
- Support earnings-surprise outcome validation in the current release

## Language signal vs risk score vs investment signal

| Term | Meaning |
|------|---------|
| **Language signal** | Raw metrics (word ratios, flags, diffs) from filing text |
| **Risk score** | Weighted 0–100 components and headline `overall_disclosure_risk_score` |
| **Investment signal** | **Not provided** — scores are not validated as alpha |

## Deterministic and "no LLM required"

Given the same filing HTML and the same artifact versions (`parser_version`, `metrics_engine_version`, `scoring_model_version`, dictionary version), output is reproducible. No external model API is called in the scoring pipeline.

## Validation cohort (canonical counts)

Source reports (paths relative to repository root):

| Metric | Value | Report |
|--------|------:|--------|
| Analysis cohort (S&P 500 FY2025 Item 1A) | **428** | `data/validation/reports/deterministic_validation_report.json` |
| Construct validity — boilerplate proxy | Spearman ρ ≈ **0.69** (n=428) | same |
| Construct validity — specificity proxy | Spearman ρ ≈ **0.84** (n=428) | same |
| Post-filing volatility association | Q5/Q1 ≈ **1.11** on **435**-firm cohort (90-day window) | `data/validation/reports/l3_outcomes_report.json` |

**Last validated:** 2026-06-21 (L2 construct gates). Corpus fetch does not cover 100% of the S&P 500 index (~84% of universe in manifest audits).

Full methodology and limitations: {doc}`../validation/evidence-and-limitations`. Version pinning: {doc}`../reference/versioning`.

## Related

- {doc}`../legal` — not investment advice, SEC EDGAR terms
- {doc}`understanding-scores` — how to read score JSON
- {doc}`../guides/production` — hosting the HTTP API safely
