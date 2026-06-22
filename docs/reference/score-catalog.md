# Score Catalog

Canonical list of deterministic scores returned by CLI, Python, HTTP, and MCP.

## Headline score

| Field | Range | Meaning |
|-------|-------|---------|
| `overall_disclosure_risk_score` | 0–100 | Weighted mean of present headline components (higher = more concern) |
| `score_coverage_ratio` | 0–1 | Fraction of headline components computed (non-null) |
| `confidence_score` | 0–1 | Blend of extraction quality, diff confidence, and coverage |
| `missing_components` | list | Component names that could not be computed |

Weights are defined in `COMPONENT_WEIGHTS` (`disclosure_alpha.scoring_types`).

## Headline components (nine)

```{include} ../_includes/component-plain-english.md
```

| Component | Weight |
|-----------|-------:|
| `risk_factor_intensity_score` | 0.20 |
| `disclosure_change_score` | 0.15 |
| `mdna_uncertainty_score` | 0.15 |
| `legal_regulatory_risk_score` | 0.10 |
| `liquidity_stress_score` | 0.10 |
| `boilerplate_risk_score` | 0.10 |
| `internal_controls_risk_score` | 0.05 |
| `event_severity_score` | 0.05 |
| `tone_negativity_score` | 0.05 |

Blend formulas: {doc}`../methodology/aggregation`.

## Supplementary component

| Field | In headline? | Notes |
|-------|--------------|-------|
| `specificity_quality_score` | No | Higher = better specificity (inverse of most risk scores) |

## Aggregates

| Field | Meaning |
|-------|---------|
| `disclosure_quality_score` | `100 - boilerplate_risk_score` when boilerplate is present |
| `disclosure_deterioration_score` | Mirrors `disclosure_change_score` when computed |

## Conditional nulls

Components are **`null`** (never zero) when required inputs are missing:

- No Item 1A → Item 1A-derived components null
- No MD&A → MD&A-derived components null
- No prior filing → `disclosure_change_score`, `event_severity_score`, and related diffs null

Full-coverage example with prior: {doc}`../examples/index`.

## Related

- {doc}`../getting-started/understanding-scores`
- {doc}`../methodology/overview`
- {doc}`versioning`
