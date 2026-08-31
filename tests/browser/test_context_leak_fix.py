"""
Integration tests for the browser context memory leak fix.

Tests:
1. Signature shrink: non-context fields produce same hash
2. Signature correctness: context-affecting fields produce different hashes
3. Refcount lifecycle: increment on get_page, decrement on release
4. LRU eviction: oldest idle context is evicted when over limit
5. Eviction respects active refcounts
6. Real browser: contexts don't leak under varying configs
7. Real browser: batch crawl reuses same context
8. Storage state path: temporary context is closed
"""
import asyncio
import time
import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import ProxyConfig, GeolocationConfig
from crawl4ai.browser_manager import BrowserManager


# ── Unit tests (no browser needed) ──────────────────────────────────────

class TestSignatureShrink:
    """Verify the whitelist signature only considers context-affecting fields."""

    def _bm(self):
        return BrowserManager(BrowserConfig(), logger=None)

    def test_non_context_fields_same_signature(self):
        """Fields that don't affect browser context must produce identical sigs."""
        bm = self._bm()
        configs = [
            CrawlerRunConfig(word_count_threshold=200),
            CrawlerRunConfig(word_count_threshold=50),
            CrawlerRunConfig(css_selector=".main"),
            CrawlerRunConfig(screenshot=True),
            CrawlerRunConfig(pdf=True, verbose=False),
            CrawlerRunConfig(scan_full_page=True, scroll_delay=0.5),
            CrawlerRunConfig(only_text=True),
            CrawlerRunConfig(wait_until="networkidle", page_timeout=30000),
            CrawlerRunConfig(capture_network_requests=True),
            CrawlerRunConfig(exclude_external_links=True),
        ]
        sigs = [bm._make_config_signature(c) for c in configs]
        assert len(set(sigs)) == 1, (
            f"Expected all same sig, got {len(set(sigs))} unique: {sigs[:3]}"
        )

    def test_proxy_changes_signature(self):
        bm = self._bm()
        c1 = CrawlerRunConfig()
        c2 = CrawlerRunConfig(proxy_config=ProxyConfig(server="http://p1:8080"))
        c3 = CrawlerRunConfig(proxy_config=ProxyConfig(server="http://p2:8080"))
        s1 = bm._make_config_signature(c1)
        s2 = bm._make_config_signature(c2)
        s3 = bm._make_config_signature(c3)
        assert s1 != s2, "proxy vs no-proxy should differ"
        assert s2 != s3, "different proxies should differ"

    def test_locale_changes_signature(self):
        bm = self._bm()
        s1 = bm._make_config_signature(CrawlerRunConfig())
        s2 = bm._make_config_signature(CrawlerRunConfig(locale="en-US"))
        s3 = bm._make_config_signature(CrawlerRunConfig(locale="fr-FR"))
        assert s1 != s2
        assert s2 != s3

    def test_timezone_changes_signature(self):
        bm = self._bm()
        s1 = bm._make_config_signature(CrawlerRunConfig())
        s2 = bm._make_config_signature(CrawlerRunConfig(timezone_id="America/New_York"))
        assert s1 != s2

    def test_geolocation_changes_signature(self):
        bm = self._bm()
        s1 = bm._make_config_signature(CrawlerRunConfig())
        s2 = bm._make_config_signature(CrawlerRunConfig(
            geolocation=GeolocationConfig(latitude=40.7, longitude=-74.0)
        ))
        assert s1 != s2

    def test_navigator_overrides_change_signature(self):
        bm = self._bm()
        base = bm._make_config_signature(CrawlerRunConfig())
        s_nav = bm._make_config_signature(CrawlerRunConfig(override_navigator=True))
        s_sim = bm._make_config_signature(CrawlerRunConfig(simulate_user=True))
        s_mag = bm._make_config_signature(CrawlerRunConfig(magic=True))
        assert base != s_nav
        assert base != s_sim
        assert base != s_mag

    def test_signature_stability(self):
        """Same config always produces the same hash."""
        bm = self._bm()
        c = CrawlerRunConfig(locale="ja-JP", override_navigator=True)
        assert bm._make_config_signature(c) == bm._make_config_signature(c)

    def test_proxy_config_with_credentials(self):
        """ProxyConfig with username/password produces distinct stable sigs."""
        bm = self._bm()
        c1 = CrawlerRunConfig(proxy_config=ProxyConfig(
            server="http://proxy:8080", username="user1", password="pass1"
        ))
        c2 = CrawlerRunConfig(proxy_config=ProxyConfig(
            server="http://proxy:8080", username="user2", password="pass2"
        ))
        s1 = bm._make_config_signature(c1)
        s2 = bm._make_config_signature(c2)
        assert s1 != s2, "different credentials should differ"
        assert s1 == bm._make_config_signature(c1), "should be stable"


class TestLRUEviction:
    """Verify eviction logic (no browser needed)."""

    def _bm(self, max_ctx=3):
        bm = BrowserManager(BrowserConfig(), logger=None)
        bm._max_contexts = max_ctx
        return bm

    def test_no_eviction_under_limit(self):
        bm = self._bm(max_ctx=5)
        for i in range(5):
            sig = f"sig_{i}"
            bm.contexts_by_config[sig] = f"ctx_{i}"
            bm._context_refcounts[sig] = 0
            bm._context_last_used[sig] = time.monotonic()
        assert bm._evict_lru_context_locked() is None

    def test_evicts_oldest_idle(self):
        bm = self._bm(max_ctx=3)
        for i in range(5):
            sig = f"sig_{i}"
            bm.contexts_by_config[sig] = f"ctx_{i}"
            bm._context_refcounts[sig] = 0
            bm._context_last_used[sig] = time.monotonic()
            time.sleep(0.002)

        evicted = bm._evict_lru_context_locked()
        assert evicted == "ctx_0", f"expected oldest ctx_0, got {evicted}"
        assert "sig_0" not in bm.contexts_by_config
        assert "sig_0" not in bm._context_refcounts
        assert "sig_0" not in bm._context_last_used

    def test_skips_active_contexts(self):
        bm = self._bm(max_ctx=2)
        # sig_0: old but active
        bm.contexts_by_config["sig_0"] = "ctx_0"
        bm._context_refcounts["sig_0"] = 3
        bm._context_last_used["sig_0"] = 0  # very old

        # sig_1: newer, idle
        bm.contexts_by_config["sig_1"] = "ctx_1"
        bm._context_refcounts["sig_1"] = 0
        bm._context_last_used["sig_1"] = time.monotonic()

        # sig_2: newest, idle
        bm.contexts_by_config["sig_2"] = "ctx_2"
        bm._context_refcounts["sig_2"] = 0
        bm._context_last_used["sig_2"] = time.monotonic()

        evicted = bm._evict_lru_context_locked()
        # sig_0 is oldest but active (refcount=3) — must skip it
        assert evicted == "ctx_1", f"expected ctx_1 (oldest idle), got {evicted}"
        assert "sig_0" in bm.contexts_by_config, "active context must NOT be evicted"

    def test_all_active_no_eviction(self):
        bm = self._bm(max_ctx=1)
        for i in range(3):
            sig = f"sig_{i}"
            bm.contexts_by_config[sig] = f"ctx_{i}"
            bm._context_refcounts[sig] = 1  # all active
            bm._context_last_used[sig] = time.monotonic()

        evicted = bm._evict_lru_context_locked()
        assert evicted is None, "cannot evict when all are active"
        assert len(bm.contexts_by_config) == 3, "all contexts should remain"

    def test_eviction_cleans_page_to_sig(self):
        bm = self._bm(max_ctx=1)
        bm.contexts_by_config["sig_old"] = "ctx_old"
        bm._context_refcounts["sig_old"] = 0
        bm._context_last_used["sig_old"] = 0

        bm.contexts_by_config["sig_new"] = "ctx_new"
        bm._context_refcounts["sig_new"] = 0
        bm._context_last_used["sig_new"] = time.monotonic()

        # Simulate a stale page mapping for the old context
        mock_page = object()
        bm._page_to_sig[mock_page] = "sig_old"

        evicted = bm._evict_lru_context_locked()
        assert evicted == "ctx_old"
        assert mock_page not in bm._page_to_sig, "stale page mapping should be cleaned"


# ── Integration tests (real browser) ────────────────────────────────────

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def run(coro):
    """Run an async function synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestRealBrowserContextLifecycle:
    """Real browser tests — verify contexts aren't leaked."""

    def test_varying_configs_same_context(self):
        """Different non-context fields should reuse the same context."""
        async def _test():
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                bm = crawler.crawler_strategy.browser_manager

                # Crawl with different non-context configs
                html = "<html><body><p>Hello World with enough words to pass threshold</p></body></html>"
                for wct in [10, 50, 200]:
                    config = CrawlerRunConfig(word_count_threshold=wct)
                    result = await crawler.arun(f"raw:{html}", config=config)
                    assert result.success

                # Should have at most 1 context (all configs hash the same)
                ctx_count = len(bm.contexts_by_config)
                assert ctx_count <= 1, (
                    f"Expected 1 context for identical browser config, got {ctx_count}"
                )
        run(_test())

    def test_batch_crawl_reuses_context(self):
        """Multiple URLs with same config should reuse a single context."""
        async def _test():
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                bm = crawler.crawler_strategy.browser_manager

                html1 = "<html><body><p>Page one content here</p></body></html>"
                html2 = "<html><body><p>Page two content here</p></body></html>"
                html3 = "<html><body><p>Page three content here</p></body></html>"

                config = CrawlerRunConfig()
                for h in [html1, html2, html3]:
                    result = await crawler.arun(f"raw:{h}", config=config)
                    assert result.success

                ctx_count = len(bm.contexts_by_config)
                assert ctx_count <= 1, f"Batch should reuse context, got {ctx_count}"
        run(_test())

    def test_refcount_drops_to_zero_after_crawl(self):
        """After a crawl completes, the context refcount should be 0."""
        async def _test():
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                bm = crawler.crawler_strategy.browser_manager
                html = "<html><body><p>Test content</p></body></html>"
                config = CrawlerRunConfig()
                result = await crawler.arun(f"raw:{html}", config=config)
                assert result.success

                # All refcounts should be 0 after crawl completes
                for sig, count in bm._context_refcounts.items():
                    assert count == 0, (
                        f"Refcount for {sig[:8]} should be 0 after crawl, got {count}"
                    )
        run(_test())

    def test_page_to_sig_cleaned_after_crawl(self):
        """After crawl, the page->sig mapping should be empty (pages released)."""
        async def _test():
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                bm = crawler.crawler_strategy.browser_manager
                html = "<html><body><p>Test</p></body></html>"
                result = await crawler.arun(f"raw:{html}", config=CrawlerRunConfig())
                assert result.success

                assert len(bm._page_to_sig) == 0, (
                    f"Expected empty _page_to_sig after crawl, got {len(bm._page_to_sig)} entries"
                )
        run(_test())

    def test_concurrent_crawls_refcount_tracking(self):
        """Concurrent crawls should all properly increment/decrement refcounts."""
        async def _test():
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                bm = crawler.crawler_strategy.browser_manager
                config = CrawlerRunConfig()

                htmls = [
                    f"raw:<html><body><p>Concurrent page {i}</p></body></html>"
                    for i in range(5)
                ]
                tasks = [crawler.arun(h, config=config) for h in htmls]
                results = await asyncio.gather(*tasks)
                for r in results:
                    assert r.success

                # All done — refcounts should be 0
                for sig, count in bm._context_refcounts.items():
                    assert count == 0, (
                        f"After concurrent crawls, refcount for {sig[:8]} = {count}"
                    )
                assert len(bm._page_to_sig) == 0
        run(_test())

    def test_lru_eviction_real_browser(self):
        """Verify LRU eviction actually closes contexts when limit exceeded."""
        async def _test():
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                bm = crawler.crawler_strategy.browser_manager
                bm._max_contexts = 2  # Low limit to trigger eviction

                html = "<html><body><p>Test</p></body></html>"

                # Crawl with 4 different locales → 4 different context signatures
                for locale in ["en-US", "fr-FR", "de-DE", "ja-JP"]:
                    config = CrawlerRunConfig(locale=locale)
                    result = await crawler.arun(f"raw:{html}", config=config)
                    assert result.success

                # Should have at most 2 contexts (limit)
                ctx_count = len(bm.contexts_by_config)
                assert ctx_count <= 2, (
                    f"Expected <= 2 contexts (limit), got {ctx_count}"
                )

                # Refcounts should all be 0
                for sig, count in bm._context_refcounts.items():
                    assert count == 0, f"refcount {sig[:8]} = {count}"
        run(_test())

    def test_close_clears_everything(self):
        """close() should clear all tracking dicts."""
        async def _test():
            crawler = AsyncWebCrawler(config=BrowserConfig(headless=True))
            await crawler.start()
            bm = crawler.crawler_strategy.browser_manager

            html = "<html><body><p>Test</p></body></html>"
            result = await crawler.arun(f"raw:{html}", config=CrawlerRunConfig())
            assert result.success

            await crawler.close()

            assert len(bm.contexts_by_config) == 0
            assert len(bm._context_refcounts) == 0
            assert len(bm._context_last_used) == 0
            assert len(bm._page_to_sig) == 0
        run(_test())
