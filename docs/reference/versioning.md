# Versioning and Reproducibility

How package, parser, metrics, dictionary, and scoring versions relate — and what can change scores.

## Version layers

| Layer | Where it appears | Example |
|-------|------------------|---------|
| **Package** | `pip show disclosure-alpha` | `1.1.0` |
| **Parser** | JSON `versions.parser_version` | `section_extractor_v1` |
| **Metrics engine** | JSON `versions.metrics_engine_version` | `text_metrics_v2` |
| **Dictionary** | JSON `versions.dictionary_version` | `built_in_dictionaries_v2` |
| **Scoring model** | JSON `versions.scoring_model_version` | `deterministic_scoring_v1` (default) or `deterministic_scoring_v2` (opt-in) |

Bump any artifact version can change scores for the same filing. Record all version fields when comparing runs over time.

## Scoring model: v1 (default) vs v2 (opt-in)

**Default:** CLI, HTTP, MCP, `score_filing_html()`, and `score_deterministic()` all use `deterministic_scoring_v1`. The `versions.scoring_model_version` field in responses is `deterministic_scoring_v1` unless you call the v2 entry point yourself.

**Opt-in v2:** `score_deterministic_v2()` in `disclosure_alpha.pipeline` runs `deterministic_scoring_v2`. It is **not** wired to HTTP or MCP today. To score with v2 in Python:

```python
from disclosure_alpha.pipeline import compute_section_metrics, score_deterministic_v2

metrics = compute_section_metrics(sections, prior_sections)
scores = score_deterministic_v2(metrics)
# Record SCORING_MODEL_VERSION_V2 when persisting: "deterministic_scoring_v2"
```

### What changed in v2

| Area | v1 | v2 |
|------|----|----|
| `risk_factor_intensity_score` | Raw tone ratios × 100 | Form-aware percentile calibration (`calibration.py`) |
| `legal_regulatory_risk_score` | Item 1A litigious ratio + legal delta + +15 flag boost | Multi-section evidence blend; flags as weighted evidence (65.0); flag-only path when no tone metrics |
| `liquidity_stress_score` | MD&A constraining + liquidity density + +15 flag boost | MD&A-first evidence with Item 1A fallback; flags as weighted evidence |
| `internal_controls_risk_score` | Controls diff + Item 1A constraining + +15 flag boost | Section-specific controls diff + constraining + serious flags as evidence |
| Confidence | `compute_overall_confidence()` (also used by v1 after P1-2) | `compute_confidence_detailed()` with explicit penalty breakdown |
| Unchanged components | — | `disclosure_change_score`, `mdna_uncertainty_score`, `boilerplate_risk_score`, `event_severity_score`, `tone_negativity_score`, `specificity_quality_score`, headline weights |

Full blend specs: {doc}`../methodology/aggregation` (v1 and v2 sections are labeled separately).

### Are v1 and v2 levels comparable?

**No — treat them as different score scales.** v2 recalibrates Item 1A tone inputs and replaces fixed +15 flag boosts with evidence-weighted blends. Numeric levels, cross-filing ranks, and time-series comparisons must stay within one scoring version. When migrating dashboards or stored scores, re-score historical filings with v2 or keep v1 pinned; do not mix versions in the same panel without relabeling.

Committed validation reports ({doc}`../validation/evidence-and-limitations`) were produced with **v1 only**. v2 is experimental until a validation pass is committed.

## Pin a release

```bash
pip install "disclosure-alpha==1.1.0"
pip install "disclosure-alpha==1.1.0[api,mcp]"
```

See {doc}`../getting-started/installation`.

## What can alter scores

- Dictionary word-list changes (`built_in_dictionaries_v*`)
- Metrics formulas or tokenization (`text_metrics_v*`)
- Aggregation weights or component blend (`deterministic_scoring_v*`) — switching v1 → v2 is a breaking score-model change
- Section extraction boundary changes (`section_extractor_v*`)
- Different prior filing resolution (affects change-related components only)
- Confidence penalty rules (affects `confidence_score` only, not component levels)

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
