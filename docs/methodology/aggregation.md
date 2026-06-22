# Aggregation

**What this page answers:** How section-level signals become nine component scores and the headline `overall_disclosure_risk_score`.

| | |
|--|--|
| **Inputs** | Section metrics, diffs, flags, language deltas, MD&A densities |
| **Outputs** | `components`, `overall_disclosure_risk_score`, coverage, confidence |
| **Default version** | `deterministic_scoring_v1` (CLI, HTTP, MCP) |
| **Opt-in version** | `deterministic_scoring_v2` (`score_deterministic_v2` only) |

## In plain terms

Aggregation blends section-level metrics, diffs, flags, and language deltas into nine filing-level component scores (0–100), then computes the weighted headline `overall_disclosure_risk_score`, coverage, and confidence. This is the last stage before JSON reaches CLI, Python, or HTTP clients.

## When you'll see this

- **CLI / Python:** final `scores` block in `disclosure-alpha score` or `score_filing_html()` output
- **HTTP:** `GET /v1/company/{ticker}/disclosure-matrix` and panel POST responses
- **Fields you read:** `overall_disclosure_risk_score`, `components`, `score_coverage_ratio`, `missing_components`, `confidence_score`
- **Audit:** request `include=provenance` on the matrix route for per-component input breakdowns

Implemented in `deterministic_scoring.py`:

- **v1:** `aggregate_deterministic_matrix()` — default pipeline path
- **v2:** `aggregate_deterministic_matrix_v2()` — calls v1, then overrides selected components

<details>
<summary>v1 full specification (`deterministic_scoring_v1`)</summary>

Combines section metrics, diffs, flags, language deltas, and MD&A densities into filing-level component scores and an overall disclosure risk score. This is what CLI, HTTP, and MCP return today.

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

Weights (`COMPONENT_WEIGHTS` — nine headline components):

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

## Related (v1)

- {doc}`metrics-engine`
- {doc}`diff-engine`
- {doc}`overview`
- {doc}`../guides/http/index`

</details>

<details>
<summary>v2 specification (`deterministic_scoring_v2`, opt-in)</summary>

`aggregate_deterministic_matrix_v2()` starts from the v1 result, then replaces four components and recomputes the headline. Entry point: `score_deterministic_v2()` in `pipeline.py`. **Not exposed on HTTP or MCP.**

### Unchanged from v1

`disclosure_change_score`, `mdna_uncertainty_score`, `boilerplate_risk_score`, `event_severity_score`, `tone_negativity_score`, `specificity_quality_score`, `COMPONENT_WEIGHTS`, and conditional-null rules for those components.

### `risk_factor_intensity_score` (v2)

When Item 1A is present, tone inputs pass through `calibrate_metric()` (`calibration.py`) using built-in 10-K percentile tables. Calibrated values are percentile ranks (0–100), not `ratio × 100`. Diff weight unchanged (0.25).

```text
blend(calibrated_negative, calibrated_uncertainty, diff_1a; weights 0.375, 0.375, 0.25)
```

Provenance records `raw_value`, `calibrated_value`, `calibration_reference`, and `calibration_status` per tone metric.

### Evidence-based components (v2)

Legal, liquidity, and internal-controls scores use `ScoreEvidence` + `blend_evidence()` instead of v1's `blend_scores()` + `_flag_boost(+15)`.

- **Serious flags** (`investigation_flag`, `going_concern_flag`, `material_weakness_flag`, etc.) contribute evidence at **65.0** with weight **0.5** and a `reason` code (e.g. `serious_flag`, `liquidity_fallback`).
- Multiple evidence rows renormalize weights over non-null inputs (same pattern as `blend_scores`).

#### `legal_regulatory_risk_score` (v2)

```text
evidence: litigious×100 per section (item_1a_risk_factors weight 0.5; legal-proceedings sections 0.35)
        + legal_language_delta (weight 0.30)
        + legal flags as evidence (weight 0.5 each)
→ blend_evidence
```

Can be non-null from flags or legal-proceedings sections even when Item 1A tone metrics are missing.

#### `liquidity_stress_score` (v2)

```text
evidence: MD&A constraining×100 (0.50) + liquidity_constraint_density (0.35)
        + Item 1A constraining×100 fallback (0.25, reason liquidity_fallback)
        + liquidity flags as evidence (0.5 each)
→ blend_evidence
```

#### `internal_controls_risk_score` (v2)

```text
evidence: controls-section diff (0.6) + Item 1A constraining×100 (0.4)
        + serious IC flags as evidence (0.5 each)
→ blend_evidence
```

Controls diff resolves `item_9a_controls` or `item_4_controls` with section attribution in provenance.

### Confidence (v2 path)

`score_deterministic_v2()` sets confidence via `compute_confidence_detailed()`: mean of extraction confidence, coverage, and diff confidence, minus penalties for missing required sections, extraction warnings, no prior filing, and low coverage. v1 uses the same underlying penalty model through `compute_overall_confidence()` after P1-2.

### Provenance source tag

v2-overridden components set `source: "deterministic_v2"` in provenance entries.

### Score product split and event components (v2)

`aggregate_deterministic_matrix_v2()` also emits supplementary aggregates and event scores (not blended into the v1 headline weights):

- `static_disclosure_quality_score`, `static_disclosure_risk_score`, `disclosure_change_risk_score`
- `cybersecurity_incident_risk_score`, `event_materiality_score`

Section diffs may include `disclosure_change_score_v2` (sentence-aligned); v1 `disclosure_change_score` is unchanged. Baseline lookup: `baselines.lookup_baseline()` with form/sector/year fallback.

### Comparability

Do not compare numeric levels between v1 and v2 without re-scoring. Validation evidence ({doc}`../validation/evidence-and-limitations`) covers v1 only.

## Related (v2)

- {doc}`../reference/versioning` — migration and pinning
- {doc}`../reference/score-catalog` — component list and weights

</details>
