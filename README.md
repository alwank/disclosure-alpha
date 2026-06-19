# Disclosure Alpha — deterministic SEC filing analytics (open source)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Parse SEC filing HTML, compute deterministic text metrics, diff sections, and produce reproducible disclosure risk scores — no LLM required.

## Install

Requires **Python 3.11+**.

```bash
pip install -e ".[dev]"
# Self-hosted HTTP API
pip install -e ".[api,dev]"
# MCP server (Cursor / Claude Desktop)
pip install -e ".[mcp,dev]"
# Everything
pip install -e ".[api,mcp,dev]"
# Optional semantic embeddings (MiniLM; default is TF-IDF)
pip install -e ".[semantic]"
```

### SEC fair access

Live ticker lookups fetch from SEC EDGAR. Set a descriptive User-Agent:

```bash
export SEC_USER_AGENT="YourName your@email.com"
```

Optional cache directory (default `data/cache/sec_filings`):

```bash
export DISCLOSURE_ALPHA_CACHE_DIR="/path/to/cache"
```

## CLI

```bash
# From local HTML
disclosure-alpha extract --html filing.html --form 10-K
disclosure-alpha score --html filing.html --form 10-K
disclosure-alpha score --html current.html --form 10-K --prior-html prior.html

# By ticker + fiscal year (fetches from EDGAR)
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K
disclosure-alpha score --ticker MSFT --fiscal-year 2025 --form 10-Q --quarter Q2
```

## Python API

```python
from disclosure_alpha import score_filing_html, score_filing_ticker

# Local HTML
result = score_filing_html(open("filing.html").read(), "10-K")

# Ticker + fiscal year
result = score_filing_ticker("AAPL", 2025, form_type="10-K")
print(result.scores.overall_disclosure_risk_score)
print(result.to_dict())
```

## Self-hosted HTTP API

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha-api
# listens on 0.0.0.0:8000 (override with HOST / PORT env)
```

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness |
| `GET /v1/company/{ticker}/filings?fiscal_year=2025` | List 10-K / 10-Q for fiscal year |
| `GET /v1/company/{ticker}/sections?fiscal_year=2025&form_type=10-K` | Extracted sections (metadata; add `include_text=true` for body text) |
| `GET /v1/company/{ticker}/disclosure-metrics?fiscal_year=2025&form_type=10-K` | Metrics, flags, diffs (no scoring) |
| `GET /v1/company/{ticker}/disclosure-matrix?fiscal_year=2025&view=deterministic` | Deterministic scores (+ metrics by default) |

For 10-Q, add `quarter=Q1|Q2|Q3`.

**Shared query params** (`sections`, `disclosure-metrics`, `disclosure-matrix`):

| Param | Default | Description |
|-------|---------|-------------|
| `compare` | `prior` | `prior` loads prior filing for diffs; `none` skips prior comparison |
| `sections` | all | Comma-separated section names, e.g. `item_1a_risk_factors,item_7_mdna` |

**Matrix-only params:**

| Param | Default | Description |
|-------|---------|-------------|
| `include` | `metrics,provenance` | Comma-set: `metrics`, `provenance`. Empty (`include=`) → scores only |
| `fields` | all | Slim scores, e.g. `fields=overall,components` |

```bash
# Full matrix (default)
curl "http://localhost:8000/v1/company/AAPL/disclosure-matrix?fiscal_year=2025&form_type=10-K&view=deterministic"

# Scores only (no metrics blob, no provenance)
curl "http://localhost:8000/v1/company/AAPL/disclosure-matrix?fiscal_year=2025&include="

# Raw analytics without aggregation
curl "http://localhost:8000/v1/company/AAPL/disclosure-metrics?fiscal_year=2025&form_type=10-K&compare=none"

# Parser output for debugging
curl "http://localhost:8000/v1/company/AAPL/sections?fiscal_year=2025&sections=item_1a_risk_factors"
```

## MCP server

Add to Cursor MCP config:

```json
{
  "mcpServers": {
    "disclosure-alpha": {
      "command": "disclosure-alpha-mcp",
      "env": {
        "SEC_USER_AGENT": "YourName your@email.com"
      }
    }
  }
}
```

**Low-level tools:** `extract_sections`, `compute_section_metrics_tool`, `diff_sections`, `score_deterministic_tool`, `score_filing_html_tool`

**Ticker tools:** `score_company_filing`, `list_company_filings`

Resource: `disclosure://taxonomy/v1`

## Versions

| Artifact | Version |
|----------|---------|
| Parser | `section_extractor_v1` |
| Metrics | `text_metrics_v1.2` |
| Scoring | `deterministic_scoring_v3` |

## Hosted vs self-hosted

This repo includes **self-hosted** `disclosure-alpha-api` and `disclosure-alpha-mcp` entry points. For a managed pre-scored S&P 500 universe, percentiles, and screeners, see the commercial **disclosure-alpha-api** hosted product.

## License

Apache-2.0
