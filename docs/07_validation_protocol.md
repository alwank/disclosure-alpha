# 07 - Automated Validation Protocol

Automated validation for deterministic scoring before marketing as "research-backed" or
"calibrated."

## Validation Levels

| Level | Name | Requirement |
|-------|------|-------------|
| L0 | Structural | Unit tests pass; deterministic replay identical |
| L1 | Parser regression | Static and synthetic fixture extraction tests pass |
| L2 | Construct validity | Correlations with literature proxies or external datasets |
| L3 | Predictive monotonicity | Quintile sorts on outcome variables |
| L4 | Production gates | Automated thresholds below met on SP100 |

**MVP launch (deterministic free tier):** L0 + L1.  
**"Validated" marketing claim:** L0-L4.

## L0 - Structural Tests

Existing: `tests/test_deterministic_scoring.py`, `tests/test_diff_engine.py`,
`tests/test_section_extractor.py`.

```bash
python3.11 -m pytest -q
```

Required assertions:

| Test | Assertion |
|------|-----------|
| Replay determinism | Same metrics dict -> identical aggregation output |
| Missing diff null | No prior -> `disclosure_change_score is None`, not 0 |
| Flag boost cap | Boosted component <= 100 |
| Coverage math | Missing components reduce coverage |

## L1 - Parser Regression

Parser quality is enforced through deterministic fixtures, not label files.

| Fixture type | Requirement |
|--------------|-------------|
| Synthetic TOC | TOC entries suppressed when body headings exist |
| Synthetic forms | 10-K, 10-Q, and 8-K section maps route correctly |
| Static filings | Expected section names are asserted in code |
| Confidence | Normal real-filing sections avoid low-confidence output |

Static filing fixtures live under `tests/fixtures/filings/`. Expectations live in tests,
not in external `labels.json` files.

## L2 - Construct Validity

Run on SP100 latest 10-K per company.

| Pair | Target |
|------|--------|
| MVP `negative_word_ratio` vs licensed LM negative % | Spearman rho >= 0.85 |
| MVP `uncertainty_word_ratio` vs licensed LM uncertainty % | Spearman rho >= 0.80 |
| `company_specificity_score` vs NER entity density | Spearman rho >= 0.60 |
| `boilerplate_phrase_ratio` vs cross-firm 4-gram boilerplate | Spearman rho >= 0.50 |

Future script: `scripts/validate_deterministic_construct.py`.

## L3 - Predictive Monotonicity

Not alpha / return forecasting. Test whether higher scores associate with adverse outcome
families used in the literature.

| Outcome | Sort | Expected direction |
|---------|------|--------------------|
| Realized volatility 90d post filing | deterministic overall quintiles | Q5 > Q1 |
| Absolute next-quarter earnings surprise | disclosure change quintiles | Q5 > Q1 |
| Known material weakness disclosures | material weakness flag | precision >= 0.70 |
| Going-concern audit opinions | going concern flag | recall >= 0.50 |

Future script: `scripts/validate_deterministic_outcomes.py`.

## L4 - Production Gates

| Gate | Metric | Threshold |
|------|--------|-----------|
| D1 | Structural test pass rate | 100% |
| D2 | Parser regression pass rate | 100% |
| D3 | LM correlation, negative | rho >= 0.85 |
| D4 | Volatility monotonicity | Q5/Q1 ratio > 1.1 |
| D5 | Change score -> earnings surprise | Q5/Q1 > 1.05 |
| D6 | Material weakness flag precision | >= 0.70 |
| D7 | Score replay across runs | 100% identical |
| D8 | Coverage on SP100 10-K | median coverage >= 0.85 |

Report in: `data/validation/reports/deterministic_validation_report.json`.

## Regression on Version Upgrades

When bumping `PARSER_VERSION`, `METRICS_ENGINE_VERSION`, or scoring weights:

1. Re-run the full unit suite.
2. Re-run parser regression fixtures.
3. Re-run construct and outcome validation when those scripts exist.
4. Document the version delta in the validation report changelog.

## External Claims

Allowed after L0 + L1:

> "Deterministic scores are computed from reproducible text metrics and filing diffs."

Allowed after L4:

> "Component scores show significant association with post-filing volatility and disclosure
> change patterns consistent with peer-reviewed textual analysis literature."

Not allowed:

> "Scores predict stock returns" or "validated trading strategy."
