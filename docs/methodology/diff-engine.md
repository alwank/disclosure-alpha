# Diff Engine

**What this page answers:** How year-over-year section diffs are matched, scored, and when change components are null.

| | |
|--|--|
| **Inputs** | Current and prior section text (matched by `section_name`) |
| **Outputs** | Lexical/semantic similarity, change score, language deltas |
| **Version** | Bundled with `section_extractor_v1` prior matching rules |

## In plain terms

The diff engine compares each section's text to the same section in a prior comparable filing. It measures lexical and semantic similarity, detects new or intensified risk topics, and produces a 0–100 change score plus language deltas that feed aggregation.

## When you'll see this

- **CLI:** automatic when `--prior-html` is set; EDGAR ticker flows resolve prior by default
- **HTTP:** `compare=prior` on metrics and matrix routes (default)
- **Components affected:** `disclosure_change_score`, `event_severity_score`, and diff inputs to `risk_factor_intensity_score` and `internal_controls_risk_score`
- **Null signal:** no prior section → `disclosure_change_score` is `null`, not zero

Implemented in the `diff_engine` module.

<details>
<summary>Full specification</summary>

Quantifies meaningful qualitative change between current and prior comparable section text. Prior sections are matched by name in `pipeline.py` (`_prior_by_name`).

## Prior section selection

When scoring with prior HTML (CLI `--prior-html`, HTTP `compare=prior`, or EDGAR prior resolution):

| Case | Prior text |
|------|------------|
| Prior section exists with same `section_name` | Prior section `cleaned_text` |
| No prior HTML or no matching section | `prior_text = None` |

EDGAR ticker flows resolve the prior filing as same ticker, same form type, earlier filing date via `resolve_prior_filing()`.

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
    diff_summary: str,
    confidence_score: float,
    language_deltas: dict[str, float],
)
```

## Similarity

| Measure | Method |
|---------|--------|
| `lexical_similarity` | TF-IDF cosine similarity (sklearn, max 2000 features) |
| `semantic_similarity` | Embedding cosine similarity via `embedding_service.semantic_similarity()` |

## Topic detection

Topics come from keyword clusters in `TOPIC_KEYWORDS` (`dictionaries.py`):

- **New topics** — in current, not in prior
- **Removed topics** — in prior, not in current
- **Intensified topics** — shared topics where current intensity > 1.2× prior (`SEVERITY_WORDS` weighting)

## Change score formula

```text
combined_sim = 0.6 × semantic_similarity + 0.4 × lexical_similarity

new_topic_score      = min(1.0, len(new_topics) / 3)
intensified_score    = min(1.0, len(intensified) / 3)
length_component     = clamp(length_change_pct, 0, 1)

disclosure_change_score =
    40 × (1 − combined_sim)
  + 20 × length_component
  + 20 × new_topic_score
  + 20 × intensified_score

clamp to [0, 100]
```

## Language deltas

Per-ratio change vs prior section (percentage-point scale):

```text
negative_language_delta     = (neg_cur − neg_prior) × 100
uncertainty_language_delta  = (unc_cur − unc_prior) × 100
legal_language_delta        = (lit_cur − lit_prior) × 100
constraining_language_delta = (con_cur − con_prior) × 100
```

Used by aggregation: uncertainty delta boosts `disclosure_change_score`; legal delta feeds `legal_regulatory_risk_score`.

## Diff confidence

When prior text exists:

```text
confidence = clamp(0.4, 0.95, 0.7 + semantic_similarity × 0.2 − |Δ uncertainty_ratio|)
```

No prior → `disclosure_change_score = null`, `confidence_score = 0.2`, summary `"No prior comparable filing section available."`

**Never substitute 0 for null** — missing prior is not "no change."

## Interpretation bands

| Score | Meaning |
|------:|---------|
| 0–25 | Minor wording; high similarity |
| 26–50 | Moderate topic or tone shift |
| 51–75 | New or intensified risk topics |
| 76–100 | Major semantic shift or multiple new topics |

## Section use in aggregation

| Component | Primary diff input |
|-----------|-------------------|
| `disclosure_change_score` | Item 1A diff (60%) + MD&A diff (40%), plus uncertainty delta boost |
| `risk_factor_intensity_score` | Item 1A diff (25% of tone blend) |
| `internal_controls_risk_score` | Controls section diff |
| `event_severity_score` | Item 1A diff only |

## API exposure

`GET /v1/company/{ticker}/disclosure-metrics` returns per-section diffs and `language_deltas` when `compare=prior` (default).

## Related

- {doc}`metrics-engine`
- {doc}`aggregation`
- {doc}`research-foundation`

</details>
