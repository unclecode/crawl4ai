"""The library's own HTTP clients honour the installed egress proxy.

Two SSRF reports (2026-09) came from the same root cause: AsyncUrlSeeder and
RobotsParser build HTTP clients that never go through the Docker server's
egress broker. The fix is one `proxy=` kwarg per client, fed from
crawl4ai.egress_policy. These tests pin both halves of that: the proxy is used
when installed, and nothing changes for plain-library users when it is not.

No network and no server: everything here is client construction.
"""

import asyncio

import aiohttp
import pytest

from crawl4ai import egress_policy
from crawl4ai.async_url_seeder import AsyncUrlSeeder
from crawl4ai.utils import RobotsParser

PROXY = "http://127.0.0.1:9"  # discard port; nothing here connects


@pytest.fixture(autouse=True)
def _reset_proxy():
    """The proxy URL is a module-level global; leaking it breaks later tests."""
    yield
    egress_policy.set_egress_proxy(None)


def _proxy_transport(client):
    """The transport httpx would use for an outbound URL, or None if direct."""
    import httpx

    transport = client._transport_for_url(httpx.URL("http://example.com/"))
    return transport if transport is not client._transport else None


# ── seeder ─────────────────────────────────────────────────────────────


def test_seeder_client_has_no_proxy_by_default():
    """Plain-library use must behave exactly as it did before the fix."""
    seeder = AsyncUrlSeeder()
    try:
        assert seeder.client._mounts == {}
        assert _proxy_transport(seeder.client) is None
    finally:
        asyncio.run(seeder.client.aclose())


def test_seeder_client_uses_installed_proxy():
    egress_policy.set_egress_proxy(PROXY)
    seeder = AsyncUrlSeeder()
    try:
        assert _proxy_transport(seeder.client) is not None
    finally:
        asyncio.run(seeder.client.aclose())


def test_seeder_keeps_http2_through_proxy():
    """The proxy must not cost the seeder HTTP/2.

    Passing `transport=` to httpx.AsyncClient silently drops http2=True; the
    `proxy=` kwarg does not, and httpcore negotiates h2 inside the CONNECT
    tunnel. This test is what stops that regression sneaking back in.
    """
    egress_policy.set_egress_proxy(PROXY)
    seeder = AsyncUrlSeeder()
    try:
        transport = _proxy_transport(seeder.client)
        assert transport._pool._http2 is True
    finally:
        asyncio.run(seeder.client.aclose())


def test_collinfo_client_uses_installed_proxy():
    """The throwaway client in _latest_index is a second construction site."""
    import inspect

    src = inspect.getsource(AsyncUrlSeeder._latest_index)
    assert "httpx.AsyncClient(proxy=proxy_url())" in src


# ── robots.txt ─────────────────────────────────────────────────────────


class _FakeResponse:
    status = 404

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _record_robots_get(monkeypatch):
    """Capture the kwargs RobotsParser hands aiohttp, without any network."""
    calls = []

    def fake_get(self, url, **kwargs):
        calls.append((url, kwargs))
        return _FakeResponse()

    monkeypatch.setattr(aiohttp.ClientSession, "get", fake_get)
    return calls


def test_robots_fetch_passes_proxy(monkeypatch, tmp_path):
    calls = _record_robots_get(monkeypatch)
    egress_policy.set_egress_proxy(PROXY)

    parser = RobotsParser(cache_dir=str(tmp_path))
    asyncio.run(parser.can_fetch("http://example.com/x", "bot"))

    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "http://example.com/robots.txt"
    assert kwargs["proxy"] == PROXY


def test_robots_fetch_is_direct_by_default(monkeypatch, tmp_path):
    calls = _record_robots_get(monkeypatch)

    parser = RobotsParser(cache_dir=str(tmp_path))
    asyncio.run(parser.can_fetch("http://example.com/x", "bot"))

    assert calls[0][1]["proxy"] is None


def test_robots_fetch_no_longer_disables_tls_verification(monkeypatch, tmp_path):
    """ssl=False made every robots fetch accept any certificate."""
    calls = _record_robots_get(monkeypatch)

    parser = RobotsParser(cache_dir=str(tmp_path))
    asyncio.run(parser.can_fetch("https://example.com/x", "bot"))

    assert calls[0][1].get("ssl", None) is None


# ── untrusted LinkPreviewConfig clamps ─────────────────────────────────


@pytest.mark.parametrize(
    "field,asked,expected",
    [
        ("max_links", 10_000_000, 100),
        ("max_links", 0, 100),
        ("concurrency", 10_000, 10),
        ("timeout", 3600, 10),
        ("max_links", 5, 5),  # a reasonable value survives
    ],
)
def test_link_preview_untrusted_values_are_clamped(field, asked, expected):
    from crawl4ai.async_configs import _enforce_untrusted

    out = _enforce_untrusted("LinkPreviewConfig", {field: asked})
    assert out[field] == expected
