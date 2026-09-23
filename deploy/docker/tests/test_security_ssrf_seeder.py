"""SSRF on the library's own HTTP clients (2026-09 reports), end to end.

Two channels fetched a caller-influenced URL without going through the egress
broker: AsyncUrlSeeder (link previews, sitemaps) and RobotsParser. The seeder
one was not blind -- the internal page's parsed <head> came back to the API
caller in result.links[*].head_data.

These run the real PinningProxy over real loopback sockets with the real
resolve_and_pin rule, so 127.0.0.1 and 169.254.169.254 are refused because they
genuinely are not global. Only "public.example" is stubbed, to stand in for a
global host without touching the network.
"""

import asyncio
import sqlite3

import pytest
from aiohttp import web

import egress_proxy
from egress_broker import PinnedTarget, resolve_and_pin
from egress_proxy import PinningProxy

from crawl4ai import egress_policy
from crawl4ai.async_url_seeder import AsyncUrlSeeder
from crawl4ai.utils import RobotsParser

pytestmark = pytest.mark.posture

INTERNAL_PAGE = (
    '<html><head><title>INTERNAL-MARKER</title>'
    '<meta name="secret" content="internal-only"></head><body>x</body></html>'
)

_PROXY_ENV = (
    "CRAWL4AI_UPSTREAM_PROXY", "HTTP_PROXY", "http_proxy",
    "HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy",
)


@pytest.fixture(autouse=True)
def _clear_proxy_env(monkeypatch):
    for name in _PROXY_ENV:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def _reset_library_proxy():
    yield
    egress_policy.set_egress_proxy(None)


async def _serve(handler):
    """Start a loopback HTTP server; return (runner, port)."""
    app = web.Application()
    app.router.add_get("/{tail:.*}", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    return runner, site._server.sockets[0].getsockname()[1]


async def _start_proxy():
    proxy = PinningProxy()
    egress_policy.set_egress_proxy(await proxy.start())
    return proxy


def _treat_port_as_public(monkeypatch, port):
    """Let one loopback port through the proxy as if it were a global host.

    Everything else keeps the real not-is_global rule, so the "internal"
    service on its own port is still refused. Using a loopback port rather
    than a made-up hostname matters: the unfixed code must be able to reach
    the first hop, or the test would pass for the wrong reason.
    """
    def fake_pin(url):
        if f":{port}" in url:
            return PinnedTarget("http", "127.0.0.1", port, "127.0.0.1")
        return resolve_and_pin(url)
    monkeypatch.setattr(egress_proxy, "resolve_and_pin", fake_pin)


@pytest.mark.asyncio
class TestSeederEgress:
    async def test_seeder_head_resolution_to_loopback_is_blocked(self):
        """_resolve_head is a separate sink from the head fetch."""
        hits = []

        async def internal(req):
            hits.append(req.path)
            return web.Response(text=INTERNAL_PAGE, content_type="text/html")

        runner, port = await _serve(internal)
        proxy = await _start_proxy()
        seeder = AsyncUrlSeeder()
        try:
            assert await seeder._resolve_head(f"http://127.0.0.1:{port}/") is None
            assert hits == []
        finally:
            await seeder.client.aclose()
            await proxy.stop()
            await runner.cleanup()

    async def test_seeder_direct_loopback_is_blocked(self):
        hits = []

        async def internal(req):
            hits.append(req.path)
            return web.Response(text=INTERNAL_PAGE, content_type="text/html")

        runner, port = await _serve(internal)
        proxy = await _start_proxy()
        seeder = AsyncUrlSeeder()
        try:
            res = await seeder.extract_head_for_urls(
                [f"http://127.0.0.1:{port}/secret"]
            )
            assert hits == [], "the internal service was reached"
            assert not (res[0].get("head_data") or {}).get("title")
        finally:
            await seeder.client.aclose()
            await proxy.stop()
            await runner.cleanup()

    async def test_seeder_redirect_into_internal_is_blocked(self, monkeypatch):
        """A public first hop must not become a free pass for the second."""
        hits = []

        async def internal(req):
            hits.append(req.path)
            return web.Response(text=INTERNAL_PAGE, content_type="text/html")

        irunner, iport = await _serve(internal)

        async def public(req):
            raise web.HTTPFound(f"http://127.0.0.1:{iport}/secret")

        prunner, pport = await _serve(public)
        _treat_port_as_public(monkeypatch, pport)

        proxy = await _start_proxy()
        seeder = AsyncUrlSeeder()
        try:
            ok, html, final = await seeder._fetch_head(
                f"http://127.0.0.1:{pport}/page", timeout=5
            )
            assert hits == [], "the redirect reached the internal service"
            assert "INTERNAL-MARKER" not in html, "the internal page came back"
        finally:
            await seeder.client.aclose()
            await proxy.stop()
            await prunner.cleanup()
            await irunner.cleanup()

    async def test_seeder_public_host_still_works(self, monkeypatch):
        """The fix must not simply block everything."""
        async def public(req):
            return web.Response(
                text='<html><head><title>PUBLIC-OK</title></head><body>x</body></html>',
                content_type="text/html",
            )

        runner, port = await _serve(public)
        _treat_port_as_public(monkeypatch, port)

        proxy = await _start_proxy()
        seeder = AsyncUrlSeeder()
        try:
            res = await seeder.extract_head_for_urls(
                [f"http://127.0.0.1:{port}/page"]
            )
            assert (res[0].get("head_data") or {}).get("title") == "PUBLIC-OK"
        finally:
            await seeder.client.aclose()
            await proxy.stop()
            await runner.cleanup()


@pytest.mark.asyncio
class TestRobotsEgress:
    async def test_robots_fetch_to_loopback_is_blocked(self, tmp_path):
        hits = []

        async def internal(req):
            hits.append(req.path)
            return web.Response(text="User-agent: *\nDisallow: /secret\n")

        runner, port = await _serve(internal)
        proxy = await _start_proxy()
        parser = RobotsParser(cache_dir=str(tmp_path))
        try:
            # Unchanged contract: every failure on this path fails open.
            assert await parser.can_fetch(
                f"http://127.0.0.1:{port}/secret", "bot"
            ) is True
            assert hits == [], "the internal service was reached"
            with sqlite3.connect(parser.db_path) as conn:
                rows = conn.execute("SELECT domain FROM robots_cache").fetchall()
            # The load-bearing assertion: nothing internal was fetched, so
            # nothing internal got persisted for the 7-day cache TTL.
            assert rows == []
        finally:
            await proxy.stop()
            await runner.cleanup()

    async def test_robots_fetch_follows_redirect_into_internal_no_further(
        self, monkeypatch, tmp_path
    ):
        hits = []

        async def internal(req):
            hits.append(req.path)
            return web.Response(text="User-agent: *\nDisallow: /secret\n")

        irunner, iport = await _serve(internal)

        async def public(req):
            raise web.HTTPFound(f"http://127.0.0.1:{iport}/robots.txt")

        prunner, pport = await _serve(public)
        _treat_port_as_public(monkeypatch, pport)

        proxy = await _start_proxy()
        parser = RobotsParser(cache_dir=str(tmp_path))
        try:
            await parser.can_fetch(f"http://127.0.0.1:{pport}/secret", "bot")
            assert hits == [], "robots fetch followed the redirect into loopback"
        finally:
            await proxy.stop()
            await prunner.cleanup()
            await irunner.cleanup()
