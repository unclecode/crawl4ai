"""
Tests for migration #1594 — MCP SSE → Streamable-HTTP migration.

The old code used mcp.server.sse.SseServerTransport with raw ASGI Route/Mount
workarounds. The new code uses FastMCP with streamable_http_app and adds the
route directly to the FastAPI app without SSE or WebSocket transports.
"""

import re
import pytest


class TestMCPStreamableHTTPMigration:
    """Verify mcp_bridge.py uses FastMCP + streamable_http, not SSE/WS."""

    def _get_source(self):
        with open("deploy/docker/mcp_bridge.py", "r") as f:
            return f.read()

    def test_uses_fastmcp(self):
        """Should import FastMCP, not SseServerTransport."""
        source = self._get_source()
        assert "from mcp.server.fastmcp import FastMCP" in source
        assert "SseServerTransport" not in source

    def test_uses_streamable_http_app(self):
        """Should call streamable_http_app()."""
        source = self._get_source()
        assert "streamable_http_app" in source

    def test_no_sse_transport(self):
        """Should NOT contain SseServerTransport or connect_sse."""
        source = self._get_source()
        assert "SseServerTransport" not in source
        assert "connect_sse" not in source
        assert "sse.handle_post_message" not in source

    def test_no_websocket_transport(self):
        """Should NOT contain websocket_route or websocket code."""
        source = self._get_source()
        assert "websocket_route" not in source

    def test_routes_appended(self):
        """Should append routes from streamable_http_app to app.routes."""
        source = self._get_source()
        assert "app.routes.append" in source

    def test_has_schema_endpoint(self):
        """Should still expose /mcp/schema."""
        source = self._get_source()
        assert "base}/schema" in source or "schema" in source

    def test_uses_add_tool(self):
        """Should register tools via mcp.add_tool()."""
        source = self._get_source()
        assert "add_tool" in source
