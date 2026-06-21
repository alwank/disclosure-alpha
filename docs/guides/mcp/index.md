# MCP Guide

Disclosure Alpha ships two [Model Context Protocol](https://modelcontextprotocol.io/) servers for AI agents in Cursor, Claude Desktop, and other MCP hosts.

**Prerequisites:** `pip install -e ".[mcp,dev]"` and `SEC_USER_AGENT` for ticker-based tools.

## Choose a bundle

| Entry point | Best for | Tools |
|-------------|----------|-------|
| `disclosure-alpha-mcp-analyst` | Ticker discovery + scoring | 2 tools + taxonomy resource |
| `disclosure-alpha-mcp-builder` | Raw HTML pipeline control | 5 low-level tools |

Legacy `disclosure-alpha-mcp` aliases to the analyst bundle.

## Analyst bundle

Start the server (stdio transport — configure in your MCP host):

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha-mcp-analyst
```

**Tools:**

| Tool | Description |
|------|-------------|
| `list_company_filings_tool` | List 10-K / 10-Q filings for a ticker and fiscal year |
| `score_company_filing_tool` | Score a filing by ticker, fiscal year, form type, optional quarter |

**Resource:** `disclosure://taxonomy/v1` — component weights and version strings.

## Builder bundle

```bash
disclosure-alpha-mcp-builder
```

**Tools:**

| Tool | Description |
|------|-------------|
| `extract_sections_tool` | Extract sections from filing HTML |
| `compute_section_metrics_tool_wrapper` | Metrics + diffs from section JSON |
| `diff_sections_tool` | Diff two section texts |
| `score_deterministic_tool_wrapper` | Aggregate scores from metrics JSON |
| `score_filing_html_tool_wrapper` | Full pipeline on HTML (optional prior HTML) |

Use the builder bundle when your agent already has filing HTML and needs step-by-step pipeline access.

## Cursor configuration example

Add to your MCP settings (paths may vary):

```json
{
  "mcpServers": {
    "disclosure-alpha": {
      "command": "disclosure-alpha-mcp-analyst",
      "env": {
        "SEC_USER_AGENT": "YourName your@email.com"
      }
    }
  }
}
```

## Related

- {doc}`../../getting-started/choose-your-surface`
- {doc}`../http/index`
- {doc}`../../getting-started/sec-edgar-setup`
