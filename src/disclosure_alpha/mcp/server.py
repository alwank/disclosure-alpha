"""MCP server — backward compat re-exports; default entry point is analyst bundle."""

from __future__ import annotations

from disclosure_alpha.mcp.analyst import main
from disclosure_alpha.mcp.tools import (
    compute_section_metrics_tool,
    diff_sections,
    extract_sections,
    list_company_filings,
    score_company_filing,
    score_deterministic_tool,
    score_filing_html_tool,
    taxonomy_payload,
)


def taxonomy() -> str:
    return taxonomy_payload()


if __name__ == "__main__":
    main()
