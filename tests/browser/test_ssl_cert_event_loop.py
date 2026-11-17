"""fetch_ssl_certificate must not block the event loop.

Report 2026-11 (docker-ssl-cert-blocks-loop): the crawl strategy called the
blocking SSLCertificate.from_url() on the event loop. A host that never
finishes the TLS handshake froze the whole one-worker Docker server for the
socket timeout. Worse, once the fetch went through the in-process egress proxy,
the proxy (on the same loop) could never answer the CONNECT, so every
certificate fetch froze the server, even for normal sites.

Real Chromium. Both servers below run on the test's own event loop, like the
Docker server's egress proxy, so a blocked loop also starves them.
"""

import asyncio
import time

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai import egress_policy

RUN = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, fetch_ssl_certificate=True, page_timeout=3000)


async def _stalled_tls_port():
    """Accepts TCP and never answers the TLS handshake."""
    held = []

    async def handle(reader, writer):
        held.append(writer)
        await asyncio.sleep(3600)

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


async def _refusing_proxy():
    """An in-loop forward proxy that refuses every CONNECT at once."""
    async def handle(reader, writer):
        while (await reader.readline()) not in (b"\r\n", b""):
            pass
        writer.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"


async def _crawl_and_watch_loop(url):
    """Crawl url and return (longest pause of a 50 ms heartbeat, crawl seconds)."""
    gaps, stop = [], False

    async def heartbeat():
        last = time.monotonic()
        while not stop:
            await asyncio.sleep(0.05)
            now = time.monotonic()
            gaps.append(now - last)
            last = now

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        await crawler.arun("raw:<html><body>warm up</body></html>", config=CrawlerRunConfig())
        hb = asyncio.create_task(heartbeat())
        start = time.monotonic()
        await crawler.arun(url, config=RUN)
        took = time.monotonic() - start
        stop = True
        await hb
    return max(gaps), took


@pytest.mark.asyncio
async def test_stalled_tls_handshake_does_not_block_the_loop():
    server, port = await _stalled_tls_port()
    try:
        worst_gap, _ = await _crawl_and_watch_loop(f"https://127.0.0.1:{port}/")
    finally:
        server.close()
    assert worst_gap < 1.0, f"event loop blocked for {worst_gap:.1f}s"


@pytest.mark.asyncio
async def test_in_loop_egress_proxy_can_answer_the_certificate_fetch():
    proxy, proxy_url = await _refusing_proxy()
    egress_policy.set_egress_proxy(proxy_url)
    try:
        worst_gap, took = await _crawl_and_watch_loop("https://example.invalid/")
    finally:
        egress_policy.set_egress_proxy(None)
        proxy.close()
    assert worst_gap < 1.0, f"event loop blocked for {worst_gap:.1f}s"
    assert took < 8, f"certificate fetch waited {took:.1f}s for a proxy that answers at once"
