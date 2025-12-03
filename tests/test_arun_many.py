import pytest

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig


@pytest.mark.asyncio
async def test_run_many():
    test_urls = [
        "https://www.python.org/",  # Generic HTTPS page
        "https://www.example.com/",  # Generic HTTPS page
    ]
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun_many(
            urls=test_urls[:2],
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS
            )
        )
        for item in result:
            assert item.status_code == 200
        
