"""
Tests for issue #1594 — MCP SSE endpoint crash.

The old code used @app.get() to mount the SSE handler, which wraps it in
Starlette middleware.  The MCP SDK's SseServerTransport calls raw ASGI
(scope, receive, send) internally, causing a middleware lifecycle conflict
(AssertionError).

Fix: mount via starlette.routing.Route (raw ASGI, no middleware wrapping).
"""

import inspect
import re

import pytest


class TestMCPSSERouting:
    """Verify mcp_bridge.py uses raw ASGI routes for SSE, not @app.get()."""

    def _get_source(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "mcp_bridge", "deploy/docker/mcp_bridge.py"
        )
        # We just need the source, not to execute it
        with open("deploy/docker/mcp_bridge.py", "r") as f:
            return f.read()

    def test_no_app_get_for_sse_endpoint(self):
        """SSE endpoint must NOT use @app.get() — that causes the crash."""
        source = self._get_source()
        # Should not have @app.get(...sse...) pattern
        assert not re.search(
            r'@app\.get\([^)]*sse[^)]*\)', source
        ), "SSE endpoint must not use @app.get() — causes AssertionError (#1594)"

    def test_uses_starlette_route_for_sse(self):
        """SSE endpoint should use starlette.routing.Route (raw ASGI)."""
        source = self._get_source()
        assert "from starlette.routing import Route" in source or \
               "from starlette.routing import Route, Mount" in source, \
            "Should import Route from starlette.routing"
        assert re.search(r'Route\([^)]*sse[^)]*\)', source), \
            "SSE endpoint should be mounted via Route()"

    def test_uses_mount_for_messages(self):
        """SSE messages endpoint should use Mount(), not app.mount()."""
        source = self._get_source()
        assert re.search(r'Mount\([^)]*messages[^)]*\)', source), \
            "Messages endpoint should use Mount()"

    def test_sse_handler_is_raw_asgi(self):
        """SSE handler should accept (scope, receive, send) — raw ASGI signature."""
        source = self._get_source()
        # The handler function should have raw ASGI params
        assert re.search(
            r'async def _mcp_sse_handler\(scope,\s*receive,\s*send\)', source
        ), "SSE handler must be raw ASGI: (scope, receive, send)"

    def test_connect_sse_uses_raw_params(self):
        """connect_sse should be called with scope, receive, send directly."""
        source = self._get_source()
        assert re.search(
            r'sse\.connect_sse\(scope,\s*receive,\s*send\)', source
        ), "connect_sse must use (scope, receive, send), not request._send"

    def test_no_request_send_usage(self):
        """Must not use request._send — that's a private Starlette attribute."""
        source = self._get_source()
        assert "request._send" not in source, \
            "Must not use request._send (private attribute, fragile)"

    def test_routes_appended_not_decorated(self):
        """Routes should be appended to app.routes, not decorated."""
        source = self._get_source()
        assert "app.routes.append" in source, \
            "SSE routes should be appended via app.routes.append()"
