"""
crawl_timeout must bound the whole page visit, not just navigation.

A page whose JS thread goes busy right after load navigates fine, then every
post-navigation call (evaluate / content) would wait forever. With crawl_timeout
set the crawl must fail within it and leave no page or refcount behind.
"""
import asyncio
import http.server
import socketserver
import threading
import time

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

TRAP_HTML = b"""<!doctype html><html><head><title>trap</title></head><body><p>hi</p>
<script>document.addEventListener('DOMContentLoaded',function(){setTimeout(function(){while(true){}},0);});</script>
</body></html>"""
OK_HTML = b"<html><body><p>ok</p>" + b"<p>filler text so the anti-bot check does not flag a near-empty page</p>" * 20 + b"</body></html>"


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(TRAP_HTML if self.path == "/trap" else OK_HTML)

    def log_message(self, *args):
        pass


@pytest.fixture
def base_url():
    srv = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def _cfg(**kw):
    return CrawlerRunConfig(crawl_timeout=5000, cache_mode=CacheMode.BYPASS, **kw)


@pytest.mark.asyncio
async def test_trap_page_fails_within_crawl_timeout_and_leaks_nothing(base_url):
    cfg = _cfg()
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        t0 = time.perf_counter()
        result = await asyncio.wait_for(crawler.arun(base_url + "/trap", config=cfg), 20)
        elapsed = time.perf_counter() - t0

        assert result.success is False
        assert "exceeded crawl_timeout" in result.error_message
        assert elapsed < 10, f"took {elapsed:.1f}s, crawl_timeout was 5s"

        bm = crawler.crawler_strategy.browser_manager
        open_urls = [p.url for c in bm.browser.contexts for p in c.pages]
        assert base_url + "/trap" not in open_urls, open_urls
        assert bm._context_refcounts.get(bm._make_config_signature(cfg), 0) == 0


@pytest.mark.asyncio
async def test_trap_page_with_overlay_removal_does_not_hang(base_url):
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        result = await asyncio.wait_for(
            crawler.arun(base_url + "/trap", config=_cfg(remove_overlay_elements=True)), 20
        )
        assert result.success is False
        assert "exceeded crawl_timeout" in result.error_message


@pytest.mark.asyncio
async def test_trap_session_is_dropped_and_next_crawl_works(base_url):
    cfg = _cfg(session_id="trap-session")
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        bm = crawler.crawler_strategy.browser_manager
        result = await asyncio.wait_for(crawler.arun(base_url + "/trap", config=cfg), 20)
        assert result.success is False
        assert "trap-session" not in bm.sessions

        result = await asyncio.wait_for(crawler.arun(base_url + "/ok", config=cfg), 20)
        assert result.success is True
        assert "ok" in result.html
        assert "trap-session" in bm.sessions  # normal crawl keeps the session page


@pytest.mark.asyncio
async def test_no_crawl_timeout_means_no_limit(base_url):
    """Default None must not cut a crawl; the trap page is bounded only by the test's own guard."""
    cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    assert cfg.crawl_timeout is None
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        task = asyncio.create_task(crawler.arun(base_url + "/trap", config=cfg))
        done, _ = await asyncio.wait({task}, timeout=8)
        assert not done, "crawl finished without a crawl_timeout; expected it to still be running"
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        bm = crawler.crawler_strategy.browser_manager
        assert bm._context_refcounts.get(bm._make_config_signature(cfg), 0) == 0
        assert sum(len(c.pages) for c in bm.browser.contexts) <= 1


@pytest.mark.asyncio
async def test_keep_last_page_rule_unchanged(base_url):
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        bm = crawler.crawler_strategy.browser_manager
        for _ in range(3):
            assert (await crawler.arun(base_url + "/ok", config=_cfg())).success
        assert sum(len(c.pages) for c in bm.browser.contexts) <= 1


@pytest.mark.asyncio
async def test_cancel_during_cleanup_still_closes_page(base_url):
    """A cancel landing inside the finally's console cleanup must not skip page close."""
    cfg = _cfg(capture_console_messages=True)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        bm = crawler.crawler_strategy.browser_manager
        in_cleanup = asyncio.Event()

        async def slow_cleanup(page, *args):
            in_cleanup.set()
            await asyncio.sleep(2)

        crawler.crawler_strategy.adapter.cleanup_console_capture = slow_cleanup

        task = asyncio.create_task(crawler.arun(base_url + "/ok", config=cfg))
        await asyncio.wait_for(in_cleanup.wait(), 20)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert bm._context_refcounts.get(bm._make_config_signature(cfg), 0) == 0
        assert sum(len(c.pages) for c in bm.browser.contexts) <= 1


@pytest.mark.asyncio
async def test_hung_cleanup_does_not_block_crawl_timeout(base_url):
    """An evaluate inside cleanup (UndetectedAdapter does this) hangs on a trap page; the 5 s cleanup bound must let the crawl fail."""
    cfg = _cfg(capture_console_messages=True)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        async def evaluate_in_cleanup(page, *args):
            return await page.evaluate("1")

        crawler.crawler_strategy.adapter.cleanup_console_capture = evaluate_in_cleanup

        t0 = time.perf_counter()
        result = await asyncio.wait_for(crawler.arun(base_url + "/trap", config=cfg), 30)
        assert not result.success
        assert "exceeded crawl_timeout" in result.error_message
        assert time.perf_counter() - t0 < 20
        bm = crawler.crawler_strategy.browser_manager
        assert bm._context_refcounts.get(bm._make_config_signature(cfg), 0) == 0
        assert all(p.url != base_url + "/trap" for c in bm.browser.contexts for p in c.pages)
