import sys

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.mark.asyncio
async def test_streaming():
    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(),
    )

    urls = ["http://example.com"] * 10

    async with AsyncWebCrawler(config=browser_config) as crawler:
        dispatcher = MemoryAdaptiveDispatcher(max_session_permit=5, check_interval=0.5)

        async for result in dispatcher.run_urls_stream(urls, crawler, crawler_config):
            assert result.result.success
            print(f"Got result for {result.url} - Success: {result.result.success}")


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
