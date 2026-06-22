"""Builder MCP bundle: low-level pipeline tools (5 tools, no ticker helpers)."""

from __future__ import annotations

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "MCP extras required: pip install disclosure-alpha[mcp]"
    ) from exc

from disclosure_alpha.mcp.tools import (
    compute_section_metrics_tool,
    diff_sections,
    extract_sections,
    score_deterministic_tool,
    score_filing_html_tool,
)

mcp = FastMCP("disclosure-alpha-builder")


@mcp.tool()
def extract_sections_tool(html: str, form_type: str) -> str:
    """Extract SEC filing sections from HTML (10-K, 10-Q, or 8-K; 8-K: local HTML only)."""
    return extract_sections(html, form_type)


@mcp.tool()
def compute_section_metrics_tool_wrapper(
    sections_json: str,
    prior_sections_json: str | None = None,
) -> str:
    """Compute deterministic text metrics and diffs from extracted section payloads."""
    return compute_section_metrics_tool(sections_json, prior_sections_json)


@mcp.tool()
def diff_sections_tool(
    current_text: str, prior_text: str, section_name: str = "section"
) -> str:
    """Diff two section texts and return change score + language deltas."""
    return diff_sections(current_text, prior_text, section_name=section_name)


@mcp.tool()
def score_deterministic_tool_wrapper(metrics_json: str) -> str:
    """Aggregate deterministic component scores from a metrics payload."""
    return score_deterministic_tool(metrics_json)


@mcp.tool()
def score_filing_html_tool_wrapper(
    html: str,
    form_type: str,
    prior_html: str | None = None,
) -> str:
    """Run full pipeline on filing HTML (10-K, 10-Q, or 8-K; 8-K: local HTML only)."""
    return score_filing_html_tool(html, form_type, prior_html=prior_html)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
