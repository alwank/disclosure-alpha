# Versioning and Reproducibility

How package, parser, metrics, dictionary, and scoring versions relate — and what can change scores.

## Version layers

| Layer | Where it appears | Example |
|-------|------------------|---------|
| **Package** | `pip show disclosure-alpha` | `1.0.1` |
| **Parser** | JSON `versions.parser_version` | `section_extractor_v1` |
| **Metrics engine** | JSON `versions.metrics_engine_version` | `text_metrics_v2` |
| **Dictionary** | JSON `versions.dictionary_version` | `built_in_dictionaries_v2` |
| **Scoring model** | JSON `versions.scoring_model_version` | `deterministic_scoring_v1` |

Bump any artifact version can change scores for the same filing. Record all version fields when comparing runs over time.

## Pin a release

```bash
pip install "disclosure-alpha==1.0.1"
pip install "disclosure-alpha==1.0.1[api,mcp]"
```

See {doc}`../getting-started/installation`.

## What can alter scores

- Dictionary word-list changes (`built_in_dictionaries_v*`)
- Metrics formulas or tokenization (`text_metrics_v*`)
- Aggregation weights or component blend (`deterministic_scoring_v*`)
- Section extraction boundary changes (`section_extractor_v*`)
- Different prior filing resolution (affects change-related components only)

Package version alone does not guarantee identical scores — check artifact versions in output JSON.

## Record versions from output

**CLI / Python:**

```python
result = score_filing_html(html, "10-K")
print(result.to_dict()["versions"])
```

**HTTP:** every matrix/metrics response includes a `versions` object.

## Validation reports

Committed reports under `data/validation/reports/`:

| Report | Purpose |
|--------|---------|
| `deterministic_validation_report.json` | L2 construct validity (n=428 cohort) |
| `l3_outcomes_report.json` | L3 volatility association (corpus mode) |
| `l3_outcomes_report_edgar.json` | L3 with full EDGAR prior-year diffs |

Reproduction scripts: `data/validation/README.md` in the repository.

## Related

- {doc}`../appendix/changelog` — release history
- {doc}`../appendix/glossary` — term definitions
- {doc}`../validation/evidence-and-limitations` — what validation covers
- {doc}`../getting-started/understanding-scores`
