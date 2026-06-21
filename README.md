# Disclosure Alpha — deterministic SEC filing analytics (open source)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Parse SEC filing HTML, compute deterministic text metrics, diff sections, and produce reproducible disclosure risk scores — no LLM required.

**Documentation:** https://disclosure-alpha.readthedocs.io/en/stable/

**What we claim today:** deterministic Item 1A analytics on **~425 S&P 500 FY2025 10-Ks** (~84% of index); construct validity on that cohort (L2); higher risk scores associate with higher 90-day post-filing volatility (partial L3, Q5/Q1 ~ 1.11). Earnings-surprise outcome validation **not supported** (FY2024 gate failed). See [Evidence & limitations](https://disclosure-alpha.readthedocs.io/en/stable/validation/evidence-and-limitations.html).

## Install

Requires **Python 3.11+**.

```bash
pip install "disclosure-alpha[dev]"
# HTTP API + MCP: pip install "disclosure-alpha[api,mcp,dev]"
```

Set `SEC_USER_AGENT="YourName your@email.com"` for ticker/EDGAR commands. Full install options, CLI, Python API, HTTP, and MCP guides: **[Getting Started](https://disclosure-alpha.readthedocs.io/en/stable/getting-started/index.html)**.

## Quick example

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K
```

```python
from disclosure_alpha import score_filing_ticker
result = score_filing_ticker("AAPL", 2025, form_type="10-K")
print(result.scores.overall_disclosure_risk_score)
```

## HTTP API & MCP

```bash
disclosure-alpha-api          # HTTP on :8000 — see Guides → HTTP
disclosure-alpha-mcp-analyst  # MCP for Cursor / Claude Desktop
```

Endpoint map, tiers, Postman collections, and MCP tool reference: **[Guides](https://disclosure-alpha.readthedocs.io/en/stable/guides/index.html)**.

## Validation & testing

Evidence summary: **[Validation](https://disclosure-alpha.readthedocs.io/en/stable/validation/evidence-and-limitations.html)** and [data/validation/README.md](data/validation/README.md).

```bash
pip install "disclosure-alpha[api,mcp,dev]"
pytest -q -m "not integration" --cov=disclosure_alpha --cov-fail-under=75
```

## License

Apache-2.0
