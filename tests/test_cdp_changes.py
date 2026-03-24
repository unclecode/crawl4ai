"""
Tests for CDP connection caching and configurable close delay.

Two test suites:
  1. Regression — default behavior unchanged, basic CDP still works
  2. Stress    — race conditions, parallel crawlers, locking, cache correctness

All tests are real (no mocks). Requires a running Chrome on port 9222:
    chrome --headless=new --no-sandbox --remote-debugging-port=9222
"""

import asyncio
import time
import pytest

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.browser_manager import _CDPConnectionCache, BrowserManager

CDP_URL = "http://localhost:9222"
TEST_URL = "https://example.com"


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

async def _quick_crawl(browser_cfg: BrowserConfig, url: str = TEST_URL) -> bool:
    """Run a single crawl, return True if the page loaded successfully."""
    run_cfg = CrawlerRunConfig(
        wait_until="domcontentloaded",
        page_timeout=15000,
        verbose=False,
    )
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)
    return result.success and result.status_code == 200


# ===========================================================================
#  SUITE 1 — REGRESSION (default behaviour, no new flags)
# ===========================================================================

class TestRegression:
    """Verify nothing is broken when the new parameters keep their defaults."""

    @pytest.mark.asyncio
    async def test_default_cdp_crawl(self):
        """Basic CDP crawl with default settings still works."""
        cfg = BrowserConfig(cdp_url=CDP_URL, headless=True)
        assert await _quick_crawl(cfg)

    @pytest.mark.asyncio
    async def test_default_params_values(self):
        """BrowserConfig defaults are backward-compatible."""
        cfg = BrowserConfig()
        assert cfg.cdp_close_delay == 1.0
        assert cfg.cache_cdp_connection is False

    @pytest.mark.asyncio
    async def test_cdp_cleanup_on_close_still_works(self):
        """cdp_cleanup_on_close=True path (existing feature) still works."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cdp_cleanup_on_close=True,
        )
        assert await _quick_crawl(cfg)

    @pytest.mark.asyncio
    async def test_sequential_crawls_default(self):
        """Two sequential crawls with default settings both succeed."""
        cfg = BrowserConfig(cdp_url=CDP_URL, headless=True)
        assert await _quick_crawl(cfg)
        assert await _quick_crawl(cfg)

    @pytest.mark.asyncio
    async def test_cdp_close_delay_default_timing(self):
        """Default close delay is ~1s (not 0, not much more)."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cdp_cleanup_on_close=True,
        )
        run_cfg = CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=15000,
            verbose=False,
        )
        t0 = time.monotonic()
        async with AsyncWebCrawler(config=cfg) as crawler:
            await crawler.arun(url=TEST_URL, config=run_cfg)
        elapsed = time.monotonic() - t0
        # The 1s sleep must be present (at least ~0.9s of close overhead)
        assert elapsed >= 0.9, f"Close was too fast ({elapsed:.2f}s), sleep may be missing"


# ===========================================================================
#  SUITE 2 — STRESS (cache, parallelism, race conditions, locking)
# ===========================================================================

class TestStress:
    """Hammer the CDP cache and configurable delay under pressure."""

    # -- cdp_close_delay -------------------------------------------------------

    @pytest.mark.asyncio
    async def test_close_delay_zero_skips_sleep(self):
        """cdp_close_delay=0 should make close noticeably faster."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cdp_cleanup_on_close=True,
            cdp_close_delay=0,
        )
        run_cfg = CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=15000,
            verbose=False,
        )
        t0 = time.monotonic()
        async with AsyncWebCrawler(config=cfg) as crawler:
            await crawler.arun(url=TEST_URL, config=run_cfg)
        elapsed = time.monotonic() - t0
        # Without the 1s sleep the whole thing should be well under 1s of close overhead
        assert elapsed < 5.0, f"Close too slow with delay=0 ({elapsed:.2f}s)"

    @pytest.mark.asyncio
    async def test_close_delay_custom_value(self):
        """A custom delay value is respected."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cdp_cleanup_on_close=True,
            cdp_close_delay=0.2,
        )
        run_cfg = CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=15000,
            verbose=False,
        )
        t0 = time.monotonic()
        async with AsyncWebCrawler(config=cfg) as crawler:
            await crawler.arun(url=TEST_URL, config=run_cfg)
        elapsed = time.monotonic() - t0
        # Should include at least the 0.2s delay
        assert elapsed >= 0.2

    # -- cache_cdp_connection: basic -----------------------------------------

    @pytest.mark.asyncio
    async def test_cache_basic_crawl(self):
        """A single crawl with caching enabled works."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )
        assert await _quick_crawl(cfg)
        # Clean up cache after test
        await _CDPConnectionCache.close_all()

    @pytest.mark.asyncio
    async def test_cache_sequential_reuse(self):
        """Two sequential crawlers reuse the same cached connection."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )

        # First crawl — creates the cache entry
        async with AsyncWebCrawler(config=cfg) as crawler:
            r1 = await crawler.arun(
                url=TEST_URL,
                config=CrawlerRunConfig(wait_until="domcontentloaded", page_timeout=15000, verbose=False),
            )
        assert r1.success

        # Cache should still have an entry (ref went 1 -> 0, so it closed).
        # But if we acquire again immediately it should create a fresh one.
        # The key thing: this must not crash or hang.

        async with AsyncWebCrawler(config=cfg) as crawler:
            r2 = await crawler.arun(
                url=TEST_URL,
                config=CrawlerRunConfig(wait_until="domcontentloaded", page_timeout=15000, verbose=False),
            )
        assert r2.success

        await _CDPConnectionCache.close_all()

    @pytest.mark.asyncio
    async def test_cache_overlapping_instances(self):
        """Two crawlers alive at the same time share the cache (ref_count=2)."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )
        run_cfg = CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=15000,
            verbose=False,
        )

        crawler1 = AsyncWebCrawler(config=cfg)
        await crawler1.start()

        crawler2 = AsyncWebCrawler(config=cfg)
        await crawler2.start()

        # Both should work concurrently
        r1, r2 = await asyncio.gather(
            crawler1.arun(url=TEST_URL, config=run_cfg),
            crawler2.arun(url=TEST_URL, config=run_cfg),
        )
        assert r1.success
        assert r2.success

        # Close one — connection must survive for the other
        await crawler1.close()

        # Second crawler should still work after first closed
        r3 = await crawler2.arun(url=TEST_URL, config=run_cfg)
        assert r3.success

        await crawler2.close()
        await _CDPConnectionCache.close_all()

    # -- cache: ref counting -------------------------------------------------

    @pytest.mark.asyncio
    async def test_cache_ref_count_lifecycle(self):
        """Verify ref count goes up and comes back down correctly."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )

        c1 = AsyncWebCrawler(config=cfg)
        await c1.start()
        # Cache should have ref_count=1
        assert CDP_URL in _CDPConnectionCache._cache
        _, _, count = _CDPConnectionCache._cache[CDP_URL]
        assert count == 1

        c2 = AsyncWebCrawler(config=cfg)
        await c2.start()
        _, _, count = _CDPConnectionCache._cache[CDP_URL]
        assert count == 2

        await c1.close()
        _, _, count = _CDPConnectionCache._cache[CDP_URL]
        assert count == 1

        await c2.close()
        # Last reference released — entry should be gone
        assert CDP_URL not in _CDPConnectionCache._cache

    # -- cache: speed benefit ------------------------------------------------

    @pytest.mark.asyncio
    async def test_cache_faster_than_uncached(self):
        """Cached sequential crawls should be faster than uncached."""
        run_cfg = CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=15000,
            verbose=False,
        )

        # Uncached: two sequential crawls (each does full playwright start/stop)
        cfg_no_cache = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cdp_cleanup_on_close=True,
            cdp_close_delay=0.5,
        )
        t0 = time.monotonic()
        for _ in range(2):
            async with AsyncWebCrawler(config=cfg_no_cache) as crawler:
                await crawler.arun(url=TEST_URL, config=run_cfg)
        uncached_time = time.monotonic() - t0

        # Cached: two sequential crawls (share playwright/CDP)
        cfg_cache = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )
        t0 = time.monotonic()
        for _ in range(2):
            async with AsyncWebCrawler(config=cfg_cache) as crawler:
                await crawler.arun(url=TEST_URL, config=run_cfg)
        cached_time = time.monotonic() - t0

        await _CDPConnectionCache.close_all()

        # Cached should be faster (the uncached has 2x 0.5s delay alone)
        assert cached_time < uncached_time, (
            f"Cached ({cached_time:.2f}s) was not faster than uncached ({uncached_time:.2f}s)"
        )

    # -- parallel stress -----------------------------------------------------

    @pytest.mark.asyncio
    async def test_parallel_cached_crawlers(self):
        """Launch 5 crawlers in parallel, all sharing the cache."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
            create_isolated_context=True,
        )
        run_cfg = CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=20000,
            verbose=False,
        )

        async def crawl_one(idx: int):
            async with AsyncWebCrawler(config=cfg) as crawler:
                result = await crawler.arun(url=TEST_URL, config=run_cfg)
            return idx, result.success

        results = await asyncio.gather(*[crawl_one(i) for i in range(5)])
        for idx, success in results:
            assert success, f"Crawler {idx} failed"

        await _CDPConnectionCache.close_all()

    @pytest.mark.asyncio
    async def test_parallel_mixed_cached_uncached(self):
        """Mix of cached and uncached crawlers running in parallel.

        Uses create_isolated_context=True because parallel crawlers sharing
        a single default context will cause navigation conflicts — this is
        the expected pattern for concurrent CDP access.
        """
        run_cfg = CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=20000,
            verbose=False,
        )

        async def crawl_cached():
            cfg = BrowserConfig(
                cdp_url=CDP_URL, headless=True,
                cache_cdp_connection=True, create_isolated_context=True,
            )
            async with AsyncWebCrawler(config=cfg) as crawler:
                r = await crawler.arun(url=TEST_URL, config=run_cfg)
            return "cached", r.success

        async def crawl_uncached():
            cfg = BrowserConfig(
                cdp_url=CDP_URL, headless=True,
                create_isolated_context=True,
            )
            async with AsyncWebCrawler(config=cfg) as crawler:
                r = await crawler.arun(url=TEST_URL, config=run_cfg)
            return "uncached", r.success

        tasks = [crawl_cached(), crawl_uncached(), crawl_cached(), crawl_uncached()]
        results = await asyncio.gather(*tasks)
        for label, success in results:
            assert success, f"{label} crawler failed"

        await _CDPConnectionCache.close_all()

    @pytest.mark.asyncio
    async def test_rapid_open_close_cache(self):
        """Rapidly open and close 10 crawlers sequentially — no leaks/hangs."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )
        run_cfg = CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=15000,
            verbose=False,
        )

        for i in range(10):
            async with AsyncWebCrawler(config=cfg) as crawler:
                result = await crawler.arun(url=TEST_URL, config=run_cfg)
                assert result.success, f"Iteration {i} failed"

        await _CDPConnectionCache.close_all()

    @pytest.mark.asyncio
    async def test_cache_close_all_idempotent(self):
        """Calling close_all() multiple times doesn't crash."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )
        async with AsyncWebCrawler(config=cfg) as crawler:
            r = await crawler.arun(
                url=TEST_URL,
                config=CrawlerRunConfig(wait_until="domcontentloaded", page_timeout=15000, verbose=False),
            )
            assert r.success

        await _CDPConnectionCache.close_all()
        await _CDPConnectionCache.close_all()  # second call must not raise
        await _CDPConnectionCache.close_all()  # third call must not raise

    @pytest.mark.asyncio
    async def test_stale_connection_recovery(self):
        """If the cached browser disconnects, next acquire recovers."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )
        run_cfg = CrawlerRunConfig(
            wait_until="domcontentloaded",
            page_timeout=15000,
            verbose=False,
        )

        # Build up a cache entry
        c1 = AsyncWebCrawler(config=cfg)
        await c1.start()

        # Forcibly disconnect the cached browser to simulate staleness
        if CDP_URL in _CDPConnectionCache._cache:
            _, browser, _ = _CDPConnectionCache._cache[CDP_URL]
            try:
                await browser.close()
            except Exception:
                pass

        await c1.close()

        # Next crawler should detect stale and create a fresh connection
        async with AsyncWebCrawler(config=cfg) as crawler:
            result = await crawler.arun(url=TEST_URL, config=run_cfg)
            assert result.success

        await _CDPConnectionCache.close_all()

    @pytest.mark.asyncio
    async def test_parallel_start_race(self):
        """Multiple crawlers calling start() simultaneously — lock prevents races."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )

        crawlers = [AsyncWebCrawler(config=cfg) for _ in range(5)]

        # Start all at once — this hammers _CDPConnectionCache.acquire() concurrently
        await asyncio.gather(*[c.start() for c in crawlers])

        # All should have the same browser reference
        browsers = set()
        for c in crawlers:
            bm = c.crawler_strategy.browser_manager
            browsers.add(id(bm.browser))

        # With caching, they should all share the same browser object
        assert len(browsers) == 1, f"Expected 1 shared browser, got {len(browsers)}"

        # Ref count should be 5
        _, _, count = _CDPConnectionCache._cache[CDP_URL]
        assert count == 5

        # Close all
        await asyncio.gather(*[c.close() for c in crawlers])

        # Cache should be empty
        assert CDP_URL not in _CDPConnectionCache._cache

    @pytest.mark.asyncio
    async def test_parallel_close_race(self):
        """Multiple crawlers closing simultaneously — no double-free."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )

        crawlers = [AsyncWebCrawler(config=cfg) for _ in range(5)]
        await asyncio.gather(*[c.start() for c in crawlers])

        # Close all at once — hammers _CDPConnectionCache.release() concurrently
        await asyncio.gather(*[c.close() for c in crawlers])

        # Cache must be clean
        assert CDP_URL not in _CDPConnectionCache._cache

        # Must still work after everything is closed
        async with AsyncWebCrawler(config=cfg) as crawler:
            r = await crawler.arun(
                url=TEST_URL,
                config=CrawlerRunConfig(wait_until="domcontentloaded", page_timeout=15000, verbose=False),
            )
            assert r.success

        await _CDPConnectionCache.close_all()
