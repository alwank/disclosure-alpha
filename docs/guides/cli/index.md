# CLI Guide

The `disclosure-alpha` CLI runs extract, metrics, and score commands against local HTML or live SEC EDGAR filings. All commands print **JSON** to stdout.

**Prerequisites:** {doc}`../../getting-started/installation`; {doc}`../../getting-started/sec-edgar-setup` for `--ticker`.

## Commands

| Command | Description |
|---------|-------------|
| `extract` | Parse HTML → section list with word counts |
| `metrics` | Extract + compute text metrics and diffs |
| `score` | Full pipeline → deterministic component scores |

## extract

```bash
disclosure-alpha extract --html filing.html --form 10-K
disclosure-alpha extract --html - --form 10-Q   # stdin
```

## metrics

```bash
disclosure-alpha metrics --html current.html --form 10-K
disclosure-alpha metrics --html current.html --form 10-K --prior-html prior.html
```

## score

**Local HTML:**

```bash
disclosure-alpha score --html filing.html --form 10-K
disclosure-alpha score --html current.html --form 10-K --prior-html prior.html
```

**By ticker** (requires `SEC_USER_AGENT`):

```bash
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K
disclosure-alpha score --ticker MSFT --fiscal-year 2025 --form 10-Q --quarter Q2
```

### score flags

| Flag | Description |
|------|-------------|
| `--html` | Path to HTML file or `-` for stdin |
| `--ticker` | Ticker symbol (fetches from EDGAR) |
| `--form` | `10-K` or `10-Q` (default `10-K`) |
| `--fiscal-year` | Required with `--ticker` |
| `--quarter` | `Q1`, `Q2`, or `Q3` — required for 10-Q |
| `--prior-html` | Prior filing HTML for section diffs |

## Output shape

`score` returns a JSON object with `overall_disclosure_risk_score`, `components`, `confidence_score`, `score_coverage_ratio`, and `missing_components`. Pipe to `jq` for filtering:

```bash
disclosure-alpha score --ticker AAPL --fiscal-year 2025 | jq '.scores.overall_disclosure_risk_score'
```

## Related

- {doc}`../../getting-started/quickstart-cli`
- {doc}`../../getting-started/concepts`
- {doc}`../python/index`
