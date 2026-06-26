"""Shared analyst MCP server factory (stdio CLI + HTTP mount)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from disclosure_alpha.mcp.tools import list_company_filings, score_company_filing, taxonomy_payload
from disclosure_alpha.version import SCORING_MODEL_VERSION

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

# Must match apps.json mcp_servers[].name and widgets.json mcp_tool.mcp_server
MCP_SERVER_NAME = "Disclosure Alpha Analyst"
TOOL_SCORE = "score_company_filing_tool"
TOOL_LIST = "list_company_filings_tool"


def create_analyst_mcp() -> FastMCP:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "MCP extras required: pip install disclosure-alpha[mcp]"
        ) from exc

    mcp = FastMCP(MCP_SERVER_NAME, json_response=True, stateless_http=True)

    @mcp.tool()
    def list_company_filings_tool(
        ticker: str,
        fiscal_year: int,
        form_type: str | None = None,
    ) -> str:
        """List available 10-K / 10-Q filings for a ticker and fiscal year."""
        return list_company_filings(ticker, fiscal_year, form_type=form_type)

    @mcp.tool()
    def score_company_filing_tool(
        ticker: str,
        fiscal_year: int,
        form_type: str = "10-K",
        quarter: str | None = None,
        scoring_model_version: str = SCORING_MODEL_VERSION,
    ) -> str:
        """Score a company filing by ticker and fiscal year (10-K or 10-Q with quarter)."""
        return score_company_filing(
            ticker,
            fiscal_year,
            form_type=form_type,
            quarter=quarter,
            scoring_model_version=scoring_model_version,
        )

    @mcp.resource("disclosure://taxonomy/v1")
    def taxonomy() -> str:
        """Score taxonomy: component weights and version strings."""
        return taxonomy_payload()

    return mcp
