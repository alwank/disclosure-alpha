"""HTTP MCP mount tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("mcp")

from disclosure_alpha.api.app_factory import create_app
from disclosure_alpha.mcp.analyst_server import (
    MCP_SERVER_NAME,
    TOOL_LIST,
    TOOL_SCORE,
    create_analyst_mcp,
)


def test_create_analyst_mcp_has_expected_tools():
    mcp = create_analyst_mcp()
    tools = list(mcp._tool_manager._tools.keys())
    assert set(tools) == {TOOL_LIST, TOOL_SCORE}
    assert mcp.name == MCP_SERVER_NAME


def test_create_analyst_mcp_has_taxonomy_resource():
    mcp = create_analyst_mcp()
    resources = list(mcp._resource_manager._resources.keys())
    assert "disclosure://taxonomy/v1" in resources


def test_app_mounts_mcp_when_extra_installed():
    with TestClient(create_app()) as client:
        resp = client.get("/mcp")
        assert resp.status_code != 404


def test_app_skips_mcp_without_extra():
    with patch("disclosure_alpha.api.app_factory.try_create_analyst_mcp", return_value=None):
        with TestClient(create_app()) as client:
            resp = client.get("/mcp")
            assert resp.status_code == 404
