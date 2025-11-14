"""
Test for arun_many with managed CDP browser to ensure each crawl gets its own tab.
"""
import pytest
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


@pytest.mark.asyncio
async def test_arun_many_with_cdp():
    """Test arun_many opens a new tab for each url with managed CDP browser."""
    # NOTE: Requires a running CDP browser at localhost:9222
    # Can be started with: crwl cdp -d 9222
    browser_cfg = BrowserConfig(
        browser_type="cdp",
        cdp_url="http://localhost:9222",
        verbose=False,
    )
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://www.python.org",
    ]
    crawler_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
    )
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        results = await crawler.arun_many(urls=urls, config=crawler_cfg)
        # All results should be successful and distinct
        assert len(results) == 3
        for result in results:
            assert result.success, f"Crawl failed: {result.url} - {result.error_message}"
            assert result.markdown is not None


@pytest.mark.asyncio
async def test_arun_many_with_cdp_sequential():
    """Test arun_many sequentially to isolate issues."""
    browser_cfg = BrowserConfig(
        browser_type="cdp",
        cdp_url="http://localhost:9222",
        verbose=True,
    )
    urls = [
        "https://example.com",
        "https://httpbin.org/html", 
        "https://www.python.org",
    ]
    crawler_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
    )
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        results = []
        for url in urls:
            result = await crawler.arun(url=url, config=crawler_cfg)
            results.append(result)
            assert result.success, f"Crawl failed: {result.url} - {result.error_message}"
            assert result.markdown is not None
        assert len(results) == 3


if __name__ == "__main__":
    asyncio.run(test_arun_many_with_cdp())