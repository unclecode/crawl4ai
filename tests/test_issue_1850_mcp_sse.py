"""
Tests for issue #1850: MCP SSE endpoint not working.

Starlette's Route wraps async functions in request_response(), which calls
handler(request) instead of handler(scope, receive, send). The fix uses a
callable class to bypass this wrapping.

These tests verify the ASGI routing behavior without requiring a running
MCP server or Docker.
"""

import inspect
import pytest
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse


# -- Core issue: Route wrapping behavior --

class TestRouteWrappingBehavior:
    """Verify that Starlette Route wraps functions but not class instances."""

    def test_async_function_is_wrapped(self):
        """An async function endpoint gets wrapped in request_response()."""
        async def handler(scope, receive, send):
            pass

        r = Route("/test", endpoint=handler)
        # Route wraps it — r.app is NOT handler
        assert r.app is not handler

    def test_callable_class_is_not_wrapped(self):
        """A callable class instance is treated as raw ASGI (not wrapped)."""
        class Handler:
            async def __call__(self, scope, receive, send):
                pass

        h = Handler()
        r = Route("/test", endpoint=h)
        # Route passes it through — r.app IS handler
        assert r.app is h

    def test_async_function_is_function(self):
        """Confirm async def is detected as function by inspect."""
        async def handler(scope, receive, send):
            pass
        assert inspect.isfunction(handler)

    def test_callable_class_is_not_function(self):
        """Confirm callable class is NOT detected as function by inspect."""
        class Handler:
            async def __call__(self, scope, receive, send):
                pass
        assert not inspect.isfunction(Handler())


# -- ASGI handler receives correct arguments --

class TestASGIHandlerArgs:
    """Verify that the callable class receives scope/receive/send correctly."""

    def test_callable_class_receives_asgi_args(self):
        """A callable class mounted via Route should get scope, receive, send."""
        received_args = {}

        class Handler:
            async def __call__(self, scope, receive, send):
                received_args["scope_type"] = scope["type"]
                response = PlainTextResponse("ok")
                await response(scope, receive, send)

        app = Starlette(routes=[Route("/test", endpoint=Handler())])
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert received_args["scope_type"] == "http"

    def test_async_function_receives_request_not_asgi(self):
        """An async function mounted via Route gets Request, not raw ASGI."""
        received_type = {}

        async def handler(*args, **kwargs):
            received_type["arg_count"] = len(args)
            if args and hasattr(args[0], "url"):
                received_type["is_request"] = True
                return PlainTextResponse("ok")
            received_type["is_request"] = False

        app = Starlette(routes=[Route("/test", endpoint=handler)])
        client = TestClient(app)
        resp = client.get("/test")
        # Starlette wraps it and passes Request object (1 arg)
        assert received_type.get("is_request") is True


# -- MCP bridge SSE handler structure --

class TestMCPBridgeSSEHandler:
    """Verify the mcp_bridge SSE handler is correctly structured."""

    def test_mcp_bridge_uses_callable_class(self):
        """The SSE handler in mcp_bridge should be a callable class, not a function."""
        # Import and check the source
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "mcp_bridge_check",
            "deploy/docker/mcp_bridge.py"
        )
        # We can't fully import mcp_bridge (needs Docker deps), so check source
        with open("deploy/docker/mcp_bridge.py") as f:
            source = f.read()

        # Should have a class-based handler
        assert "class _MCPSseApp" in source
        assert "async def __call__(self, scope, receive, send)" in source

    def test_mcp_bridge_no_async_def_sse_handler(self):
        """Should NOT have a plain async def _mcp_sse_handler."""
        with open("deploy/docker/mcp_bridge.py") as f:
            source = f.read()

        # The old buggy pattern should be gone
        assert "async def _mcp_sse_handler(scope, receive, send)" not in source

    def test_mcp_bridge_route_uses_class_instance(self):
        """Route should be created with _MCPSseApp() instance, not a function."""
        with open("deploy/docker/mcp_bridge.py") as f:
            source = f.read()

        assert "_MCPSseApp()" in source


# -- Regression: ensure Route + callable class pattern works end-to-end --

class TestRouteCallableClassEndToEnd:
    """End-to-end test that a callable class works as a Route endpoint."""

    def test_sse_like_handler(self):
        """Simulate an SSE-like raw ASGI handler via Route."""
        class SSEHandler:
            async def __call__(self, scope, receive, send):
                response = PlainTextResponse(
                    "event: endpoint\ndata: /test\n\n",
                    media_type="text/event-stream",
                )
                await response(scope, receive, send)

        app = Starlette(routes=[Route("/sse", endpoint=SSEHandler())])
        client = TestClient(app)
        resp = client.get("/sse")
        assert resp.status_code == 200
        assert "event: endpoint" in resp.text

    def test_multiple_routes_with_mixed_handlers(self):
        """Callable class and regular function handlers can coexist."""
        class RawHandler:
            async def __call__(self, scope, receive, send):
                response = PlainTextResponse("raw")
                await response(scope, receive, send)

        async def regular_handler(request):
            return PlainTextResponse("regular")

        app = Starlette(routes=[
            Route("/raw", endpoint=RawHandler()),
            Route("/regular", endpoint=regular_handler),
        ])
        client = TestClient(app)
        assert client.get("/raw").text == "raw"
        assert client.get("/regular").text == "regular"
