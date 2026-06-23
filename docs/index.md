# Disclosure Alpha

Parse SEC filing HTML, compute deterministic text metrics, diff sections, and produce reproducible disclosure risk scores — **no LLM required**.

```{admonition} Scope
:class: note

Not investment advice. Scores summarize language and change signals in filings. Full claims and limits: {doc}`getting-started/scope-and-claims`.
```

## Start here

| I want to… | Start here |
|------------|------------|
| Prove it works in five minutes | {doc}`getting-started/first-successful-run` |
| Evaluate whether to trust this | {doc}`getting-started/evidence` |
| Understand the numbers | {doc}`getting-started/understanding-scores` |
| Score in terminal | {doc}`getting-started/quickstart-cli` |
| Build a screener | {doc}`guides/http/index` → {doc}`guides/workflows/index` |
| Use in Python | {doc}`getting-started/quickstart-python` |
| Wire an agent | {doc}`guides/mcp/index` |
| Copy-paste examples | {doc}`examples/index` |

## Get started in three steps

**1. Install** (Python 3.11+)

```bash
pip install "disclosure-alpha"
export SEC_USER_AGENT="YourName your@email.com"
```

**2. Score a filing**

```bash
disclosure-alpha score --ticker AAPL --fiscal-year 2025 --form 10-K
```

Or score local HTML with no network: {doc}`getting-started/first-successful-run`.

**3. Pick your integration surface**

CLI, Python SDK, HTTP API, or MCP — see {doc}`getting-started/choose-your-surface`.

Full install options: {doc}`getting-started/installation`.

## What you get

- **Deterministic scores** — ten computed components (nine headline-weighted, 0–100) plus an overall disclosure risk score; see {doc}`reference/score-catalog`
- **Section extraction** — Item 1A, MD&A, controls, and more from 10-K / 10-Q HTML (8-K via local `--html` or MCP Builder only; not EDGAR or HTTP ticker routes)
- **Change detection** — lexical and semantic diffs vs the prior comparable filing
- **Multiple surfaces** — terminal CLI, Python imports, REST API, and MCP tools for agents

## Documentation

```{toctree}
:maxdepth: 2
:caption: Start Here

getting-started/index
```

```{toctree}
:maxdepth: 2
:caption: Guides

guides/index
```

```{toctree}
:maxdepth: 1
:caption: Examples

examples/index
```

```{toctree}
:maxdepth: 2
:caption: Reference

reference/index
```

```{toctree}
:maxdepth: 2
:caption: Methodology

methodology/index
```

```{toctree}
:maxdepth: 1
:caption: Appendix

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
