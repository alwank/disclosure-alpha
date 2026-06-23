# Deterministic Scoring Overview

## What it is

Deterministic scoring converts extracted SEC filing sections into a **0–100 disclosure risk matrix** using only:

1. **Text metrics** — word-list ratios, specificity proxies, readability
2. **Section diffs** — change vs prior comparable filing
3. **Boolean flags** — phrase-pattern risk events
4. **Language deltas** — tone ratio shifts vs prior section

No LLM. Fully reproducible given the same version strings and input text.

## What it is not

- Not a buy/sell signal or investment advice
- Not a substitute for reading the filing
- Not full S&P 500 index coverage in empirical cohorts — see {doc}`../getting-started/scope-and-claims`

## Pipeline

```{include} ../_includes/pipeline-diagram.md
```

CLI, Python SDK, HTTP API, and MCP all call this same pipeline.

## How to read a score

Before diving into formulas, see {doc}`../getting-started/understanding-scores` for an annotated JSON walkthrough, component plain-English names, and the score scale.

## Artifact versions

Version strings appear in every score response. Canonical lookup: {doc}`../reference/versioning` and {doc}`../appendix/changelog` — not duplicated here.

## Score scale

```{include} ../_includes/score-scale.md
```

## Component scores

```{include} ../_includes/component-plain-english.md
```

**Headline score:** weighted mean of nine components listed in `COMPONENT_WEIGHTS`. `specificity_quality_score` is computed and returned in `components` but is not in the headline weights.

Blend formulas and weights: {doc}`aggregation`.

## Headline score and confidence

```text
overall = weighted mean of present headline components (weights renormalized)
coverage = (# non-null headline components) / 9
confidence = blend of extraction confidence, diff confidence, and coverage
```

Request provenance via HTTP `include=provenance` or inspect CLI JSON output.

## Prior filing rules

When prior HTML is supplied (CLI `--prior-html`, HTTP `compare=prior`, or EDGAR prior resolution):

- Match by **same section name** between current and prior extractions
- Prior filing is resolved as the same ticker, same form type, earlier filing date (see EDGAR resolver)
- No prior section → `disclosure_change_score = null` for that section (not zero)

Never compare 10-K sections to 10-Q for primary scores.

## Required sections by form

| Form | Required for full coverage |
|------|---------------------------|
| 10-K | `item_1a_risk_factors`, `item_7_mdna` |
| 10-Q | `item_1a_risk_factors`, `item_2_mdna` |

Missing sections → lower `score_coverage_ratio`, component `null`s, reduced confidence. Section names: {doc}`../reference/section-taxonomy`.

## HTTP API

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/company/{ticker}/disclosure-metrics` | Raw metrics, flags, diffs |
| `GET /v1/company/{ticker}/disclosure-matrix` | Component scores from deterministic scoring |

## Related

- {doc}`metrics-engine` — per-section metrics and flags
- {doc}`diff-engine` — section change scoring
- {doc}`aggregation` — component blends and provenance
- {doc}`research-foundation` — literature motivation
- {doc}`../getting-started/scope-and-claims`
