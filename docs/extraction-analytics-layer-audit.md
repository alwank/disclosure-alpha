# Extraction & Analytics Layer Audit

**Date:** 2026-06-25  
**Scope:** Extraction (`section_extractor.py`, taxonomy, pipeline extraction path) and analytics (`text_metrics.py`, `diff_engine.py`, `deterministic_scoring.py`, `confidence.py`, `pipeline.py`)  
**Method:** Read-only code audit (static analysis; pytest not run in audit environment)  
**Status:** Findings only — no fixes implemented

**Sources:** Unified synthesis of extraction audit (`862d09fc`) and analytics audit (`33740634`).

Related: broader project audit in [`codebase-audit-report.md`](codebase-audit-report.md).

---

## Implementation tracker

Use issue numbers from the [Unified Issues Table](#unified-issues-table) below.

| # | Priority | Tag | Status | Notes |
|---|----------|-----|--------|-------|
| 1 | P0 | Both | done | `compute_section_metrics()` aggregates section warnings, sets `required_sections_present`, accepts `form_type` |
| 2 | P0 | Both | done | Confidence penalties fire via wired metadata; integration tests in `test_pipeline.py` |
| 3 | P1 | Analytics | done | `form_type` passed on matrix/changes/MCP `score_for_model` rescoring |
| 4 | P1 | Analytics | done | `dictionary_version` in `build_versions()`, MCP taxonomy, and versioned examples |
| 5 | P1 | Both | done | `filter_metrics_result()` scopes `extraction_confs`, warnings, and required-section check |
| 6 | P1 | Extraction | done | Form-aware sec_parser: 10-K / 10-Q / fallback by normalized form type |
| 7 | P1 | Extraction | done | `SECTION_HEADING_SPECS` imported from `dictionaries/base.py` as single source |
| 8 | P1 | Extraction | done | `_metrics_dict()` preserves `None`; `section_metrics` typed `float \| None` |
| 9 | P1 | Extraction | done | `missing_required_section` no longer stamped on every extracted section |
| 10 | P1 | Analytics | done | v2 matrix uses `diffs_for_change` throughout; `event_severity_score` null in v2 path |
| 11 | P2 | Analytics | done | Validation scopes table in `evidence.md` links Item 1A vs L3 cohorts |
| 12 | P2 | Analytics | done | `confidence_details` on CLI `to_dict()` and MCP score payloads; HTTP deferred |
| 13 | P2 | Analytics | done | Changes API exposes `section_diffs_v2` + `scoring_model_version` query param |
| 14 | P2 | Extraction | done | `sec_parser_unavailable` warning when `_parse_blocks` fails |
| 15 | P2 | Extraction | done | `item_7a_market_risk` in `MATRIX_SECTIONS_10K` |
| 16 | P2 | Analytics | done | L3 report registered in `COMMITTED_REPORTS` |
| 17 | P2 | Both | done | Integration tests for extraction metadata, form_type, filter scoping, P2 surfaces |


---

# Unified Audit Report

**Scope:** Read-only synthesis; no fixes implemented. Key cross-cutting items verified in `pipeline.py`, `confidence.py`, `section_extractor.py`, API/MCP entry points, and `build_versions()`.

---


## Executive Summary

### P0 — Critical

| Issue | Tag |
|-------|-----|
| **`required_sections_present` and `extraction_warnings` are never populated in `compute_section_metrics()`** — `MetricsResult` defaults (`required_sections_present=True`, `extraction_warnings=[]`) flow unchanged into `score_deterministic()` / `score_deterministic_v2()`. Section-level warnings from extraction exist on `ExtractedSection.warnings` but are not aggregated. Confidence penalties for missing required sections, short sections, suspect extraction, etc. never fire. Downstream scores, matrix API, changes API, and MCP all inherit optimistic confidence. | **Both** |

### P1 — High

| Issue | Tag |
|-------|-----|
| **`form_type` not passed when rescoring filtered metrics** — `disclosure_matrix`, `disclosure_changes`, and MCP `score_filing_html_tool` / `score_company_filing` call `score_for_model(metrics, version)` without `form_type`, so v2 calibration context defaults incorrectly (contrast: `score_filing_html` and `score_panel_tickers` pass it). | **Analytics** |
| **`dictionary_version` missing from `build_versions()`** — runtime version payloads omit `built_in_dictionaries_v3` while validation tooling (`matrix_gates`, `construct`) reports it separately. | **Analytics** |
| **`filter_metrics_result()` does not scope extraction metadata** — `extraction_confs`, `extraction_warnings`, and `required_sections_present` are copied wholesale when `sections=` filter is applied; confidence reflects full-filing extraction quality, not the requested subset. | **Both** |
| **`Edgar10QParser` used for all form types** — 10-K and 8-K HTML routed through the 10-Q parser; silent degradation risk. | **Extraction** |
| **Dual heading-pattern systems** — `SECTION_HEADING_SPECS` in `section_extractor.py` vs regex patterns in `dictionaries/base.py`; drift risk on section boundaries. | **Extraction** |
| **`_metrics_dict()` coerces `None` → `0.0`** — absent metrics read as zero density, not missing; affects scoring coverage semantics. | **Extraction** |
| **`missing_required_section` stamped on every extracted section** — when any required section is absent, all sections get the warning via `extra_warnings`; pollutes per-section signal and would over-penalize if warnings were wired. | **Extraction** |
| **v2 scoring mixes v1 and v2 diff sources** — `aggregate_deterministic_matrix_v2` uses `section_diffs_v2` for disclosure change and event materiality, but `risk_factor_intensity` and `internal_controls_risk` still read v1 `section_diffs`; legacy `event_severity_score` from the v1 base path may coexist with v2 `event_materiality_score`. | **Analytics** |
| **`evidence.md` vs internal L3 validation report mismatch** — public evidence page describes Item 1A–only cohort (n=478); full-matrix L3 report scope/headline numbers differ. | **Analytics** |

### P2 — Medium

| Issue | Tag |
|-------|-----|
| **`sec_parser` silent fallback** — import/parse failures return `[]` blocks with only a log warning; extraction may proceed via weaker heuristics without surfacing failure downstream. | **Extraction** |
| **Matrix validation corpus omits `item_7a_market_risk`** — dictionary defines it; `MATRIX_SECTIONS_10K` does not include it. | **Extraction** |
| **Changes API exposes v1 diffs only** — `shape_changes_payload` returns `metrics.section_diffs`, not `section_diffs_v2`; no `scoring_model_version` parameter on endpoint. | **Analytics** |
| **`confidence_details` not exposed** — `compute_confidence_detailed()` penalty breakdown is computed in v2 path then discarded (`_, _`); not in API, MCP, or `FilingScoreResult.to_dict()`. | **Analytics** |
| **`COMMITTED_REPORTS` is empty** — `check_report_versions()` is a no-op in the public repo; version drift on committed validation JSON is unchecked. | **Analytics** |
| **Test coverage gaps** — no tests asserting warning/required-section wiring in `compute_section_metrics`; no tests for form_type on rescoring paths; `filter_metrics_result` test does not cover metadata scoping. | **Both** |
| **Tests not executed in subagent environments** — Python 3.9 env could not run pytest; findings are static-analysis only. | **Both** |

### Confirmed Working

- Missing sections are **not fabricated** — absent sections stay absent.
- **Section IDs align** across extractor, dictionaries, and scoring.
- **Parser version** is stamped consistently on extracted sections.
- **Matrix `sections=` filter** correctly scopes section dicts (metrics, diffs, flags, densities, language_deltas, section_diffs_v2).

---

## Unified Issues Table

| # | Location | Issue | Impact | Suggested fix | Tag |
|---|----------|-------|--------|---------------|-----|
| 1 | `pipeline.py` → `compute_section_metrics()` | Never sets `extraction_warnings` or `required_sections_present`; never calls `required_sections_present(form_type, sections)` or aggregates `section.warnings` | Confidence systematically optimistic across CLI, API, MCP, and validation | After loop: compute `required_sections_present` from form type + section names; flatten/dedupe section warnings into `extraction_warnings`; accept optional `form_type` param | **Both** |
| 2 | `confidence.py` + all scoring consumers | Penalty model exists but receives empty/default inputs (see #1) | Users cannot distinguish high- vs low-quality extractions in `confidence_score` | Fix upstream wiring (#1); optionally expose `confidence_details` (#12) | **Both** |
| 3 | `api/endpoints/matrix.py:78`, `changes.py:51`, `mcp/tools.py:85,110,130` | `score_for_model(metrics, version)` omits `form_type` | v2 calibrated scores (tone, baselines) use default `CalibrationContext` instead of filing form | Pass `base` / `result.filing["form_type"]` / tool `form_type` into `score_for_model` | **Analytics** |
| 4 | `analytics_config.py` → `build_versions()` | Returns `parser_version`, `metrics_engine_version`, `analytics_config_id`, `scoring_model_version` only — no `dictionary_version` | API `versions` block incomplete; harder to audit dictionary drift | Add `DICTIONARY_VERSION` from `version.py` | **Analytics** |
| 5 | `pipeline.py` → `filter_metrics_result()` | `extraction_confs`, `extraction_warnings`, `required_sections_present` not filtered/recomputed for `section_names` | Filtered matrix/changes confidence reflects full filing, not requested sections | Filter `extraction_confs` by section index/name map; recompute warnings and required-section check for subset + form type | **Both** |
| 6 | `section_extractor.py:146` | `sp.Edgar10QParser().parse(html)` for all forms | 10-K/8-K structure mis-parse risk; wrong block boundaries | Use form-appropriate parser (10-K / 10-Q / generic) or document + test fallback | **Extraction** |
| 7 | `section_extractor.py` `SECTION_HEADING_SPECS` vs `dictionaries/base.py` patterns | Two independent heading-regex sources | Section boundary drift when dictionaries update but extractor specs do not | Single source of truth (import patterns from dictionaries) | **Extraction** |
| 8 | `pipeline.py` → `_metrics_dict()` | `float(x or 0)` on all metric fields | `None` metrics become 0.0; scoring treats "missing" as "zero signal" | Preserve `None` or use explicit sentinel; let scoring `missing_components` handle absence | **Extraction** |
| 9 | `section_extractor.py:708–733` | `extra_warnings=["missing_required_section"]` applied to every extracted section when any required section missing | Per-section warning noise; multiplicative penalty if wired (#1) | Attach filing-level warning once on `MetricsResult`, or only on sections that are present but suspect | **Extraction** |
| 10 | `deterministic_scoring.py` → `aggregate_deterministic_matrix_v2()` | `diffs_for_change` (v2) used for disclosure change + event materiality; `section_diffs` (v1) still used for risk factor intensity, internal controls, and inherited `event_severity_score` | Inconsistent change semantics within a single v2 score | Unify diff source per component with explicit provenance; drop or replace legacy `event_severity_score` in v2 | **Analytics** |
| 11 | `docs/getting-started/evidence.md` vs internal L3 report | Public page: Item 1A cohort n=478; L3 report describes different scope/headlines | Trust/documentation mismatch for external readers | Reconcile numbers or add scope disclaimers linking each claim to its cohort | **Analytics** |
| 12 | `pipeline.py:244`, `FilingScoreResult.to_dict()`, API schemas | `compute_confidence_detailed()` details discarded | Operators cannot debug why confidence is low | Add optional `confidence_details` to score result and analyst-tier API | **Analytics** |
| 13 | `api/shapes.py` → `shape_changes_payload()` | Returns `metrics.section_diffs` only | Changes endpoint always v1 diffs even when default scoring is v2 | Expose `section_diffs_v2` and/or `scoring_model_version` query param | **Analytics** |
| 14 | `section_extractor.py:137–154` | `sec_parser` failures return `[]` silently | Extraction quality collapse without downstream warning | Propagate parse failure into `extraction_warnings` or extraction method metadata | **Extraction** |
| 15 | `validation/matrix_corpus.py` `MATRIX_SECTIONS_10K` | Omits `item_7a_market_risk` (defined in dictionaries) | Matrix validation does not cover 7A market-risk section | Add to corpus section list if 7A is in product scope | **Extraction** |
| 16 | `validation/report_versions.py` | `COMMITTED_REPORTS = {}` | No CI guard on committed validation JSON versions | Populate when internal reports ship, or document intentional emptiness | **Analytics** |
| 17 | `tests/` | Gaps on confidence wiring, form_type rescoring, filter metadata scoping | Regressions on P0/P1 issues would go undetected | Add targeted unit tests per rows #1, #3, #5 | **Both** |

---

## Cross-Cutting Conclusions

### Versioning
Runtime `versions` from `build_versions()` cover parser, metrics engine, analytics config, and scoring model — but **not dictionary version**, which validation modules report separately. `COMMITTED_REPORTS` is empty, so automated report-version checks do not run in the public repo. Consumers comparing API responses to validation artifacts must manually align dictionary version.

### API parity
**Inconsistent `form_type` threading:** full-pipeline paths (`score_filing_html`, `score_panel_tickers`) pass `form_type` into v2 calibration; **rescoring paths** (matrix GET, changes GET, MCP rescoring wrappers) do not. **Diff parity:** changes API serves v1 `section_diffs` while default scoring is v2. **Confidence parity:** v2 computes detailed penalties internally but API/MCP expose only the scalar `confidence_score`.

### Null semantics
Two related problems: **`_metrics_dict` null→0.0 coercion** makes absent text metrics look like zero signal; **`MetricsResult` boolean/warning defaults** make absent extraction quality look like a clean filing. Together they bias both component scores and confidence upward.

### Provenance
Section-level `ExtractedSection.warnings` and `extraction_method` are available on the sections API but **do not flow into `MetricsResult`** or scoring provenance. Operators see per-section warnings in extraction output but not in matrix/changes confidence rationale.

### Test gaps
Existing tests cover `filter_metrics_result` section dict filtering, `required_sections_present()` helper, and `compute_confidence_detailed()` in isolation — but **not the integration gap** between extraction warnings and `compute_section_metrics()`. No tests guard `form_type` on matrix/changes/MCP rescoring. Neither subagent could run pytest (Python 3.9 environment limitation).

### Docs vs code
- **`evidence.md`** documents Item 1A–only construct validity (n=478) and points maintainers to `internal` branch for full validation — but headline numbers may not match full-matrix L3 reports referenced in analytics audit.
- **`docs/methodology/aggregation.md`** documents confidence penalties for missing required sections and extraction warnings — behavior **not currently wired** in `compute_section_metrics()`.
- **`analytics-scoring-layer-improvement-plan.md`** already lists `extraction_warnings`, `required_sections_present`, and optional `confidence_details` — plan items remain open.

---

## Test Coverage Note

Both subagent audits performed **static code review only**. Pytest could not be executed in their environments (Python 3.9 constraint reported). All severity assignments and "working" confirmations are based on source inspection, not green test runs. Before treating any issue as resolved, run the full test suite on the project's supported Python version and add the integration tests identified in row #17.

---

## Audit IDs

| Audit | Agent transcript |
|-------|------------------|
| Extraction | [862d09fc-3e3f-4c6e-9445-1256bffa6e7a](862d09fc-3e3f-4c6e-9445-1256bffa6e7a) |
| Analytics | [33740634-8d18-4231-807a-43bdadb1ff5b](33740634-8d18-4231-807a-43bdadb1ff5b) |

---

# Appendix A — Extraction Layer Detail

## Extraction findings summary (P0/P1/P2)

**P0**
- **`required_sections_present` and `extraction_warnings` are never populated in the pipeline.** `compute_section_metrics()` (`pipeline.py:143–191`) builds `MetricsResult` without calling `required_sections_present()` or aggregating `ExtractedSection.warnings`. Fields default to `required_sections_present=True` and `extraction_warnings=[]` (`pipeline.py:62–63`), so v2 confidence (`score_deterministic_v2`, `pipeline.py:244–252`) and serialized API/CLI metrics always behave as if extraction is complete and clean — contradicting guardrails in `docs/analytics-scoring-layer-improvement-plan.md` (conditional null / missing-evidence semantics).
- **Section-level warnings are invisible downstream.** Per-section warnings (`extraction_suspect`, `last_resort_extraction`, `missing_required_section`, etc. in `section_extractor.py`) never reach `MetricsResult.extraction_warnings`, so `_WARNING_PENALTIES` in `confidence.py:14–18` never fire in production.

**P1**
- **All forms parsed with `Edgar10QParser` only** (`section_extractor.py:146`), including 10-K and 8-K. No form-aware parser selection; correctness relies on merge/fallback heuristics.
- **Two independent heading-pattern systems** — `SECTION_HEADING_SPECS` (`section_extractor.py:69–84`) for sec_parser path vs `SUPPORTED_SECTIONS_*` regex in `dictionaries/base.py:95–118` for fallback/clean-HTML reslice. They can disagree (e.g. 10-K `item_1a` is looser in `base.py` than sec_parser title matching).
- **`filter_metrics_result()` does not scope extraction metadata** (`pipeline.py:323–336`): `extraction_confs`, `diff_confs`, `extraction_warnings`, and `required_sections_present` pass through unfiltered when HTTP `sections=` is used — confidence can reflect unfiltered sections while scores use filtered metrics.
- **Metrics boundary coerces missing ratios to `0.0`** in `_metrics_dict()` (`pipeline.py:95–112`) after extraction. Missing *sections* correctly omit keys (scoring returns `None` via `_section_metrics`, `deterministic_scoring.py:78–85`), but within an extracted section, zero-word ratios are indistinguishable from “no signal” at the metrics dict layer.
- **No `edgar/*` HTML parsers** — `edgar/resolver.py`, `client.py`, `cache.py` only resolve/fetch HTML; extraction is entirely in `section_extractor.py`.

**P2**
- **`missing_required_section` warning applied to every extracted section** when any required section is absent (`section_extractor.py:705–733`), not just the missing ones.
- **sec_parser failures degrade silently** to regex fallback (`section_extractor.py:137–154`, `788–795`) with only log warnings; `extraction_method` changes but `parser_version` stays `section_extractor_v1`.
- **Validation matrix corpus omits `item_7a_market_risk`** (`validation/matrix_corpus.py:13–19`) though taxonomy and extractor support it (`base.py:100`, `SECTION_HEADING_SPECS:74`).
- **Tests could not be executed** in this environment (Python 3.9; project requires `>=3.11` per `pyproject.toml:11`).

**Working as intended**
- Missing sections are **not fabricated** (`test_missing_section_not_fabricated`, `section_extractor.py` returns only found headings).
- Section IDs in taxonomy (`dictionaries/base.py`, `docs/reference/section-taxonomy.md`) match scoring lookups (`deterministic_scoring.py` `_LEGAL_SECTIONS`, `_EVENT_SECTIONS`, etc.).
- Prior diffs return `disclosure_change_score=None` when no prior text (`diff_engine.py:170–177`).
- Matrix `sections=` filter now scores filtered metrics first (`api/endpoints/matrix.py:75–78`; test `test_api_matrix_tiers.py:68–101`) — improvement-plan P0-1 appears **fixed**.
- Parser version `section_extractor_v1` is consistent across `version.py`, public evidence (`docs/getting-started/evidence.md:31`), L3 report (`data/validation/reports/l3_outcomes_report_fy2025_v2.json:5–7`), and examples.

---

## Issues table

| Location | Issue | Impact | Suggested fix |
|----------|-------|--------|---------------|
| `pipeline.py:143–191` | `compute_section_metrics()` never sets `required_sections_present` or `extraction_warnings` | Confidence and metrics JSON overstate extraction quality; missing Item 1A/MD&A not penalized | Accept `form_type`; call `required_sections_present()`; flatten deduped section warnings into `MetricsResult` |
| `pipeline.py:62–63`, `confidence.py:33–38` | Defaults `required_sections_present=True`, `extraction_warnings=[]` consumed by scoring | 0.25 penalty for missing required sections never applied in real runs | Wire extraction metadata in `compute_section_metrics`; pass `form_type` through `score_filing_html` / ticker paths |
| `section_extractor.py:146` | `Edgar10QParser()` used for 10-K, 10-Q, and 8-K HTML | Potential structural parse bias on non-10-Q filings; hidden dependency on merge/fallback | Select parser by normalized form type (`Edgar10KParser` / `Edgar10QParser` / 8-K path) or document intentional single-parser choice |
| `section_extractor.py:69–84` vs `dictionaries/base.py:95–118` | Duplicate, non-identical heading patterns (sec_parser vs fallback) | Primary/fallback can disagree on boundaries; maintenance drift | Single source of truth for patterns per section ID |
| `pipeline.py:323–336` | `filter_metrics_result()` leaves `extraction_confs`, `required_sections_present` unscoped | Section-filtered matrix/metrics responses can show optimistic confidence | Filter confs/warnings to selected sections; recompute `required_sections_present` for filter scope |
| `pipeline.py:95–112` | `_metrics_dict()` maps `None` ratios → `0.0` | Weak/null metric signals may look like zero signal after extraction | Preserve `None` for optional metrics or document that extraction output is always fully numeric |
| `section_extractor.py:705–733` | `missing_required_section` on all sections when one required section missing | Noisy warnings; hard to attribute which section failed | Attach warning only to missing section or add filing-level metadata |
| `validation/matrix_corpus.py:13–19` | `MATRIX_SECTIONS_10K` lacks `item_7a_market_risk` | Matrix validation under-tests 7A extraction | Add `item_7a_market_risk` to corpus gates |
| `edgar/resolver.py:22–26` | `normalize_form_type()` rejects `8-K` | Ticker/EDGAR paths cannot exercise 8-K extraction (by design per docs) | No extraction change unless product expands; keep docs surface matrix prominent |
| `tests/test_section_extractor.py` | No test that pipeline propagates warnings / `required_sections_present` | Regression risk on P0 wiring gap | Add `test_compute_section_metrics_extraction_metadata` |
| `tests/` (general) | No E2E `8-K` HTML → `score_filing_html` test | 8-K extraction tested; scoring integration only via synthetic metrics (`test_deterministic_scoring.py:503`) | Add fixture-based 8-K pipeline test |

---

## Versioning inventory (extraction/parser)

| Artifact | Constant / location | Value | Notes |
|----------|---------------------|-------|-------|
| **Parser (response)** | `src/disclosure_alpha/version.py:1` `PARSER_VERSION` | `section_extractor_v1` | Emitted via `build_versions()` (`analytics_config.py:122`), per-section `ExtractedSection.parser_version` (`section_extractor.py:39`) |
| **Extraction methods** | `section_extractor.py` | `sec_parser_sequence_v1`, `heading_boundary_fallback`, `heading_boundary_fallback_merged`, `clean_html_best_match`, `clean_html_last_resort` | Method strings are **not** versioned separately; all roll up under `section_extractor_v1` |
| **sec_parser dependency** | `pyproject.toml:25` | `sec-parser>=0.58.1,<0.59` | Block parser in `_parse_blocks()` |
| **Metrics engine** | `version.py:2` | `text_metrics_v3` | Downstream of extraction; not parser version |
| **Dictionary** | `version.py:6` | `built_in_dictionaries_v3` | Section maps in `dictionaries/base.py` |
| **Public evidence** | `docs/getting-started/evidence.md:31` | `section_extractor_v1` + `text_metrics_v3` + `built_in_dictionaries_v3` | Aligned with code |
| **L3 validation report** | `data/validation/reports/l3_outcomes_report_fy2025_v2.json:5–7` | Same trio + `deterministic_scoring_v2` | Fresh (2026-06-23) |
| **Stale built docs** | `docs/_build/html/_sources/validation/evidence-and-limitations.md.txt` (if present) | May still cite `text_metrics_v2` / v1 scoring | Source docs on `main` appear updated; rebuild HTML may lag |

No `section_extractor_v2` exists despite substantial internal method diversity (sec_parser + regex merge + Item 1A reslice). Any boundary-algorithm change currently ships under the same `section_extractor_v1` string.

---

## Test coverage notes

**`tests/test_section_extractor.py`** (14 tests on disk; **not run** here — env Python 3.9 vs required 3.11):

| Covered | Not covered |
|---------|-------------|
| Item 1A + Item 7 on sample 10-K | sec_parser unavailable / import failure → full fallback path |
| Missing section not fabricated | Amendment forms (`10-K/A`) |
| TOC suppression, duplicate headings | `item_1c_cybersecurity` boundary cases |
| Item 7 vs 7A split | `_ensure_item1a` / `_best_item1a_from_clean_html` end-to-end (only unit tests for helpers) |
| 10-Q and 8-K section routing (synthetic HTML) | Real 8-K or 10-Q filing fixtures |
| Real 10-K regressions (AAPL, TGT, AMZN) | `Edgar10QParser` on 10-K structural fidelity |
| Fallback, confidence helpers, `_pick_best_extraction` | Warning propagation into `MetricsResult` |
| `required_sections_present()` on fixtures | `compute_section_metrics` + `form_type` integration |

**Related tests outside `test_section_extractor.py`:**
- `tests/test_pipeline.py` — `filter_metrics_result`, `compute_section_metrics` flags; no extraction metadata assertions
- `tests/test_api_matrix_tiers.py` — filtered scoring (fixed P0-1)
- `tests/test_deterministic_scoring.py:503` — 8-K **scoring** with hand-built metrics, not extracted HTML
- `tests/test_edgar_resolver.py:89` — 8-K rejected at resolver (expected)
- `tests/test_cli.py:65` — CLI ticker 8-K rejected (expected)

**Coverage command note:** `pytest` failed at collection (`float | None` on Python 3.9). Use Python 3.11+ per `pyproject.toml`.

---

## Docs vs code (extraction-specific)

| Topic | Docs say | Code does | Verdict |
|-------|----------|-----------|---------|
| **8-K support** | `scope-and-claims.md:9–22` — local HTML / MCP Builder only; not EDGAR/HTTP ticker | `extract_sections()` supports 8-K (`base.py:112–118`); `edgar/resolver.py:22–26` rejects 8-K | **Aligned** if surface matrix is read |
| **Required sections** | `overview.md:69–76`, `section-taxonomy.md` — missing → lower coverage, null components | Scoring nulls work; `required_sections_present` in metrics **always `True`** in pipeline | **Overclaim** in example JSON (`required_sections_present: true` in `docs/examples/score-minimal-10k.json:133`) |
| **Section taxonomy** | `section-taxonomy.md` lists 10-K/10-Q/8-K IDs | Matches `SUPPORTED_SECTIONS_*` and `SECTION_HEADING_SPECS` keys | **Aligned** |
| **8-K required for scoring** | `section-taxonomy.md:31` — `item_2_02` required | `REQUIRED_SECTIONS["8-K"]` = `["item_2_02"]` (`base.py:125`) | **Aligned** |
| **Parser version naming** | `versioning.md:10` — `section_extractor_v1` | `PARSER_VERSION` matches; `extraction_method` uses `sec_parser_sequence_v1` internally | **Aligned** (method name ≠ version string) |
| **Evidence cohort** | `evidence.md` — Item 1A only, 478 firms | Validation uses extraction quality filters; not full multi-section matrix | **Conservative / accurate** |
| **Matrix section filter** | Improvement plan P0-1 described pre-filter scoring bug | `matrix.py:75–78` filters before `score_for_model` | **Fixed**; plan doc is historical |
| **Event materiality** | `score-catalog.md:64–66` — needs 8-K sections | Extraction provides IDs; `event_materiality_score` not in headline weights (`scoring_types.py:4–14`) | **Aligned**; extraction enables but doesn't score headline for 10-K |
| **`edgar/` parsers** | User scope mentioned `edgar/*` parsers | No parsers — fetch/resolve only | **Clarify**: extraction is not in `edgar/` |

---

## Pipeline flow (extraction → analytics)

```mermaid
flowchart LR
  HTML[Filing HTML] --> ES[extract_sections]
  ES --> SEC[sec_parser blocks]
  SEC -->|fail/empty| FB[regex fallback]
  SEC --> MERGE[merge + Item1A ensure]
  FB --> MERGE
  MERGE --> XS[list ExtractedSection]
  XS --> CSM[compute_section_metrics]
  CSM --> MR[MetricsResult keyed by section_name]
  MR --> SFM[score_for_model]
  SFM --> SC[component scores null if section missing]
```

**Type contract:** Downstream expects `section_name` keys from `dictionaries/base.py` (`item_1a_risk_factors`, `item_7_mdna`, `item_2_mdna`, 8-K `item_*` IDs). `ExtractedSection` → `compute_section_metrics` maps `section.section_name` → `section_metrics[section_name]` (`pipeline.py:156–161`). Scoring reads those keys explicitly (`deterministic_scoring.py`). **IDs match.**

**Null semantics at extraction boundary:** Absent sections → absent dict keys → component `None`. **Good.** Prior missing → `section_diffs[name]` omitted or `None` (`pipeline.py:171–172`). **Good.** Extraction does not insert placeholder sections with empty text.

**Gap:** Filing-level extraction quality (`required_sections_present`, aggregated warnings) is computed in `section_extractor.required_sections_present()` (`section_extractor.py:684–688`) but **never connected** to `MetricsResult`, so analytics layer cannot distinguish “partial extraction” from “full extraction” despite API schema fields existing.

---

# Appendix B — Analytics Layer Detail

### Analytics findings summary (P0/P1/P2)

**P0 — correctness / API parity**
1. **Confidence inputs never wired in the pipeline** — `compute_section_metrics()` never populates `extraction_warnings` or `required_sections_present` on `MetricsResult` (defaults stay `[]` / `True`), so production confidence ignores extractor warnings and missing required sections despite docs and `compute_confidence_detailed()` supporting those penalties.
2. **`form_type` not passed to scoring on HTTP matrix/changes and most MCP paths** — only `score_filing_html()` passes `form_type` into `score_for_model()` → `resolved_calibration()`. HTTP matrix/changes and MCP rescoring use default `CalibrationContext(form_type="10-K")`, so **10-Q (and other forms) can get wrong v2 calibration** vs CLI `--html`.
3. **MCP rescoring overwrites correctly calibrated scores** — `score_filing_html_tool` / `score_company_filing` call `score_filing_html()` / `score_filing_ticker()` (which score with `form_type`), then replace scores with `score_for_model(metrics, version)` **without** `form_type` (`mcp/tools.py` 109–110, 127–130).

**P1 — versioning, semantics, internal consistency**
4. **`dictionary_version` missing from runtime `versions` objects** — `build_versions()` emits parser, metrics, analytics_config_id, scoring_model_version only; docs/README claim `dictionary_version` in every response.
5. **Section-filtered matrix confidence is not section-scoped** — `filter_metrics_result()` filters metrics/diffs but keeps full `extraction_confs` / `diff_confs` lists (`pipeline.py` 331–332), so filtered matrix responses can show **higher confidence than filtered coverage warrants**.
6. **v2 scoring mixes v1 and v2 diff inputs** — `aggregate_deterministic_matrix_v2()` uses `section_diffs_v2` for `disclosure_change_score` but leaves `event_severity_score` (and `risk_factor_intensity` diff leg) on v1 `section_diffs` (`deterministic_scoring.py` 746–773, 333–340).
7. **Public evidence vs committed L3 report mismatch** — `docs/getting-started/evidence.md` cites Q5/Q1 ≈ 1.15 (n=435); `data/validation/reports/l3_outcomes_report_fy2025_v2.json` reports 1.1237 (n=497).
8. **Validation report hygiene not enforced** — `COMMITTED_REPORTS` is empty (`validation/report_versions.py` 9); committed L3 report is not checked in CI.

**P2 — docs, edge cases, tests**
9. **Changes API exposes v1 diffs only** — `shape_changes_payload()` serializes `metrics.section_diffs`, not `section_diffs_v2`, while v2 scoring may use v2 diffs internally.
10. **`confidence_details` not exposed** in HTTP/CLI/MCP responses (only scalar `confidence_score`).
11. **`compute_metric_families()` untested**; no test that v2 `disclosure_change_score` uses `section_diffs_v2`.
12. **Tests could not be executed** in this environment (Python 3.9 default; 3.11 hit numpy import error). Coverage numbers are **inferred from test file review**, not measured.

**Fixed since improvement plan (note)**
- P0-1 matrix `sections=` mismatch appears **fixed**: matrix filters metrics before scoring (`matrix.py` 76–78; `test_api_matrix_tiers.py` 68–101).

---

### Issues table

| Location | Issue | Impact | Suggested fix |
|----------|-------|--------|---------------|
| `pipeline.py` 143–191 | `compute_section_metrics()` never sets `extraction_warnings` / `required_sections_present` | Confidence overstated for short/suspect extractions and missing Item 1A/MD&A | Aggregate `section.warnings` and call `required_sections_present(form_type, sections)` |
| `api/endpoints/matrix.py` 78 | `score_for_model(metrics, scoring_version)` — no `form_type` | 10-Q matrix scores use 10-K calibration | Pass `form_type=base` (or `result.filing["form_type"]`) |
| `api/endpoints/changes.py` 51 | Same; no `scoring_model_version` param | 10-Q change scores + no v1 opt-in | Pass `form_type` and optional `scoring_model_version` |
| `mcp/tools.py` 109–110, 127–130 | Rescore without `form_type` after full pipeline | MCP 10-Q scores differ from CLI `--html` | Pass `form_type` to `score_for_model`, or drop redundant rescoring |
| `mcp/tools.py` 76–85 | `score_deterministic_tool` has no `form_type` | Metrics-only MCP path cannot calibrate per form | Add optional `form_type` argument |
| `analytics_config.py` 119–125 | `build_versions()` omits `dictionary_version` | Version pinning incomplete vs docs | Add `DICTIONARY_VERSION` to `build_versions()` |
| `pipeline.py` 323–336 | `filter_metrics_result()` keeps unfiltered conf lists | Filtered matrix `confidence_score` too high | Filter `extraction_confs`/`diff_confs` to selected sections |
| `deterministic_scoring.py` 746–773, 333–340 | v2 uses `section_diffs_v2` for change only; `event_severity` stays on v1 diffs | Inconsistent change semantics within v2 | Align `event_severity` (and RF diff leg) with `diffs_for_change` or document split |
| `api/shapes.py` 52–55 | Changes payload omits `section_diffs_v2` | API consumers can't see sentence-aligned diffs | Expose `section_diffs_v2` or unify under one field |
| `pipeline.py` 95–112 | `_metrics_dict()` uses `or 0` for all metrics | Empty extracted sections → zero metrics, not absent evidence | Distinguish missing section vs empty section if needed |
| `docs/getting-started/evidence.md` vs `data/validation/reports/l3_outcomes_report_fy2025_v2.json` | Vol association 1.15/n=435 vs 1.12/n=497 | Public evidence may not match latest internal run | Reconcile cohorts or update public table |
| `validation/report_versions.py` 9 | `COMMITTED_REPORTS = {}` | Stale validation JSON not caught in CI | Register L3 report + expected versions |
| `docs/methodology/aggregation.md` 294 | Says v1 `disclosure_change_score` unchanged | v2 **component** uses v2 diffs when prior exists | Clarify field-level vs component-level behavior |

---

### API path comparison (CLI vs HTTP vs MCP)

| Path | Entry | Scoring function | Default model | `form_type` to calibration | Section filter affects scores | Notes |
|------|--------|------------------|---------------|---------------------------|------------------------------|-------|
| **CLI** `score --html` | `score_filing_html()` | `score_for_model(..., form_type=args.form)` | v2 | Yes | N/A | Full `to_dict()` incl. provenance |
| **CLI** `score --ticker` | `score_filing_ticker()` → `score_filing_html()` | same | v2 | Yes (from filing) | N/A | EDGAR prior resolution |
| **CLI** `metrics` | `compute_section_metrics()` | none | — | — | — | Raw metrics only |
| **HTTP** `GET .../disclosure-matrix` | `metrics_filing_ticker` → `filter_metrics_result` → `score_for_model` | v2 (query override v1) | **No** | Yes (`sections=` pre-filter) | P0-1 fixed |
| **HTTP** `POST .../panel/disclosure-matrix` | `score_panel_tickers` | v2 | **Yes** (2nd `score_for_model` only) | No section filter | Double-scores; 2nd call wins |
| **HTTP** `GET .../disclosure-changes` | `metrics_filing_ticker` → `score_for_model` | v2 (implicit) | **No** | Yes (`sections=`) | No `scoring_model_version` param |
| **HTTP** `GET .../disclosure-metrics` | metrics only | none | — | Yes (`sections=`) | — |
| **MCP** `score_filing_html_tool` | `score_filing_html` then **rescore** | v2 | **Lost on rescore** | N/A | Redundant rescore |
| **MCP** `score_company_filing` | `score_filing_ticker` then **rescore** | v2 | **Lost on rescore** | N/A | Same bug as HTML tool |
| **MCP** `score_deterministic_tool` | `score_for_model(metrics, version)` | v2 default | **No** | N/A | Metrics JSON has no form |
| **Python SDK** | `score_filing_html()` / `score_for_model()` | v2 | Yes when using `score_filing_html` | N/A | Canonical path |

**Bottom line:** CLI `--html` and direct SDK `score_filing_html()` are the reference path. HTTP matrix/changes and MCP scoring tools can **diverge for 10-Q** and for confidence when extraction warnings exist.

---

### Versioning inventory (metrics/scoring)

| Artifact | Runtime constant (`version.py`) | In `build_versions()` / examples | In validation reports | In public docs |
|----------|----------------------------------|-----------------------------------|----------------------|----------------|
| Parser | `section_extractor_v1` | Yes | L3: yes | `evidence.md`: yes |
| Metrics | `text_metrics_v3` | Yes | L3: yes | `evidence.md`: yes |
| Dictionary | `built_in_dictionaries_v3` | **No** | L3: **no** | `evidence.md`: yes |
| Scoring | `deterministic_scoring_v2` (default) | Yes | L3: yes | `evidence.md`, `versioning.md`: yes |
| Analytics config | `builtin_default` | Yes | — | `versioning.md`: yes |

**Scoring versions in code**
- v1: `score_deterministic()` → `aggregate_deterministic_matrix()` (`pipeline.py` 194–220)
- v2: `score_deterministic_v2()` → `aggregate_deterministic_matrix_v2()` (`pipeline.py` 223–254)
- Router: `score_for_model()` (`pipeline.py` 257–270)

**Diff versioning**
- Per-section: `disclosure_change_score` (v1) in `section_diffs`; `disclosure_change_score_v2` in `section_diffs_v2` (`pipeline.py` 171–175)
- v2 aggregation uses `section_diffs_v2` when non-empty (`deterministic_scoring.py` 746)

**Stale doc artifacts**
- Built HTML still contains old `docs/validation/evidence-and-limitations.md` (v1 default) — source file removed; active claims are in `docs/getting-started/evidence.md`
- `docs/methodology/aggregation.md` example JSON still shows `text_metrics_v2` / `deterministic_scoring_v1` (lines 208–209) — historical v1 spec, not current runtime

---

### Provenance audit

**HTTP `include=provenance`**
- Matrix/panel: `shape_matrix_scores(..., include_provenance=...)` strips provenance unless requested (`helpers.py` 95–103). Tier `analyst` includes it (`shapes.py` 13).

**What provenance contains (v2)**
- **Good:** v2-overridden components (`legal`, `liquidity`, `internal_controls`, calibrated `risk_factor_intensity`) use `source: "deterministic_v2"` with `blend_evidence` inputs including `section`, `raw_value`, `reason` (`deterministic_scoring.py` 714–727, 494–605).
- **Good:** Calibration provenance nested under `negative_word_ratio` / `uncertainty_word_ratio` via `calibration_provenance()` (`deterministic_scoring.py` 782–785).
- **Gap:** Unchanged v1-derived components (`mdna_uncertainty`, `boilerplate`, `tone_negativity`, `specificity`, `event_severity`) keep `source: "deterministic"` and v1-style flat inputs — still accurate for those formulas but **mixed sources in one response**.
- **Gap:** `event_severity_score` provenance shows v1 `diff_1a` even when `disclosure_change_score` was recomputed from v2 diffs.
- **Gap:** `confidence_score` has no provenance / `confidence_details` in API or `FilingScoreResult.to_dict()`.
- **Gap:** `cybersecurity_incident_risk_score` / `event_materiality_score` provenance appended only when non-null (`deterministic_scoring.py` 826–851) — correct, but not in headline weights (`scoring_types.py` 4–14).

**CLI**
- `FilingScoreResult.to_dict()` always includes full provenance (`pipeline.py` 86) — no `include=` gate.

---

### Test coverage notes

**Execution status:** `pytest` failed in this environment (system Python 3.9 incompatible with `float | None` syntax; Python 3.11 hit numpy/sklearn import error). **No measured coverage %** — review below is from test source inspection.

| Module | Test file | Strengths | Gaps |
|--------|-----------|-----------|------|
| `text_metrics.py` | `tests/test_text_metrics.py` | Ratios, flags, MD&A density, 8-K section list, dictionary v3 | No `compute_metric_families()` |
| `diff_engine.py` | `tests/test_diff_engine.py` | v1/v2 scores, alignment, numeric changes, missing prior → null | No embedding-backend matrix; sklearn path only |
| `deterministic_scoring.py` | `tests/test_deterministic_scoring.py` | Null-not-zero, coverage math, v1/v2 flag paths, split aggregates, custom config | No `section_diffs_v2` → component wiring; no calibration integration; v2 tests don't pass `section_diffs_v2` |
| `confidence.py` | `tests/test_confidence.py` | Penalty unit tests | **No pipeline integration** (warnings never wired) |
| `pipeline.py` | `tests/test_pipeline.py`, API tests | `filter_metrics_result`, panel errors, matrix section filter | No `required_sections_present` / warnings propagation; no form_type parity across surfaces |

**Additional test files (adjacent):** `tests/test_calibration.py` (calibration module), `tests/test_api_matrix_tiers.py` (P0-1 fix), `tests/test_validation_report_versions.py` (empty `COMMITTED_REPORTS` only).

**Recommended new tests (audit suggestions only)**
1. Pipeline: warnings on sections → lower `confidence_score` vs clean extraction.
2. HTTP matrix 10-Q: assert `score_for_model` receives `form_type="10-Q"` (mock).
3. MCP `score_filing_html_tool` 10-Q: scores match CLI for same HTML.
4. v2: `section_diffs_v2` changes `disclosure_change_score` vs v1 diffs only.
5. `filter_metrics_result`: confidence recalculated from filtered conf lists.
6. `build_versions()` includes `dictionary_version`.

---

### Docs vs code (overclaims)

| Doc claim | Code reality |
|-----------|--------------|
| `overview.md`: "CLI, Python SDK, HTTP API, and MCP all call this same pipeline" | **Partially true** — shared `compute_section_metrics` + `score_for_model`, but HTTP/MCP omit `form_type` and MCP rescoring diverges |
| `overview.md` / `aggregation.md`: confidence blends extraction, diff, coverage with penalties for warnings/missing sections | Penalties implemented in `confidence.py` but **not fed** from pipeline |
| `versioning.md`: dictionary version in every response | **Missing** from `build_versions()` and examples (`docs/examples/score-minimal-10k.json` 311–316) |
| `scope-and-claims.md`: reproducible given same artifact versions including dictionary | Dictionary version not returned in score JSON |
| `evidence.md`: vol Q5/Q1 ≈ 1.15, n=435 | L3 report: 1.12, n=497 |
| `aggregation.md` 294: v1 `disclosure_change_score` unchanged | v2 **aggregation** replaces component using `section_diffs_v2` when present |
| Improvement plan P0-2 stale `text_metrics_v1` in L3 | Current L3 report uses `text_metrics_v3` — **resolved** for committed file; CI check still disabled |

---

AUDIT ONLY — no code changes were made. Switch to Agent mode if you want fixes prioritized (I'd start with pipeline confidence wiring + `form_type` on HTTP/MCP scoring).
