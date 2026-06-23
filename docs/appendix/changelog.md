# Changelog

Version history for parser, metrics engine, dictionary packs, and scoring model.

## deterministic_scoring_v2 (2026-06-22)

Introduced an **opt-in** scoring model (`SCORING_MODEL_VERSION_V2` / `deterministic_scoring_v2`). Default surfaces unchanged — still `deterministic_scoring_v1`.

### What shipped

| Component | Change |
|-----------|--------|
| `risk_factor_intensity_score` | Form-aware percentile calibration for Item 1A tone ratios (`calibration.py`) |
| `legal_regulatory_risk_score` | Multi-section evidence model; flag-only paths |
| `liquidity_stress_score` | MD&A-first evidence with Item 1A fallback; flag-only paths |
| `internal_controls_risk_score` | Section-attributed controls diff + evidence-based flags |
| Confidence (v2 path) | `compute_confidence_detailed()` with explicit penalties |

### Entry points

- **v1 (default):** `score_deterministic()`, `score_filing_html()`, HTTP matrix/panel, MCP
- **v2 (opt-in):** `score_deterministic_v2()`; HTTP matrix/panel via `scoring_model_version`; MCP scoring tools via same parameter

### Artifact versions (unchanged in this release)

| Artifact | Version |
|----------|---------|
| Parser | `section_extractor_v1` |
| Metrics engine | `text_metrics_v2` |
| Dictionary | `built_in_dictionaries_v2` |
| Scoring (default) | `deterministic_scoring_v1` |
| Scoring (opt-in) | `deterministic_scoring_v2` |

Committed validation reports remain on **v1** for production claims. v2 **smoke** reports on CI fixtures ship in `data/validation/reports/*_v2.json` — see {doc}`../validation/evidence-and-limitations`.

### In v2 (opt-in, smoke-validated only)

Available via `score_deterministic_v2()` or opt-in `scoring_model_version` on HTTP matrix/panel and MCP scoring tools — not validated at SP500 scale:

- `static_disclosure_quality_score`, `static_disclosure_risk_score`, `disclosure_change_risk_score` (score product split)
- `cybersecurity_incident_risk_score`, `event_materiality_score` (excluded from v1 headline weights)
- `disclosure_change_score_v2` on section diffs (v1 `disclosure_change_score` unchanged)
- Sector/form baselines via `baselines.py` + `calibration.py`

### Still deferred

- v2 headline migration (validation committed; default remains v1)

## 1.2.0 (2026-06-23)

- **Validation:** FY2025 v2 evidence committed — L2 construct pairs (n=428), matrix gates on partial EDGAR matrix corpus (n=330), L3 volatility association (n=435, corpus mode). v1 FY2025 reports refreshed (PR #19).
- **Tooling:** EDGAR full-matrix corpus builder (`build_matrix_validation_corpus_from_edgar.py`, PR #18).
- **Opt-in:** v2 scoring on HTTP matrix/panel and MCP (unchanged from 1.1.x; now backed by SP500 reports).
- **Docs:** {doc}`../validation/evidence-and-limitations` updated for v2 claims and FY2024 partial robustness notes.

## 1.1.0 (2026-06-22)

- **Breaking:** removed `view` from `/disclosure-matrix` and panel `/disclosure-matrix` request/response (deterministic scoring only).
- **Fix:** `disclosure_quality_score` is correct when `boilerplate_risk_score` is `0.0` (no longer treated as missing).
- **Internal:** unified `confidence_score` via `score_deterministic`; removed unused `llm_confidences` parameter.
- **Deprecation intent:** `disclosure-alpha-mcp` (legacy shim to the analyst bundle) remains for backward compatibility; prefer `disclosure-alpha-mcp-analyst` or `disclosure-alpha-mcp-builder` for new deployments. No removal planned in 1.1.x.

## Score catalog cleanup (2026-06-22)

Public docs and examples aligned with the deterministic scoring surface:

- **Removed dead fields** from documentation and generated fixtures: `business_model_fragility_score`, `cybersecurity_risk_score`, `hidden_risk_score`.
- **Ten computed components** — nine headline-weighted scores plus supplementary `specificity_quality_score`; canonical list: {doc}`../reference/score-catalog`.
- **Validation cohorts** — construct validity n=428; L3 volatility n=435 (distinct cohorts). See {doc}`../validation/evidence-and-limitations`.
- **Doc scope cleanup** — removed composite/OSS product-scope notes from public pages; renamed score catalog page to {doc}`../reference/score-catalog`.

## built_in_dictionaries_v2 / text_metrics_v2 (2026-06-21)

Shipped the built-in dictionary enrichment documented in {doc}`../methodology/metrics-engine`.

### Dictionary additions

| Pack | Count (approx.) | Notes |
|------|----------------:|-------|
| `NEGATIVE_WORDS` | 42 | Fraud, insolvency, impairment, outage terms |
| `UNCERTAINTY_WORDS` | 30 | Contingency, fluctuation, exposure terms |
| `LITIGIOUS_WORDS` | 26 | Arbitration, antitrust, indemnification terms |
| `CONSTRAINING_WORDS` | 28 | Covenant, lien, forbearance terms |
| Modal tiers | 18 | `WEAK_MODAL_WORDS`, `MODERATE_MODAL_WORDS`, `STRONG_MODAL_WORDS` |
| `BOILERPLATE_PHRASES` | 20 | Safe-harbor and generic risk language |
| `TOPIC_KEYWORDS` | 21 topics | Investable risk clusters for diff engine |
| `FLAG_PATTERNS` | 13 flags | SEC/PCAOB/FASB-grounded event phrases |
| `MDNA_DENSITY_TERMS` | 4 packs | MD&A uncertainty, demand, margin, liquidity density |

v2 flag phrase additions: `material weaknesses in internal control over financial reporting`, `plans are intended to mitigate`, `no longer expects`, `incident response`, `systems outage`.

`TERM_PACK_METADATA` now documents all shipped packs (negative, uncertainty, litigious, constraining, modal, boilerplate, topics, severity, flags, mdna_density, geography, segment).

### Matching behavior (metrics engine)

- **Boilerplate:** each phrase counted at most once per sentence.
- **Topics:** word-boundary phrase matching (no substring false positives); removed standalone `competitive` from competition topic.
- **Severity:** topic intensity uses severity words within ±10 tokens of a topic hit only.
- Shared helpers live in `disclosure_alpha.text_matching`.

### Version bumps

| Artifact | v1 | v2 |
|----------|----|----|
| `DICTIONARY_VERSION` | `built_in_dictionaries_v1` | `built_in_dictionaries_v2` |
| `METRICS_ENGINE_VERSION` | `text_metrics_v1` | `text_metrics_v2` |
| `SCORING_MODEL_VERSION` | unchanged | `deterministic_scoring_v1` |

### Validation (S&P 500 FY2025 Item 1A)

See {doc}`../validation/evidence-and-limitations` for canonical cohort counts and gate results (n=428 construct validity; n=435 volatility cohort).

### Out of scope (deferred)

- External Loughran–McDonald loader
- Package split of `dictionaries.py`
- Flag suppressions (`no material weakness`) pending false-positive review

## built_in_dictionaries_v1 / text_metrics_v1

Initial license-safe built-in lists and deterministic text metrics engine.
