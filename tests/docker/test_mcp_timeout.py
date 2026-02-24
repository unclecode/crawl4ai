# tests/docker/test_mcp_timeout.py
"""
Tests for MCP Bridge HTTP timeout (Issue #1769).
Verifies 300s timeout allows slow LLM responses and that TimeoutException
is converted to a friendly HTTP 504 message.

Run from repo root. Requires: pytest, pytest-asyncio, httpx, fastapi.
For full deploy/docker deps (mcp_bridge): run from deploy/docker or install
mcp, sse-starlette, etc.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Allow importing mcp_bridge from deploy/docker when running from repo root
_deploy_docker = Path(__file__).resolve().parent.parent.parent / "deploy" / "docker"
if str(_deploy_docker) not in sys.path:
    sys.path.insert(0, str(_deploy_docker))

try:
    from fastapi import HTTPException
    from mcp_bridge import LLM_REQUEST_TIMEOUT, _make_http_proxy
except ImportError as e:
    HTTPException = None  # type: ignore[misc, assignment]
    LLM_REQUEST_TIMEOUT = 300.0
    _make_http_proxy = None  # type: ignore[assignment]
    _MCP_BRIDGE_IMPORT_ERROR = e
else:
    _MCP_BRIDGE_IMPORT_ERROR = None


def _make_fake_route(path: str = "/test", method: str = "GET"):
    route = MagicMock()
    route.path = path
    route.methods = (
        {method, "HEAD", "OPTIONS"} if method != "GET" else {"GET", "HEAD", "OPTIONS"}
    )
    return route


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        _make_http_proxy is None,
        reason="mcp_bridge not importable (need fastapi, mcp); run from deploy/docker or install deps",
    ),
]


async def test_mcp_proxy_succeeds_when_backend_responds_in_10s():
    """Simulate backend responding in 10s; with 300s limit request should succeed."""
    route = _make_fake_route("/slow", "GET")
    base_url = "http://testserver"
    proxy = _make_http_proxy(base_url, route)

    async def slow_get(*args, **kwargs):
        await asyncio.sleep(0.1)  # 100ms in test to keep CI fast (simulates "slow" > 5s in prod)
        resp = MagicMock()
        resp.status_code = 200
        resp.text = '{"ok": true}'
        resp.raise_for_status = MagicMock()
        return resp

    fake_client = MagicMock()
    fake_client.get = AsyncMock(side_effect=slow_get)
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)

    with patch("mcp_bridge.httpx.AsyncClient", return_value=fake_client):
        result = await proxy()
    assert result == '{"ok": true}'


async def test_mcp_proxy_raises_friendly_504_on_timeout():
    """When backend times out, proxy should raise HTTPException 504 with our message."""
    route = _make_fake_route("/timeout", "GET")
    base_url = "http://testserver"
    proxy = _make_http_proxy(base_url, route)

    fake_client = MagicMock()
    fake_client.get = AsyncMock(side_effect=httpx.TimeoutException("read timeout"))
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)

    with patch("mcp_bridge.httpx.AsyncClient", return_value=fake_client):
        with pytest.raises(HTTPException) as exc_info:
            await proxy()
    assert exc_info.value.status_code == 504
    assert "timed out" in exc_info.value.detail
    assert "300" in exc_info.value.detail or str(int(LLM_REQUEST_TIMEOUT)) in exc_info.value.detail
    assert "backend latency" in exc_info.value.detail.lower()


async def test_mcp_proxy_post_timeout_raises_friendly_504():
    """POST request that times out should also yield our 504 message."""
    route = _make_fake_route("/run", "POST")
    base_url = "http://testserver"
    proxy = _make_http_proxy(base_url, route)

    fake_client = MagicMock()
    fake_client.request = AsyncMock(side_effect=httpx.TimeoutException("read timeout"))
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)

    with patch("mcp_bridge.httpx.AsyncClient", return_value=fake_client):
        with pytest.raises(HTTPException) as exc_info:
            await proxy(foo="bar")
    assert exc_info.value.status_code == 504
    assert "timed out" in exc_info.value.detail
    assert "backend latency" in exc_info.value.detail.lower()
