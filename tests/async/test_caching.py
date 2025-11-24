import pytest

import os
import shutil
import sys
import tempfile
from unittest.mock import Mock, patch

import pytest_asyncio

from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.cache_client import CacheClient
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


class TestCacheClient(CacheClient):
    """
    A simple local file-based cache client. Does not support cache expiration.
    """
    def __init__(self):
        self.base_directory = tempfile.mkdtemp(prefix="crawl4ai_test_cache_")

    def _get_file_path(self, key: str) -> str:
        safe_key = key.replace(":", "_").replace("/", "_")
        return os.path.join(self.base_directory, safe_key)

    def get(self, key: str) -> str | None:
        file_path = self._get_file_path(key)
        if os.path.exists(self._get_file_path(key)):
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        return None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        file_path = self._get_file_path(key)
        with open(file_path, "w+", encoding="utf-8") as f:
            f.write(value)

    def clear(self, prefix: str) -> None:
        for filename in os.listdir(self.base_directory):
            if filename.startswith(prefix.replace(":", "_")):
                file_path = os.path.join(self.base_directory, filename)
                os.remove(file_path)
    
    # === UTILITY METHODS FOR TESTING ===
    
    def count(self) -> int:
        return len(os.listdir(self.base_directory))

    def cleanup(self):
        shutil.rmtree(self.base_directory)


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
