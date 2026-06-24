# Versioning and Reproducibility

How package, parser, metrics, dictionary, and scoring versions relate — and what can change scores.

## Version layers

| Layer | Where it appears | Example |
|-------|------------------|---------|
| **Package** | `pip show disclosure-alpha` | `1.4.0` |
| **Parser** | JSON `versions.parser_version` | `section_extractor_v1` |
| **Metrics engine** | JSON `versions.metrics_engine_version` | `text_metrics_v3` |
| **Dictionary** | JSON `versions.dictionary_version` | `built_in_dictionaries_v3` |
| **Scoring model** | JSON `versions.scoring_model_version` | `deterministic_scoring_v2` (default) or `deterministic_scoring_v1` (legacy) |
| **Analytics config** | JSON `versions.analytics_config_id` | `builtin_default` or a custom id / `custom_<hash>` from `PipelineConfig` |

Bump any artifact version can change scores for the same filing. Record all version fields when comparing runs over time.

Custom `ScoringConfig` weights or flag constants change scores under the same `scoring_model_version`; use `analytics_config_id` to distinguish those runs from built-in defaults.

## Scoring model: v2 (default) vs v1 (legacy)

**Default:** CLI, HTTP, MCP, `score_filing_html()`, and `score_for_model()` all use `deterministic_scoring_v2`. The `versions.scoring_model_version` field in responses is `deterministic_scoring_v2` unless you opt into v1.

**Legacy v1 (HTTP):** `GET /v1/company/{ticker}/disclosure-matrix` and `POST /v1/panel/disclosure-matrix` accept `scoring_model_version=deterministic_scoring_v1` (query param on matrix; JSON body field on panel).

**Legacy v1 (MCP):** scoring tools accept optional `scoring_model_version=deterministic_scoring_v1`.

**Legacy v1 (Python):** `score_deterministic()` runs the v1 aggregation explicitly. Default pipeline helpers use v2 via `score_for_model()`:

```python
from disclosure_alpha.pipeline import compute_section_metrics, score_for_model

metrics = compute_section_metrics(sections, prior_sections)
scores = score_for_model(metrics)  # deterministic_scoring_v2
legacy = score_for_model(metrics, "deterministic_scoring_v1")
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

Public empirical evidence for v2: {doc}`../getting-started/evidence`.

## Pin a release

```bash
pip install "disclosure-alpha==1.4.0"
pip install "disclosure-alpha==1.4.0[api,mcp]"
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

## Related

- {doc}`../appendix/changelog` — release history
- {doc}`../appendix/glossary` — term definitions
- {doc}`../getting-started/evidence` — what's proven
- {doc}`../getting-started/scope-and-claims` — scope and limits
- {doc}`../getting-started/understanding-scores`
