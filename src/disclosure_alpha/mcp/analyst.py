"""Analyst MCP bundle: ticker discovery + scoring (2 tools + taxonomy).

EDGAR-backed tools support 10-K and 10-Q only. For 8-K, use the Builder bundle
with local HTML.
"""

from __future__ import annotations

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "MCP extras required: pip install disclosure-alpha[mcp]"
    ) from exc

from disclosure_alpha.mcp.tools import list_company_filings, score_company_filing, taxonomy_payload

mcp = FastMCP("disclosure-alpha-analyst")


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
) -> str:
    """Score a company filing by ticker and fiscal year (10-K or 10-Q with quarter)."""
    return score_company_filing(ticker, fiscal_year, form_type=form_type, quarter=quarter)


@mcp.resource("disclosure://taxonomy/v1")
def taxonomy() -> str:
    """Score taxonomy: component weights and version strings."""
    return taxonomy_payload()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
