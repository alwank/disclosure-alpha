"""MCP Builder bundle tests — Track E owns implementation."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp")

from disclosure_alpha.mcp.analyst import mcp as analyst_mcp
from disclosure_alpha.mcp.builder import mcp as builder_mcp


def test_builder_exposes_five_tools():
    tools = list(builder_mcp._tool_manager._tools.keys())
    assert len(tools) == 5
    assert set(tools) == {
        "extract_sections_tool",
        "compute_section_metrics_tool_wrapper",
        "diff_sections_tool",
        "score_deterministic_tool_wrapper",
        "score_filing_html_tool_wrapper",
    }


def test_builder_does_not_expose_analyst_tools():
    analyst_tools = set(analyst_mcp._tool_manager._tools.keys())
    builder_tools = set(builder_mcp._tool_manager._tools.keys())
    assert analyst_tools.isdisjoint(builder_tools)
