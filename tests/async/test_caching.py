import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.async_database import AsyncDatabaseManager, async_db_manager
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.cache_context import CacheMode
from crawl4ai.models import AsyncCrawlResponse

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

EXAMPLE_RAW_HTML = """<!DOCTYPE html><html lang="en"><head><title>Example Domain</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#eee;width:60vw;margin:15vh auto;font-family:system-ui,sans-serif}h1{font-size:1.5em}div{opacity:0.8}a:link,a:visited{color:#348}</style></head><body><div><h1>Example Domain</h1><p>This domain is for use in documentation examples without needing permission. Avoid use in operations.</p><p><a href="https://iana.org/domains/example">Learn more</a></p></div>\n</body></html>"""
EXAMPLE_URL = "https://example.com"


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
    async with AsyncWebCrawler(verbose=True) as crawler:
        # First crawl (should not use cache)
        start_time = asyncio.get_event_loop().time()
        result1 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED
        ))
        end_time = asyncio.get_event_loop().time()
        time_taken1 = end_time - start_time
        cache_size = await async_db_manager.aget_total_count()

        assert result1.success
        assert cache_size > 0

        # Second crawl (should use cache)
        start_time = asyncio.get_event_loop().time()
        result2 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED
        ))
        end_time = asyncio.get_event_loop().time()
        time_taken2 = end_time - start_time
        final_cache_size = await async_db_manager.aget_total_count()

        assert result2.success
        assert time_taken2 < time_taken1  # Cached result should be faster
        assert final_cache_size == cache_size


@pytest.mark.asyncio
async def test_cache_base_directory(mock_async_crawl_response, tmp_path):
    custom_base_dir = tmp_path / "test_crawl4ai_base"
    custom_db_path = custom_base_dir / ".crawl4ai" / "crawl4ai.db"

    with patch("crawl4ai.async_database.DB_PATH", str(custom_db_path)):
        test_db_manager = AsyncDatabaseManager()
        assert str(custom_db_path) == test_db_manager.db_path

        with patch('crawl4ai.async_webcrawler.async_db_manager', test_db_manager):
            await test_db_manager.initialize()
            assert os.path.exists(test_db_manager.db_path)

            cache_size = await test_db_manager.aget_total_count()
            assert cache_size == 0
        
            async with AsyncWebCrawler(base_directory=str(custom_base_dir), verbose=True) as crawler:
                result = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
                    cache_mode=CacheMode.ENABLED
                ))
                
                assert result.success
                assert result.html == EXAMPLE_RAW_HTML
                
                cache_size = await test_db_manager.aget_total_count()
                assert cache_size == 1
    
        await test_db_manager.cleanup()


@pytest.mark.asyncio
async def test_cache_excluded_tags(mock_async_crawl_response):
    async with AsyncWebCrawler(verbose=True) as crawler:
        result1 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            excluded_tags=["p"]
        ))
        cache_size = await async_db_manager.aget_total_count()
        
        assert result1.success
        assert result1.markdown == "# Example Domain\n"
        assert cache_size > 0

        result2 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            excluded_tags=["h1"]
        ))
        cache_size2 = await async_db_manager.aget_total_count()

        assert result2.success
        assert result2.markdown == "This domain is for use in documentation examples without needing permission. Avoid use in operations.\n[Learn more](https://iana.org/domains/example)\n"
        assert cache_size2 == cache_size

        result3 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
        ))
        cache_size3 = await async_db_manager.aget_total_count()

        assert result3.success
        assert result3.markdown == "# Example Domain\nThis domain is for use in documentation examples without needing permission. Avoid use in operations.\n[Learn more](https://iana.org/domains/example)\n"
        assert cache_size3 == cache_size


@pytest.mark.asyncio
async def test_bypass_cache():
    aget_cached_url_spy = AsyncMock(wraps=async_db_manager.aget_cached_url)

    with patch.object(async_db_manager, 'aget_cached_url', aget_cached_url_spy):
        async with AsyncWebCrawler(verbose=True) as crawler:
            result1 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED
            ))

            assert result1.success
            assert aget_cached_url_spy.call_count == 1

            result2 = await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS
            ))
            
            assert result2.success
            assert aget_cached_url_spy.call_count == 1


@pytest.mark.asyncio
async def test_clear_cache():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Crawl and cache
        await crawler.arun(url=EXAMPLE_URL, config=CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED
        ))
        cache_size = await async_db_manager.aget_total_count()
        assert cache_size > 0

        # Clear cache
        await async_db_manager.aclear_db()

        # Check cache size
        cache_size = await async_db_manager.aget_total_count()
        assert cache_size == 0


# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
