# L2 Construct Validity — S&P 500 Corpus

Default validation universe is **S&P 500** latest 10-K Item 1A per company.

Universe reference: [data/universe/sp500.csv](../universe/sp500.csv) (~503 tickers).

## Option A — Build from EDGAR (recommended)

```bash
export SEC_USER_AGENT="YourName your@email.com"

# Refresh universe list (optional)
python scripts/fetch_sp500_universe.py

# Build corpus (~500 filings; use --resume to continue)
python scripts/build_validation_corpus_from_edgar.py --fiscal-year 2025 --resume

# Run L2 validation
python scripts/validate_deterministic_construct.py
```

Smoke test:

```bash
python scripts/build_validation_corpus_from_edgar.py --fiscal-year 2025 --limit 5
```

The EDGAR build script writes a manifest alongside the corpus:
`data/validation/corpus/sp500_item1a.manifest.json` (fetch failures by ticker/reason).

Targeted retry after parser fixes (re-fetches manifest failures + filter drops only):

```bash
python scripts/build_validation_corpus_from_edgar.py \
  --fiscal-year 2025 \
  --retry-failures \
  --validation-report data/validation/reports/deterministic_validation_report.json

python scripts/audit_validation_corpus.py
```

## Option B — Local HTML files

```bash
python scripts/build_validation_corpus.py \
  --html-dir ./my_sp500_html \
  --universe data/universe/sp500.csv
```

Expected layout: `{html_dir}/{TICKER}_10k.html` or any `*.html` with ticker from filename prefix.

## Corpus format (JSONL)

Output path (gitignored): `data/validation/corpus/sp500_item1a.jsonl`

```json
{
  "ticker": "AAPL",
  "fiscal_year": 2025,
  "section_name": "item_1a_risk_factors",
  "cleaned_text": "...",
  "word_count": 8420,
  "extraction_confidence": 0.92,
  "extraction_method": "heading_boundary_fallback_merged",
  "warnings": ["open_ended_boundary"],
  "quality_tier": "analysis",
  "accession_number": "optional",
  "cik": "0000320193"
}
```

### Filters (default)

- `section_name` must be `item_1a_risk_factors`
- `word_count >= 200`
- `extraction_confidence >= 0.75` when present
- Recommended cohort `n >= 80` for stable Spearman estimates (target ~500)

The validation report includes `filter_breakdown` (skip reasons) and
`filtered_tickers_sample` for diagnosing filter drops.

### Optional holdout

`data/validation/holdout_tickers.txt` — one ticker per line, excluded from pass/fail headline.

## Run L2 validation

```bash
pip install -e ".[validation,dev]"
python -m spacy download en_core_web_sm

python scripts/validate_deterministic_construct.py \
  --corpus data/validation/corpus/sp500_item1a.jsonl \
  --universe data/universe/sp500.csv
```

Dev / CI mini corpus:

```bash
python scripts/validate_deterministic_construct.py \
  --corpus tests/fixtures/validation/mini_corpus.jsonl \
  --min-n 3 --boilerplate-min-docs 2
```

## Dictionary distribution shift (v2+)

After dictionary or matching changes, compare metrics and component scores against the frozen baseline:

```bash
# First time (or after accepted engine change): refresh baseline
python scripts/validate_dictionary_shift.py --write-baseline

# Compare current engine to committed baseline
python scripts/validate_dictionary_shift.py
```

Baseline: `data/validation/baselines/dictionary_shift_baseline.json`  
Report: `data/validation/reports/dictionary_shift_report.json`  
Gate: component score shift > 5 points on ≤ 5% of corpus (428-firm cohort).

CI runs the compare step as a non-blocking check.

## L2 results

### Achieved status (FY2025, accepted MVP)

| Metric | Value |
|--------|-------|
| Universe | 503 |
| Fetched / analysis cohort | **436** fetched / **428** analysis (~85%) |
| `construct_pass` | **true** |
| `edgar_pass` | **false** |
| `overall_l2_pass` | **false** (accepted for MVP) |

| Gate / pair | Protocol | Achieved | Status |
|-------------|----------|----------|--------|
| E1 fetch rate | >= 0.90 | 0.87 (436/503) | fail |
| E2 analysis rate | >= 0.85 | 0.85 (428/503) | pass |
| E3 filter retention | >= 0.85 | 0.98 (428/436) | pass |
| E4 median confidence | >= 0.75 | 0.95 | pass |
| E5 min analysis n | >= 80 | 428 | pass |
| `specificity_vs_ner` | rho >= 0.60 | rho 0.84 (n=428) | pass |
| `boilerplate_vs_ls4gram` | rho >= 0.50 | rho 0.69 (n=428) | pass |

Re-run `scripts/audit_validation_corpus.py` after corpus changes to refresh figures.

### Protocol targets (aspirational)

| Result | Meaning |
|--------|---------|
| `edgar_pass` | EDGAR coverage gates E1–E5 |
| `construct_pass` | NER + boilerplate Spearman thresholds |
| `overall_l2_pass` | both pass |

| Pair | Spearman rho |
|------|------------|
| `company_specificity_score` vs NER entity density | >= 0.60 |
| `boilerplate_phrase_ratio` vs cross-firm 4-gram | >= 0.50 |

| Gate | Metric | Threshold |
|------|--------|-----------|
| E1 | fetch rate (corpus rows / universe) | >= 0.90 |
| E2 | analysis rate (post-filter / universe) | >= 0.85 |
| E3 | filter retention (post-filter / input) | >= 0.85 |
| E4 | median extraction confidence | >= 0.75 |
| E5 | min analysis cohort size | >= 80 |

### Known gaps

**14 manifest failures** (not in corpus): ALB, CLX, DASH, DVN, FDXF, HAL, IBKR, ICE, MCD, MO, MS, SATS, SWKS, TSLA (FDXF = `filing_not_found`; rest = `no_item_1a`).

Diagnose: `python scripts/diagnose_item1a.py`  
Retry: `--retry-failures` on the EDGAR build script (optional; not required for current MVP claims).

See [Evidence & limitations](https://disclosure-alpha.readthedocs.io/en/latest/validation/evidence-and-limitations.html).

## L3 outcomes (OpenBB + yfinance)

Post-filing outcome variables for predictive monotonicity (L3). Requires a running
[OpenBB Platform API](https://docs.openbb.co/) (default `http://127.0.0.1:6900`) for
90-day realized volatility via `equity/price/historical` (`provider=yfinance`).
Next-quarter earnings surprise uses **yfinance** directly (quarterly estimate vs reported).

```bash
export SEC_USER_AGENT="YourName your@email.com"
export OPENBB_API_URL="http://127.0.0.1:6900"   # optional if default

pip install -e ".[outcomes]"

# Smoke test (3 tickers)
python scripts/fetch_validation_outcomes.py \
  --corpus data/validation/corpus/sp500_item1a.jsonl \
  --limit 3

# Full cohort (slow: EDGAR filing_date resolve + OpenBB + yfinance per ticker)
python scripts/fetch_validation_outcomes.py
```

Output: `data/validation/outcomes/sp500_outcomes.jsonl` (gitignored).

Each row includes `realized_vol_90d`, `earnings_surprise_abs`, sources, and `errors`.
Rebuild corpus with `filing_date` embedded (re-run EDGAR build) to skip per-row EDGAR lookups.

FMP free-tier limits apply to OpenBB estimate routes; this pipeline does **not** require FMP.

### Run L3 gates (after outcomes fetch)

Default corpus mode (MVP canonical vol claim):

```bash
python scripts/validate_deterministic_outcomes.py
```

Uses corpus Item 1A scores (fast) for **volatility vs overall** quintile gate.
`disclosure_change_score` gate is skipped in corpus mode (no prior-year diff); use
`--score-mode edgar` for full 10-K + prior scoring (slow, needs SEC cache).

Optional robustness run (FY2024 EDGAR — **completed**; earnings gate failed):

```bash
python scripts/fetch_validation_outcomes.py \
  --universe data/universe/sp500.csv \
  --fiscal-year 2024

python scripts/validate_deterministic_outcomes.py \
  --fiscal-year 2024 \
  --score-mode edgar
```

Reports:
- FY2025 corpus: `data/validation/reports/l3_outcomes_report.json`
- FY2025 EDGAR: `data/validation/reports/l3_outcomes_report_edgar.json`
- FY2024 EDGAR robustness: `data/validation/reports/l3_outcomes_report_edgar_fy2024.json`

### L3 achieved (partial, accepted MVP — vol only)

L3 validation **closed for MVP**. External vol claim uses FY2025 corpus only (Q5/Q1 ~1.11).

**Cohort note:** L2 construct validity uses **428** post-filter Item 1A rows (`deterministic_validation_report.json`). L3 volatility monotonicity uses **435** tickers with valid vol outcomes (`l3_outcomes_report.json`) — a separate pairing cohort, not the L2 analysis count.

| Gate | FY2025 corpus | FY2025 EDGAR | FY2024 EDGAR | MVP status |
|------|---------------|--------------|--------------|------------|
| Volatility vs overall score | **pass** Q5/Q1 1.11 n=435 | **pass** Q5/Q1 1.10 n=435 | pass Q5/Q1 1.005 n=499 | **claim corpus only** |
| Earnings vs change score | skipped (no prior) | skipped n=14 | **fail** Q5/Q1 0.54 n=490 | **do not claim** |
| ICW / GCO flags | not run | not run | not run | **deferred** |

See [Evidence & limitations](https://disclosure-alpha.readthedocs.io/en/latest/validation/evidence-and-limitations.html) for supported outcome claims.
