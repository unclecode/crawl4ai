import pytest
import time
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    MemoryAdaptiveDispatcher,
    SemaphoreDispatcher,
    RateLimiter,
    CrawlerMonitor,
    DisplayMode,
    CacheMode,
)


@pytest.fixture
def browser_config():
    return BrowserConfig(headless=True, verbose=False)


@pytest.fixture
def run_config():
    return CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)


@pytest.fixture
def test_urls():
    return [
        "http://example.com",
        "http://example.com/page1",
        "http://example.com/page2",
    ]


@pytest.mark.asyncio
class TestDispatchStrategies:
    async def test_memory_adaptive_basic(self, browser_config, run_config, test_urls):
        async with AsyncWebCrawler(config=browser_config) as crawler:
            dispatcher = MemoryAdaptiveDispatcher(
                memory_threshold_percent=70.0, max_session_permit=2, check_interval=0.1
            )
            results = await crawler.arun_many(
                test_urls, config=run_config, dispatcher=dispatcher
            )
            assert len(results) == len(test_urls)
            assert all(r.success for r in results)

    async def test_memory_adaptive_with_rate_limit(
        self, browser_config, run_config, test_urls
    ):
        async with AsyncWebCrawler(config=browser_config) as crawler:
            dispatcher = MemoryAdaptiveDispatcher(
                memory_threshold_percent=70.0,
                max_session_permit=2,
                check_interval=0.1,
                rate_limiter=RateLimiter(
                    base_delay=(0.1, 0.2), max_delay=1.0, max_retries=2
                ),
            )
            results = await crawler.arun_many(
                test_urls, config=run_config, dispatcher=dispatcher
            )
            assert len(results) == len(test_urls)
            assert all(r.success for r in results)

    async def test_semaphore_basic(self, browser_config, run_config, test_urls):
        async with AsyncWebCrawler(config=browser_config) as crawler:
            dispatcher = SemaphoreDispatcher(semaphore_count=2)
            results = await crawler.arun_many(
                test_urls, config=run_config, dispatcher=dispatcher
            )
            assert len(results) == len(test_urls)
            assert all(r.success for r in results)

    async def test_semaphore_with_rate_limit(
        self, browser_config, run_config, test_urls
    ):
        async with AsyncWebCrawler(config=browser_config) as crawler:
            dispatcher = SemaphoreDispatcher(
                semaphore_count=2,
                rate_limiter=RateLimiter(
                    base_delay=(0.1, 0.2), max_delay=1.0, max_retries=2
                ),
            )
            results = await crawler.arun_many(
                test_urls, config=run_config, dispatcher=dispatcher
            )
            assert len(results) == len(test_urls)
            assert all(r.success for r in results)

    async def test_memory_adaptive_memory_error(
        self, browser_config, run_config, test_urls
    ):
        async with AsyncWebCrawler(config=browser_config) as crawler:
            dispatcher = MemoryAdaptiveDispatcher(
                memory_threshold_percent=1.0,  # Set unrealistically low threshold
                max_session_permit=2,
                check_interval=0.1,
                memory_wait_timeout=1.0,  # Short timeout for testing
            )
            with pytest.raises(MemoryError):
                await crawler.arun_many(
                    test_urls, config=run_config, dispatcher=dispatcher
                )

    async def test_empty_urls(self, browser_config, run_config):
        async with AsyncWebCrawler(config=browser_config) as crawler:
            dispatcher = MemoryAdaptiveDispatcher(max_session_permit=2)
            results = await crawler.arun_many(
                [], config=run_config, dispatcher=dispatcher
            )
            assert len(results) == 0

    async def test_single_url(self, browser_config, run_config):
        async with AsyncWebCrawler(config=browser_config) as crawler:
            dispatcher = MemoryAdaptiveDispatcher(max_session_permit=2)
            results = await crawler.arun_many(
                ["http://example.com"], config=run_config, dispatcher=dispatcher
            )
            assert len(results) == 1
            assert results[0].success

    async def test_invalid_urls(self, browser_config, run_config):
        async with AsyncWebCrawler(config=browser_config) as crawler:
            dispatcher = MemoryAdaptiveDispatcher(max_session_permit=2)
            results = await crawler.arun_many(
                ["http://invalid.url.that.doesnt.exist"],
                config=run_config,
                dispatcher=dispatcher,
            )
            assert len(results) == 1
            assert not results[0].success

    async def test_rate_limit_backoff(self, browser_config, run_config):
        urls = ["http://example.com"] * 5  # Multiple requests to same domain
        async with AsyncWebCrawler(config=browser_config) as crawler:
            dispatcher = MemoryAdaptiveDispatcher(
                max_session_permit=2,
                rate_limiter=RateLimiter(
                    base_delay=(0.1, 0.2),
                    max_delay=1.0,
                    max_retries=2,
                    rate_limit_codes=[200],  # Force rate limiting for testing
                ),
            )
            start_time = time.time()
            results = await crawler.arun_many(
                urls, config=run_config, dispatcher=dispatcher
            )
            duration = time.time() - start_time
            assert len(results) == len(urls)
            assert duration > 1.0  # Ensure rate limiting caused delays

    async def test_monitor_integration(self, browser_config, run_config, test_urls):
        async with AsyncWebCrawler(config=browser_config) as crawler:
            monitor = CrawlerMonitor(
                max_visible_rows=5, display_mode=DisplayMode.DETAILED
            )
            dispatcher = MemoryAdaptiveDispatcher(max_session_permit=2, monitor=monitor)
            results = await crawler.arun_many(
                test_urls, config=run_config, dispatcher=dispatcher
            )
            assert len(results) == len(test_urls)
            # Check monitor stats
            assert len(monitor.stats) == len(test_urls)
            assert all(stat.end_time is not None for stat in monitor.stats.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
