# 01 — Deterministic Scoring Overview

## What it is

Deterministic scoring converts extracted SEC filing sections into a **0–100 disclosure risk matrix** using only:

1. **Text metrics** — word-list ratios, specificity proxies, readability
2. **Section diffs** — change vs prior comparable filing
3. **Boolean flags** — phrase-pattern risk events (v1.1)
4. **Language deltas** — tone ratio shifts vs prior section (v1.1)

No LLM. Fully reproducible given the same `metrics_engine_version` and input text.

## What it is not

- Not a buy/sell signal or investment advice
- Not a substitute for reading the filing
- Not equivalent to the **composite** matrix (which blends LLM interpretation)
- Not validated to predict returns until calibration gates pass (see [07_validation_protocol.md](./07_validation_protocol.md))

## Pipeline placement

```
ingest → extract sections
           ↓
deterministic stage (MetricsService)
  • compute_text_metrics()
  • detect_section_flags()
  • compute_density_metrics()
  • compute_section_diff() vs prior filing
  • persist section_text_metrics, section_diff_results
           ↓
aggregate stage (partial — deterministic path)
  • aggregate_deterministic_matrix()
  • persist deterministic_scores_json, deterministic_overall_score
```

**Current gap (v1.1):** `--phase deterministic` does not persist the matrix. Scores materialize only when `aggregate` runs. **v2 target:** deterministic stage writes `deterministic_scores_json` without requiring LLM.

## Score scale

All components use 0–100:

| Range | Interpretation |
|------:|----------------|
| 0–25 | Low concern — language/change signals weak |
| 26–50 | Moderate |
| 51–75 | Elevated |
| 76–100 | High — strong negative tone, large change, or hard flags |

Higher = more disclosure risk / deterioration (except `specificity_quality_score`, where higher = better specificity).

## Component families (deterministic)

| Component | Primary sections | Signal type |
|-----------|------------------|-------------|
| `risk_factor_intensity_score` | Item 1A | Tone + change |
| `disclosure_change_score` | Item 1A, MD&A | Diff + language delta |
| `mdna_uncertainty_score` | Item 7 / Item 2 | Tone + readability + flag |
| `legal_regulatory_risk_score` | Item 1A (+ flags) | Litigious tone + flag |
| `liquidity_stress_score` | MD&A (+ flags) | Constraining tone + flag |
| `boilerplate_risk_score` | Item 1A | Boilerplate + low specificity |
| `internal_controls_risk_score` | Controls + Item 1A | Diff + tone + IC flags |
| `event_severity_score` | Item 1A | Diff only |
| `specificity_quality_score` | Item 1A | Numeric + entity proxy |
| `tone_negativity_score` | Item 1A + MD&A | Cross-section tone |

**Excluded from deterministic headline:** `cybersecurity_risk_score`, `business_model_fragility_score` (LLM-only today).

## Headline score

`deterministic_overall_score` = weighted mean of present components using `DETERMINISTIC_COMPONENT_WEIGHTS` (9 components, weights renormalized when some are missing).

```text
confidence = clamp(0.3, 0.95, 0.5 + coverage × 0.4)
coverage   = (# non-null weighted components) / 9
```

## Product tiers

| Tier | Surface | View |
|------|---------|------|
| Free | `GET /v1/company/{ticker}/disclosure-metrics` | Raw metrics, flags, diffs |
| Free | Matrix endpoint | `view=deterministic` — component scores, no LLM evidence |
| Pro | Matrix endpoint | `view=composite` or `view=full` |

**Marketing claim (deterministic):** "Measurable language and filing-change signals backed by peer-reviewed textual analysis methods."

**Do not claim:** "AI-identified hidden risks" on deterministic-only output.

## Required sections by form

| Form | Required for full coverage |
|------|---------------------------|
| 10-K | `item_1a_risk_factors`, `item_7_mdna` |
| 10-Q | `item_1a_risk_factors`, `item_2_mdna` |

Missing sections → lower `score_coverage_ratio`, component `null`s, reduced confidence.

## Prior filing rules

- Same `form_type`, earlier `filing_date`, same `section_name`
- Amendments: diff against `amends_filing_id` when set
- No prior → `disclosure_change_score = null` for that section (not zero)

## Versioning

Bump `metrics_engine_version` when:

- Dictionary lists change materially
- Metric formulas change
- Diff weights change

Bump `deterministic_scoring_v2` (new `scoring_model_version`) when:

- Component blend weights change
- New components added to deterministic set
- Flag boost logic changes

Store both on `score_runs` for point-in-time reproducibility.
