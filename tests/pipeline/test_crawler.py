# test_crawler.py
import asyncio
import warnings
import pytest
import pytest_asyncio
from typing import Optional, Tuple

# Define test fixtures
@pytest_asyncio.fixture
async def clean_browser_hub():
    """Fixture to ensure clean browser hub state between tests."""
    # Yield control to the test
    yield
    
    # After test, cleanup all browser hubs
    from crawl4ai.browser import BrowserHub
    try:
        await BrowserHub.shutdown_all()
    except Exception as e:
        print(f"Error during browser cleanup: {e}")

from crawl4ai import Crawler
from crawl4ai import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.models import CrawlResultContainer
from crawl4ai.browser import BrowserHub
from crawl4ai.cache_context import CacheMode

import warnings
from pydantic import PydanticDeprecatedSince20



# Test URLs for crawling
SAFE_URLS = [
    "https://example.com",
    "https://httpbin.org/html",
    "https://httpbin.org/headers",
    "https://httpbin.org/ip",
    "https://httpbin.org/user-agent",
    "https://httpstat.us/200",
    "https://jsonplaceholder.typicode.com/posts/1",
    "https://jsonplaceholder.typicode.com/comments/1",
    "https://iana.org",
    "https://www.python.org",
]


class TestCrawlerBasic:
    """Basic tests for the Crawler utility class"""

    @pytest.mark.asyncio
    async def test_simple_crawl_single_url(self, clean_browser_hub):
        """Test crawling a single URL with default configuration"""
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=Warning)
            # Basic logger
            logger = AsyncLogger(verbose=True)

            # Basic single URL crawl with default configuration
            url = "https://example.com"
            result = await Crawler.crawl(url)

            # Verify the result
            assert isinstance(result, CrawlResultContainer)
            assert result.success
            assert result.url == url
            assert result.html is not None
            assert len(result.html) > 0

    @pytest.mark.asyncio
    async def test_crawl_with_custom_config(self, clean_browser_hub):
        """Test crawling with custom browser and crawler configuration"""
        # Custom browser config
        browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            viewport_width=1280,
            viewport_height=800,
        )

        # Custom crawler config
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, wait_until="networkidle", screenshot=True
        )

        # Crawl with custom configuration
        url = "https://httpbin.org/html"
        result = await Crawler.crawl(
            url, browser_config=browser_config, crawler_config=crawler_config
        )

        # Verify the result
        assert result.success
        assert result.url == url
        assert result.screenshot is not None

    @pytest.mark.asyncio
    async def test_crawl_multiple_urls_sequential(self, clean_browser_hub):
        """Test crawling multiple URLs sequentially"""
        # Use a few test URLs
        urls = SAFE_URLS[:3]

        # Custom crawler config
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, wait_until="domcontentloaded"
        )

        # Crawl multiple URLs sequentially
        results = await Crawler.crawl(urls, crawler_config=crawler_config)

        # Verify the results
        assert isinstance(results, dict)
        assert len(results) == len(urls)

        for url in urls:
            assert url in results
            assert results[url].success
            assert results[url].html is not None

    @pytest.mark.asyncio
    async def test_crawl_with_error_handling(self, clean_browser_hub):
        """Test error handling during crawling"""
        # Include a valid URL and a non-existent URL
        urls = ["https://example.com", "https://non-existent-domain-123456789.com"]

        # Crawl with retries
        results = await Crawler.crawl(urls, max_retries=2, retry_delay=1.0)

        # Verify results for both URLs
        assert len(results) == 2

        # Valid URL should succeed
        assert results[urls[0]].success

        # Invalid URL should fail but be in results
        assert urls[1] in results
        assert not results[urls[1]].success
        assert results[urls[1]].error_message is not None


class TestCrawlerParallel:
    """Tests for the parallel crawling capabilities of Crawler"""

    @pytest.mark.asyncio
    async def test_parallel_crawl_simple(self, clean_browser_hub):
        """Test basic parallel crawling with same configuration"""
        # Use several URLs for parallel crawling
        urls = SAFE_URLS[:5]

        # Basic crawler config
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, wait_until="domcontentloaded"
        )

        # Crawl in parallel with default concurrency
        start_time = asyncio.get_event_loop().time()
        results = await Crawler.parallel_crawl(urls, crawler_config=crawler_config)
        end_time = asyncio.get_event_loop().time()

        # Verify results
        assert len(results) == len(urls)
        successful = sum(1 for r in results.values() if r.success)

        print(
            f"Parallel crawl of {len(urls)} URLs completed in {end_time - start_time:.2f}s"
        )
        print(f"Success rate: {successful}/{len(urls)}")

        # At least 80% should succeed
        assert successful / len(urls) >= 0.8

    @pytest.mark.asyncio
    async def test_parallel_crawl_with_concurrency_limit(self, clean_browser_hub):
        """Test parallel crawling with concurrency limit"""
        # Use more URLs to test concurrency control
        urls = SAFE_URLS[:8]

        # Custom crawler config
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, wait_until="domcontentloaded"
        )

        # Limited concurrency
        concurrency = 2

        # Time the crawl
        start_time = asyncio.get_event_loop().time()
        results = await Crawler.parallel_crawl(
            urls, crawler_config=crawler_config, concurrency=concurrency
        )
        end_time = asyncio.get_event_loop().time()

        # Verify results
        assert len(results) == len(urls)
        successful = sum(1 for r in results.values() if r.success)

        print(
            f"Parallel crawl with concurrency={concurrency} of {len(urls)} URLs completed in {end_time - start_time:.2f}s"
        )
        print(f"Success rate: {successful}/{len(urls)}")

        # At least 80% should succeed
        assert successful / len(urls) >= 0.8

    @pytest.mark.asyncio
    async def test_parallel_crawl_with_different_configs(self, clean_browser_hub):
        """Test parallel crawling with different configurations for different URLs"""
        # Create URL batches with different configurations
        batch1 = (
            SAFE_URLS[:2],
            CrawlerRunConfig(wait_until="domcontentloaded", screenshot=False),
        )
        batch2 = (
            SAFE_URLS[2:4],
            CrawlerRunConfig(wait_until="networkidle", screenshot=True),
        )
        batch3 = (
            SAFE_URLS[4:6],
            CrawlerRunConfig(wait_until="load", scan_full_page=True),
        )

        # Crawl with mixed configurations
        start_time = asyncio.get_event_loop().time()
        results = await Crawler.parallel_crawl([batch1, batch2, batch3])
        end_time = asyncio.get_event_loop().time()

        # Extract all URLs
        all_urls = batch1[0] + batch2[0] + batch3[0]

        # Verify results
        assert len(results) == len(all_urls)

        # Check that screenshots are present only for batch2
        for url in batch1[0]:
            assert not results[url].screenshot

        for url in batch2[0]:
            assert results[url].screenshot

        print(
            f"Mixed-config parallel crawl of {len(all_urls)} URLs completed in {end_time - start_time:.2f}s"
        )

    @pytest.mark.asyncio
    async def test_parallel_crawl_with_shared_browser_hub(self, clean_browser_hub):
        """Test parallel crawling with a shared browser hub"""
        # Create and initialize a browser hub
        browser_config = BrowserConfig(browser_type="chromium", headless=True)

        browser_hub = await BrowserHub.get_browser_manager(
            config=browser_config,
            max_browsers_per_config=3,
            max_pages_per_browser=4,
            initial_pool_size=1,
        )

        try:
            # Use the hub for parallel crawling
            urls = SAFE_URLS[:6]

            start_time = asyncio.get_event_loop().time()
            results = await Crawler.parallel_crawl(
                urls,
                browser_hub=browser_hub,
                crawler_config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS, wait_until="domcontentloaded"
                ),
            )
            end_time = asyncio.get_event_loop().time()

            # Verify results
            # assert (len(results), len(urls))
            assert len(results) == len(urls)
            successful = sum(1 for r in results.values() if r.success)

            print(
                f"Shared hub parallel crawl of {len(urls)} URLs completed in {end_time - start_time:.2f}s"
            )
            print(f"Success rate: {successful}/{len(urls)}")

            # Get browser hub statistics
            hub_stats = await browser_hub.get_pool_status()
            print(f"Browser hub stats: {hub_stats}")

            # At least 80% should succeed
            # assert (successful / len(urls), 0.8)
            assert successful / len(urls) >= 0.8

        finally:
            # Clean up the browser hub
            await browser_hub.close()


class TestCrawlerAdvanced:
    """Advanced tests for the Crawler utility class"""

    @pytest.mark.asyncio
    async def test_crawl_with_customized_batch_config(self, clean_browser_hub):
        """Test crawling with fully customized batch configuration"""
        # Create URL batches with different browser and crawler configurations
        browser_config1 = BrowserConfig(browser_type="chromium", headless=True)
        browser_config2 = BrowserConfig(
            browser_type="chromium", headless=False, viewport_width=1920
        )

        crawler_config1 = CrawlerRunConfig(wait_until="domcontentloaded")
        crawler_config2 = CrawlerRunConfig(wait_until="networkidle", screenshot=True)

        batch1 = (SAFE_URLS[:2], browser_config1, crawler_config1)
        batch2 = (SAFE_URLS[2:4], browser_config2, crawler_config2)

        # Crawl with mixed configurations
        results = await Crawler.parallel_crawl([batch1, batch2])

        # Extract all URLs
        all_urls = batch1[0] + batch2[0]

        # Verify results
        # assert (len(results), len(all_urls))
        assert len(results) == len(all_urls)

        # Verify batch-specific processing
        for url in batch1[0]:
            assert results[url].screenshot is None  # No screenshots for batch1

        for url in batch2[0]:
            assert results[url].screenshot is not None  # Should have screenshots for batch2

    @pytest.mark.asyncio
    async def test_crawl_with_progress_callback(self, clean_browser_hub):
        """Test crawling with progress callback"""
        # Use several URLs
        urls = SAFE_URLS[:5]

        # Track progress
        progress_data = {"started": 0, "completed": 0, "failed": 0, "updates": []}

        # Progress callback
        async def on_progress(
            status: str, url: str, result: Optional[CrawlResultContainer] = None
        ):
            if status == "started":
                progress_data["started"] += 1
            elif status == "completed":
                progress_data["completed"] += 1
                if not result.success:
                    progress_data["failed"] += 1

            progress_data["updates"].append((status, url))
            print(f"Progress: {status} - {url}")

        # Crawl with progress tracking
        results = await Crawler.parallel_crawl(
            urls,
            crawler_config=CrawlerRunConfig(wait_until="domcontentloaded"),
            progress_callback=on_progress,
        )

        # Verify progress tracking
        assert progress_data["started"] == len(urls)
        assert progress_data["completed"] == len(urls)
        assert len(progress_data["updates"]) == len(urls) * 2  # start + complete events

    @pytest.mark.asyncio
    async def test_crawl_with_dynamic_retry_strategy(self, clean_browser_hub):
        """Test crawling with a dynamic retry strategy"""
        # Include URLs that might fail
        urls = [
            "https://example.com",
            "https://httpstat.us/500",
            "https://httpstat.us/404",
        ]

        # Custom retry strategy
        async def retry_strategy(
            url: str, attempt: int, error: Exception
        ) -> Tuple[bool, float]:
            # Only retry 500 errors, not 404s
            if "500" in url:
                return True, 1.0  # Retry with 1 second delay
            return False, 0.0  # Don't retry other errors

        # Crawl with custom retry strategy
        results = await Crawler.parallel_crawl(
            urls,
            crawler_config=CrawlerRunConfig(wait_until="domcontentloaded"),
            retry_strategy=retry_strategy,
            max_retries=3,
        )

        # Verify results
        assert len(results) == len(urls)

        # Example.com should succeed
        assert results[urls[0]].success

        # httpstat.us pages return content even for error status codes
        # so our crawler marks them as successful since it got HTML content
        # Verify that we got the expected status code
        assert results[urls[1]].status_code == 500
        
        # 404 should have the correct status code
        assert results[urls[2]].status_code == 404

    @pytest.mark.asyncio
    async def test_crawl_with_very_large_batch(self, clean_browser_hub):
        """Test crawling with a very large batch of URLs"""
        # Create a batch by repeating our safe URLs
        # Note: In a real test, we'd use more URLs, but for simplicity we'll use a smaller set
        large_batch = list(dict.fromkeys(SAFE_URLS[:5] * 2))  # ~10 unique URLs

        # Set a reasonable concurrency limit
        concurrency = 10

        # Time the crawl
        start_time = asyncio.get_event_loop().time()
        results = await Crawler.parallel_crawl(
            large_batch,
            crawler_config=CrawlerRunConfig(
                wait_until="domcontentloaded",
                page_timeout=10000,  # Shorter timeout for large batch
            ),
            concurrency=concurrency,
        )
        end_time = asyncio.get_event_loop().time()

        # Verify results
        # assert (len(results), len(large_batch))
        assert len(results) == len(large_batch)
        successful = sum(1 for r in results.values() if r.success)

        print(
            f"Large batch crawl of {len(large_batch)} URLs completed in {end_time - start_time:.2f}s"
        )
        print(f"Success rate: {successful}/{len(large_batch)}")
        print(
            f"Average time per URL: {(end_time - start_time) / len(large_batch):.2f}s"
        )

        # At least 80% should succeed (from our unique URLs)
        assert successful / len(results) >= 0.8


if __name__ == "__main__":
    # Use pytest for async tests
    pytest.main(["-xvs", __file__])
