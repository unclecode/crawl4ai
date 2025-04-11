import sys

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, PruningContentFilter
from crawl4ai.models import CrawlResultContainer
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.mark.asyncio
async def test_crawler():
    # Setup configurations
    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0)
        ),
    )

    # Test URLs - mix of different sites
    urls = ["http://example.com", "http://example.org", "http://example.net"] * 10  # 15 total URLs

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("\n=== Testing Streaming Mode ===")
        async for result in await crawler.arun_many(urls=urls, config=crawler_config.clone(stream=True)):
            print(f"Received result for: {result.url} - Success: {result.success}")

        print("\n=== Testing Batch Mode ===")
        results = await crawler.arun_many(urls=urls, config=crawler_config)
        assert isinstance(results, CrawlResultContainer)
        assert len(results) == len(urls), "Expected the same number of results as URLs"
        print(f"Received all {len(results)} results at once")
        for result in results:
            assert result.success
            print(f"Batch result for: {result.url} - Success: {result.success}")


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
