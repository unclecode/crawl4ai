import sys
import time

from httpx import codes
import pytest

from crawl4ai import CrawlerRunConfig, AsyncWebCrawler, CacheMode
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter, ContentTypeFilter, ContentRelevanceFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.types import CrawlResult


@pytest.mark.asyncio
@pytest.mark.timeout(60)
async def test_deep_crawl():
    """Example deep crawl of documentation site."""
    filter_chain = FilterChain([
        URLPatternFilter(patterns=["*2025*"]),
        DomainFilter(allowed_domains=["techcrunch.com"]),
        ContentRelevanceFilter(query="Use of artificial intelligence in Defence applications", threshold=1),
        ContentTypeFilter(allowed_types=["text/html","application/javascript"])
    ])
    max_pages: int = 5
    config = CrawlerRunConfig(
        deep_crawl_strategy = BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=KeywordRelevanceScorer(keywords=["anduril", "defence", "AI"]),
            max_pages=max_pages,
        ),
        stream=False,
        verbose=True,
        cache_mode=CacheMode.BYPASS,
        scraping_strategy=LXMLWebScrapingStrategy()
    )

    async with AsyncWebCrawler() as crawler:
        print("Starting deep crawl in streaming mode:")
        config.stream = True
        start_time = time.perf_counter()
        result: CrawlResult
        pages: int = 0
        async for result in await crawler.arun(
            url="https://techcrunch.com",
            config=config
        ):
            assert result.status_code == codes.OK
            assert result.url
            assert result.metadata
            assert result.metadata.get("depth", -1) >= 0
            assert result.metadata.get("depth", -1) <= 2
            pages += 1
            print(f"→ {result.url} (Depth: {result.metadata.get('depth', 0)})")

        print(f"Crawled {pages} pages in: {time.perf_counter() - start_time:.2f} seconds")
        assert pages == max_pages

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
