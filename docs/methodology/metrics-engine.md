# Metrics Engine

**What this page answers:** What raw text signals are computed per section, which artifact versions apply, and which component scores they feed.

| | |
|--|--|
| **Inputs** | Extracted section `cleaned_text` per section name |
| **Outputs** | Per-section ratios, flags, MD&A densities (`TextMetricResult`) |
| **Version** | `text_metrics_v4`, dictionary `built_in_dictionaries_v3` |

## In plain terms

The metrics engine counts tone words, boilerplate phrases, specificity proxies, and risk flags in each extracted section. Those per-section numbers feed the diff engine and aggregation — they are the raw signals behind component scores like `mdna_uncertainty_score` and `legal_regulatory_risk_score`.

## When you'll see this

- **CLI:** `disclosure-alpha metrics --html filing.html --form 10-K`
- **Python:** `compute_section_metrics()` in the pipeline module
- **HTTP:** `GET /v1/company/{ticker}/disclosure-metrics`
- **Components affected:** tone-driven scores (`risk_factor_intensity_score`, `mdna_uncertainty_score`, `boilerplate_risk_score`, …) and flag-boosted scores (`legal_regulatory_risk_score`, `liquidity_stress_score`)

Module: `text_metrics.py` (metrics engine) and the built-in dictionary package (`built_in_dictionaries_v3`).

<details>
<summary>Full specification</summary>

Computes per-section text metrics, boolean risk flags, and MD&A keyword densities. Output feeds the diff engine and aggregation stage.

## Input / output

```python
SectionTextInput(section_name: str, cleaned_text: str, fiscal_year: int | None = None) → TextMetricResult
```

All ratios are **per-word** unless noted. Scores on the 0–100 scale are capped with `min(100, ...)`.

## Tokenization

```python
tokenize_words(text)   # alphabetic tokens, lowercased
split_sentences(text)  # split on . ! ?
```

Word counts use alphabetic tokens. Sentence count uses non-empty sentence splits (minimum 1).

## Base metrics

### Counts

| Field | Formula |
|-------|---------|
| `word_count` | `len(tokens)` |
| `sentence_count` | `max(1, non-empty sentence splits)` |
| `average_sentence_length` | `word_count / sentence_count` |

### Tone ratios

| Field | Formula | Dictionary |
|-------|---------|------------|
| `negative_word_ratio` | `hits(NEGATIVE) / word_count` | `NEGATIVE_WORDS` |
| `uncertainty_word_ratio` | `hits(UNCERTAINTY) / word_count` | `UNCERTAINTY_WORDS` |
| `litigious_word_ratio` | `hits(LITIGIOUS) / word_count` | `LITIGIOUS_WORDS` |
| `constraining_word_ratio` | `hits(CONSTRAINING) / word_count` | `CONSTRAINING_WORDS` |
| `modal_word_ratio` | `hits(MODAL) / word_count` | `MODAL_WORDS` |

For aggregation, ratios are multiplied by 100 before blending into 0–100 component scores.

### Specificity

| Field | Formula |
|-------|---------|
| `numeric_specificity_score` | `min(100, numeric_tokens / word_count × 1000)` |
| `company_specificity_score` | `min(100, (capitals + numeric + geo + segment hits) / word_count × 100)` |

### Boilerplate

| Field | Formula |
|-------|---------|
| `boilerplate_phrase_ratio` | `min(1.0, phrase_hits / sentence_count)` |
| `boilerplate_cross_firm_ratio` | fraction of words in committed cross-firm 4-grams (`data/baselines/item_1a_risk_factors_boilerplate_4grams_fy{year}.json`) |
| `boilerplate_combined_ratio` | `0.4 × phrase + 0.6 × cross_firm` (default blend; see {doc}`boilerplate-v4-diagnostics`) |

Phrase hits use `BOILERPLATE_PHRASES` in `dictionaries.py`. Cross-firm grams follow Lang & Stice-Lawrence-style universe frequency (≥25% of docs in baseline build). `boilerplate_risk_score` uses **`boilerplate_combined_ratio`** in aggregation.

### Readability

| Field | Formula |
|-------|---------|
| `readability_score` | `min(100, avg_sentence_length × 2 + long_word_pct × 100)` |

## Boolean flags

`detect_section_flags(text, section_name)` returns all flags defined in `FLAG_PATTERNS`. Each flag is scoped to specific sections via `FLAG_SECTION_SCOPE` — out-of-scope sections always return `false`.

Representative flags used in aggregation (with +15 boost when true):

| Flag | Used in |
|------|---------|
| `material_weakness_flag`, `restatement_flag`, `ineffective_controls_flag` | `internal_controls_risk_score` |
| `investigation_flag`, `material_legal_proceeding_flag` | `legal_regulatory_risk_score` |
| `going_concern_flag`, `covenant_breach_flag` | `liquidity_stress_score` |
| `guidance_withdrawal_flag` | `mdna_uncertainty_score` |

Other flags (e.g. `cybersecurity_incident_flag`) are computed and exposed via the metrics/flags API but are not blended into the deterministic headline score today.

## MD&A density packs

`compute_density_metrics(text, section_name)` runs only on MD&A sections (`item_7_mdna`, `item_2_mdna`):

```text
density = min(100, term_hits / word_count × 1000)
```

| Key | Term pack |
|-----|-----------|
| `uncertainty_term_density` | `MDNA_DENSITY_TERMS.uncertainty_term_density` |
| `demand_softness_density` | demand decline phrases |
| `margin_pressure_density` | margin compression phrases |
| `liquidity_constraint_density` | liquidity / covenant phrases |

Non-MD&A sections return zero densities. Densities are merged into aggregation for `mdna_uncertainty_score` and `liquidity_stress_score` — see {doc}`aggregation`.

## Pipeline output

`compute_section_metrics()` in `pipeline.py` returns a `MetricsResult` with:

| Field | Contents |
|-------|----------|
| `section_metrics` | Per-section `TextMetricResult` fields as floats |
| `section_flags` | Per-section boolean flag dicts |
| `section_densities` | Per-section density dicts |
| `section_diffs` | Per-section change scores (from diff engine) |
| `language_deltas` | Per-section tone deltas vs prior |

Exposed via CLI `metrics` command, Python `compute_section_metrics()`, and `GET /v1/company/{ticker}/disclosure-metrics`.

## Edge cases

| Case | Behavior |
|------|----------|
| Empty section | Ratios 0; specificity 0; flags false; densities 0 |
| Section out of flag scope | Flag forced `false` |
| Non-MD&A section | All density keys 0 |

## Related

- {doc}`diff-engine`
- {doc}`aggregation`
- {doc}`research-foundation`
- {doc}`../reference/section-taxonomy`

</details>
