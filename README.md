# Disclosure Alpha — deterministic SEC filing analytics (open source)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Parse SEC filing HTML, compute deterministic text metrics, diff sections, and produce reproducible disclosure risk scores — no LLM required.

## Install

```bash
pip install -e ".[dev]"
# MCP server (Cursor / Claude Desktop)
pip install -e ".[mcp,dev]"
# Optional semantic embeddings (MiniLM; default is TF-IDF)
pip install -e ".[semantic]"
```

## CLI

```bash
disclosure-alpha extract --html filing.html --form 10-K
disclosure-alpha score --html filing.html --form 10-K
disclosure-alpha score --html current.html --form 10-K --prior-html prior.html
```

## Python API

```python
from disclosure_alpha import score_filing_html

result = score_filing_html(open("filing.html").read(), "10-K")
print(result.scores.overall_disclosure_risk_score)
print(result.to_dict())
```

## MCP server

Add to Cursor MCP config:

```json
{
  "mcpServers": {
    "disclosure-alpha": {
      "command": "disclosure-alpha-mcp"
    }
  }
}
```

Tools: `extract_sections`, `compute_section_metrics_tool`, `diff_sections`, `score_deterministic_tool`, `score_filing_html_tool`

Resource: `disclosure://taxonomy/v1`

## Versions

| Artifact | Version |
|----------|---------|
| Parser | `section_extractor_v1` |
| Metrics | `text_metrics_v1.2` |
| Scoring | `deterministic_scoring_v2` |

## Hosted API

For pre-scored S&P 500 universe, percentiles, and screeners, see **disclosure-alpha-api** (commercial hosted product).

## License

Apache-2.0
