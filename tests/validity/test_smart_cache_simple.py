"""
Simple test for SMART cache mode functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.cache_context import CacheMode
import time


async def test_smart_cache():
    """Test SMART cache mode with a simple example"""
    
    print("Testing SMART Cache Mode")
    print("-" * 40)
    
    # Test URL
    url = "https://example.com"
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # First crawl with normal caching
        print("\n1. Initial crawl with ENABLED mode:")
        config1 = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
        result1 = await crawler.arun(url=url, config=config1)
        print(f"   Crawled: {len(result1.html)} bytes")
        print(f"   Headers: {list(result1.response_headers.keys())[:3]}...")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Re-crawl with SMART mode
        print("\n2. Re-crawl with SMART mode:")
        config2 = CrawlerRunConfig(cache_mode=CacheMode.SMART)
        start = time.time()
        result2 = await crawler.arun(url=url, config=config2)
        elapsed = time.time() - start
        
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Result: {len(result2.html)} bytes")
        print(f"   Should use cache (content unchanged)")
        
        # Test with dynamic content
        print("\n3. Testing with dynamic URL:")
        dynamic_url = "https://httpbin.org/uuid"
        
        # First crawl
        config3 = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
        result3 = await crawler.arun(url=dynamic_url, config=config3)
        content1 = result3.html
        
        # Re-crawl with SMART
        config4 = CrawlerRunConfig(cache_mode=CacheMode.SMART)
        result4 = await crawler.arun(url=dynamic_url, config=config4)
        content2 = result4.html
        
        print(f"   Content changed: {content1 != content2}")
        print(f"   Should re-crawl (dynamic content)")


if __name__ == "__main__":
    print(f"Python path: {sys.path[0]}")
    print(f"CacheMode values: {[e.value for e in CacheMode]}")
    print()
    asyncio.run(test_smart_cache())