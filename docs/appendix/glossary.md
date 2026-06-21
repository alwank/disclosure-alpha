# Glossary

Terms used across CLI, HTTP, Python, and methodology docs.

## Scores

| Term | Meaning |
|------|---------|
| **Overall disclosure risk score** | Weighted headline score (0–100) from nine deterministic components. Higher = more disclosure risk / deterioration. See {doc}`../getting-started/understanding-scores` for the scale. |
| **Component score** | One of nine blended signals (e.g. `risk_factor_intensity_score`, `liquidity_stress_score`). See {doc}`../methodology/overview`. |

### Component scores

```{include} ../_includes/component-plain-english.md
```

## Scores (continued)

| Term | Meaning |
|------|---------|
| **Specificity quality score** | Higher = *better* specificity (inverse of most other components). |
| **Score coverage ratio** | Fraction of headline components that were computed (non-null). Lower when required sections are missing. |
| **Confidence score** | 0–1 blend of extraction quality, diff confidence, and coverage. |
| **Missing components** | Component names that could not be computed (usually missing sections or no prior filing). |
| **Provenance** | Per-component breakdown of inputs used in aggregation (`include=provenance` on HTTP matrix). |

## Pipeline

| Term | Meaning |
|------|---------|
| **Deterministic scoring** | Scores from word lists, diffs, flags, and densities only — no LLM. |
| **Composite scoring** | LLM-blended matrix — **not** available in the open-source HTTP API (returns HTTP 402). |
| **Prior filing** | Earlier comparable filing (same form type) used for section diffs. |
| **Language delta** | Change in a tone ratio vs the prior section (percentage points). |
| **Boilerplate** | Fixed-phrase repetition proxy in Item 1A (see {doc}`../methodology/research-foundation`). |

## Sections

| Term | Meaning |
|------|---------|
| **Section name** | Stable ID such as `item_1a_risk_factors`, `item_7_mdna`. See {doc}`../reference/section-taxonomy`. |
| **Required sections** | Sections needed for full coverage on a form (10-K: Item 1A + Item 7 MD&A). |

## Versions

| Artifact | Current value |
|----------|---------------|
| Parser | `section_extractor_v1` |
| Metrics engine | `text_metrics_v2` |
| Scoring model | `deterministic_scoring_v1` |
| Dictionary | `built_in_dictionaries_v2` |

See {doc}`changelog` for history.

## Related

- {doc}`../methodology/overview`
- {doc}`../validation/evidence-and-limitations`
