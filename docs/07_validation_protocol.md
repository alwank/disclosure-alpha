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
| L4 | Production gates | Automated thresholds below met on S&P 500 |

**MVP launch (deterministic free tier):** L0 + L1 + **partial L2** + **partial L3** (vol monotonicity on ~435-firm cohort).  
**"Validated" marketing claim (full ladder):** L0-L4 (L3 requires >= 2 of 4 outcome families).

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

Run on S&P 500 latest 10-K per company. **Build the corpus** from
[data/universe/sp500.csv](../data/universe/sp500.csv) via EDGAR or local HTML. See
[data/validation/README.md](../data/validation/README.md).

L2 reports three independent outcomes:

| Result | Meaning |
|--------|---------|
| `edgar_pass` | S&P 500 ingestion + extraction quality gates |
| `construct_pass` | NER + boilerplate Spearman thresholds |
| `overall_l2_pass` | `edgar_pass AND construct_pass` |

### L2 achieved status (accepted MVP, FY2025)

**Accepted for MVP:** `construct_pass: true`, `edgar_pass: false`, `overall_l2_pass: false`.

Re-run `scripts/audit_validation_corpus.py` and validation after corpus changes to refresh figures.

Report: [data/validation/reports/deterministic_validation_report.json](../data/validation/reports/deterministic_validation_report.json)  
Manifest: [data/validation/corpus/sp500_item1a.manifest.json](../data/validation/corpus/sp500_item1a.manifest.json)

#### EDGAR gates (achieved vs protocol)

| Gate | Protocol | Achieved (FY2025) | Status |
|------|----------|-------------------|--------|
| E1 fetch rate | >= 0.90 (453/503) | 425/503 = **0.84** | fail |
| E2 analysis rate | >= 0.85 (428/503) | 425/503 = **0.84** | fail |
| E3 filter retention | >= 0.85 | 425/425 = **1.00** | pass |
| E4 median confidence | >= 0.75 | **0.95** | pass |
| E5 min analysis n | >= 80 | **425** | pass |

#### Construct pairs (achieved vs protocol)

| Pair | Protocol | Achieved (FY2025) | Status |
|------|----------|-------------------|--------|
| `specificity_vs_ner` | rho >= 0.60 | rho **0.79** (n=425) | pass |
| `boilerplate_vs_ls4gram` | rho >= 0.50 | rho **0.68** (n=425) | pass |

#### Manifest failures (14 tickers not in corpus)

| Reason | Tickers |
|--------|---------|
| `no_item_1a` (13) | ALB, CLX, DASH, DVN, HAL, IBKR, ICE, MCD, MO, MS, SATS, SWKS, TSLA |
| `filing_not_found` (1) | FDXF |

Improving E1/E2 is optional future work; not required for current MVP external claims.

### Construct pairs (protocol targets)

| Pair | Target |
|------|--------|
| `company_specificity_score` vs NER entity density | Spearman rho >= 0.60 |
| `boilerplate_phrase_ratio` vs cross-firm 4-gram boilerplate | Spearman rho >= 0.50 |

### EDGAR coverage gates (protocol targets)

| Gate | Metric | Threshold |
|------|--------|-----------|
| E1 | `fetch_rate` = corpus rows / universe | >= 0.90 |
| E2 | `analysis_rate` = post-filter rows / universe | >= 0.85 |
| E3 | `filter_retention` = post-filter / input | >= 0.85 |
| E4 | median `extraction_confidence` on analysis cohort | >= 0.75 |
| E5 | `min_analysis_n` | >= 80 |

Script: `scripts/validate_deterministic_construct.py`

NER pair reports **`skipped`** when `spacy` is not installed (`pip install -e ".[validation]"`).

```bash
export SEC_USER_AGENT="YourName your@email.com"
python scripts/build_validation_corpus_from_edgar.py --fiscal-year 2025 --resume

PYTHONUNBUFFERED=1 .venv/bin/python scripts/validate_deterministic_construct.py \
  --corpus data/validation/corpus/sp500_item1a.jsonl \
  --universe data/universe/sp500.csv \
  --out data/validation/reports/deterministic_validation_report.json
```

CI runs construct logic on `tests/fixtures/validation/mini_corpus.jsonl` via
`tests/test_construct_validity.py`.

## L3 - Predictive Monotonicity

Not alpha / return forecasting. Test whether higher scores associate with adverse outcome
families used in the literature.

| Outcome | Sort | Expected direction |
|---------|------|--------------------|
| Realized volatility 90d post filing | deterministic overall quintiles | Q5 > Q1 |
| Absolute next-quarter earnings surprise | disclosure change quintiles | Q5 > Q1 |
| Known material weakness disclosures | material weakness flag | precision >= 0.70 |
| Going-concern audit opinions | going concern flag | recall >= 0.50 |

**Protocol pass:** >= 2 of 4 tests pass ([02_research_foundation.md](./02_research_foundation.md)).

Scripts:

```bash
pip install -e ".[outcomes]"
export OPENBB_API_URL="http://127.0.0.1:6900"   # optional; default localhost
export SEC_USER_AGENT="YourName your@email.com"

python scripts/fetch_validation_outcomes.py
python scripts/validate_deterministic_outcomes.py                    # corpus / Item 1A scores
python scripts/validate_deterministic_outcomes.py --score-mode edgar # full 10-K + prior
```

### L3 achieved status (accepted partial MVP — vol only)

**Accepted for MVP:** volatility monotonicity **pass** on FY2025 corpus-scored cohort; **not** full L3 (1 of 4 gates). L3 validation chapter **closed for MVP** — no further L3 runs planned.

Re-run fetch + validate after corpus or scoring changes.

Outcomes (FY2025): [data/validation/outcomes/sp500_outcomes.jsonl](../data/validation/outcomes/sp500_outcomes.jsonl)  
Outcomes (FY2024): [data/validation/outcomes/sp500_outcomes_fy2024.jsonl](../data/validation/outcomes/sp500_outcomes_fy2024.jsonl)  
Report (FY2025 corpus): [data/validation/reports/l3_outcomes_report.json](../data/validation/reports/l3_outcomes_report.json)  
Report (FY2025 EDGAR): [data/validation/reports/l3_outcomes_report_edgar.json](../data/validation/reports/l3_outcomes_report_edgar.json)  
Report (FY2024 EDGAR robustness): [data/validation/reports/l3_outcomes_report_edgar_fy2024.json](../data/validation/reports/l3_outcomes_report_edgar_fy2024.json)

| Gate | Protocol | FY2025 corpus | FY2025 EDGAR | FY2024 EDGAR | MVP status |
|------|----------|---------------|--------------|--------------|------------|
| Volatility vs `overall_disclosure_risk_score` | Q5 > Q1 | Q5/Q1 **1.11**, n=**435** | Q5/Q1 **1.10**, n=**435** | Q5/Q1 **1.005**, n=**499** | **claim FY2025 corpus only** |
| Earnings surprise vs `disclosure_change_score` | Q5 > Q1 | skipped (no prior diff) | skipped (n=**14**; min 50) | **fail** Q5/Q1 **0.54**, n=**490** | **do not claim** |
| ICW vs `material_weakness_flag` | precision >= 0.70 | not run | not run | not run | **deferred** |
| GCO vs `going_concern_flag` | recall >= 0.50 | not run | not run | not run | **deferred** |

**EDGAR mode** uses full 10-K + prior (`score_filing_ticker`). FY2025 EDGAR vol association holds on production-style scores. FY2024 EDGAR robustness run confirmed sufficient earnings coverage (n=490 pairs); the earnings gate **failed** in the wrong direction (Q5 mean surprise below Q1) — hypothesis not supported on this cohort/measurement.

**Caveats (corpus mode):** scores use **Item 1A text only** (not full 10-K matrix). FY2024 EDGAR vol (Q5/Q1 ~1.005) is internal robustness only — too weak for external claims.

Outcome coverage (fetch): FY2025 vol **435/436**, earnings **427/436**; FY2024 vol **499/503**, earnings **494/503**.

**Deferred post-MVP:** ICW/GCO gates, earnings gate rework, strict L3 (>= 2 of 4). Next product track: L4 production gates and dictionary enrichment ([08_dictionary_enrichment_research.md](./08_dictionary_enrichment_research.md)).

## L4 - Production Gates

L4 remains future work beyond partial L3. L4 D3 still targets E2 >= 0.85 on the full S&P 500 universe.

| Gate | Metric | Threshold |
|------|--------|-----------|
| D1 | Structural test pass rate | 100% |
| D2 | Parser regression pass rate | 100% |
| D3 | EDGAR analysis cohort rate (E2) | >= 0.85 |
| D4 | Volatility monotonicity | Q5/Q1 ratio > 1.1 |
| D5 | Change score -> earnings surprise | Q5/Q1 > 1.05 |
| D6 | Material weakness flag precision | >= 0.70 |
| D7 | Score replay across runs | 100% identical |
| D8 | Coverage on S&P 500 10-K | median coverage >= 0.85 |

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

Allowed after L0 + L1 + partial L2 (current MVP):

> "Deterministic Item 1A metrics validated on **425 S&P 500 FY2025 10-Ks** (~84% of index)."
>
> "Boilerplate phrase ratio correlates with cross-firm 4-gram boilerplate reference (Spearman rho ~ 0.68)."
>
> "Company specificity correlates with NER entity density (Spearman rho ~ 0.79)."
>
> "100% filter retention on the fetched cohort; median extraction confidence 0.95."

Allowed after L0 + L1 + partial L2 + partial L3 (current):

> "Higher deterministic disclosure risk scores on our S&P 500 FY2025 cohort associate with higher **90-day post-filing realized volatility** (quintile Q5/Q1 ~ **1.11**, n ~ **435**)."
>
> Item 1A corpus scoring was used for this check; not a full production-matrix L3 pass.

Allowed after L4:

> "Component scores show significant association with post-filing volatility and disclosure
> change patterns consistent with peer-reviewed textual analysis literature."

Not allowed:

> "L2 validation passed", `overall_l2_pass`, or "validated on the S&P 500" (implies full universe).
>
> "L3 validation passed" or "fully validated on outcomes" (requires >= 2 of 4 L3 gates).
>
> Earnings surprise or `disclosure_change_score` outcome claims (FY2024 EDGAR gate **failed**, n=490).
>
> Citing FY2024 EDGAR vol (Q5/Q1 ~1.005) as validation evidence.
>
> Wording that implies the earnings gate passed or was inconclusive.
>
> "85%+ universe coverage" (current cohort is ~84%).
>
> "Scores predict stock returns", "validated trading strategy", or LM-validated tone.
