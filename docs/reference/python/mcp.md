# mcp

**Use when:** You want an MCP client to call Disclosure Alpha tools — either by ticker (analyst) or from raw HTML (builder).

## Start here

**Analyst bundle** (`disclosure-alpha-mcp-analyst`) — agent knows tickers:

- `list_company_filings_tool` — filing index for a ticker
- `score_company_filing_tool` — score by ticker + fiscal year

**Builder bundle** (`disclosure-alpha-mcp-builder`) — agent has filing HTML:

- `extract_sections_tool`, `compute_section_metrics_tool_wrapper`, `diff_sections_tool`
- `score_deterministic_tool_wrapper`, `score_filing_html_tool_wrapper`

Configure `SEC_USER_AGENT` in the MCP server environment. User guide: {doc}`../../guides/mcp/index`.

## Example

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha-mcp-analyst   # ticker discovery + scoring
disclosure-alpha-mcp-builder     # raw HTML pipeline steps
```

## Full API

### Analyst bundle

```{eval-rst}
.. automodule:: disclosure_alpha.mcp.analyst
   :members: list_company_filings_tool, score_company_filing_tool, main
```

### Builder bundle

```{eval-rst}
.. automodule:: disclosure_alpha.mcp.builder
   :members: extract_sections_tool, compute_section_metrics_tool_wrapper, diff_sections_tool, score_deterministic_tool_wrapper, score_filing_html_tool_wrapper, main
```

Tool implementations: `disclosure_alpha.mcp.tools`.
