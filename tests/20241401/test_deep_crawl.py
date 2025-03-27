import sys
import time
import pytest


from crawl4ai import CrawlerRunConfig, AsyncWebCrawler, CacheMode
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy


@pytest.mark.asyncio
async def test_deep_crawl():
    """Example deep crawl of documentation site."""
    config = CrawlerRunConfig(
        deep_crawl_strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            include_external=False
        ),
        stream=False,
        verbose=True,
        cache_mode=CacheMode.BYPASS,
        scraping_strategy=LXMLWebScrapingStrategy()
    )

    async with AsyncWebCrawler() as crawler:
        start_time = time.perf_counter()
        print("\nStarting deep crawl in batch mode:")
        results = await crawler.arun(
            url="https://docs.crawl4ai.com",
            config=config
        )
        print(f"Crawled {len(results)} pages")
        print(f"Example page: {results[0].url}")
        print(f"Duration: {time.perf_counter() - start_time:.2f} seconds\n")

        print("Starting deep crawl in streaming mode:")
        config.stream = True
        start_time = time.perf_counter()
        async for result in await crawler.arun(
            url="https://docs.crawl4ai.com",
            config=config
        ):
            print(f"→ {result.url} (Depth: {result.metadata.get('depth', 0)})")
        print(f"Duration: {time.perf_counter() - start_time:.2f} seconds")

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", "-v", str(__file__)]))
