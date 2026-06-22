# Analytics and Scoring Layer Improvement Plan

Cursor agent brief for addressing the analytics and deterministic scoring audit.

This plan is intentionally implementation-oriented. Each work item includes the problem, target files, recommended change, tests, acceptance criteria, and sequencing notes. Do not implement every item in one PR. Start with P0/P1 correctness and validation work, then move into scoring model version changes.

## Guardrails

- Preserve deterministic behavior unless a work item explicitly introduces a new versioned model.
- Do not change `deterministic_scoring_v1` semantics silently. If score formulas change, introduce a new scoring version such as `deterministic_scoring_v2`.
- Keep provenance complete. Any new component or calibration transform must expose raw inputs, normalized inputs, and reason codes.
- Keep conditional null semantics. Missing required evidence should produce `None`, not synthetic zero, unless a flag-only evidence rule explicitly supports a non-null component.
- Add tests before broad refactors.
- Regenerate or update docs/examples only after code behavior is settled.

## Recommended Sequence

1. P0-1: Fix section-filter scoring mismatch.
2. P0-2: Refresh validation version hygiene and stale report handling.
3. P1-1: Add component evidence model and section-specific inputs.
4. P1-2: Add improved confidence model.
5. P1-3: Introduce calibrated scoring v2 behind a versioned entry point.
6. P2-1: Upgrade diff engine.
7. P2-2: Add full-matrix validation corpus and gates.
8. P2-3: Split score products and add sector/form baselines.
9. P2-4: Add cyber and 8-K event scoring.

## P0-1: Fix Matrix `sections=` Scoring Mismatch

### Problem

`GET /v1/company/{ticker}/disclosure-matrix?sections=...` filters metrics after scoring. The response can show filtered metrics but unfiltered filing-level scores, which is misleading.

Current path:

- `src/disclosure_alpha/api/endpoints/matrix.py`
- `disclosure_matrix()` computes `scores = score_deterministic(result.metrics)` before applying `filter_metrics_result()`.

### Target Files

- `src/disclosure_alpha/api/endpoints/matrix.py`
- `tests/test_api_matrix_tiers.py` or `tests/test_api.py`
- `docs/guides/http/index.md`
- `docs/reference/http/endpoints.md` if generated manually or via script

### Implementation Plan

1. Decide response semantics:
   - Recommended: if `sections=` is supplied, compute scores from filtered metrics.
   - Alternative: always return filing-level scores and add `score_scope: "filing"` metadata. This requires a response shape change, so prefer filtered scoring for now.
2. In `disclosure_matrix()`:
   - Fetch metrics.
   - If `section_filter` exists, call `filter_metrics_result()` before both scoring and metrics serialization.
   - Compute `scores = score_deterministic(metrics_for_scope)`.
3. Add a test that mocks a metrics result containing Item 1A and MD&A:
   - Request only `sections=item_1a_risk_factors`.
   - Assert MD&A-derived components are missing or null.
   - Assert returned metrics only include Item 1A.
4. Add a doc note:
   - `sections=` changes both metrics and computed scores for matrix responses.
   - Panel endpoint has no section filter unless added later.

### Acceptance Criteria

- A section-filtered matrix request scores only the selected sections.
- `score_coverage_ratio` and `missing_components` reflect filtered evidence.
- Existing unfiltered matrix behavior remains unchanged.
- Tests cover filtered and unfiltered responses.

## P0-2: Fix Validation Version Hygiene

### Problem

Validation docs and reports are not fully aligned:

- L2 report uses `text_metrics_v2`.
- Some L3 reports still record `text_metrics_v1`.
- L2 construct pairs pass, but `overall_l2_pass` is false because EDGAR gate values are missing.
- Public evidence should clearly distinguish construct validity, EDGAR gate pass/fail, and outcome association.

### Target Files

- `data/validation/reports/*.json`
- `docs/validation/evidence-and-limitations.md`
- `scripts/validate_deterministic_outcomes.py`
- `src/disclosure_alpha/validation/outcomes_validation.py`
- `src/disclosure_alpha/validation/construct.py`
- `tests/test_construct_validity.py`
- `tests/test_outcomes.py`

### Implementation Plan

1. Inspect why L3 reports record `text_metrics_v1`.
   - Confirm `src/disclosure_alpha/version.py` current values.
   - Re-run outcome validation after version update if data files exist locally.
2. Add a report freshness check:
   - Validation report versions should match runtime artifact constants.
   - Add a small test or script mode that fails if committed reports are stale.
3. Improve report status fields:
   - Add explicit `construct_pairs_pass`.
   - Add explicit `edgar_gates_pass`.
   - Add explicit `outcome_gates_pass`.
   - Avoid presenting `overall_l2_pass=false` as a contradiction when construct pairs passed.
4. Update docs:
   - State that current evidence is Item 1A construct validity plus limited volatility association.
   - State full multi-section matrix validation is not yet complete.
5. Add a `--check-versions` option to validation scripts or a standalone helper.

### Acceptance Criteria

- Committed validation reports do not claim stale metric/scoring versions.
- Docs distinguish what passed from what failed or was skipped.
- CI can detect stale validation reports without network access.
- Public claims remain conservative and reproducible.

## P1-1: Add Component Evidence Model and Section-Specific Inputs

### Problem

Several component scores depend on broad Item 1A or MD&A metrics even when direct evidence exists in more relevant sections.

Examples:

- `internal_controls_risk_score` uses controls diff but falls back to Item 1A constraining language.
- `legal_regulatory_risk_score` requires Item 1A metrics even when Item 3 or 10-Q Item 1 legal flags exist.
- `liquidity_stress_score` requires MD&A metrics even when going concern or covenant flags exist elsewhere.
- Direct flags can fail to create non-null scores when base metrics are missing.

### Target Files

- `src/disclosure_alpha/deterministic_scoring.py`
- `src/disclosure_alpha/scoring_types.py`
- `src/disclosure_alpha/pipeline.py`
- `tests/test_deterministic_scoring.py`
- `docs/methodology/aggregation.md`
- `docs/reference/score-catalog.md`

### Implementation Plan

1. Introduce a small internal evidence representation:

```python
@dataclass
class ScoreEvidence:
    name: str
    value: float | None
    weight: float
    section: str | None = None
    raw_value: float | bool | None = None
    reason: str = ""
```

2. Add a helper:

```python
def blend_evidence(evidence: list[ScoreEvidence]) -> tuple[float | None, dict[str, Any]]:
    ...
```

3. Refactor one component at a time:
   - Start with `internal_controls_risk_score`.
   - Then `legal_regulatory_risk_score`.
   - Then `liquidity_stress_score`.
4. For each component, use direct section metrics first:
   - Controls: `item_9a_controls`, `item_4_controls`.
   - Legal: `item_3_legal_proceedings`, `item_1_legal_proceedings`, plus Item 1A.
   - Liquidity: MD&A plus Item 1A.
5. Allow serious flags to create non-null evidence:
   - Material weakness/restatement/ineffective controls.
   - Going concern/covenant breach.
   - Investigation/material legal proceeding.
6. Preserve v1 behavior until ready for a new scoring version:
   - Either introduce `aggregate_deterministic_matrix_v2()`.
   - Or gate new logic behind `model_version="deterministic_scoring_v2"`.

### Acceptance Criteria

- A material weakness flag in Item 9A can produce a non-null controls score even if Item 1A is missing.
- A legal flag in Item 3 can produce a non-null legal score even if Item 1A is missing.
- A going concern flag can produce a non-null liquidity score when relevant source text exists.
- Provenance shows section, raw input, normalized input, and reason.
- Existing v1 tests still pass or are explicitly versioned.

## P1-2: Improve Confidence Scoring

### Problem

`compute_overall_confidence()` averages extraction confidence, score coverage, and diff confidence. It does not account for extraction warnings, short sections, missing required sections, fallback extraction methods, missing prior filing, or section-level score importance.

### Target Files

- `src/disclosure_alpha/confidence.py`
- `src/disclosure_alpha/pipeline.py`
- `src/disclosure_alpha/section_extractor.py`
- `tests/test_confidence.py`
- `tests/test_pipeline.py`
- `docs/methodology/aggregation.md`

### Implementation Plan

1. Add a richer confidence input dataclass:

```python
@dataclass
class ConfidenceInput:
    extraction_confidences: list[float]
    extraction_warnings: list[str]
    coverage_ratio: float
    required_sections_present: bool
    diff_confidence: float | None = None
    has_prior: bool = False
```

2. Keep the current function as a backward-compatible wrapper.
3. Add penalties:
   - `missing_required_section`: strong penalty.
   - `short_section`, `extraction_suspect`, `last_resort_extraction`: moderate penalty.
   - No prior filing when change components are expected: moderate penalty.
   - Coverage below 0.75: nonlinear penalty.
4. Make confidence provenance visible:
   - Add optional `confidence_details` to result shape if feasible.
   - If response shape changes are too large, expose in provenance first.
5. Update `score_deterministic()` to pass warnings from extracted sections. If that requires larger plumbing, add a new `score_deterministic_with_context()` and migrate endpoints gradually.

### Acceptance Criteria

- Low extraction confidence plus warning-heavy extraction yields lower confidence than clean extraction with same score coverage.
- Missing required sections reduce confidence.
- No prior filing reduces confidence for change-heavy score requests.
- Existing confidence bounds remain 0-1.

## P1-3: Add Calibrated Scoring V2

### Problem

Current component scores blend raw ratios and heuristic scores directly. A `negative_word_ratio * 100` of 3 is treated as a score of 3 even if that is sector-extreme. This makes score levels difficult to compare across sectors, years, and form types.

### Target Files

- New: `src/disclosure_alpha/calibration.py`
- `src/disclosure_alpha/deterministic_scoring.py`
- `src/disclosure_alpha/scoring_types.py`
- `src/disclosure_alpha/version.py`
- `tests/test_deterministic_scoring.py`
- New: `tests/test_calibration.py`
- `docs/methodology/aggregation.md`
- `docs/reference/versioning.md`
- `docs/reference/score-catalog.md`

### Implementation Plan

1. Introduce calibration transforms:
   - Percentile rank.
   - Robust z-score.
   - Winsorized min-max.
2. Start with built-in default calibration tables generated from the existing validation corpus.
   - If no table is available, fall back to transparent v1 scaling and mark `calibration_status="fallback"`.
3. Add a data structure:

```python
@dataclass
class CalibrationContext:
    form_type: str = "10-K"
    sector: str | None = None
    fiscal_year: int | None = None
```

4. Add raw-to-calibrated mapping:

```python
calibrate_metric("negative_word_ratio", raw_value, context) -> CalibratedValue
```

5. Use calibrated metrics in v2 component blends:
   - Tone ratios.
   - Specificity proxies.
   - Boilerplate ratio.
   - MD&A density.
   - Readability.
6. Update provenance:
   - `raw_value`
   - `calibrated_value`
   - `calibration_reference`
   - `calibration_status`
7. Introduce `SCORING_MODEL_VERSION = "deterministic_scoring_v2"` only when endpoints intentionally switch. Until then expose a separate function for experiments.

### Acceptance Criteria

- Calibration functions are deterministic and unit-tested.
- Scores can be reproduced with committed calibration references.
- v1 output remains available or migration is documented.
- Provenance explains every calibration transform.

## P2-1: Upgrade Diff Engine with Sentence/Paragraph Alignment

### Problem

The diff engine uses document-level lexical/semantic similarity, length growth, and topic counts. It does not identify exact added risk language, numeric changes, materiality terms, or benign rewrites.

### Target Files

- `src/disclosure_alpha/diff_engine.py`
- `src/disclosure_alpha/text_matching.py`
- `tests/test_diff_engine.py`
- `docs/methodology/diff-engine.md`
- `docs/methodology/aggregation.md`

### Implementation Plan

1. Add sentence segmentation output:
   - Existing `split_sentences()` can be reused.
2. Align current and prior sentences:
   - Use TF-IDF cosine similarity for sentence pairs.
   - Treat unmatched current sentences as added.
   - Treat unmatched prior sentences as removed.
3. Compute added-language metrics:
   - Added negative/uncertain/litigious/constraining density.
   - Added severity words.
   - Added numeric disclosure count.
   - Added topic count.
4. Compute changed numeric disclosures:
   - Extract percentages, dollar amounts, dates, and counts.
   - Record added, removed, and changed numeric tokens.
5. Produce richer `SectionDiffResult`:
   - `added_sentence_count`
   - `removed_sentence_count`
   - `changed_numeric_count`
   - `added_risk_language_score`
   - `diff_evidence`
6. Replace or supplement the current change score:
   - Keep current score for v1.
   - Add `disclosure_change_score_v2` or version-gate the formula.

### Acceptance Criteria

- Pure reordering or minor wording changes score lower than new severe risk additions.
- New risk sentences increase change score even if document-level similarity remains high.
- Numeric disclosure changes are captured in provenance.
- Existing missing-prior behavior remains `None`.

## P2-2: Build Full-Matrix Validation Corpus and Gates

### Problem

Current validation is mostly Item 1A-oriented. The full multi-section matrix is not validated across Item 1A, MD&A, controls, legal proceedings, cybersecurity, and 10-Q/8-K sections.

### Target Files

- New or updated scripts under `scripts/`
- `src/disclosure_alpha/validation/*`
- `data/validation/README.md`
- `docs/validation/evidence-and-limitations.md`
- `tests/test_construct_validity.py`
- `tests/test_outcomes.py`

### Implementation Plan

1. Add a corpus builder for full filing matrix:
   - Store section-level extracted text and section metadata.
   - Include current and prior sections when available.
2. Store per-section quality metadata:
   - word count
   - extraction confidence
   - warnings
   - extraction method
3. Add validation gates:
   - Required-section extraction rate.
   - Median extraction confidence.
   - Component coverage by form type.
   - Score distribution sanity by sector.
   - Dictionary shift stability.
   - Outcome monotonicity where sufficient pairs exist.
4. Add a small committed fixture corpus for CI.
5. Keep large corpora optional and documented.

### Acceptance Criteria

- Validation can score the full matrix, not only Item 1A.
- Reports include component-level coverage and pass/fail gates.
- CI can run a small non-network validation smoke test.
- Public docs clearly identify which components are empirically validated.

## P2-3: Split Static Quality from Risk Change

### Problem

`overall_disclosure_risk_score` mixes static tone, boilerplate, specificity, uncertainty, controls, legal, liquidity, and year-over-year change. This makes interpretation harder.

### Target Files

- `src/disclosure_alpha/scoring_types.py`
- `src/disclosure_alpha/deterministic_scoring.py`
- `src/disclosure_alpha/api/schemas/matrix.py`
- `tests/test_deterministic_scoring.py`
- `tests/test_api.py`
- `docs/reference/score-catalog.md`
- `docs/getting-started/understanding-scores.md`

### Implementation Plan

1. Add separate aggregate scores:
   - `static_disclosure_quality_score`
   - `static_disclosure_risk_score`
   - `disclosure_change_risk_score`
   - keep `overall_disclosure_risk_score` for backward compatibility.
2. Define component membership:
   - Static risk: tone, boilerplate, MD&A uncertainty, legal, liquidity, controls.
   - Change risk: disclosure change, event severity, language deltas.
   - Quality: specificity and inverse boilerplate.
3. Decide whether `overall_disclosure_risk_score` remains weighted blend or becomes a documented composite.
4. Add provenance for aggregate construction.

### Acceptance Criteria

- Users can distinguish current disclosure quality from deterioration vs prior filing.
- Backward-compatible headline score remains unless a major version bump is planned.
- Docs explain which aggregate should be used for screening vs monitoring.

## P2-4: Add Sector/Form-Aware Baselines

### Problem

Baseline disclosure language differs heavily by sector and form type. Banks, biotech, retailers, and software companies should not be compared only on raw text ratios.

### Target Files

- New: `src/disclosure_alpha/baselines.py`
- `src/disclosure_alpha/calibration.py`
- `src/disclosure_alpha/edgar/types.py` if sector metadata is added
- `data/validation/README.md`
- `tests/test_calibration.py`
- `docs/methodology/aggregation.md`

### Implementation Plan

1. Define optional baseline keys:
   - form type
   - fiscal year
   - sector or SIC group
2. Add an API for baseline lookup:

```python
lookup_baseline(metric_name, context) -> BaselineStats | None
```

3. Add fallback hierarchy:
   - sector + form + year
   - sector + form
   - form + year
   - global form
   - no baseline fallback
4. Add baseline provenance:
   - baseline cohort
   - sample size
   - fallback level
5. Do not require sector metadata for local HTML scoring. Use global baseline when sector is unknown.

### Acceptance Criteria

- Scores are reproducible when baseline tables are present.
- Unknown sector still works with documented fallback.
- Provenance shows baseline source and sample size.

## P2-5: Add Cybersecurity and 8-K Event Scoring

### Problem

`cybersecurity_incident_flag` is computed but not used in the headline score. 8-K sections are extractable locally, but scoring is not event-specific enough for Item 1.05 and related event sections.

### Target Files

- `src/disclosure_alpha/dictionaries.py`
- `src/disclosure_alpha/text_metrics.py`
- `src/disclosure_alpha/deterministic_scoring.py`
- `src/disclosure_alpha/scoring_types.py`
- `tests/test_text_metrics.py`
- `tests/test_deterministic_scoring.py`
- `docs/reference/score-catalog.md`
- `docs/reference/section-taxonomy.md`

### Implementation Plan

1. Add component fields:
   - `cybersecurity_incident_risk_score`
   - `event_materiality_score`
2. Define evidence for cybersecurity:
   - `cybersecurity_incident_flag`
   - materiality phrases
   - outage/business interruption phrases
   - data compromise phrases
   - regulatory/customer notification phrases
3. Define evidence for 8-K event materiality:
   - Item 1.01 material agreements.
   - Item 1.05 cyber incidents.
   - Item 2.02 results.
   - Item 5.02 departures.
   - Item 8.01 other events.
4. Keep these out of the existing headline until validation exists, or add them to a v2 headline with documented weights.
5. Add tests for:
   - cyber incident in Item 1.05 produces non-null cyber score.
   - cyber governance language in Item 1C does not produce incident score.
   - 8-K local HTML score has event-specific coverage.

### Acceptance Criteria

- Cyber incident flag feeds a score, not only raw metrics.
- Governance-only cybersecurity disclosures avoid false incident elevation.
- 8-K event scoring is documented as local HTML supported unless EDGAR 8-K resolver support is added.

## P3-1: Documentation and Migration Plan for Scoring V2

### Problem

Any score formula change affects users, examples, validation reports, and versioning claims.

### Target Files

- `src/disclosure_alpha/version.py`
- `docs/reference/versioning.md`
- `docs/reference/score-catalog.md`
- `docs/methodology/aggregation.md`
- `docs/getting-started/understanding-scores.md`
- `docs/appendix/changelog.md`
- `scripts/generate_docs_examples.py`
- `tests/test_docs_examples.py`

### Implementation Plan

1. Add a clear migration note:
   - What changed.
   - Which components changed.
   - Whether score levels are comparable to v1.
2. Regenerate examples.
3. Update validation docs with new report versions.
4. Add changelog entries for every artifact version change:
   - parser
   - metrics engine
   - scoring model
   - dictionary version
5. Make docs example generation fail when examples are stale.

### Acceptance Criteria

- `scripts/generate_docs_examples.py --check` passes.
- Public docs do not mix v1 and v2 formulas.
- Users can pin old behavior or understand that v2 is a breaking score model change.

## Suggested PR Breakdown

### PR 1: Correctness Fix

- P0-1 only.
- Small API behavior fix plus tests and doc note.

### PR 2: Validation Hygiene

- P0-2 only.
- Report version checks, docs clarification, no scoring changes.

### PR 3: Evidence Model Foundation

- Add `ScoreEvidence`.
- Refactor one component, preferably controls.
- Keep public scoring version unchanged if output is equivalent.

### PR 4: Component Coverage Improvements

- Legal, liquidity, and controls flag-only evidence.
- Decide whether this becomes `deterministic_scoring_v2`.

### PR 5: Confidence Upgrade

- New confidence detail model.
- Pipeline integration.
- Tests for warning and missing-section penalties.

### PR 6: Calibration V2

- Calibration module.
- Baseline tables or fallback.
- Versioned v2 aggregation path.

### PR 7: Diff V2

- Sentence alignment.
- Added-language and numeric-change evidence.
- Optional v2 change score.

### PR 8: Full-Matrix Validation

- Full matrix corpus builder.
- Component-level gates.
- Small CI fixture.

### PR 9: Score Product Split and Event Components

- Static vs change aggregates.
- Cyber and 8-K event components.
- Docs and examples.

## Test Checklist

Run after each PR where applicable:

```bash
python3 -m pytest -q
python3 scripts/generate_docs_examples.py --check
sphinx-build -E -W -b html docs docs/_build/html
```

For validation changes:

```bash
python3 scripts/validate_deterministic_construct.py --corpus tests/fixtures/validation/mini_corpus.jsonl --out /tmp/construct_report.json --min-n 2
python3 scripts/validate_deterministic_outcomes.py --help
```

## Done Definition

The improvement program is complete when:

- Matrix `sections=` responses are internally consistent.
- Score formulas that change are versioned.
- Component scores can be produced from direct section evidence where appropriate.
- Confidence reflects coverage, warnings, missing required sections, and prior availability.
- Calibration or baseline provenance explains score levels.
- Full-matrix validation exists and separates passed, failed, and skipped gates.
- Docs and examples match the runtime artifact versions.
