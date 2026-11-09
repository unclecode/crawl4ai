"""
Tests for #2490: only complete, successful crawls are written to the cache.

A cached row is replayed as a success, so a failed or partial result must not
be stored. Runs offline against a local server, with a temporary cache.
"""
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import pytest_asyncio

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from crawl4ai.async_database import async_db_manager
from crawl4ai.models import CrawlResult, MarkdownGenerationResult
from crawl4ai.utils import ensure_content_dirs

FULL_PAGE = b"<html><head><title>t</title></head><body><h1>Hello</h1><p>" + b"real page text " * 60 + b"</p></body></html>"
BLOCKED_PAGE = b"<html><body>no</body></html>"


class Site:
    """A local site that can be switched on and off on a stable port."""

    def __init__(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self.body = FULL_PAGE
        self.server = None

    def url(self, path="page"):
        return f"http://127.0.0.1:{self.port}/{path}"

    def up(self):
        site = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(site.body)))
                self.end_headers()
                self.wfile.write(site.body)

            def log_message(self, *args):
                pass

        ThreadingHTTPServer.allow_reuse_address = True
        self.server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def down(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None


@pytest_asyncio.fixture
async def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(async_db_manager, "db_path", str(tmp_path / "crawl4ai.db"))
    monkeypatch.setattr(async_db_manager, "content_paths", ensure_content_dirs(str(tmp_path)))
    # initialize() would otherwise mark the real cache as migrated
    monkeypatch.setattr(async_db_manager.version_manager, "needs_update", lambda: False)
    await async_db_manager.ainit_db()
    await async_db_manager.update_db_schema()
    yield async_db_manager
    await async_db_manager.cleanup()


@pytest.fixture
def site():
    s = Site()
    yield s
    s.down()


async def crawl(url, mode=CacheMode.ENABLED, **config):
    async with AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy(), verbose=False) as crawler:
        return await crawler.arun(url, config=CrawlerRunConfig(cache_mode=mode, max_retries=1, **config))


@pytest.mark.asyncio
async def test_failed_crawl_reports_its_own_error(cache, site):
    result = await crawl(site.url())

    assert not result.success
    assert result.error_message.startswith("All proxies failed: Connection failed")
    assert "validation error" not in result.error_message
    assert await cache.aget_cached_url(site.url()) is None


@pytest.mark.asyncio
async def test_failure_does_not_stop_later_caching(cache, site):
    await crawl(site.url())

    site.up()
    assert (await crawl(site.url())).success
    site.down()

    replay = await crawl(site.url())
    assert replay.success and replay.cache_status == "hit"


@pytest.mark.asyncio
async def test_failure_keeps_good_cached_copy(cache, site):
    site.up()
    assert (await crawl(site.url())).success
    site.down()

    assert not (await crawl(site.url(), CacheMode.WRITE_ONLY)).success

    replay = await crawl(site.url())
    assert replay.success and replay.cache_status == "hit"
    assert "real page text" in replay.markdown


@pytest.mark.asyncio
async def test_blocked_page_is_not_replayed_as_success(cache, site):
    site.body = BLOCKED_PAGE
    site.up()

    first = await crawl(site.url())
    second = await crawl(site.url())

    assert not first.success and "Blocked" in first.error_message
    assert not second.success and second.cache_status != "hit"


@pytest.mark.asyncio
async def test_prefetch_does_not_fill_cache_with_partial_result(cache, site):
    site.up()

    prefetch = await crawl(site.url(), prefetch=True)
    assert prefetch.success and prefetch.html

    full = await crawl(site.url())
    assert full.success and full.cache_status == "miss"
    assert "real page text" in full.markdown


@pytest.mark.asyncio
async def test_successful_crawl_is_still_cached(cache, site):
    site.up()
    first = await crawl(site.url())
    second = await crawl(site.url())

    assert first.cache_status == "miss"
    assert second.cache_status == "hit"
    assert str(second.markdown) == str(first.markdown)


@pytest.mark.asyncio
async def test_cache_write_handles_result_without_markdown(cache):
    url = "https://example.invalid/no-markdown"
    await cache.acache_url(CrawlResult(url=url, html="<p>x</p>", success=True))

    assert (await cache.aget_cached_url(url)).html == "<p>x</p>"


def test_markdown_result_defaults_to_empty():
    empty = MarkdownGenerationResult()
    assert (empty.raw_markdown, empty.markdown_with_citations, empty.references_markdown) == ("", "", "")
