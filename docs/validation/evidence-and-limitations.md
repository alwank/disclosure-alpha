# Evidence & Limitations

Disclosure Alpha is research-oriented open-source software. This page summarizes what the current release supports — and what it does not.

## What is supported today

Deterministic Item 1A analytics on **~425 S&P 500 FY2025 10-Ks** (~84% of the index):

| Check | Result |
|-------|--------|
| Construct validity (boilerplate proxy) | Spearman ρ ~ 0.68 vs literature measure |
| Construct validity (specificity proxy) | Spearman ρ ~ 0.84 vs NER-based specificity (v2) |
| Post-filing volatility association | Q5/Q1 ~ 1.11 on ~435-firm cohort (90-day window) |

These results come from automated validation on a fixed corpus. Scores in the open-source product use the same deterministic engine (`deterministic_scoring_v1`).

## Limitations

```{admonition} Not supported
:class: warning

- Buy/sell signals or return prediction
- Earnings-surprise outcome validation (FY2024 gate did not pass)
- Full S&P 500 validation coverage (corpus fetch rate ~84%, not 100%)
- Composite LLM scoring in the open-source HTTP API (`view=composite` returns HTTP 402)
```

**Scope note:** validation runs used **Item 1A text** for corpus scoring, not the full multi-section matrix. Missing filing sections reduce score coverage and confidence.

**Disclaimer:** Output is for research and integration testing. Read the underlying SEC filings before making decisions.

## Score versioning

Reproducibility is tied to artifact version strings:

| Artifact | Version |
|----------|---------|
| Parser | `section_extractor_v1` |
| Metrics | `text_metrics_v2` |
| Scoring | `deterministic_scoring_v1` |
| Dictionary | `built_in_dictionaries_v2` |

See {doc}`../getting-started/concepts` for how these fit in the pipeline.

Corpus layout and reproduction scripts live in the repository under `data/validation/`.
