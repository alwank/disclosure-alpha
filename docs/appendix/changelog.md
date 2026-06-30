# Changelog

Version history for parser, metrics engine, dictionary packs, and scoring model.

## 1.5.1 (2026-06-26)

OpenBB Workspace addon modernization plus API pipeline performance and EDGAR improvements.

### Evidence correction (2026-06-29)

| Area | Change |
|------|--------|
| **Boilerplate construct** | Public evidence updated to **ρ ≈ 0.92** (n=478) for `boilerplate_combined_ratio` vs LS proxy — full L2 re-run on EDGAR-built FY2025 corpus; prior **0.96** headline was overstated |

### OpenBB Workspace

| Area | Change |
|------|--------|
| **OpenBB `apps.json`** | Curated Copilot prompts; `mcp_servers` for Disclosure Alpha Analyst at `/mcp` |
| **OpenBB `widgets.json`** | `imgUrl`, `subCategory`, `mcp_tool` linking widget to `score_company_filing_tool` |
| **HTTP MCP** | Analyst MCP mounted at `/mcp` on `disclosure-alpha-api` when `[mcp]` installed (Streamable HTTP) |
| **CORS** | `Mcp-Session-Id` exposed for browser MCP clients |
| **Docs** | OpenBB guide and quickstart: `[api,mcp]` install, Copilot/MCP connect, port 8000 consistency |

### API and pipeline

| Area | Change |
|------|--------|
| **Metrics cache** | In-process TTL cache on `metrics_filing_ticker` (`METRICS_CACHE_TTL_SECONDS`, `METRICS_CACHE_MAX_SIZE`) |
| **Pipeline timing** | Optional per-stage timing logs on `metrics_filing_ticker` (`PIPELINE_TIMING`) |
| **Panel screener** | Concurrent ticker scoring via `PANEL_MAX_WORKERS` |
| **EDGAR** | Metadata-first filing resolution (`resolve_filing_with_prior`) |

## 1.5.0 (2026-06-25)

Metrics-engine v4 release with refreshed boilerplate construct evidence and extraction/scoring pipeline fixes.

### text_metrics_v4

| Area | Change |
|------|--------|
| **Metrics engine** | `text_metrics_v4` — `boilerplate_cross_firm_ratio`, `boilerplate_combined_ratio`; `boilerplate_risk_score` uses combined ratio |
| **Baselines** | `data/baselines/item_1a_risk_factors_boilerplate_4grams_fy2025.json` committed 4-gram set |
| **Validation** | L2 construct primary pair: `boilerplate_combined_ratio` vs LS 4-gram at **ρ ≈ 0.96** (n=478) |

### Extraction and scoring fixes

| Area | Change |
|------|--------|
| **Extraction metadata** | `confidence_details` and extraction metadata surfaced consistently across matrix/changes responses |
| **Diff payload** | `section_diffs_v2` parity improvements in API/MCP payloads |
| **Form-aware scoring** | `form_type` wiring tightened on rescoring paths to align calibration behavior |

### Docs and evidence refresh

| Area | Change |
|------|--------|
| **Evidence docs** | Public evidence and scope docs updated to boilerplate construct **ρ ≈ 0.96** |
| **Version pins** | Installation/versioning/glossary docs aligned to `1.5.0` + `text_metrics_v4` |

## 1.4.0 (2026-06-24)

Python SDK configuration for tunable scoring and reproducibility metadata.

### What shipped

| Area | Change |
|------|--------|
| **Python SDK** | `PipelineConfig` and `ScoringConfig` on `score_filing_html()`, `score_filing_ticker()`, `score_for_model()`, and `score_panel_tickers()` — tune `component_weights`, `flag_boost_points`, `flag_evidence_score`, and v2 `calibration_context` without forking the parser |
| **Versions output** | `versions.analytics_config_id` in pipeline, MCP taxonomy, and panel batch responses (`builtin_default` when unset) |
| **Docs / examples** | Pipeline and versioning docs updated; full-coverage example uses cyber incident language; score-catalog clarifies v2-only components on 10-K vs 8-K fixtures |

Default scores are unchanged when no custom config is passed. Custom weights are tracked via `analytics_config_id`, not a new `scoring_model_version`.

## 1.3.0 (2026-06-24)

Package release consolidating artifact bumps and default-surface updates.

### What shipped

| Area | Change |
|------|--------|
| **Dictionaries / metrics** | `built_in_dictionaries_v3` and `text_metrics_v3` — dictionary package split, flag suppressions, legal phrases, modal tiers, topic tuning |
| **Scoring default** | **`deterministic_scoring_v2` is now the default** on CLI, HTTP, MCP, and `score_filing_html()` / `score_for_model()`; legacy `deterministic_scoring_v1` remains opt-in |
| **Validation data** | Reports and baselines removed from the public repository |
| **Docs** | Evidence, scope, HTTP/MCP guides, versioning pins, and glossary aligned to current artifact versions |
| **Release tooling** | Version sync test, HTTP endpoints doc drift check, hardened PyPI publish workflow |

### Current artifact defaults

| Artifact | Version |
|----------|---------|
| Parser | `section_extractor_v1` |
| Metrics engine | `text_metrics_v3` |
| Dictionary | `built_in_dictionaries_v3` |
| Scoring (default) | `deterministic_scoring_v2` |
| Scoring (legacy) | `deterministic_scoring_v1` |

**Breaking behavior note:** scores may differ from 1.2.0 for callers who did not pin `scoring_model_version=deterministic_scoring_v1`. Pin package and scoring versions for reproducibility — see {doc}`../reference/versioning`.

## built_in_dictionaries_v3 / text_metrics_v3 (2026-06-23)

Shipped v3 dictionary enrichment and package reorganization.

### What shipped

| Area | Change |
|------|--------|
| Dictionary package | Split monolith into `src/disclosure_alpha/dictionaries/` modules (`base.py`, `sentiment.py`, `phrases.py`, `topics.py`, `flags.py`) with backward-compatible `disclosure_alpha.dictionaries` exports |
| Flag precision | Added `FLAG_SUPPRESSIONS` with sentence-scoped suppression logic in `detect_section_flags()` |
| Legal phrases | Added `LEGAL_REGULATORY_PHRASES` and emitted `legal_regulatory_phrase_ratio` |
| Modal metrics | Added `weak_modal_word_ratio`, `moderate_modal_word_ratio`, `strong_modal_word_ratio` while preserving `modal_word_ratio` |
| Topic tuning | Tightened broad topics (`climate`, `labor`) and added high-value phrases like `net interest margin` / `semiconductor inventory` |
| MD&A density | Added v3 phrase candidates for uncertainty, demand, margin, and liquidity packs |
| Tooling | Added `scripts/mine_dictionary_candidates.py` for corpus-driven candidate mining |

### Version bumps

| Artifact | v2 | v3 |
|----------|----|----|
| `DICTIONARY_VERSION` | `built_in_dictionaries_v2` | `built_in_dictionaries_v3` |
| `METRICS_ENGINE_VERSION` | `text_metrics_v2` | `text_metrics_v3` |
| `SCORING_MODEL_VERSION` | `deterministic_scoring_v1` | unchanged at ship time (v2 default in 1.3.0) |

## deterministic_scoring_v2 (2026-06-22)

Introduced `SCORING_MODEL_VERSION_V2` / `deterministic_scoring_v2`. Shipped as opt-in in 1.2.0; **default on all surfaces in 1.3.0**.

### What shipped

| Component | Change |
|-----------|--------|
| `risk_factor_intensity_score` | Form-aware percentile calibration for Item 1A tone ratios (`calibration.py`) |
| `legal_regulatory_risk_score` | Multi-section evidence model; flag-only paths |
| `liquidity_stress_score` | MD&A-first evidence with Item 1A fallback; flag-only paths |
| `internal_controls_risk_score` | Section-attributed controls diff + evidence-based flags |
| Confidence (v2 path) | `compute_confidence_detailed()` with explicit penalties |

### Entry points (as of 1.3.0)

- **v2 (default):** `score_filing_html()`, `score_for_model()`, HTTP matrix/panel, MCP scoring tools
- **v1 (legacy):** `score_deterministic()`; HTTP/MCP via `scoring_model_version=deterministic_scoring_v1`

### Artifact versions at v2 ship (2026-06-22)

| Artifact | Version |
|----------|---------|
| Parser | `section_extractor_v1` |
| Metrics engine | `text_metrics_v2` |
| Dictionary | `built_in_dictionaries_v2` |
| Scoring (default at ship) | `deterministic_scoring_v1` |
| Scoring (new) | `deterministic_scoring_v2` |

Public empirical evidence (v2): on **478** S&P 500 FY2025 Item 1A sections, company-specificity correlates **ρ ≈ 0.87** with an independent NER-based specificity measure — see {doc}`../getting-started/scope-and-claims`.

### v2-only components (smoke-validated; not all validated at SP500 scale)

Available via `score_deterministic_v2()` or default `score_for_model()` on HTTP matrix/panel and MCP scoring tools:

- `static_disclosure_quality_score`, `static_disclosure_risk_score`, `disclosure_change_risk_score` (score product split)
- `cybersecurity_incident_risk_score`, `event_materiality_score` (excluded from v1 headline weights)
- `disclosure_change_score_v2` on section diffs (v1 `disclosure_change_score` unchanged)
- Sector/form baselines via `baselines.py` + `calibration.py`

## 1.2.0 (2026-06-23)

- **Evidence:** v2 specificity construct validity on 478 S&P 500 FY2025 Item 1A sections (ρ ≈ 0.87 vs NER) — see {doc}`../getting-started/scope-and-claims`.

## 1.1.0 (2026-06-22)

- **Breaking:** removed `view` from `/disclosure-matrix` and panel `/disclosure-matrix` request/response (deterministic scoring only).
- **Fix:** `disclosure_quality_score` is correct when `boilerplate_risk_score` is `0.0` (no longer treated as missing).
- **Internal:** unified `confidence_score` via `score_deterministic`; removed unused `llm_confidences` parameter.
- **Deprecation intent:** `disclosure-alpha-mcp` (legacy shim to the analyst bundle) remains for backward compatibility; prefer `disclosure-alpha-mcp-analyst` or `disclosure-alpha-mcp-builder` for new deployments. No removal planned in 1.1.x.

## Score catalog cleanup (2026-06-22)

Public docs and examples aligned with the deterministic scoring surface:

- **Removed dead fields** from documentation and generated fixtures: `business_model_fragility_score`, `cybersecurity_risk_score`, `hidden_risk_score`.
- **Ten computed components** — nine headline-weighted scores plus supplementary `specificity_quality_score`; canonical list: {doc}`../reference/score-catalog`.
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

### Empirical evidence (S&P 500 FY2025 Item 1A, v2)

On **478** sections, company-specificity correlates **ρ ≈ 0.87** with an independent NER-based specificity measure — see {doc}`../getting-started/scope-and-claims`.

### Out of scope (deferred)

- External Loughran–McDonald loader
- Package split of `dictionaries.py`
- Flag suppressions (`no material weakness`) pending false-positive review

## built_in_dictionaries_v1 / text_metrics_v1

Initial license-safe built-in lists and deterministic text metrics engine.
