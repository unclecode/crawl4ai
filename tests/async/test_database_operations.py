import os
import sys
import pytest
import asyncio
import json

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler

@pytest.mark.asyncio
async def test_cache_url():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.example.com"
        # First run to cache the URL
        result1 = await crawler.arun(url=url, bypass_cache=True)
        assert result1.success

        # Second run to retrieve from cache
        result2 = await crawler.arun(url=url, bypass_cache=False)
        assert result2.success
        assert result2.html == result1.html

@pytest.mark.asyncio
async def test_bypass_cache():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.python.org"
        # First run to cache the URL
        result1 = await crawler.arun(url=url, bypass_cache=True)
        assert result1.success

        # Second run bypassing cache
        result2 = await crawler.arun(url=url, bypass_cache=True)
        assert result2.success
        assert result2.html != result1.html  # Content might be different due to dynamic nature of websites

@pytest.mark.asyncio
async def test_cache_size():
    async with AsyncWebCrawler(verbose=True) as crawler:
        initial_size = await crawler.aget_cache_size()
        
        url = "https://www.nbcnews.com/business"
        await crawler.arun(url=url, bypass_cache=True)
        
        new_size = await crawler.aget_cache_size()
        assert new_size == initial_size + 1

@pytest.mark.asyncio
async def test_clear_cache():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.example.org"
        await crawler.arun(url=url, bypass_cache=True)
        
        initial_size = await crawler.aget_cache_size()
        assert initial_size > 0

        await crawler.aclear_cache()
        new_size = await crawler.aget_cache_size()
        assert new_size == 0

@pytest.mark.asyncio
async def test_flush_cache():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.example.net"
        await crawler.arun(url=url, bypass_cache=True)
        
        initial_size = await crawler.aget_cache_size()
        assert initial_size > 0

        await crawler.aflush_cache()
        new_size = await crawler.aget_cache_size()
        assert new_size == 0

        # Try to retrieve the previously cached URL
        result = await crawler.arun(url=url, bypass_cache=False)
        assert result.success  # The crawler should still succeed, but it will fetch the content anew

# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])