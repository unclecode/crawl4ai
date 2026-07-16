"""
Tests for bug fix batch: PR #1622, #1786, #1796

- #1622: _resolve_head should verify redirect targets are alive
- #1786: arun_many should wire mean_delay/max_range into dispatcher
- #1796: process_iframes should use DOMParser instead of innerHTML
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


# ── PR #1622: Redirect target verification in _resolve_head ──────────────


@pytest.fixture
def seeder():
    """Create an AsyncUrlSeeder with a mocked HTTP client."""
    from crawl4ai.async_url_seeder import AsyncUrlSeeder

    s = AsyncUrlSeeder()
    s.client = AsyncMock(spec=httpx.AsyncClient)
    return s


def _make_response(status_code, headers=None, url="https://example.com"):
    """Helper to create a mock httpx Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.url = httpx.URL(url)
    return resp


@pytest.mark.asyncio
async def test_resolve_head_direct_2xx(seeder):
    """Direct 2xx hit should return the URL."""
    seeder.client.head = AsyncMock(
        return_value=_make_response(200, url="https://example.com/page")
    )
    result = await seeder._resolve_head("https://example.com/page")
    assert result == "https://example.com/page"


@pytest.mark.asyncio
async def test_resolve_head_redirect_to_live_target(seeder):
    """3xx redirect to a live target should return the target URL."""
    redirect_resp = _make_response(
        301, headers={"location": "https://example.com/new-page"}
    )
    target_resp = _make_response(200, url="https://example.com/new-page")

    seeder.client.head = AsyncMock(side_effect=[redirect_resp, target_resp])
    result = await seeder._resolve_head("https://example.com/old-page")
    assert result == "https://example.com/new-page"
    assert seeder.client.head.call_count == 2


@pytest.mark.asyncio
async def test_resolve_head_redirect_to_dead_target(seeder):
    """3xx redirect to a dead (non-2xx) target should return None."""
    redirect_resp = _make_response(
        302, headers={"location": "https://example.com/dead"}
    )
    target_resp = _make_response(404, url="https://example.com/dead")

    seeder.client.head = AsyncMock(side_effect=[redirect_resp, target_resp])
    result = await seeder._resolve_head("https://example.com/old")
    assert result is None


@pytest.mark.asyncio
async def test_resolve_head_redirect_target_timeout(seeder):
    """3xx redirect where target times out should return None."""
    redirect_resp = _make_response(
        301, headers={"location": "https://example.com/slow"}
    )

    seeder.client.head = AsyncMock(
        side_effect=[redirect_resp, httpx.TimeoutException("timeout")]
    )
    result = await seeder._resolve_head("https://example.com/old")
    assert result is None


@pytest.mark.asyncio
async def test_resolve_head_self_redirect(seeder):
    """Self-redirect (Location == original URL) should return None."""
    redirect_resp = _make_response(
        301, headers={"location": "https://example.com/loop"}
    )
    seeder.client.head = AsyncMock(return_value=redirect_resp)
    result = await seeder._resolve_head("https://example.com/loop")
    assert result is None
    # Should NOT make a second request for self-redirect
    assert seeder.client.head.call_count == 1


@pytest.mark.asyncio
async def test_resolve_head_relative_redirect(seeder):
    """Relative Location header should be resolved against original URL."""
    redirect_resp = _make_response(301, headers={"location": "/new-path"})
    target_resp = _make_response(200, url="https://example.com/new-path")

    seeder.client.head = AsyncMock(side_effect=[redirect_resp, target_resp])
    result = await seeder._resolve_head("https://example.com/old-path")
    assert result == "https://example.com/new-path"


@pytest.mark.asyncio
async def test_resolve_head_4xx_returns_none(seeder):
    """4xx status should return None."""
    seeder.client.head = AsyncMock(return_value=_make_response(404))
    result = await seeder._resolve_head("https://example.com/missing")
    assert result is None


@pytest.mark.asyncio
async def test_resolve_head_network_error(seeder):
    """Network error should return None (not raise)."""
    seeder.client.head = AsyncMock(
        side_effect=httpx.ConnectError("connection refused")
    )
    result = await seeder._resolve_head("https://example.com/down")
    assert result is None


@pytest.mark.asyncio
async def test_resolve_head_no_location_header(seeder):
    """3xx without Location header should return None."""
    seeder.client.head = AsyncMock(return_value=_make_response(301, headers={}))
    result = await seeder._resolve_head("https://example.com/no-loc")
    assert result is None


# ── PR #1786: mean_delay / max_range wired into dispatcher ───────────────


class TestDispatcherWiring:
    """Test that arun_many wires CrawlerRunConfig delay params into the dispatcher."""

    def test_default_config_values(self):
        """CrawlerRunConfig should have mean_delay=0.1 and max_range=0.3 by default."""
        from crawl4ai.async_configs import CrawlerRunConfig

        cfg = CrawlerRunConfig()
        assert cfg.mean_delay == 0.1
        assert cfg.max_range == 0.3

    def test_custom_config_values(self):
        """CrawlerRunConfig should accept custom mean_delay and max_range."""
        from crawl4ai.async_configs import CrawlerRunConfig

        cfg = CrawlerRunConfig(mean_delay=2.0, max_range=1.0)
        assert cfg.mean_delay == 2.0
        assert cfg.max_range == 1.0

    @pytest.mark.asyncio
    async def test_dispatcher_uses_config_delays(self):
        """When no dispatcher is provided, arun_many should create one using config delays."""
        from crawl4ai.async_webcrawler import AsyncWebCrawler
        from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig
        from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher, RateLimiter

        captured_dispatcher = {}

        original_init = MemoryAdaptiveDispatcher.__init__

        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            captured_dispatcher["rate_limiter"] = self.rate_limiter

        with patch.object(MemoryAdaptiveDispatcher, "__init__", patched_init):
            # We just need to trigger the dispatcher creation path
            # We'll patch run_urls to avoid actually crawling
            with patch.object(
                MemoryAdaptiveDispatcher, "run_urls", new_callable=AsyncMock
            ) as mock_run:
                mock_run.return_value = []

                crawler = AsyncWebCrawler(config=BrowserConfig())
                crawler.ready = True  # skip browser setup
                crawler.crawler_strategy = MagicMock()

                cfg = CrawlerRunConfig(mean_delay=2.0, max_range=1.5)
                try:
                    await crawler.arun_many(urls=["https://example.com"], config=cfg)
                except Exception:
                    pass  # may fail on result processing, that's fine

                rl = captured_dispatcher.get("rate_limiter")
                assert rl is not None, "Dispatcher should have been created"
                assert rl.base_delay == (2.0, 3.5), (
                    f"Expected base_delay=(2.0, 3.5), got {rl.base_delay}"
                )

    @pytest.mark.asyncio
    async def test_dispatcher_uses_first_config_from_list(self):
        """When config is a list, should use the first config's delays."""
        from crawl4ai.async_webcrawler import AsyncWebCrawler
        from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig
        from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher, RateLimiter

        captured_dispatcher = {}

        original_init = MemoryAdaptiveDispatcher.__init__

        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            captured_dispatcher["rate_limiter"] = self.rate_limiter

        with patch.object(MemoryAdaptiveDispatcher, "__init__", patched_init):
            with patch.object(
                MemoryAdaptiveDispatcher, "run_urls", new_callable=AsyncMock
            ) as mock_run:
                mock_run.return_value = []

                crawler = AsyncWebCrawler(config=BrowserConfig())
                crawler.ready = True
                crawler.crawler_strategy = MagicMock()

                cfg1 = CrawlerRunConfig(mean_delay=5.0, max_range=2.0)
                cfg2 = CrawlerRunConfig(mean_delay=0.5, max_range=0.1)
                try:
                    await crawler.arun_many(
                        urls=["https://a.com", "https://b.com"],
                        config=[cfg1, cfg2],
                    )
                except Exception:
                    pass

                rl = captured_dispatcher.get("rate_limiter")
                assert rl is not None
                assert rl.base_delay == (5.0, 7.0), (
                    f"Expected base_delay=(5.0, 7.0) from first config, got {rl.base_delay}"
                )

    @pytest.mark.asyncio
    async def test_explicit_dispatcher_not_overridden(self):
        """When user provides their own dispatcher, config delays should NOT override it."""
        from crawl4ai.async_webcrawler import AsyncWebCrawler
        from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig
        from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher, RateLimiter

        custom_rl = RateLimiter(base_delay=(10.0, 20.0))
        custom_dispatcher = MemoryAdaptiveDispatcher(rate_limiter=custom_rl)

        with patch.object(
            MemoryAdaptiveDispatcher, "run_urls", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = []

            crawler = AsyncWebCrawler(config=BrowserConfig())
            crawler.ready = True
            crawler.crawler_strategy = MagicMock()

            cfg = CrawlerRunConfig(mean_delay=0.5, max_range=0.1)
            try:
                await crawler.arun_many(
                    urls=["https://example.com"],
                    config=cfg,
                    dispatcher=custom_dispatcher,
                )
            except Exception:
                pass

            # Custom dispatcher's rate limiter should be untouched
            assert custom_rl.base_delay == (10.0, 20.0)


# ── PR #1796: DOMParser in process_iframes ───────────────────────────────


class TestProcessIframesDOMParser:
    """Verify that process_iframes uses DOMParser instead of innerHTML."""

    def test_source_code_uses_domparser(self):
        """The process_iframes method should use DOMParser, not innerHTML for injection."""
        import inspect
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

        source = inspect.getsource(AsyncPlaywrightCrawlerStrategy.process_iframes)

        # Should contain DOMParser usage
        assert "DOMParser" in source, "process_iframes should use DOMParser"
        assert "parseFromString" in source, "process_iframes should call parseFromString"
        assert "doc.body.firstChild" in source, (
            "process_iframes should move nodes from parsed doc"
        )

        # The old innerHTML assignment pattern should NOT be present
        # Note: document.body.innerHTML for READING iframe content is fine
        # The dangerous pattern is div.innerHTML = `{_iframe}` for WRITING
        lines = source.split("\n")
        for line in lines:
            stripped = line.strip()
            # Only flag div.innerHTML assignment, not reading from document.body
            if "div.innerHTML" in stripped and "=" in stripped:
                pytest.fail(
                    f"Found unsafe innerHTML assignment: {stripped}"
                )

    def test_js_snippet_structure(self):
        """The JS snippet should properly create DOM nodes from parsed HTML."""
        import inspect
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

        source = inspect.getsource(AsyncPlaywrightCrawlerStrategy.process_iframes)

        # Verify the correct pattern: parse then move child nodes
        assert "new DOMParser()" in source
        assert "'text/html'" in source
        assert "appendChild" in source
