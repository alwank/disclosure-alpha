# 03 — Metrics Engine Specification

Module: `app/core/text_metrics.py`  
Storage: `section_text_metrics` (`flags_json`, `density_json` in v1)

## Input / output

```python
SectionTextInput(section_name: str, cleaned_text: str) → TextMetricResult
```

All ratios are **per-word** unless noted. Scores 0–100 are capped with `min(100, ...)`.

## Tokenization (current)

```python
re.findall(r"\b[a-zA-Z]+\b", text.lower())  # words
re.split(r"[.!?]+\s+", text)                  # sentences
```

### v2 tokenization (target)

Align with Loughran & McDonald (2011) internet appendix:

1. Strip HTML artifacts (already done in section extractor)
2. Lowercase; keep hyphenated tokens as single token when hyphen not followed by line break
3. Match against master dictionary / LM lists
4. Document token count method in `metrics_engine_version` changelog

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
| `negative_word_ratio` | `hits(NEGATIVE) / word_count` | `dictionaries.NEGATIVE_WORDS` |
| `uncertainty_word_ratio` | `hits(UNCERTAINTY) / word_count` | `UNCERTAINTY_WORDS` |
| `litigious_word_ratio` | `hits(LITIGIOUS) / word_count` | `LITIGIOUS_WORDS` |
| `constraining_word_ratio` | `hits(CONSTRAINING) / word_count` | `CONSTRAINING_WORDS` |
| `modal_word_ratio` | `hits(MODAL) / word_count` | `MODAL_WORDS` |

**Normalization for scoring:** multiply ratios by 100 before blending into 0–100 components.

**v2 dictionary expansion:**

| List | MVP size | v2 target |
|------|----------|-----------|
| Negative | ~20 terms | LM negative (~2,300) or licensed subset |
| Uncertainty | ~12 | LM uncertainty (~297) |
| Litigious | ~12 | LM litigious (~903) |
| Modal | ~11 | LM weak + strong modal |

### Specificity

| Field | Formula (current) |
|-------|-------------------|
| `numeric_specificity_score` | `min(100, numeric_tokens / word_count × 1000)` |
| `company_specificity_score` | `min(100, (capitals + numerics + geo_hits + segment_hits) / word_count × 100)` |

**v2 (Hope et al. 2016 aligned):**

```text
specificity_ner = (ner_entity_count + numeric_entity_count) / word_count × 1000
```

Use Stanford NER or `spacy` `en_core_web_sm` behind a feature flag. Keep heuristic as fallback when NER unavailable.

### Boilerplate

| Field | Formula (current) |
|-------|-------------------|
| `boilerplate_phrase_ratio` | `min(1.0, phrase_hits / sentence_count)` |

Phrases: `BOILERPLATE_PHRASES` in `dictionaries.py`.

**v2 (Lang & Stice-Lawrence 2015 aligned):**

```text
boilerplate_pct = words_in_shared_4grams / total_words
```

Where shared 4-grams appear in ≥ 75% of firms in the same fiscal year (precomputed annual phrase table).

### Readability

| Field | Formula (current) |
|-------|-------------------|
| `readability_score` | `min(100, avg_sentence_len × 2 + long_word_pct × 100)` |

**v2:** Emit `fog_index` as separate column; use `readability_score` only inside MD&A uncertainty blend until calibrated.

## Section flags (v1)

Function: `detect_section_flags(text, section_name) → dict[str, bool]`

13 flags via substring match on `FLAG_PATTERNS`, gated by `FLAG_SECTION_SCOPE`.

| Flag | Scoring consumer |
|------|------------------|
| `material_weakness_flag` | `internal_controls_risk_score` (+15) |
| `restatement_flag` | `internal_controls_risk_score` (+15) |
| `ineffective_controls_flag` | `internal_controls_risk_score` (+15) |
| `going_concern_flag` | `liquidity_stress_score` (+15) |
| `covenant_breach_flag` | `liquidity_stress_score` (+15) |
| `investigation_flag` | `legal_regulatory_risk_score` (+15) |
| `material_legal_proceeding_flag` | `legal_regulatory_risk_score` (+15) |
| `guidance_withdrawal_flag` | `mdna_uncertainty_score` (+15) |
| `cybersecurity_incident_flag` | Persisted for API; not in aggregation v1 |
| Others | Persisted for API; not in aggregation v1 |

**v2 flag rules:**

- Require word boundaries for single-word patterns (`\brestatement\b`) to reduce false positives
- Log matched phrase span in `flags_json` metadata for audit: `{"material_weakness_flag": {"hit": true, "span": "..."}}`
- Add `substantial_doubt_flag` as alias check for going concern

## MD&A density metrics (v1)

Function: `compute_density_metrics(text, section_name)`  
Sections: `item_7_mdna`, `item_2_mdna` only.

```text
density = min(100, term_hits / word_count × 1000)
```

| Key | Term pack |
|-----|-----------|
| `uncertainty_term_density` | `MDNA_DENSITY_TERMS.uncertainty_term_density` |
| `demand_softness_density` | demand decline phrases |
| `margin_pressure_density` | margin compression phrases |
| `liquidity_constraint_density` | liquidity / covenant phrases |

**v2 wiring (not in aggregation today):**

| Density | Target component | Weight |
|---------|------------------|--------|
| `uncertainty_term_density` | `mdna_uncertainty_score` | 0.15 |
| `demand_softness_density` | `mdna_uncertainty_score` | 0.10 |
| `margin_pressure_density` | `mdna_uncertainty_score` | 0.10 |
| `liquidity_constraint_density` | `liquidity_stress_score` | 0.20 |

## Persistence schema

`section_text_metrics` columns + JSON:

```json
{
  "flags_json": {"going_concern_flag": false, "...": false},
  "density_json": {"uncertainty_term_density": 12.4, "...": 0.0}
}
```

Tag rows with `metric_version = metrics_engine_version` on score runs.

## Edge cases

| Case | Behavior |
|------|----------|
| Empty section | All ratios 0; specificity 0; flags false; densities 0 |
| `word_count < 50` | Set `low_confidence_metric = true` in metadata (v2); still compute |
| Section out of flag scope | Flag forced `false` |
| Non-MD&A section | `density_json` all zeros |

## Unit test checklist

- [ ] Empty text → stable zeros
- [ ] Known phrase triggers correct flag
- [ ] Ratio monotonicity: more negative words → higher `negative_word_ratio`
- [ ] Specificity increases with injected numbers and entity names
- [ ] MD&A density zero on Item 1A
- [ ] Same input → identical output (determinism)
