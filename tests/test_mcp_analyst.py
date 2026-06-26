"""MCP Analyst bundle tests."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp")

from disclosure_alpha.mcp.analyst import mcp
from disclosure_alpha.mcp.analyst_server import TOOL_LIST, TOOL_SCORE, create_analyst_mcp


def test_analyst_exposes_two_tools():
    tools = list(mcp._tool_manager._tools.keys())
    assert len(tools) == 2
    assert set(tools) == {TOOL_LIST, TOOL_SCORE}


def test_create_analyst_mcp_matches_analyst_module():
    factory = create_analyst_mcp()
    assert set(factory._tool_manager._tools.keys()) == set(mcp._tool_manager._tools.keys())


def test_analyst_has_taxonomy_resource():
    resources = list(mcp._resource_manager._resources.keys())
    assert "disclosure://taxonomy/v1" in resources


def test_analyst_main_invokes_run(monkeypatch):
    from disclosure_alpha.mcp import analyst

    called: list[str] = []
    monkeypatch.setattr(analyst.mcp, "run", lambda: called.append("run"))
    analyst.main()
    assert called == ["run"]
