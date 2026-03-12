"""
Tests for issue #1594 — Version-aware MCP transport selection.

Verifies:
- Transport detection from installed MCP SDK
- Auto/explicit transport selection logic
- Config defaults and env var overrides
- Error handling for unsupported transports
- SSE handler is mounted as raw ASGI (not middleware-wrapped)
- Version matrix: behavior across simulated SDK v1.6.0, v1.18.0, v1.20.0, v1.26.0
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure deploy/docker is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "deploy", "docker"))


class TestDetectTransports:
    """Test _detect_transports() populates capabilities correctly."""

    def test_detect_returns_version(self):
        from mcp_bridge import _TRANSPORTS_AVAILABLE
        assert "version" in _TRANSPORTS_AVAILABLE
        assert isinstance(_TRANSPORTS_AVAILABLE["version"], str)

    def test_detect_sse_available(self):
        from mcp_bridge import _TRANSPORTS_AVAILABLE
        # SSE should be available in any supported MCP SDK version
        assert _TRANSPORTS_AVAILABLE.get("sse") is True

    def test_detect_streamable_http_is_bool(self):
        from mcp_bridge import _TRANSPORTS_AVAILABLE
        # May or may not be available depending on SDK version
        assert isinstance(_TRANSPORTS_AVAILABLE.get("streamable_http"), bool)


class TestTransportSelection:
    """Test transport selection logic in attach_mcp()."""

    def _make_app(self):
        from fastapi import FastAPI
        return FastAPI(title="test")

    def test_auto_picks_streamable_if_available(self):
        """auto mode should prefer streamable_http when available."""
        from mcp_bridge import _TRANSPORTS_AVAILABLE
        if not _TRANSPORTS_AVAILABLE.get("streamable_http"):
            pytest.skip("streamable_http not available in installed SDK")

        from mcp_bridge import attach_mcp
        app = self._make_app()
        # Should not raise
        attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "auto"})

        # Should have the /mcp/mcp route (streamable) and /mcp/ws (websocket)
        paths = [getattr(r, "path", "") for r in app.routes]
        assert "/mcp/mcp" in paths
        assert "/mcp/ws" in paths

    def test_auto_falls_back_to_sse(self):
        """auto mode should fall back to sse when streamable_http is unavailable."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, {"streamable_http": False, "sse": True}):
            app = self._make_app()
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "auto"})

            paths = [getattr(r, "path", "") for r in app.routes]
            assert "/mcp/sse" in paths
            assert "/mcp/ws" in paths

    def test_explicit_sse_works(self):
        """Explicit sse transport should mount SSE routes."""
        from mcp_bridge import attach_mcp
        app = self._make_app()
        attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "sse"})

        paths = [getattr(r, "path", "") for r in app.routes]
        assert "/mcp/sse" in paths
        assert "/mcp/messages" in paths

    def test_explicit_streamable_http_works(self):
        """Explicit streamable_http transport should mount the unified route."""
        from mcp_bridge import _TRANSPORTS_AVAILABLE
        if not _TRANSPORTS_AVAILABLE.get("streamable_http"):
            pytest.skip("streamable_http not available in installed SDK")

        from mcp_bridge import attach_mcp
        app = self._make_app()
        attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "streamable_http"})

        paths = [getattr(r, "path", "") for r in app.routes]
        assert "/mcp/mcp" in paths

    def test_unsupported_streamable_raises(self):
        """Requesting streamable_http on old SDK should raise RuntimeError."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, {"streamable_http": False, "version": "1.18.0"}):
            app = self._make_app()
            with pytest.raises(RuntimeError, match="streamable_http"):
                attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "streamable_http"})

    def test_no_transports_raises(self):
        """auto mode with no transports available should raise RuntimeError."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, {"sse": False, "streamable_http": False, "version": "0.0.0"}):
            app = self._make_app()
            with pytest.raises(RuntimeError, match="No supported MCP transport"):
                attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "auto"})

    def test_unknown_transport_raises(self):
        """Unknown transport name should raise ValueError."""
        from mcp_bridge import attach_mcp
        app = self._make_app()
        with pytest.raises(ValueError, match="Unknown MCP transport"):
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "grpc"})


class TestConfigDefaults:
    """Test config defaults and env var overrides."""

    def test_default_config_values(self):
        from utils import DEFAULT_CONFIG
        mcp_cfg = DEFAULT_CONFIG["mcp"]
        assert mcp_cfg["enabled"] is True
        assert mcp_cfg["transport"] == "auto"
        assert mcp_cfg["base_path"] == "/mcp"
        assert mcp_cfg["server_name"] is None
        assert mcp_cfg["timeout"] is None

    def test_env_var_overrides_transport(self):
        """MCP_TRANSPORT env var should override config."""
        with patch.dict(os.environ, {"MCP_TRANSPORT": "sse"}):
            from utils import load_config
            cfg = load_config()
            assert cfg["mcp"]["transport"] == "sse"

    def test_disabled_skips_attachment(self):
        """mcp.enabled=False should skip MCP attachment entirely."""
        from mcp_bridge import attach_mcp
        from fastapi import FastAPI
        app = FastAPI(title="test")
        initial_route_count = len(app.routes)

        attach_mcp(app, base_url="http://localhost:8000", mcp_config={"enabled": False})

        # No new routes should have been added
        assert len(app.routes) == initial_route_count


class TestVersionMatrix:
    """
    Simulate different MCP SDK versions by mocking _TRANSPORTS_AVAILABLE.

    Version landscape:
    - v1.6.0  — SSE only (SseServerTransport introduced)
    - v1.18.0 — SSE only (last version before StreamableHTTP)
    - v1.20.0 — SSE + StreamableHTTP (StreamableHTTPSessionManager introduced)
    - v1.26.0 — SSE + StreamableHTTP (current)
    - v0.1.0  — hypothetical ancient: neither transport available
    """

    VERSION_PROFILES = {
        "v1.6.0_sse_only": {
            "version": "1.6.0",
            "sse": True,
            "streamable_http": False,
        },
        "v1.18.0_sse_only": {
            "version": "1.18.0",
            "sse": True,
            "streamable_http": False,
        },
        "v1.20.0_both": {
            "version": "1.20.0",
            "sse": True,
            "streamable_http": True,
        },
        "v1.26.0_both": {
            "version": "1.26.0",
            "sse": True,
            "streamable_http": True,
        },
        "v0.1.0_neither": {
            "version": "0.1.0",
            "sse": False,
            "streamable_http": False,
        },
    }

    def _make_app(self):
        from fastapi import FastAPI
        return FastAPI(title="test-version-matrix")

    def _get_route_paths(self, app):
        return [getattr(r, "path", "") for r in app.routes]

    # ── auto transport across versions ────────────────────────

    @pytest.mark.parametrize("profile_name,profile", [
        ("v1.26.0_both", VERSION_PROFILES["v1.26.0_both"]),
        ("v1.20.0_both", VERSION_PROFILES["v1.20.0_both"]),
    ], ids=["v1.26.0", "v1.20.0"])
    def test_auto_prefers_streamable_on_new_sdk(self, profile_name, profile):
        """On SDK >=1.20.0, auto should select streamable_http."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, profile, clear=True):
            app = self._make_app()
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "auto"})
            paths = self._get_route_paths(app)
            assert "/mcp/mcp" in paths, f"Expected streamable route for {profile_name}"
            assert "/mcp/ws" in paths, "WebSocket should always be mounted"
            # SSE should NOT be mounted when streamable is chosen
            assert "/mcp/sse" not in paths

    @pytest.mark.parametrize("profile_name,profile", [
        ("v1.6.0_sse_only", VERSION_PROFILES["v1.6.0_sse_only"]),
        ("v1.18.0_sse_only", VERSION_PROFILES["v1.18.0_sse_only"]),
    ], ids=["v1.6.0", "v1.18.0"])
    def test_auto_falls_back_to_sse_on_old_sdk(self, profile_name, profile):
        """On SDK <1.20.0, auto should fall back to SSE."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, profile, clear=True):
            app = self._make_app()
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "auto"})
            paths = self._get_route_paths(app)
            assert "/mcp/sse" in paths, f"Expected SSE fallback for {profile_name}"
            assert "/mcp/messages" in paths
            assert "/mcp/ws" in paths
            assert "/mcp/mcp" not in paths

    def test_auto_raises_on_ancient_sdk(self):
        """On hypothetical SDK with neither transport, auto should raise."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE
        profile = self.VERSION_PROFILES["v0.1.0_neither"]

        with patch.dict(_TRANSPORTS_AVAILABLE, profile, clear=True):
            app = self._make_app()
            with pytest.raises(RuntimeError, match="No supported MCP transport"):
                attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "auto"})

    # ── explicit sse across versions ──────────────────────────

    @pytest.mark.parametrize("profile_name,profile", [
        ("v1.6.0_sse_only", VERSION_PROFILES["v1.6.0_sse_only"]),
        ("v1.18.0_sse_only", VERSION_PROFILES["v1.18.0_sse_only"]),
        ("v1.20.0_both", VERSION_PROFILES["v1.20.0_both"]),
        ("v1.26.0_both", VERSION_PROFILES["v1.26.0_both"]),
    ], ids=["v1.6.0", "v1.18.0", "v1.20.0", "v1.26.0"])
    def test_explicit_sse_works_across_versions(self, profile_name, profile):
        """Explicit transport='sse' should work on any SDK that has SSE."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, profile, clear=True):
            app = self._make_app()
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "sse"})
            paths = self._get_route_paths(app)
            assert "/mcp/sse" in paths
            assert "/mcp/messages" in paths

    def test_explicit_sse_raises_when_unavailable(self):
        """Explicit transport='sse' on SDK without SSE should raise."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE
        profile = self.VERSION_PROFILES["v0.1.0_neither"]

        with patch.dict(_TRANSPORTS_AVAILABLE, profile, clear=True):
            app = self._make_app()
            with pytest.raises(RuntimeError, match="sse"):
                attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "sse"})

    # ── explicit streamable_http across versions ──────────────

    @pytest.mark.parametrize("profile_name,profile", [
        ("v1.20.0_both", VERSION_PROFILES["v1.20.0_both"]),
        ("v1.26.0_both", VERSION_PROFILES["v1.26.0_both"]),
    ], ids=["v1.20.0", "v1.26.0"])
    def test_explicit_streamable_works_on_new_sdk(self, profile_name, profile):
        """Explicit transport='streamable_http' should work on SDK >=1.20.0."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, profile, clear=True):
            app = self._make_app()
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "streamable_http"})
            paths = self._get_route_paths(app)
            assert "/mcp/mcp" in paths

    @pytest.mark.parametrize("profile_name,profile", [
        ("v1.6.0_sse_only", VERSION_PROFILES["v1.6.0_sse_only"]),
        ("v1.18.0_sse_only", VERSION_PROFILES["v1.18.0_sse_only"]),
    ], ids=["v1.6.0", "v1.18.0"])
    def test_explicit_streamable_raises_on_old_sdk(self, profile_name, profile):
        """Explicit transport='streamable_http' on SDK <1.20.0 should raise with clear message."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, profile, clear=True):
            app = self._make_app()
            with pytest.raises(RuntimeError, match=r"streamable_http.*requires.*>=1\.20\.0"):
                attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "streamable_http"})

    # ── error message quality ─────────────────────────────────

    def test_error_includes_installed_version(self):
        """Runtime errors should include the installed SDK version for debugging."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, {"streamable_http": False, "sse": True, "version": "1.18.0"}, clear=True):
            app = self._make_app()
            with pytest.raises(RuntimeError) as exc_info:
                attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "streamable_http"})
            assert "1.18.0" in str(exc_info.value)

    def test_error_on_no_transports_includes_version(self):
        """No-transport error should include SDK version."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, {"sse": False, "streamable_http": False, "version": "0.1.0"}, clear=True):
            app = self._make_app()
            with pytest.raises(RuntimeError) as exc_info:
                attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "auto"})
            assert "0.1.0" in str(exc_info.value)

    # ── websocket always mounted regardless of transport ──────

    @pytest.mark.parametrize("transport", ["auto", "sse"])
    def test_websocket_always_mounted(self, transport):
        """WebSocket route should be mounted regardless of HTTP transport choice."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, self.VERSION_PROFILES["v1.18.0_sse_only"], clear=True):
            app = self._make_app()
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": transport})
            paths = self._get_route_paths(app)
            assert "/mcp/ws" in paths

    # ── schema endpoint always mounted ────────────────────────

    @pytest.mark.parametrize("transport", ["sse", "auto"])
    def test_schema_endpoint_always_mounted(self, transport):
        """GET /mcp/schema should be mounted regardless of transport."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, self.VERSION_PROFILES["v1.18.0_sse_only"], clear=True):
            app = self._make_app()
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": transport})
            paths = self._get_route_paths(app)
            assert "/mcp/schema" in paths

    # ── custom base_path across versions ──────────────────────

    def test_custom_base_path_sse(self):
        """Custom base_path should be respected for SSE routes."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, self.VERSION_PROFILES["v1.18.0_sse_only"], clear=True):
            app = self._make_app()
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "sse", "base_path": "/api/mcp"})
            paths = self._get_route_paths(app)
            assert "/api/mcp/sse" in paths
            assert "/api/mcp/messages" in paths
            assert "/api/mcp/ws" in paths
            assert "/api/mcp/schema" in paths

    def test_custom_base_path_streamable(self):
        """Custom base_path should be respected for StreamableHTTP routes."""
        from mcp_bridge import attach_mcp, _TRANSPORTS_AVAILABLE

        with patch.dict(_TRANSPORTS_AVAILABLE, self.VERSION_PROFILES["v1.26.0_both"], clear=True):
            app = self._make_app()
            attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "streamable_http", "base_path": "/v2/mcp"})
            paths = self._get_route_paths(app)
            assert "/v2/mcp/mcp" in paths
            assert "/v2/mcp/ws" in paths
            assert "/v2/mcp/schema" in paths


class TestSSEHandlerIsRawASGI:
    """Verify SSE handler is mounted via Route (raw ASGI), not @app.get()."""

    def test_sse_route_is_starlette_route(self):
        """The /mcp/sse route should be a starlette.routing.Route, not an APIRoute."""
        from mcp_bridge import attach_mcp
        from fastapi import FastAPI
        from starlette.routing import Route

        app = FastAPI(title="test")
        attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "sse"})

        sse_routes = [r for r in app.routes if getattr(r, "path", "") == "/mcp/sse"]
        assert len(sse_routes) == 1
        # Should be a plain Starlette Route, not a FastAPI APIRoute
        assert type(sse_routes[0]) is Route

    def test_messages_mount_is_starlette_mount(self):
        """The /mcp/messages mount should be a starlette.routing.Mount."""
        from mcp_bridge import attach_mcp
        from fastapi import FastAPI
        from starlette.routing import Mount

        app = FastAPI(title="test")
        attach_mcp(app, base_url="http://localhost:8000", mcp_config={"transport": "sse"})

        msg_routes = [r for r in app.routes if getattr(r, "path", "") == "/mcp/messages"]
        assert len(msg_routes) == 1
        assert isinstance(msg_routes[0], Mount)
