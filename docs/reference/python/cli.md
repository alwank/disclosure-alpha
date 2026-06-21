# cli

**Use when:** You want terminal access to extraction, metrics, or full scoring without writing Python — ideal for scripts, CI, and quick checks.

## Start here

- **`disclosure-alpha score`** — full pipeline → deterministic scores (HTML or EDGAR ticker)
- **`disclosure-alpha extract`** — section extraction only
- **`disclosure-alpha metrics`** — extract + compute section metrics (optional `--prior-html`)

All commands print JSON to stdout. Full flag reference: {doc}`../../guides/cli/index`.

## Example

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K \
  | jq '.scores.overall_disclosure_risk_score'
disclosure-alpha extract --html filing.html --form 10-K
```

## Full API

```{eval-rst}
.. automodule:: disclosure_alpha.cli
   :members: main
```
