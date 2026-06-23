# Universe lists

## S&P 500 (`sp500.csv`)

Checked-in reference list (**503** constituents).

Refresh from Wikipedia:

```bash
python scripts/fetch_sp500_universe.py
```

Columns: `ticker`, `cik`, `company_name`, `as_of_date`

Tickers use SEC-style hyphenation (e.g. `BRK-B` not `BRK.B`).

Supported empirical evidence uses this universe — see [Scope and claims](https://disclosure-alpha.readthedocs.io/en/latest/getting-started/scope-and-claims.html).
