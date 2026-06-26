"""Analyst MCP bundle: ticker discovery + scoring (2 tools + taxonomy).

EDGAR-backed tools support 10-K and 10-Q only. For 8-K, use the Builder bundle
with local HTML.
"""

from __future__ import annotations

from disclosure_alpha.mcp.analyst_server import create_analyst_mcp

mcp = create_analyst_mcp()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
