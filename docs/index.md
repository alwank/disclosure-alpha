# Disclosure Alpha

Parse SEC filing HTML, compute deterministic text metrics, diff sections, and produce reproducible disclosure risk scores — **no LLM required**.

## Start here

| I want to… | Start here |
|------------|------------|
| Understand the numbers | {doc}`getting-started/understanding-scores` |
| Score in terminal | {doc}`getting-started/quickstart-cli` |
| Build a screener | {doc}`guides/http/index` → {doc}`guides/workflows/index` |
| Use in Python | {doc}`getting-started/quickstart-python` |
| Wire an agent | {doc}`guides/mcp/index` |
| Know what we claim | {doc}`validation/evidence-and-limitations` |

## Get started in three steps

**1. Install** (Python 3.11+)

```bash
pip install "disclosure-alpha[dev]"
export SEC_USER_AGENT="YourName your@email.com"
```

**2. Score a filing**

```bash
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K
```

**3. Pick your integration surface**

CLI, Python SDK, HTTP API, or MCP — see {doc}`getting-started/choose-your-surface`.

Full install options: {doc}`getting-started/installation`.

## What you get

- **Deterministic scores** — nine weighted component scores (0–100) plus an overall disclosure risk score
- **Section extraction** — Item 1A, MD&A, controls, and more from 10-K / 10-Q / 8-K HTML
- **Change detection** — lexical and semantic diffs vs the prior comparable filing
- **Multiple surfaces** — terminal CLI, Python imports, REST API, and MCP tools for agents

Not investment advice. Scores summarize language and change signals in filings — they do not predict returns. See {doc}`validation/evidence-and-limitations` and {doc}`legal`.

## Documentation

```{toctree}
:maxdepth: 2
:caption: User guide

getting-started/index
guides/index
reference/index
```

```{toctree}
:maxdepth: 2
:caption: Methodology & evidence

methodology/index
validation/index
```

```{toctree}
:maxdepth: 1
:caption: Release notes

appendix/changelog
appendix/glossary
```

```{toctree}
:maxdepth: 1
:caption: Legal

legal
```

## License

Apache-2.0. Details: {doc}`legal`.

```{toctree}
:hidden:

CONTRIBUTING_DOCS
developer/architecture
developer/testing
```
