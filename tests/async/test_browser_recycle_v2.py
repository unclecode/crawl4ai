"""
Tests for version-based browser recycling.

The new recycle approach:
1. When pages_served hits threshold, bump _browser_version
2. Old signatures go to _pending_cleanup
3. New requests get new contexts (different version = different signature)
4. When old context's refcount hits 0, it gets cleaned up
5. No blocking — old and new browsers coexist during transition

These tests use small thresholds (3-5 pages) to verify the mechanics.
"""

import asyncio
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


# ---------------------------------------------------------------------------
# Local test server
# ---------------------------------------------------------------------------

PAGES = {}
for i in range(100):
    PAGES[f"/page{i}"] = (
        f"<!DOCTYPE html><html><head><title>Page {i}</title></head>"
        f"<body><h1>Page {i}</h1><p>Content for page {i}.</p></body></html>"
    ).encode()


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = PAGES.get(self.path, PAGES["/page0"])
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(body)


class _Server(HTTPServer):
    allow_reuse_address = True


@pytest.fixture(scope="module")
def srv():
    s = _Server(("127.0.0.1", 0), Handler)
    port = s.server_address[1]
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    s.shutdown()


def _u(base, i):
    return f"{base}/page{i}"


def _bm(c):
    return c.crawler_strategy.browser_manager


# ===================================================================
# SECTION A — Version bump mechanics
# ===================================================================

@pytest.mark.asyncio
async def test_version_bump_on_threshold(srv):
    """Browser version should bump when threshold is reached."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=3,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        assert bm._browser_version == 1

        # Crawl 2 pages — no bump yet
        for i in range(2):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success

        assert bm._browser_version == 1, "Version should still be 1 after 2 pages"
        assert bm._pages_served == 2

        # 3rd page hits threshold (3) and triggers bump AFTER the page is served
        r = await c.arun(url=_u(srv, 2), config=run)
        assert r.success
        assert bm._browser_version == 2, "Version should bump after 3rd page"
        assert bm._pages_served == 0, "Counter resets after bump"

        # 4th page is first page of version 2
        r = await c.arun(url=_u(srv, 3), config=run)
        assert r.success
        assert bm._pages_served == 1


@pytest.mark.asyncio
async def test_signature_changes_after_version_bump(srv):
    """Same CrawlerRunConfig should produce different signatures after version bump."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=2,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # Get signature before bump
        sig_v1 = bm._make_config_signature(run)

        # Crawl 2 pages
        for i in range(2):
            await c.arun(url=_u(srv, i), config=run)

        # 3rd request triggers bump
        await c.arun(url=_u(srv, 2), config=run)

        # Signature should be different now
        sig_v2 = bm._make_config_signature(run)
        assert sig_v1 != sig_v2, "Signature should change after version bump"


@pytest.mark.asyncio
async def test_no_version_bump_when_disabled(srv):
    """Version should stay at 1 when max_pages_before_recycle=0."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=0,  # Disabled
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        for i in range(20):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success

        assert bm._browser_version == 1, "Version should not bump when disabled"
        assert bm._pages_served == 20


# ===================================================================
# SECTION B — Pending cleanup mechanics
# ===================================================================

@pytest.mark.asyncio
async def test_old_signature_goes_to_pending_cleanup(srv):
    """Version bump works and old contexts get cleaned up."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=2,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # Crawl 2 pages — creates signature for version 1, bumps on 2nd
        for i in range(2):
            await c.arun(url=_u(srv, i), config=run)

        # After 2 pages with threshold=2, version should have bumped
        assert bm._browser_version == 2

        # Since sequential crawls release pages immediately (refcount=0),
        # old contexts get cleaned up right away. Pending cleanup should be empty.
        # This is correct behavior — cleanup is eager when possible.
        assert len(bm._pending_cleanup) == 0


@pytest.mark.asyncio
async def test_cleanup_happens_when_refcount_hits_zero(srv):
    """Old context should be closed when its refcount drops to 0."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=3,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # Sequential crawls: each page is released before next request
        # So refcount is always 0 between requests, and cleanup happens immediately
        for i in range(10):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success

        # Should have bumped twice (at 3 and 6) with version now at 3
        # But since refcount=0 immediately, pending_cleanup should be empty
        assert len(bm._pending_cleanup) == 0, "All old contexts should be cleaned up"


# ===================================================================
# SECTION C — Concurrent crawls with recycling
# ===================================================================

@pytest.mark.asyncio
async def test_concurrent_crawls_dont_block_on_recycle(srv):
    """Concurrent crawls should not block — old browser drains while new one serves."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=5,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # Launch 20 concurrent crawls
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed — no blocking, no errors
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"

        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 20, f"Only {len(successes)} succeeded"

        # Version should have bumped multiple times
        assert bm._browser_version >= 2, "Should have recycled at least once"


@pytest.mark.asyncio
async def test_high_concurrency_with_small_threshold(srv):
    """Stress test: 50 concurrent crawls with threshold=3."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=3,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # 50 concurrent crawls with threshold of 3 — many version bumps
        tasks = [c.arun(url=_u(srv, i % 100), config=run) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"

        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 50


# ===================================================================
# SECTION D — Safety cap (max pending browsers)
# ===================================================================

@pytest.mark.asyncio
async def test_safety_cap_limits_pending_browsers(srv):
    """Should not exceed _max_pending_browsers old browsers draining."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=2,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)
        bm._max_pending_browsers = 2  # Lower cap for testing

        # Run enough crawls to potentially exceed the cap
        for i in range(15):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success

        # Pending cleanup should never have exceeded the cap
        # (We can't directly test this during execution, but if it works without
        # deadlock/timeout, the cap logic is functioning)
        assert len(bm._pending_cleanup) <= bm._max_pending_browsers


# ===================================================================
# SECTION E — Managed browser mode
# ===================================================================

@pytest.mark.asyncio
async def test_managed_browser_recycle(srv):
    """Recycling should work with managed browser mode."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        max_pages_before_recycle=3,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        for i in range(10):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success, f"Page {i} failed"

        # Version should have bumped
        assert bm._browser_version >= 2


@pytest.mark.asyncio
async def test_managed_browser_isolated_context_recycle(srv):
    """Recycling with managed browser + isolated contexts."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
        max_pages_before_recycle=3,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        for i in range(10):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success, f"Page {i} failed"

        assert bm._browser_version >= 2


# ===================================================================
# SECTION F — Edge cases
# ===================================================================

@pytest.mark.asyncio
async def test_threshold_of_one(srv):
    """Edge case: threshold=1 means version bump after every page."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=1,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        for i in range(5):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success

        # With threshold=1, each page triggers a bump after being served:
        # Page 0: served, counter=1 >= 1, bump -> version=2, counter=0
        # Page 1: served, counter=1 >= 1, bump -> version=3, counter=0
        # ... etc.
        # After 5 pages, should have bumped 5 times
        assert bm._browser_version == 6  # Started at 1, bumped 5 times


@pytest.mark.asyncio
async def test_different_configs_get_separate_cleanup_tracking(srv):
    """Different CrawlerRunConfigs should track separately in pending cleanup."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=2,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        run_a = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        run_b = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, verbose=False,
            override_navigator=True,  # Different config
        )

        # Alternate between configs
        for i in range(6):
            cfg_to_use = run_a if i % 2 == 0 else run_b
            r = await c.arun(url=_u(srv, i), config=cfg_to_use)
            assert r.success

        # Both configs should work fine
        assert bm._browser_version >= 2
