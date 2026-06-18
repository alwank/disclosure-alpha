# 05 — Aggregation Specification

Module: `app/core/deterministic_scoring.py`  
Function: `aggregate_deterministic_matrix()`

## Inputs

```python
aggregate_deterministic_matrix(
    section_metrics: dict[str, dict[str, float]],
    section_diffs: dict[str, float | None],
    section_flags: dict[str, dict[str, bool]] | None = None,
    language_deltas: dict[str, dict[str, float]] | None = None,
) → MatrixAggregationResult
```

Section keys: `item_1a_risk_factors`, `item_7_mdna` / `item_2_mdna`, `item_9a_controls` / `item_4_controls`.

## Helper functions

### `blend_scores(*values, weights)`

Weighted average over **non-null** values only; weights renormalized. Returns `None` if all inputs null.

### `_flag_boost(flags, names)`

`+15.0` if any named flag is true (merged across sections). Capped at 100 after addition.

### `_language_delta_blend(language_deltas, sections)`

Mean of `max(0, uncertainty_language_delta)` across sections.

## Component formulas (v1.1)

Let `m_1a` = Item 1A metrics, `m_7` = MD&A metrics, `d_*` = section diff scores.

### 1. `risk_factor_intensity_score`

```text
blend(
  m_1a.negative_word_ratio × 100,    weight 0.375
  m_1a.uncertainty_word_ratio × 100, weight 0.375
  d_1a,                              weight 0.25
)
```

### 2. `disclosure_change_score`

```text
base = blend(d_1a, weight 0.6; d_mdna, weight 0.4)
unc_delta = mean(max(0, uncertainty_language_delta)) over [1A, MD&A]
if base and unc_delta:
  base = min(100, base + unc_delta × 0.1)
```

### 3. `mdna_uncertainty_score`

```text
base = blend(
  m_7.uncertainty_word_ratio × 100,  weight 0.40
  m_7.modal_word_ratio × 100,        weight 0.35
  m_7.readability_score,             weight 0.25
)
if guidance_withdrawal_flag: base = min(100, base + 15)
```

### 4. `legal_regulatory_risk_score`

```text
base = m_1a.litigious_word_ratio × 100
if investigation_flag or material_legal_proceeding_flag: base = min(100, base + 15)
```

### 5. `liquidity_stress_score`

```text
base = m_7.constraining_word_ratio × 100
if going_concern_flag or covenant_breach_flag: base = min(100, base + 15)
```

### 6. `boilerplate_risk_score`

```text
blend(
  m_1a.boilerplate_phrase_ratio × 100,
  100 - m_1a.numeric_specificity_score,
  100 - m_1a.company_specificity_score,
  weights [⅓, ⅓, ⅓]
)
```

Higher = more boilerplate / less specific = worse.

### 7. `internal_controls_risk_score`

```text
base = blend(
  d_controls (9A or 4),              weight 0.6
  m_1a.constraining_word_ratio × 100, weight 0.4
)
if material_weakness or restatement or ineffective_controls: base = min(100, base + 15)
```

### 8. `event_severity_score`

```text
d_1a  # diff only
```

### 9. `specificity_quality_score`

```text
blend(m_1a.numeric_specificity_score, m_1a.company_specificity_score, weights [0.5, 0.5])
```

Higher = better quality (inverse of boilerplate risk).

### 10. `tone_negativity_score`

```text
blend(
  m_1a.negative_word_ratio × 100,
  m_7.uncertainty_word_ratio × 100,
  weights [0.5, 0.5]
)
```

## Headline: `deterministic_overall_score`

Weights (`DETERMINISTIC_COMPONENT_WEIGHTS` — excludes `cybersecurity_risk_score`):

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

**Note:** `specificity_quality_score` and `event_severity_score` are computed but **not** in headline weights v1.1. Exposed in `components` JSON for transparency.

### v2 headline weight proposal

Add `specificity_quality_score` at 0.05; reduce `boilerplate_risk_score` to 0.05 (they overlap). Requires new `scoring_model_version`.

## Coverage and confidence

```text
coverage = |{components in DETERMINISTIC_COMPONENT_WEIGHTS with non-null values}| / 9
confidence = clamp(0.3, 0.95, 0.5 + coverage × 0.4)
missing_components = [names where value is null]
```

**v2 confidence:** incorporate mean extraction confidence and mean diff confidence (see `AggregationService` composite path).

## Derived aggregates

| Field | Source |
|-------|--------|
| `disclosure_deterioration_score` | `disclosure_change_score` |
| `disclosure_quality_score` | `100 - boilerplate_risk_score` (or null) |

## Output persistence

On aggregate stage:

```json
{
  "deterministic_scores_json": { "risk_factor_intensity_score": 42, ... },
  "deterministic_overall_score": 38.5,
  "score_coverage_ratio": 0.8889,
  "missing_components": ["internal_controls_risk_score"]
}
```

## Separation from composite

`aggregate_composite_matrix()` re-blends the same inputs with LLM section scores. **Deterministic values must remain immutable** in `deterministic_scores_json` when composite is computed — composite writes separate `component_scores_json` and `overall_disclosure_risk_score`.

## Score provenance (v2)

Each component should record:

```json
{
  "score_name": "liquidity_stress_score",
  "value": 58,
  "inputs": {
    "constraining_word_ratio": 0.024,
    "going_concern_flag": true,
    "flag_boost": 15
  },
  "source": "deterministic"
}
```

Enables API consumers and auditors to reproduce the score without re-running the pipeline.
