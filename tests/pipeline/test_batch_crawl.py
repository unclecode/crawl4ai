"""Test the Crawler class for batch crawling capabilities."""

import asyncio
import pytest
from typing import List, Dict, Any, Optional, Tuple

from crawl4ai import Crawler
from crawl4ai import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.models import CrawlResult, CrawlResultContainer
from crawl4ai.browser import BrowserHub
from crawl4ai.cache_context import CacheMode

# Test URLs for crawling
SAFE_URLS = [
   "https://example.com",
   "https://httpbin.org/html",
   "https://httpbin.org/headers",
   "https://httpbin.org/ip",
   "https://httpbin.org/user-agent",
   "https://httpstat.us/200",
   "https://jsonplaceholder.typicode.com/posts/1",
   "https://jsonplaceholder.typicode.com/comments/1",
   "https://iana.org",
   "https://www.python.org"
]

# Simple test for batch crawling
@pytest.mark.asyncio
async def test_batch_crawl_simple():
    """Test simple batch crawling with multiple URLs."""
    # Use a few test URLs
    urls = SAFE_URLS[:3]
    
    # Custom crawler config
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded"
    )
    
    # Crawl multiple URLs using batch crawl
    results = await Crawler.crawl(
        urls,
        crawler_config=crawler_config
    )
    
    # Verify the results
    assert isinstance(results, dict)
    assert len(results) == len(urls)
    
    for url in urls:
        assert url in results
        assert results[url].success
        assert results[url].html is not None

# Test parallel batch crawling
@pytest.mark.asyncio
async def test_parallel_batch_crawl():
    """Test parallel batch crawling with multiple URLs."""
    # Use several URLs for parallel crawling
    urls = SAFE_URLS[:5]
    
    # Basic crawler config
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded"
    )
    
    # Crawl in parallel
    start_time = asyncio.get_event_loop().time()
    results = await Crawler.parallel_crawl(
        urls,
        crawler_config=crawler_config
    )
    end_time = asyncio.get_event_loop().time()
    
    # Verify results
    assert len(results) == len(urls)
    successful = sum(1 for r in results.values() if r.success)
    
    print(f"Parallel crawl of {len(urls)} URLs completed in {end_time - start_time:.2f}s")
    print(f"Success rate: {successful}/{len(urls)}")
    
    # At least 80% should succeed
    assert successful / len(urls) >= 0.8

# Test batch crawling with different configurations
@pytest.mark.asyncio
async def test_batch_crawl_mixed_configs():
    """Test batch crawling with different configurations for different URLs."""
    # Create URL batches with different configurations
    batch1 = (SAFE_URLS[:2], CrawlerRunConfig(wait_until="domcontentloaded", screenshot=False))
    batch2 = (SAFE_URLS[2:4], CrawlerRunConfig(wait_until="networkidle", screenshot=True))
    
    # Crawl with mixed configurations
    start_time = asyncio.get_event_loop().time()
    results = await Crawler.parallel_crawl([batch1, batch2])
    end_time = asyncio.get_event_loop().time()
    
    # Extract all URLs
    all_urls = batch1[0] + batch2[0]
    
    # Verify results
    assert len(results) == len(all_urls)
    
    # Check that screenshots are present only for batch2
    for url in batch1[0]:
        assert results[url].screenshot is None
    
    for url in batch2[0]:
        assert results[url].screenshot is not None
    
    print(f"Mixed-config parallel crawl of {len(all_urls)} URLs completed in {end_time - start_time:.2f}s")

# Test shared browser hub
@pytest.mark.asyncio
async def test_batch_crawl_shared_hub():
    """Test batch crawling with a shared browser hub."""
    # Create and initialize a browser hub
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )
    
    browser_hub = await BrowserHub.get_browser_manager(
        config=browser_config,
        max_browsers_per_config=3,
        max_pages_per_browser=4,
        initial_pool_size=1
    )
    
    try:
        # Use the hub for parallel crawling
        urls = SAFE_URLS[:3]
        
        start_time = asyncio.get_event_loop().time()
        results = await Crawler.parallel_crawl(
            urls,
            browser_hub=browser_hub,
            crawler_config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_until="domcontentloaded"
            )
        )
        end_time = asyncio.get_event_loop().time()
        
        # Verify results
        assert len(results) == len(urls)
        successful = sum(1 for r in results.values() if r.success)
        
        print(f"Shared hub parallel crawl of {len(urls)} URLs completed in {end_time - start_time:.2f}s")
        print(f"Success rate: {successful}/{len(urls)}")
        
        # Get browser hub statistics
        hub_stats = await browser_hub.get_pool_status()
        print(f"Browser hub stats: {hub_stats}")
        
        # At least 80% should succeed
        assert successful / len(urls) >= 0.8
        
    finally:
        # Clean up the browser hub
        await browser_hub.close()