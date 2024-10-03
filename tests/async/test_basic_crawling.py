import os
import sys
import pytest
import asyncio
import time

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler

@pytest.mark.asyncio
async def test_successful_crawl():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert result.url == url
        assert result.html
        assert result.markdown
        assert result.cleaned_html

@pytest.mark.asyncio
async def test_invalid_url():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.invalidurl12345.com"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert not result.success
        assert result.error_message

@pytest.mark.asyncio
async def test_multiple_urls():
    async with AsyncWebCrawler(verbose=True) as crawler:
        urls = [
            "https://www.nbcnews.com/business",
            "https://www.example.com",
            "https://www.python.org"
        ]
        results = await crawler.arun_many(urls=urls, bypass_cache=True)
        assert len(results) == len(urls)
        assert all(result.success for result in results)
        assert all(result.html for result in results)

@pytest.mark.asyncio
async def test_javascript_execution():
    async with AsyncWebCrawler(verbose=True) as crawler:
        js_code = "document.body.innerHTML = '<h1>Modified by JS</h1>';"
        url = "https://www.example.com"
        result = await crawler.arun(url=url, bypass_cache=True, js_code=js_code)
        assert result.success
        assert "<h1>Modified by JS</h1>" in result.html

@pytest.mark.asyncio
async def test_concurrent_crawling_performance():
    async with AsyncWebCrawler(verbose=True) as crawler:
        urls = [
            "https://www.nbcnews.com/business",
            "https://www.example.com",
            "https://www.python.org",
            "https://www.github.com",
            "https://www.stackoverflow.com"
        ]
        
        start_time = time.time()
        results = await crawler.arun_many(urls=urls, bypass_cache=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        print(f"Total time for concurrent crawling: {total_time:.2f} seconds")
        
        assert all(result.success for result in results)
        assert len(results) == len(urls)
        
        # Assert that concurrent crawling is faster than sequential
        # This multiplier may need adjustment based on the number of URLs and their complexity
        assert total_time < len(urls) * 5, f"Concurrent crawling not significantly faster: {total_time:.2f} seconds"

# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])