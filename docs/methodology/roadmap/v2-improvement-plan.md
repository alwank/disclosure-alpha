# 06 — v2 Improvement Plan

> **Internal / historical — excluded from public RTD build.** Pre-1.1.0 API shapes (`--phase deterministic`, `view=deterministic`, LLM/matrix split paths) were **removed in 1.1.0** — see {doc}`../../appendix/changelog`.

Prioritized upgrades from literature review and production gaps. Each item has an effort estimate and dependency.

## Priority matrix

| P | Item | Impact | Effort | Blocks |
|---|------|--------|--------|--------|
| P0 | Persist matrix at end of deterministic phase | Product | S | — |
| P0 | Deterministic score provenance JSON | Audit | M | — |
| P1 | LM dictionary alignment (licensed) | Validation | L | Legal |
| P1 | Wire MD&A densities into aggregation | Signal | S | — |
| P1 | Validation protocol execution on SP100 | Credibility | M | Labels |
| P2 | Cross-firm boilerplate measure | Quality | L | Annual phrase table |
| P2 | NER-based specificity (Hope et al.) | Quality | M | spacy/stanford |
| P2 | Diff blend lexical + semantic | Robustness | S | — |
| P3 | Abnormal tone (Huang et al. 2014) | Calibration | L | Firm history |
| P3 | LDA topic overlay | Explainability | L | — |

S = days, M = 1–2 weeks, L = multi-week

---

## P0 — Ship deterministic as standalone product

### 1. Matrix without LLM

**Problem:** ~~`--phase deterministic`~~ *(removed in 1.1.0)* computed metrics but returned no matrix.

**Target:**

```python
# scoring_service.py — after deterministic stage
det = aggregate_deterministic_matrix(...)
persist_deterministic_matrix(run_id, det)  # no LLM required
```

**Acceptance:**

- `deterministic_scores_json` populated after deterministic-only run
- ~~`ingest_universe.py --phase deterministic`~~ *(removed in 1.1.0)* does not error expecting matrix from LLM path

### 2. Component provenance

**Problem:** Consumers cannot see why `liquidity_stress_score = 58`.

**Target:** `deterministic_provenance_json` on `score_outputs` / matrix with per-component input breakdown (see [aggregation spec](../aggregation.md)).

**Acceptance:** ~~API `view=deterministic`~~ *(removed in 1.1.0; deterministic scoring only)* includes provenance when `include_provenance=true`.

---

## P1 — Signal quality (no new dependencies)

### 3. Wire MD&A densities

**Problem:** `density_json` persisted but ignored in aggregation.

**Change in `deterministic_scoring.py`:**

```text
mdna_uncertainty = blend(
  existing inputs...,
  m_7.uncertainty_term_density,   weight 0.10
  m_7.demand_softness_density,    weight 0.05
  m_7.margin_pressure_density,    weight 0.05
  # renormalize other weights
)

liquidity_stress = blend(
  m_7.constraining_word_ratio × 100, weight 0.50
  m_7.liquidity_constraint_density,  weight 0.35
  # flags unchanged
)
```

Bump `metrics_engine_version` for density wiring or matching changes; use `v2.0` if adopting licensed LM-style dictionaries.

### 4. Diff engine lexical blend

**Change:**

```text
combined_sim = 0.6 × semantic_similarity + 0.4 × lexical_similarity
disclosure_change_score uses (1 - combined_sim) instead of (1 - semantic_sim)
```

### 5. Flag matching precision

**Change:** Word-boundary regex for single-token flags; multi-word phrases stay substring.

**Add tests:** `"investigation"` in `"reinvestigation"` → false.

### 6. `legal_language_delta` in legal score

```text
legal_regulatory = blend(
  litigious_ratio × 100,  weight 0.70
  max(0, legal_language_delta), weight 0.30
) + flag_boost
```

---

## P1 — Dictionary upgrade path

### 7. Loughran–McDonald alignment

**Steps:**

1. Obtain commercial license or confirm academic use scope
2. Add `app/core/dictionaries_lm.py` (or load from licensed data file)
3. Feature flag: `USE_LM_DICTIONARY=true` in settings
4. Run correlation study: MVP ratios vs LM ratios on SP100 (target ρ > 0.85 for negative/uncertainty)
5. Switch default when gates pass

**Do not** ship LM lists in repo without license.

### 8. Tokenization parity

Match LM appendix: hyphen handling, master dictionary filter, inflection policy (stem vs exact).

Document in `03_metrics_spec.md` changelog.

---

## P2 — Literature-aligned measures

### 9. Hope et al. specificity

- Add optional `ner_specificity_score` column
- Blend into `specificity_quality_score`: 0.5 × heuristic + 0.5 × NER when available
- Fallback to heuristic-only when NER disabled

### 10. Lang & Stice-Lawrence boilerplate

- Annual job: compute firm-year 4-gram frequency table from universe
- `boilerplate_cross_firm_ratio` per section
- Replace or blend with phrase-list ratio (0.5 / 0.5)

### 11. Stickiness metric

```text
stickiness = shared_8grams_with_prior_year / total_8grams
```

High stickiness → **lower** `disclosure_change_score` adjustment (Dyer et al. 2017).

---

## P3 — Advanced calibration

### 12. Abnormal tone

```text
abnormal_negative_1a = negative_ratio - firm_median_negative_1a (prior 3 years)
```

Use in `tone_negativity_score` and `risk_factor_intensity_score` per Huang et al. (2014).

### 13. Outcome-calibrated weights

Grid search weights on SP100 to maximize monotonicity vs:

- 90-day realized volatility (MVP partial L3 pass on FY2025 corpus)
- Next-quarter earnings surprise absolute value (**deferred** — FY2024 EDGAR gate failed; rework post-MVP)

Constraints: weights sum to 1, each ≥ 0.03. Not return prediction (regulatory).

### 14. Percentile ranks

Store universe percentiles per component (`scripts/compute_percentiles.py`) for API `risk_band` calibration.

---

## Version bump checklist

When implementing v2:

- [ ] Update `metrics_engine_version` in `app/config.py`
- [ ] Add the next deterministic scoring version to `scoring_model_version`
- [ ] Alembic migration if new JSON columns (provenance)
- [ ] Backfill: ~~`ingest_universe.py --phase deterministic --resume`~~ *(removed in 1.1.0)*
- [ ] Re-aggregate without LLM
- [ ] Run validation harness (`data/validation/README.md`)
- [ ] Update API schema docs

---

## Out of scope for deterministic v2

- LLM section scoring
- Return forecasting or alpha claims
- FinBERT / transformer tone (separate research track)
- Non-10-K/10-Q forms beyond current MVP
