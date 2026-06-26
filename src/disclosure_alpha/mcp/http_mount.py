"""Optional HTTP MCP mount for disclosure-alpha-api."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def try_create_analyst_mcp() -> FastMCP | None:
    """Return analyst FastMCP or None if [mcp] extra is not installed."""
    try:
        from disclosure_alpha.mcp.analyst_server import create_analyst_mcp
    except ImportError:
        return None
    return create_analyst_mcp()
