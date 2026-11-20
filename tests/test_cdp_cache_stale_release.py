"""A stale cached CDP connection's late release must not close its replacement.

When the cached connection dies, the next acquire() drops it and caches a new
one with count 1. Before the fix, release() never checked which connection the
caller held, so the old user's close() then closed the NEW connection, and
every crawler on it failed. The pool's dead-browser recovery hit this on every
relaunch (#842).

Runs against a real Chromium started with a remote-debugging port.
"""
import asyncio
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.browser_manager import BrowserManager, _CDPConnectionCache


class _Page(BaseHTTPRequestHandler):
    def do_GET(self):
        # Enough text that the anti-bot check does not call it an empty page.
        text = "<p>This page is served by the test to prove the browser works.</p>" * 40
        body = f"<html><body><h1>alive</h1>{text}</body></html>".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


# A real page, so a crawl goes through the browser (raw:// HTML skips it).
_server = ThreadingHTTPServer(("127.0.0.1", 0), _Page)
threading.Thread(target=_server.serve_forever, daemon=True).start()
PAGE_URL = f"http://127.0.0.1:{_server.server_port}/"


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest_asyncio.fixture
async def cdp_url():
    port = _free_port()
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=[f"--remote-debugging-port={port}"]
        )
        yield f"http://127.0.0.1:{port}"
        await _CDPConnectionCache.close_all()
        await browser.close()


def _cfg(url):
    return BrowserConfig(headless=True, cdp_url=url, cache_cdp_connection=True)


async def _manager(url):
    bm = BrowserManager(browser_config=_cfg(url))
    await bm.start()
    return bm


async def _drop_connection(bm):
    """Make bm's cached connection stale, the way a crash or network drop does."""
    await bm.browser.close()  # for connect_over_cdp this only disconnects
    assert not bm.browser.is_connected()


@pytest.mark.asyncio
async def test_stale_release_keeps_replacement_alive(cdp_url):
    old = await _manager(cdp_url)
    await _drop_connection(old)
    new = await _manager(cdp_url)
    assert new.browser is not old.browser

    await old.close()  # the late release from the stale user

    assert new.browser.is_connected(), "old close() killed the new connection"
    assert _CDPConnectionCache._cache[cdp_url][2] == 1
    await new.close()
    assert cdp_url not in _CDPConnectionCache._cache


@pytest.mark.asyncio
async def test_many_stale_users_release_after_replacement(cdp_url):
    stale = [await _manager(cdp_url) for _ in range(3)]
    assert len({id(m.browser) for m in stale}) == 1  # all share one connection
    await _drop_connection(stale[0])
    new = await _manager(cdp_url)

    await asyncio.gather(*(m.close() for m in stale))

    assert new.browser.is_connected()
    assert _CDPConnectionCache._cache[cdp_url][2] == 1
    await new.close()


@pytest.mark.asyncio
async def test_shared_refcount_unchanged(cdp_url):
    """No regression: healthy sharers still count down and the last one closes."""
    a, b = await _manager(cdp_url), await _manager(cdp_url)
    assert a.browser is b.browser
    assert _CDPConnectionCache._cache[cdp_url][2] == 2

    await a.close()
    assert b.browser.is_connected()
    assert _CDPConnectionCache._cache[cdp_url][2] == 1

    browser = b.browser
    await b.close()
    assert cdp_url not in _CDPConnectionCache._cache
    assert not browser.is_connected()


@pytest.mark.asyncio
async def test_release_without_browser_keeps_old_behavior(cdp_url):
    """Callers that pass no browser still decrement, as before."""
    a, b = await _manager(cdp_url), await _manager(cdp_url)
    await _CDPConnectionCache.release(cdp_url)
    assert _CDPConnectionCache._cache[cdp_url][2] == 1
    await _CDPConnectionCache.release(cdp_url)
    assert cdp_url not in _CDPConnectionCache._cache
    a._using_cached_cdp = b._using_cached_cdp = False  # already released


@pytest.mark.asyncio
async def test_crawl_works_after_stale_crawler_closes(cdp_url):
    old = AsyncWebCrawler(config=_cfg(cdp_url))
    await old.start()
    await _drop_connection(old.crawler_strategy.browser_manager)
    new = AsyncWebCrawler(config=_cfg(cdp_url))
    await new.start()

    await old.close()

    result = await new.arun(PAGE_URL, config=CrawlerRunConfig())
    assert result.success, result.error_message
    assert "alive" in result.html
    await new.close()
