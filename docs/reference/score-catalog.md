# Score Catalog

Canonical list of deterministic scores returned by CLI, Python, HTTP, and MCP.

```{admonition} Scoring version
:class: note

**This page describes `deterministic_scoring_v2`**, the default for CLI, HTTP, MCP, and `score_filing_html`. For legacy v1 differences, see {doc}`versioning` and the v1 section in {doc}`../methodology/aggregation`.
```

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

Blend formulas (v1): {doc}`../methodology/aggregation`.

### v2 overrides (opt-in only)

These four components use different blends when you call `score_deterministic_v2()`. Headline weights and component names are unchanged; only the formulas and provenance differ.

| Component | v1 summary | v2 summary |
|-----------|------------|------------|
| `risk_factor_intensity_score` | `negative×100`, `uncertainty×100`, diff | Calibrated percentile ranks for tone ratios + diff |
| `legal_regulatory_risk_score` | Item 1A litigious + legal delta + flag boost | Multi-section litigious evidence, legal delta, flag evidence (no +15 boost) |
| `liquidity_stress_score` | MD&A constraining + liquidity density + flag boost | MD&A evidence + Item 1A fallback + flag evidence |
| `internal_controls_risk_score` | Controls diff + Item 1A constraining + flag boost | Controls-section diff + constraining + serious IC flag evidence |

v2 can emit non-null scores from flags alone when required tone metrics are absent. v1 often leaves those components null without Item 1A or MD&A text.

### v2-only supplementary fields (opt-in)

Not in the v1 headline blend; populated by `score_deterministic_v2()` when evidence exists:

| Field | Meaning |
|-------|---------|
| `static_disclosure_quality_score` | Specificity / inverse boilerplate (current filing) |
| `static_disclosure_risk_score` | Tone, legal, liquidity, controls without YoY change |
| `disclosure_change_risk_score` | Change, event severity, language deltas |
| `cybersecurity_incident_risk_score` | Incident flags (Item 1.05 / cyber sections) |
| `event_materiality_score` | 8-K event materiality proxies |

`overall_disclosure_risk_score` weights are unchanged in v1 and v2.

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
