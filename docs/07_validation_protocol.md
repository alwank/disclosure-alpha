# 07 — Validation Protocol

Empirical validation for deterministic scoring before marketing as "research-backed" or "calibrated." Complements unit tests and [SCORING_AUDIT.md](../SCORING_AUDIT.md).

## Validation levels

| Level | Name | Requirement |
|-------|------|-------------|
| L0 | Structural | Unit tests pass; deterministic replay identical |
| L1 | Face validity | Manual review of 50 high/low scores |
| L2 | Construct validity | Correlations with literature proxies |
| L3 | Predictive monotonicity | Quintile sorts on outcome variables |
| L4 | Production gates | Thresholds below met on SP100 |

**MVP launch (deterministic free tier):** L0 + L1 + partial L2  
**"Validated" marketing claim:** L0–L4

---

## L0 — Structural tests

Existing: `tests/test_deterministic_scoring.py`, `tests/test_diff_engine.py`, `tests/test_score_stages.py`.

Add:

| Test | Assertion |
|------|-----------|
| Replay determinism | Same metrics dict → identical `aggregate_deterministic_matrix` output |
| Missing diff null | No prior → `disclosure_change_score is None`, not 0 |
| Flag boost cap | Boosted component ≤ 100 |
| Coverage math | 7/9 components → coverage ≈ 0.778 |

```bash
pytest tests/test_deterministic_scoring.py tests/test_diff_engine.py -q
```

---

## L1 — Face validity sample

**Sample:** 50 filings stratified:

- 10 highest `deterministic_overall_score`
- 10 lowest
- 10 highest `disclosure_change_score`
- 10 with any hard flag true
- 10 random

**Reviewers** (2+) independently rate: "Does the score direction match a 5-minute read of Item 1A + MD&A?"

**Gate:** ≥ 80% agreement on direction (higher score = more concern).

**Artifact:** `data/validation/deterministic_face_validity_sheet.csv`

```csv
filing_id,ticker,accession,deterministic_overall,reviewer1_direction,reviewer2_direction,agree,notes
```

---

## L2 — Construct validity

Run on SP100 latest 10-K per company (n ≈ 100).

### 2a. Dictionary correlation (if LM licensed)

| Pair | Target Spearman ρ |
|------|-------------------|
| MVP `negative_word_ratio` vs LM negative % | ≥ 0.85 |
| MVP `uncertainty_word_ratio` vs LM uncertainty % | ≥ 0.80 |

### 2b. Specificity proxy

| Pair | Target |
|------|--------|
| `company_specificity_score` vs NER entity density | ρ ≥ 0.60 |

### 2c. Boilerplate

| Pair | Target |
|------|--------|
| `boilerplate_phrase_ratio` vs cross-firm 4-gram boilerplate (if computed) | ρ ≥ 0.50 |

### 2d. Internal consistency

| Check | Target |
|-------|--------|
| `boilerplate_risk_score` vs `100 - specificity_quality_score` | ρ ≥ 0.40 |
| `tone_negativity_score` vs `negative_word_ratio` (1A) | ρ ≥ 0.70 |

**Script (to implement):** `scripts/validate_deterministic_construct.py`  
**Output:** `data/validation/reports/deterministic_construct_report.json`

---

## L3 — Predictive monotonicity

Not alpha / return forecasting. Test whether higher scores associate with **bad outcomes** in the literature.

### Test 1 — Volatility (Loughran & McDonald 2011)

```text
Outcome: realized_vol_90d post filing_date
Sort: quintiles by deterministic_overall_score
Expect: Q5 vol > Q1 vol (t-test p < 0.10 on SP100)
```

### Test 2 — Disclosure change (Cohen et al. 2020)

```text
Outcome: |earnings_surprise_next_q|
Sort: quintiles by disclosure_change_score
Expect: Q5 > Q1
```

### Test 3 — Flags (precision)

```text
Outcome: known material_weakness filings (SOX 404 disclosures)
Metric: precision of material_weakness_flag ≥ 0.70
```

```text
Outcome: going-concern audit opinions (subset with labels)
Metric: recall ≥ 0.50 (flags are sparse; precision matters more)
```

### Test 4 — Specificity (Hope et al. 2016)

```text
Outcome: |CAR[-1,+1]| around 10-K filing
Sort: quintiles by specificity_quality_score
Expect: Q5 |CAR| > Q1 (more specific → stronger market reaction)
```

**Script (to implement):** `scripts/validate_deterministic_outcomes.py`  
**Data needs:** Price/volatility feed or exported CRSP substitute; `validation_labels` table.

---

## L4 — Production gates

| Gate | Metric | Threshold | Status |
|------|--------|-----------|--------|
| D1 | Structural test pass rate | 100% | — |
| D2 | Face validity agreement | ≥ 80% | — |
| D3 | LM correlation (negative) | ρ ≥ 0.85 | pending license |
| D4 | Volatility monotonicity | Q5/Q1 ratio > 1.1 | — |
| D5 | Change score → earnings surprise | Q5/Q1 > 1.05 | — |
| D6 | MW flag precision | ≥ 0.70 | — |
| D7 | Score replay across runs | 100% identical | — |
| D8 | Coverage on SP100 10-K | median coverage ≥ 0.85 | — |

Report in: `data/validation/reports/deterministic_validation_report.json`

```json
{
  "validated_at": "2026-06-18T...",
  "metrics_engine_version": "text_metrics_v1.1",
  "scoring_model_version": "deterministic_scoring_v3",
  "gates": {
    "D1": {"status": "pass", "value": 1.0},
    "D4": {"status": "pending", "value": null}
  },
  "overall_status": "partial"
}
```

---

## Operational workflow

```bash
# 1. Ensure deterministic backfill complete
python scripts/ingest_universe.py --phase deterministic --universe sp100 --resume

# 2. Aggregate deterministic only
python scripts/backfill_score_sources.py --deterministic-only --limit 500

# 3. Export matrices
python scripts/validate_scores.py --export-csv data/validation/sp100_deterministic.csv

# 4. Run construct + outcome validation (when scripts exist)
python scripts/validate_deterministic_construct.py
python scripts/validate_deterministic_outcomes.py

# 5. Face validity — manual CSV fill, then:
python scripts/run_scoring_audit.py  # extend for deterministic gates
```

---

## Label table extensions

Add to `validation_labels` (or CSV import):

| label_type | label_value | Use |
|------------|-------------|-----|
| `deterministic_direction` | `concern` / `benign` | Face validity |
| `material_weakness` | `true` / `false` | Flag precision |
| `going_concern` | `true` / `false` | Flag recall |
| `high_volatility_90d` | `true` / `false` | Outcome bucket |

---

## Regression on version upgrades

When bumping `metrics_engine_version` or scoring weights:

1. Re-run L0 (unit tests)
2. Re-run L2 correlations (should not drop > 0.05 ρ)
3. Re-run L3 monotonicity (direction must hold)
4. Document delta in validation report changelog

---

## What we report externally

**Allowed after L0 + L1:**

> "Deterministic scores are computed from reproducible text metrics and filing diffs."

**Allowed after L4 (partial, no return claims):**

> "Component scores show significant association with post-filing volatility and disclosure change patterns consistent with peer-reviewed textual analysis literature (Loughran & McDonald 2011; Cohen, Malloy & Nguyen 2020)."

**Not allowed:**

> "Scores predict stock returns" or "validated trading strategy"
