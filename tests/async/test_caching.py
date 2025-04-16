import asyncio
import sys

import pytest

from crawl4ai import CacheMode
from crawl4ai.async_webcrawler import AsyncWebCrawler


@pytest.mark.asyncio
async def test_caching():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"

        # First crawl (should not use cache)
        start_time = asyncio.get_event_loop().time()
        result1 = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS)
        end_time = asyncio.get_event_loop().time()
        time_taken1 = end_time - start_time

        assert result1.success

        # Second crawl (should use cache)
        start_time = asyncio.get_event_loop().time()
        result2 = await crawler.arun(url=url, bypass_cache=False)
        end_time = asyncio.get_event_loop().time()
        time_taken2 = end_time - start_time

        assert result2.success
        assert time_taken2 < time_taken1  # Cached result should be faster


@pytest.mark.asyncio
async def test_bypass_cache():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"

        # First crawl
        result1 = await crawler.arun(url=url, bypass_cache=False)
        assert result1.success

        # Second crawl with cache_mode=CacheMode.BYPASS
        result2 = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS)
        assert result2.success

        # Content should be different (or at least, not guaranteed to be the same)
        assert result1.html != result2.html or result1.markdown != result2.markdown


@pytest.mark.asyncio
async def test_clear_cache():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"

        # Crawl and cache
        await crawler.arun(url=url, bypass_cache=False)

        # Clear cache
        await crawler.aclear_cache()

        # Check cache size
        cache_size = await crawler.aget_cache_size()
        assert cache_size == 0


@pytest.mark.asyncio
async def test_flush_cache():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"

        # Crawl and cache
        await crawler.arun(url=url, bypass_cache=False)

        # Flush cache
        await crawler.aflush_cache()

        # Check cache size
        cache_size = await crawler.aget_cache_size()
        assert cache_size == 0


# Entry point for debugging
if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
