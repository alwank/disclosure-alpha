# 06 — v2 Improvement Plan

> **Internal / historical — excluded from public RTD build.** Pre-1.1.0 API shapes (LLM/matrix split paths, ingest phases) were **removed in 1.1.0** — see {doc}`../../appendix/changelog`.

> **Superseded (2026-06):** Most P0–P2 scoring and API items below shipped via [analytics-scoring-layer-improvement-plan](../../analytics-scoring-layer-improvement-plan.md) (`deterministic_scoring_v2`, MD&A density wiring, lexical+semantic diff blend, provenance on matrix/panel `include=provenance`). Treat this page as a literature backlog for P2–P3 research items not yet implemented.

Prioritized upgrades from literature review and production gaps. Each item has an effort estimate and dependency.

## Priority matrix

| P | Item | Impact | Effort | Status |
|---|------|--------|--------|--------|
| P0 | Persist matrix at end of deterministic phase | Product | S | **Done** (1.1.0 — deterministic-only product) |
| P0 | Deterministic score provenance JSON | Audit | M | **Done** (`include=provenance` on matrix/panel) |
| P1 | LM dictionary alignment (licensed) | Validation | L | Open |
| P1 | Wire MD&A densities into aggregation | Signal | S | **Done** (`text_metrics_v2`) |
| P1 | Validation protocol execution on SP100 | Credibility | M | Partial (see evidence page) |
| P2 | Cross-firm boilerplate measure | Quality | L | Open |
| P2 | NER-based specificity (Hope et al.) | Quality | M | Open |
| P2 | Diff blend lexical + semantic | Robustness | S | **Done** (`diff_engine`) |
| P3 | Abnormal tone (Huang et al. 2014) | Calibration | L | Open |
| P3 | LDA topic overlay | Explainability | L | Open |

S = days, M = 1–2 weeks, L = multi-week

---

## P0 — Ship deterministic as standalone product

### 1. Matrix without LLM — **done (1.1.0)**

**Historical problem:** Pre-1.1.0 ingest ran a separate deterministic phase that computed metrics but did not persist a matrix for consumers.

**Shipped:** Deterministic scoring is the only product path; matrix and panel endpoints return scores from the unified pipeline.

### 2. Component provenance — **done**

**Problem:** Consumers cannot see why `liquidity_stress_score = 58`.

**Shipped:** Per-component provenance on matrix and panel when `include=provenance` (or `tier=analyst` on single-ticker GET matrix). See [aggregation spec](../aggregation.md).

---

## P1 — Signal quality (no new dependencies)

### 3. Wire MD&A densities — **done**

MD&A density metrics feed `mdna_uncertainty_score` and `liquidity_stress_score` in `deterministic_scoring.py` (`text_metrics_v2`).

### 4. Diff engine lexical blend — **done**

`combined_sim = 0.6 × semantic_similarity + 0.4 × lexical_similarity`; `disclosure_change_score` uses `(1 - combined_sim)`.

### 5. Flag matching precision — **done**

Word-boundary matching for single-token flags; multi-word phrases stay substring. Tests cover `"investigation"` in `"reinvestigation"` → false.

### 6. `legal_language_delta` in legal score — **done**

`legal_regulatory_score` blends `litigious_word_ratio` (0.70) with `legal_language_delta` (0.30) plus flag boost.

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

When implementing remaining v2 items:

- [ ] Update `metrics_engine_version` in config
- [ ] Add the next deterministic scoring version to `scoring_model_version`
- [ ] Migration if new JSON columns (provenance extensions)
- [ ] Re-run validation harness (`data/validation/README.md`)
- [ ] Update API schema docs

---

## Out of scope for deterministic v2

- LLM section scoring
- Return forecasting or alpha claims
- FinBERT / transformer tone (separate research track)
- Non-10-K/10-Q forms beyond current MVP
