# Disclosure Alpha — deterministic SEC filing analytics (open source)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Parse SEC filing HTML, compute deterministic text metrics, diff sections, and produce reproducible disclosure risk scores — no LLM required.

**What we claim today:** deterministic Item 1A analytics on **~425 S&P 500 FY2025 10-Ks** (~84% of index); construct validity on that cohort (L2); higher risk scores associate with higher 90d post-filing volatility (partial L3, Q5/Q1 ~ 1.11). Earnings-surprise outcome validation **not supported** (FY2024 gate failed). See [validation protocol](docs/07_validation_protocol.md).

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
| `GET /v1/company/{ticker}/disclosure-flags?fiscal_year=2025` | Boolean risk flags only (no scores) |
| `GET /v1/company/{ticker}/disclosure-changes?fiscal_year=2025` | Section diffs and change score |
| `POST /v1/panel/disclosure-matrix` | Batch screener (max 25 tickers) |

For 10-Q, add `quarter=Q1|Q2|Q3`.

See [docs/09_product_surfaces.md](docs/09_product_surfaces.md) for product map and tier presets.

**Shared query params** (`sections`, `disclosure-metrics`, `disclosure-matrix`):

| Param | Default | Description |
|-------|---------|-------------|
| `compare` | `prior` | `prior` loads prior filing for diffs; `none` skips prior comparison |
| `sections` | all | Comma-separated section names, e.g. `item_1a_risk_factors,item_7_mdna` |

**Matrix-only params:**

| Param | Default | Description |
|-------|---------|-------------|
| `view` | `deterministic` | `deterministic` only; `composite` / `full` return HTTP 402 (not in OSS) |
| `tier` | — | `lite`, `standard`, or `analyst` — overrides `include`/`fields` |
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

Two focused bundles plus a legacy alias:

| Entry point | Use when |
|-------------|----------|
| `disclosure-alpha-mcp-analyst` | Ticker filings + scores (2 tools) |
| `disclosure-alpha-mcp-builder` | Raw HTML pipeline (5 tools) |
| `disclosure-alpha-mcp` | Legacy alias → analyst (deprecated) |

**Analyst** (Cursor / Claude Desktop):

```json
{
  "mcpServers": {
    "disclosure-alpha-analyst": {
      "command": "disclosure-alpha-mcp-analyst",
      "env": {
        "SEC_USER_AGENT": "YourName your@email.com"
      }
    }
  }
}
```

**Builder** (custom HTML workflows):

```json
{
  "mcpServers": {
    "disclosure-alpha-builder": {
      "command": "disclosure-alpha-mcp-builder"
    }
  }
}
```

**Analyst tools:** `list_company_filings_tool`, `score_company_filing_tool` — resource `disclosure://taxonomy/v1`

**Builder tools:** `extract_sections_tool`, `compute_section_metrics_tool_wrapper`, `diff_sections_tool`, `score_deterministic_tool_wrapper`, `score_filing_html_tool_wrapper`

## Versions

| Artifact | Version |
|----------|---------|
| Parser | `section_extractor_v2` |
| Metrics | `text_metrics_v1.3` |
| Scoring | `deterministic_scoring_v3` |

## L2 validation (partial, accepted MVP)

Tested on **425 of 503** S&P 500 constituents (FY2025 Item 1A). **Construct validity passes** on this cohort (boilerplate rho ~ 0.68, specificity-vs-NER rho ~ 0.79). Full-index EDGAR gates (E1/E2) are below protocol targets; **not** claiming `overall_l2_pass`.

```bash
export SEC_USER_AGENT="YourName your@email.com"
python scripts/build_validation_corpus_from_edgar.py --fiscal-year 2025 --resume

pip install -e ".[validation]"
python -m spacy download en_core_web_sm
PYTHONUNBUFFERED=1 .venv/bin/python scripts/validate_deterministic_construct.py \
  --universe data/universe/sp500.csv
```

See [data/validation/README.md](data/validation/README.md) and [docs/07_validation_protocol.md](docs/07_validation_protocol.md#l2-achieved-status-accepted-mvp-fy2025).

## Testing

Default test run is **offline-safe** (no live SEC or yfinance):

```bash
pip install -e ".[api,mcp,dev]"
pytest -q -m "not integration" --cov=disclosure_alpha --cov-fail-under=75
```

Live integration tests (yfinance, optional EDGAR smoke):

```bash
RUN_INTEGRATION=1 pytest -q -m integration
```

### Pre-publish checklist (v0.1.0)

- [ ] `pytest -m "not integration"` green on Python 3.11 and 3.12
- [ ] `pip install -e ".[api,mcp,dev]"` — entry points resolve: `disclosure-alpha`, `disclosure-alpha-api`, `disclosure-alpha-mcp`, `disclosure-alpha-mcp-analyst`, `disclosure-alpha-mcp-builder`
- [ ] Smoke: `disclosure-alpha extract --html …`, `curl localhost:8000/health`, MCP tools import
- [ ] No secrets in repo; `SEC_USER_AGENT` documented only

## Hosted vs self-hosted

This repo includes **self-hosted** `disclosure-alpha-api` and `disclosure-alpha-mcp` entry points. For a managed pre-scored S&P 500 universe, percentiles, and screeners, see the commercial **disclosure-alpha-api** hosted product.

## License

Apache-2.0
