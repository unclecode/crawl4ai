import sys
import time
from httpx import codes
import pytest


from crawl4ai import CrawlerRunConfig, AsyncWebCrawler, CacheMode
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

from pytest_httpserver import HTTPServer


URLS = [
    "/",
    "/level1",
    "/level2/article1",
    "/level2/article2",
]

@pytest.fixture
def site(httpserver: HTTPServer) -> HTTPServer:
    """Fixture to serve multiple pages for a crawl."""
    httpserver.expect_request("/").respond_with_data(content_type="text/html", response_data="""
        <html><body>
        <a href="/level1">Go to level 1</a>
        </body></html>
    """)
    httpserver.expect_request("/level1").respond_with_data(content_type="text/html", response_data="""
        <html><body>
        <a href="/level2/article1">Go to level 2 - Article 1</a>
        <a href="/level2/article2">Go to level 2 - Article 2</a>
        </body></html>
    """)
    httpserver.expect_request("/level2/article1").respond_with_data(content_type="text/html", response_data="""
        <html><body>
        <p>This is level 2 - Article 1</p>
        </body></html>
    """)
    httpserver.expect_request("/level2/article2").respond_with_data(content_type="text/html", response_data="""
        <html><body>
        <p>This is level 2 - Article 2</p>
        </body></html>
    """)
    return httpserver

@pytest.mark.asyncio
async def test_deep_crawl_batch(site: HTTPServer):
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
            url=site.url_for("/"),
            config=config
        )
        print(f"Crawled {len(results)} pages")
        print(f"Example page: {results[0].url}")
        print(f"Duration: {time.perf_counter() - start_time:.2f} seconds\n")

        assert len(results) == len(URLS)
        for idx, result in enumerate(results):
            assert result.url == site.url_for(URLS[idx])
            assert result.status_code == codes.OK

@pytest.mark.asyncio
async def test_deep_crawl_stream(site: HTTPServer):
    config = CrawlerRunConfig(
        deep_crawl_strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            include_external=False
        ),
        stream=True,
        verbose=True,
        cache_mode=CacheMode.BYPASS,
        scraping_strategy=LXMLWebScrapingStrategy()
    )

    async with AsyncWebCrawler() as crawler:
        print("Starting deep crawl in streaming mode:")
        start_time = time.perf_counter()
        last_time = start_time
        idx = 0
        async for result in await crawler.arun(
            url=site.url_for("/"),
            config=config
        ):
            now = time.perf_counter()
            duration = now - last_time
            last_time = now
            assert result.status_code == codes.OK
            assert result.url == site.url_for(URLS[idx])
            assert result.metadata
            print(f"→ {result.url} (Depth: {result.metadata.get('depth', 0)}) ({duration:.2f} seconds)")
            idx += 1
        print(f"Crawled {idx} pages")
        print(f"Duration: {time.perf_counter() - start_time:.2f} seconds")

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
