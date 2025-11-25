import pytest

from unittest.mock import Mock, patch

import pytest_asyncio

from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.cache_context import CacheMode
from crawl4ai.models import AsyncCrawlResponse
from tests.helpers import EXAMPLE_RAW_HTML, EXAMPLE_URL, TestCacheClient


@pytest_asyncio.fixture
async def mock_async_crawl_response(monkeypatch):
    mock_crawl_response = AsyncCrawlResponse(
        html=EXAMPLE_RAW_HTML,
        response_headers={
            'accept-ranges': 'bytes',
            'alt-svc': 'h3=":443"; ma=93600',
            'cache-control': 'max-age=86000',
            'content-length': '513',
            'content-type': 'text/html',
            'date': 'Wed, 19 Nov 2025 20:09:52 GMT',
            'etag': '"bc2473a18e003bdb249eba5ce893033f:1760028122.592274"',
            'last-modified': 'Thu, 09 Oct 2025 16:42:02 GMT'
        },
        js_execution_result=None,
        status_code=200,
        screenshot=None,
        pdf_data=None,
        mhtml_data=None,
        downloaded_files=None,
        ssl_certificate=None,
        redirected_url=EXAMPLE_URL,
        network_requests=None,
        console_messages=None
    )
    async def mock_crawl(self, url, **kwargs):
        return mock_crawl_response
    monkeypatch.setattr("crawl4ai.async_crawler_strategy.AsyncPlaywrightCrawlerStrategy.crawl", mock_crawl)


@pytest.mark.asyncio
async def test_caching():
    cache_client = TestCacheClient()

    async with AsyncWebCrawler(cache_client=cache_client) as crawler:
        # First crawl (should not use cache)
        result1 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED
        ))
        cache_size = cache_client.count()

        assert result1.success
        assert cache_size == 1

        # Second crawl (should use cache)
        result2 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED
        ))
        final_cache_size = cache_client.count()

        assert result2.success
        assert result2.html == result1.html
        assert final_cache_size == 1
    
    cache_client.cleanup()


@pytest.mark.asyncio
async def test_cache_excluded_tags(mock_async_crawl_response):
    cache_client = TestCacheClient()

    async with AsyncWebCrawler(cache_client=cache_client) as crawler:
        result1 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            excluded_tags=["p"]
        ))
        cache_size = cache_client.count()
        
        assert result1.success
        assert result1.markdown == "# Example Domain\n"
        assert cache_size == 1

        result2 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            excluded_tags=["h1"]
        ))
        cache_size2 = cache_client.count()

        assert result2.success
        assert result2.markdown == "This domain is for use in documentation examples without needing permission. Avoid use in operations.\n[Learn more](https://iana.org/domains/example)\n"
        assert cache_size2 == cache_size

        result3 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
        ))
        cache_size3 = cache_client.count()

        assert result3.success
        assert result3.markdown == "# Example Domain\nThis domain is for use in documentation examples without needing permission. Avoid use in operations.\n[Learn more](https://iana.org/domains/example)\n"
        assert cache_size3 == cache_size
    
    cache_client.cleanup()


@pytest.mark.asyncio
async def test_bypass_cache():
    cache_client = TestCacheClient()
    get_spy = Mock(wraps=cache_client.get)

    with patch.object(TestCacheClient, 'get', get_spy):
        async with AsyncWebCrawler(cache_client=cache_client) as crawler:
            result1 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED
            ))

            assert result1.success
            assert get_spy.call_count == 1

            result2 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS
            ))
            
            assert result2.success
            assert get_spy.call_count == 1

    cache_client.cleanup()


@pytest.mark.asyncio
async def test_clear_cache():
    cache_client = TestCacheClient()

    async with AsyncWebCrawler(cache_client=cache_client) as crawler:
        await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED
        ))
        assert cache_client.count() == 1

        cache_client.clear(prefix="")
        assert cache_client.count() == 0

    cache_client.cleanup()


# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
