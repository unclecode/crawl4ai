import os
import sys
import pytest
import asyncio
import time

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler

@pytest.mark.asyncio
async def test_crawl_speed():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        start_time = time.time()
        result = await crawler.arun(url=url, bypass_cache=True)
        end_time = time.time()
        
        assert result.success
        crawl_time = end_time - start_time
        print(f"Crawl time: {crawl_time:.2f} seconds")
        
        assert crawl_time < 10, f"Crawl took too long: {crawl_time:.2f} seconds"

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
        
        assert total_time < len(urls) * 5, f"Concurrent crawling not significantly faster: {total_time:.2f} seconds"

@pytest.mark.asyncio
async def test_crawl_speed_with_caching():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        
        start_time = time.time()
        result1 = await crawler.arun(url=url, bypass_cache=True)
        end_time = time.time()
        first_crawl_time = end_time - start_time
        
        start_time = time.time()
        result2 = await crawler.arun(url=url, bypass_cache=False)
        end_time = time.time()
        second_crawl_time = end_time - start_time
        
        assert result1.success and result2.success
        print(f"First crawl time: {first_crawl_time:.2f} seconds")
        print(f"Second crawl time (cached): {second_crawl_time:.2f} seconds")
        
        assert second_crawl_time < first_crawl_time / 2, "Cached crawl not significantly faster"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])