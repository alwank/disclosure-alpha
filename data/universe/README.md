# Universe lists for validation cohorts

## S&P 500 (`sp500.csv`)

Checked-in reference list (**503** constituents). Current validated analysis cohort: **425** FY2025 Item 1A extractions (~84%). See [data/validation/README.md](../validation/README.md) for manifest failures and [Evidence & limitations](https://disclosure-alpha.readthedocs.io/en/stable/validation/evidence-and-limitations.html) for supported claims.

Refresh from Wikipedia:

```bash
python scripts/fetch_sp500_universe.py
```

Columns: `ticker`, `cik`, `company_name`, `as_of_date`

Tickers use SEC-style hyphenation (e.g. `BRK-B` not `BRK.B`).

## Build L2 corpus from EDGAR

Requires `SEC_USER_AGENT`:

```bash
export SEC_USER_AGENT="YourName your@email.com"

python scripts/build_validation_corpus_from_edgar.py \
  --fiscal-year 2025 \
  --resume
```

Output: `data/validation/corpus/sp500_item1a.jsonl` (gitignored).

Use `--limit 10` for a smoke test. Full run takes ~1 hour at SEC rate limits.

## Build from local HTML

```bash
python scripts/build_validation_corpus.py \
  --html-dir ./my_sp500_html \
  --universe data/universe/sp500.csv
```
