# Aggregation

## In plain terms

Aggregation blends section-level metrics, diffs, flags, and language deltas into nine filing-level component scores (0–100), then computes the weighted headline `overall_disclosure_risk_score`, coverage, and confidence. This is the last stage before JSON reaches CLI, Python, or HTTP clients.

## When you'll see this

- **CLI / Python:** final `scores` block in `disclosure-alpha score` or `score_filing_html()` output
- **HTTP:** `GET /v1/company/{ticker}/disclosure-matrix` and panel POST responses
- **Fields you read:** `overall_disclosure_risk_score`, `components`, `score_coverage_ratio`, `missing_components`, `confidence_score`
- **Audit:** request `include=provenance` on the matrix route for per-component input breakdowns

Module: `src/disclosure_alpha/deterministic_scoring.py`  
Function: `aggregate_deterministic_matrix()`

<details>
<summary>Full specification</summary>

Combines section metrics, diffs, flags, language deltas, and MD&A densities into filing-level component scores and an overall disclosure risk score.

## Inputs

```python
aggregate_deterministic_matrix(
    section_metrics: dict[str, dict[str, float]],
    section_diffs: dict[str, float | None],
    section_flags: dict[str, dict[str, bool]] | None = None,
    language_deltas: dict[str, dict[str, float]] | None = None,
    section_densities: dict[str, dict[str, float]] | None = None,
) → DeterministicAggregationResult
```

Section keys include `item_1a_risk_factors`, `item_7_mdna` / `item_2_mdna`, `item_9a_controls` / `item_4_controls`.

## Helper: `blend_scores`

Weighted average over **non-null** inputs; weights renormalized. Returns `None` if all inputs are null.

## Flag boost

`_flag_boost(flags, names)` adds **+15.0** when any named flag is true (merged across sections). Result capped at 100 after addition.

## Component blends

Tone ratios are scaled × 100 before blending. Diff scores are already 0–100.

### `risk_factor_intensity_score`

```text
blend(negative×100, uncertainty×100, diff_1a; weights 0.375, 0.375, 0.25)
```

### `disclosure_change_score`

```text
blend(diff_1a, diff_mdna; weights 0.6, 0.4)
+ 0.1 × avg(positive uncertainty_language_delta)  # when present
```

### `mdna_uncertainty_score`

```text
blend(
  uncertainty×100, modal×100, readability,
  uncertainty_term_density, demand_softness_density, margin_pressure_density;
  weights 0.40, 0.35, 0.25, 0.10, 0.05, 0.05
)
+ flag_boost(guidance_withdrawal_flag)
```

### `legal_regulatory_risk_score`

```text
blend(litigious×100, legal_language_delta; weights 0.70, 0.30)
+ flag_boost(investigation_flag, material_legal_proceeding_flag)
```

### `liquidity_stress_score`

```text
blend(constraining×100, liquidity_constraint_density; weights 0.50, 0.35)
+ flag_boost(going_concern_flag, covenant_breach_flag)
```

### `boilerplate_risk_score`

```text
blend(boilerplate×100, 100−numeric_specificity, 100−company_specificity; equal weights)
```

### `internal_controls_risk_score`

```text
blend(diff_controls, constraining×100; weights 0.6, 0.4)
+ flag_boost(material_weakness_flag, restatement_flag, ineffective_controls_flag)
```

### `event_severity_score`

```text
diff_1a  # single input
```

### `specificity_quality_score`

```text
blend(numeric_specificity, company_specificity; weights 0.5, 0.5)
```

Computed and returned in `components` but **not** in headline weights.

### `tone_negativity_score`

```text
blend(negative×100 from 1A, uncertainty×100 from MD&A; weights 0.5, 0.5)
```

## Headline score

Weights (`DETERMINISTIC_COMPONENT_WEIGHTS` — nine components, excludes `cybersecurity_risk_score`):

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

```text
overall = Σ (weight_i × component_i) / Σ (weight_i for present components)
clamp(overall, 0, 100)
```

## Coverage and confidence

```text
coverage = |{headline components with non-null values}| / 9
missing_components = [names where value is null]
```

Initial confidence from coverage: `clamp(0.3, 0.95, 0.5 + coverage × 0.4)`.

`score_deterministic()` in `pipeline.py` then refines confidence via `compute_overall_confidence()` using extraction confidences and average diff confidence.

## Derived aggregates

| Field | Source |
|-------|--------|
| `disclosure_deterioration_score` | `disclosure_change_score` |
| `disclosure_quality_score` | `100 − boilerplate_risk_score` (or null) |

## Provenance

Each component records a `DeterministicComponentProvenance` entry:

```json
{
  "score_name": "liquidity_stress_score",
  "value": 58.0,
  "inputs": {
    "constraining_word_ratio": 0.024,
    "liquidity_constraint_density": 12.4,
    "going_concern_flag": true,
    "flag_boost": 15.0
  },
  "source": "deterministic"
}
```

Available in CLI/ Python JSON (`scores.provenance`) and HTTP matrix responses when `include=provenance`.

## Output shape

`ScoreResult.to_dict()` (CLI / Python) returns:

```json
{
  "scores": {
    "overall_disclosure_risk_score": 38.5,
    "score_coverage_ratio": 0.8889,
    "confidence_score": 0.82,
    "missing_components": ["internal_controls_risk_score"],
    "components": { "...": 42.0 },
    "aggregates": { "...": null },
    "provenance": [ "..."]
  },
  "versions": {
    "parser_version": "section_extractor_v1",
    "metrics_engine_version": "text_metrics_v2",
    "scoring_model_version": "deterministic_scoring_v1"
  }
}
```

## Related

- {doc}`metrics-engine`
- {doc}`diff-engine`
- {doc}`overview`
- {doc}`../guides/http/index`

</details>
