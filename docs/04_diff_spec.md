# 04 — Diff Engine Specification

Module: `app/core/diff_engine.py`  
Storage: `section_diff_results` (`language_deltas_json` in v1)

## Purpose

Quantify **meaningful qualitative change** between current and prior comparable section. Core product differentiator; empirically supported by Cohen, Malloy & Nguyen (2020) *Lazy Prices*.

## Comparable section selection

Implemented in `MetricsService._get_prior_section()`:

| Case | Prior filing |
|------|--------------|
| Standard | Same company, same `form_type`, same `section_name`, earlier `filing_date`, non-amendment |
| Amendment | `amends_filing_id` target filing |
| First filing | No prior → null diff |

**Never** compare 10-K to 10-Q for primary scores.

## Outputs

```python
SectionDiffResult(
    lexical_similarity: float | None,      # 0–1
    semantic_similarity: float | None,     # 0–1
    length_change_pct: float | None,
    new_topics: list[str],
    removed_topics: list[str],
    intensified_topics: list[str],
    disclosure_change_score: float | None, # 0–100
    language_deltas: dict[str, float],
    confidence_score: float,
    diff_summary: str,
)
```

## Lexical similarity

```text
lexical_similarity = cosine_similarity(TfidfVectorizer(max_features=2000), current, prior)
```

Range [0, 1]. Lower = more lexical change.

**Literature:** Cohen et al. use cosine similarity among four measures; this aligns directly.

## Semantic similarity

Embedding cosine similarity via `embedding_service.semantic_similarity()`.

**v2:** Document embedding model name + version on diff rows for reproducibility.

## Length change

```text
length_change_pct = (current_words - prior_words) / prior_words
```

Used in change score as `max(0, min(1, length_change_pct))` — only **growth** contributes (Cohen-style emphasis on added content).

## Topic extraction (MVP)

Keyword clusters from `TOPIC_KEYWORDS`:

- `new_topics` = in current, not in prior
- `removed_topics` = in prior, not in current
- `intensified_topics` = in both, current intensity > 1.2 × prior

Intensity:

```text
hits(topic_keywords) + 0.5 × severity_word_hits
```

**v2:** Optional LDA topic overlap (Dyer et al. 2017) behind feature flag; keep keyword method as default for explainability.

## Disclosure change score (current)

```text
new_topic_score      = min(1, len(new_topics) / 3)
intensified_score    = min(1, len(intensified_topics) / 3)
length_component     = clamp(length_change_pct, 0, 1)

disclosure_change_score =
    40 × (1 - semantic_similarity)
  + 20 × length_component
  + 20 × new_topic_score
  + 20 × intensified_score

clamp to [0, 100]
```

### Interpretation bands

| Score | Meaning |
|------:|---------|
| 0–25 | Minor wording; high similarity |
| 26–50 | Moderate topic or tone shift |
| 51–75 | New or intensified risk topics |
| 76–100 | Major semantic shift or multiple new topics |

### v2 proposed adjustments

| Change | Rationale |
|--------|-----------|
| Blend lexical + semantic: `sim = 0.6×semantic + 0.4×lexical` | Cohen uses multiple measures; reduces embedding-only noise |
| Add `removed_topic_score` (10 pts) | Removed risks can also be informative |
| Weight litigation topic changes 1.5× | Cohen et al. — litigation language especially informative |
| Penalize stickiness: if `lexical > 0.95` and `semantic > 0.95` but flags fired, floor score at 25 | Avoid false "no change" when flags disagree |

## Language deltas (v1)

Per-ratio change vs prior section (× 100 for percentage-point scale):

```text
negative_language_delta     = (neg_cur - neg_prior) × 100
uncertainty_language_delta  = (unc_cur - unc_prior) × 100
legal_language_delta        = (lit_cur - lit_prior) × 100
constraining_language_delta = (con_cur - con_prior) × 100
```

Consumed by `disclosure_change_score` enrichment (+10% of positive avg `uncertainty_language_delta` across 1A + MD&A).

**v2:** Feed `legal_language_delta` into `legal_regulatory_risk_score` blend (weight 0.15).

## Confidence score

```text
confidence = clamp(0.4, 0.95, 0.7 + semantic_similarity × 0.2 - |Δ uncertainty_ratio|)
```

No prior filing → `confidence = 0.2`, `disclosure_change_score = null`.

**v2:** Also factor extraction confidence from `filing_sections.extraction_confidence`.

## Missing prior behavior

| Field | Value |
|-------|-------|
| `disclosure_change_score` | `null` |
| `confidence_score` | `0.2` |
| `diff_summary` | `"No prior comparable filing section available."` |

**Never substitute 0** — missing is not "no change."

## Section priority for filing-level diffs

| Component | Primary diff section |
|-----------|---------------------|
| `disclosure_change_score` | 1A (60%), MD&A (40%) |
| `risk_factor_intensity_score` | 1A diff (25% of blend) |
| `internal_controls_risk_score` | `item_9a_controls` or `item_4_controls` |
| `event_severity_score` | 1A diff only |

## API exposure

`GET /v1/company/{ticker}/disclosure-metrics` → `diff_highlights[]` with `language_deltas`.

## Unit test checklist

- [ ] Identical text → similarity ≈ 1, change score ≈ 0
- [ ] Large new paragraph → lower similarity, higher change
- [ ] New topic keyword → appears in `new_topics`
- [ ] No prior → null score, low confidence
- [ ] Language deltas sign correct when tone increases
