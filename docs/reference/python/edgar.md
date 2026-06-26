# edgar

**Use when:** You need to resolve tickers to CIKs, list filings, fetch HTML from SEC EDGAR, or locate prior comparable filings for diffs.

## Start here

- **`resolve_filing_with_prior()`** — resolve current + prior filing in one submissions fetch (used by the pipeline)
- **`resolve_filing_targets()`** — batch-resolve multiple fiscal-year targets in one scan
- **`resolve_filing()`** — resolve ticker + fiscal year + form to a `FilingRef`
- **`resolve_prior_filing()`** — find the prior comparable filing for diffs
- **`load_filing_html()`** — download (or read from cache) filing HTML
- **`resolve_cik()`** / **`list_filings()`** — ticker lookup and filing index
- **`fetch_json()`** / **`fetch_text()`** — low-level SEC HTTP helpers

Requires `SEC_USER_AGENT` in the environment. See {doc}`../../getting-started/sec-edgar-setup`.

## Example

```python
import os
os.environ["SEC_USER_AGENT"] = "YourName your@email.com"

from disclosure_alpha.edgar.resolver import resolve_filing_with_prior, load_filing_html

current, prior = resolve_filing_with_prior("AAPL", fiscal_year=2025, form_type="10-K")
html = load_filing_html(current)
```

## Full API

```{eval-rst}
.. automodule:: disclosure_alpha.edgar.resolver
   :members: resolve_filing, resolve_filing_with_prior, resolve_filing_targets, resolve_prior_filing, load_filing_html, resolve_cik, list_filings
.. automodule:: disclosure_alpha.edgar.client
   :members: fetch_json, fetch_text, fetch_text_prefix, fetch_company_tickers
```
