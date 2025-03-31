import sys

from httpx import codes
import pytest

from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    HTTPCrawlerConfig,
    PruningContentFilter,
)
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from crawl4ai.async_logger import AsyncLogger


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "https://httpbin.org/get",
        "raw://<html><body>Test content</body></html>"
    ]
)
async def test_async_crawl(url: str):
    # Initialize HTTP crawler strategy
    http_strategy = AsyncHTTPCrawlerStrategy(
        browser_config=HTTPCrawlerConfig(
            method="GET",
            verify_ssl=True,
            follow_redirects=True
        ),
        logger=AsyncLogger(verbose=True)
    )

    # Initialize web crawler with HTTP strategy
    async with AsyncWebCrawler(crawler_strategy=http_strategy) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.48,
                    threshold_type="fixed",
                    min_word_threshold=0
                )
            )
        )

        result = await crawler.arun(url=url, config=crawler_config)
        assert result.status_code == codes.OK
        assert result.html
        assert result.markdown
        assert result.markdown.raw_markdown
        print(f"Status: {result.status_code}")
        print(f"Raw HTML length: {len(result.html)}")
        print(f"Markdown length: {len(result.markdown.raw_markdown)}")

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
