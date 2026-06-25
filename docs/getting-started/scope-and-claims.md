# What This Does and Does Not Claim

Canonical scope statement for public docs. Other pages link here instead of repeating full disclaimers.

## Supported product claims

Disclosure Alpha **does**:

- Parse **10-K and 10-Q** HTML and extract named sections (Item 1A, MD&A, controls, etc.); **8-K** via local HTML or MCP Builder only (see surface matrix below)
- Compute **deterministic** text metrics, boolean flags, and section diffs — **no LLM required**
- Produce reproducible **0–100 disclosure risk scores** with versioned artifact strings in every response
- Expose the same pipeline via **CLI, Python SDK, HTTP API, and MCP**

### Form-type support by surface

| Surface | 10-K / 10-Q | 8-K |
|---------|-------------|-----|
| CLI `--html` | Yes | Yes |
| CLI `--ticker` / EDGAR | Yes | No |
| HTTP ticker routes | Yes | No |
| MCP Analyst | Yes | No |
| MCP Builder | Yes | Yes (local HTML) |

Scores summarize **language and change signals** in filings. They are research and integration tools, not trading signals.

## What's proven

Headline result: on **478** S&P 500 FY2025 Item 1A sections (`deterministic_scoring_v2`), company-specificity correlates **ρ ≈ 0.87** with an independent NER-based measure (Spearman).

Full cohort counts, boilerplate construct validity (ρ ≈ 0.96), post-filing volatility association (Q5/Q1 ≈ 1.15), and limitations: {doc}`evidence`.

## Unsupported claims

Disclosure Alpha **does not**:

- Provide buy/sell signals or return prediction
- Replace reading the underlying SEC filing
- Guarantee full S&P 500 index coverage in any empirical cohort
- Claim earnings-surprise or other outcome prediction
- Offer investment signals — scores are not validated as alpha

## Language signal vs risk score vs investment signal

| Term | Meaning |
|------|---------|
| **Language signal** | Raw metrics (word ratios, flags, diffs) from filing text |
| **Risk score** | Weighted 0–100 components and headline `overall_disclosure_risk_score` |
| **Investment signal** | **Not provided** — scores are not validated as alpha |

## Deterministic and "no LLM required"

Given the same filing HTML and the same artifact versions (`parser_version`, `metrics_engine_version`, `scoring_model_version`, dictionary version), output is reproducible. No external model API is called in the scoring pipeline.

Version pinning: {doc}`../reference/versioning`.

## Related

- {doc}`evidence` — empirical validation table and cohort detail
- {doc}`../legal` — not investment advice, SEC EDGAR terms
- {doc}`understanding-scores` — how to read score JSON
- {doc}`../guides/production` — hosting the HTTP API safely
