"""
Tests for migration #1850 — MCP SSE callable-class → FastMCP migration.

The old code required a callable class (_MCPSseApp) to bypass Starlette Route
wrapping. With FastMCP + streamable_http_app, the SDK handles ASGI routing
natively — no raw ASGI workarounds needed.
"""

import pytest
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

from mcp.server.fastmcp import FastMCP


class TestFastMCPRouteBehavior:
    """Verify that FastMCP streamable_http_app creates proper routes."""

    def test_fastmcp_creates_route(self):
        """streamable_http_app should create a Starlette app with a Route."""
        mcp = FastMCP("test", streamable_http_path="/mcp")
        starlette_app = mcp.streamable_http_app()
        routes = starlette_app.routes
        assert len(routes) >= 1
        # The main route should be at the configured path
        assert any(r.path == "/mcp" for r in routes)

    def test_fastmcp_route_is_callable(self):
        """The route endpoint should be callable."""
        mcp = FastMCP("test", streamable_http_path="/test")
        starlette_app = mcp.streamable_http_app()
        for route in starlette_app.routes:
            if hasattr(route, 'endpoint'):
                assert callable(route.endpoint)

    def test_no_raw_asgi_workaround_needed(self):
        """FastMCP handles ASGI internally — no _MCPSseApp needed."""
        with open("deploy/docker/mcp_bridge.py") as f:
            source = f.read()
        assert "_MCPSseApp" not in source

    def test_session_manager_available_after_app(self):
        """Session manager should be accessible after streamable_http_app()."""
        mcp = FastMCP("test")
        mcp.streamable_http_app()
        # Should not raise RuntimeError
        sm = mcp.session_manager
        assert sm is not None
