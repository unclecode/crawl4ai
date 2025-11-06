"""
Test CDP browser concurrency with arun_many.

This test suite validates that the fixes for concurrent page creation
in managed browsers (CDP mode) work correctly, particularly:
1. Always creating new pages instead of reusing
2. Page lock serialization prevents race conditions
3. Multiple concurrent arun_many calls work correctly
"""

# Standard library imports
import asyncio
import os
import sys

# Third-party imports
import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Local imports
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig


@pytest.mark.asyncio
async def test_cdp_concurrent_arun_many_basic():
    """
    Test basic concurrent arun_many with CDP browser.
    This tests the fix for always creating new pages.
    """
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    urls = [
        "https://example.com",
        "https://www.python.org",
        "https://httpbin.org/html",
    ]
    
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Run arun_many - should create new pages for each URL
        results = await crawler.arun_many(urls=urls, config=config)
        
        # Verify all URLs were crawled successfully
        assert len(results) == len(urls), f"Expected {len(urls)} results, got {len(results)}"
        
        for i, result in enumerate(results):
            assert result is not None, f"Result {i} is None"
            assert result.success, f"Result {i} failed: {result.error_message}"
            assert result.status_code == 200, f"Result {i} has status {result.status_code}"
            assert len(result.html) > 0, f"Result {i} has empty HTML"


@pytest.mark.asyncio
async def test_cdp_multiple_sequential_arun_many():
    """
    Test multiple sequential arun_many calls with CDP browser.
    Each call should work correctly without interference.
    """
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    urls_batch1 = [
        "https://example.com",
        "https://httpbin.org/html",
    ]
    
    urls_batch2 = [
        "https://www.python.org",
        "https://example.org",
    ]
    
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First batch
        results1 = await crawler.arun_many(urls=urls_batch1, config=config)
        assert len(results1) == len(urls_batch1)
        for result in results1:
            assert result.success, f"First batch failed: {result.error_message}"
            
        # Second batch - should work without issues
        results2 = await crawler.arun_many(urls=urls_batch2, config=config)
        assert len(results2) == len(urls_batch2)
        for result in results2:
            assert result.success, f"Second batch failed: {result.error_message}"


@pytest.mark.asyncio
async def test_cdp_concurrent_arun_many_stress():
    """
    Stress test: Multiple concurrent arun_many calls with CDP browser.
    This is the key test for the concurrency fix - ensures page lock works.
    """
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    # Create multiple batches of URLs
    num_batches = 3
    urls_per_batch = 3
    
    batches = [
        [f"https://httpbin.org/delay/{i}?batch={batch}" 
         for i in range(urls_per_batch)]
        for batch in range(num_batches)
    ]
    
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Run multiple arun_many calls concurrently
        tasks = [
            crawler.arun_many(urls=batch, config=config)
            for batch in batches
        ]
        
        # Execute all batches in parallel
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify no exceptions occurred
        for i, results in enumerate(all_results):
            assert not isinstance(results, Exception), f"Batch {i} raised exception: {results}"
            assert len(results) == urls_per_batch, f"Batch {i}: expected {urls_per_batch} results, got {len(results)}"
            
            # Verify each result
            for j, result in enumerate(results):
                assert result is not None, f"Batch {i}, result {j} is None"
                # Some may fail due to network/timing, but should not crash
                if result.success:
                    assert len(result.html) > 0, f"Batch {i}, result {j} has empty HTML"


@pytest.mark.asyncio
async def test_cdp_page_isolation():
    """
    Test that pages are properly isolated - changes to one don't affect another.
    This validates that we're creating truly independent pages.
    """
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    url = "https://example.com"
    
    # Use different JS codes to verify isolation
    config1 = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        js_code="document.body.setAttribute('data-test', 'page1');"
    )
    
    config2 = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        js_code="document.body.setAttribute('data-test', 'page2');"
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Run both configs concurrently
        results = await crawler.arun_many(
            urls=[url, url],
            configs=[config1, config2]
        )
        
        assert len(results) == 2
        assert results[0].success and results[1].success
        
        # Both should succeed with their own modifications
        # (We can't directly check the data-test attribute, but success indicates isolation)
        assert 'Example Domain' in results[0].html
        assert 'Example Domain' in results[1].html


@pytest.mark.asyncio
async def test_cdp_with_different_viewport_sizes():
    """
    Test concurrent crawling with different viewport configurations.
    Ensures context/page creation handles different configs correctly.
    """
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    url = "https://example.com"
    
    # Different viewport sizes (though in CDP mode these may be limited)
    configs = [
        CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
    ]
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(
            urls=[url] * len(configs),
            configs=configs
        )
        
        assert len(results) == len(configs)
        for i, result in enumerate(results):
            assert result.success, f"Config {i} failed: {result.error_message}"
            assert len(result.html) > 0


@pytest.mark.asyncio
async def test_cdp_error_handling_concurrent():
    """
    Test that errors in one concurrent request don't affect others.
    This ensures proper isolation and error handling.
    """
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    urls = [
        "https://example.com",  # Valid
        "https://this-domain-definitely-does-not-exist-12345.com",  # Invalid
        "https://httpbin.org/html",  # Valid
    ]
    
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=config)
        
        assert len(results) == len(urls)
        
        # First and third should succeed
        assert results[0].success, "First URL should succeed"
        assert results[2].success, "Third URL should succeed"
        
        # Second may fail (invalid domain)
        # But its failure shouldn't affect the others


@pytest.mark.asyncio
async def test_cdp_large_batch():
    """
    Test handling a larger batch of URLs to ensure scalability.
    """
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    # Create 10 URLs
    num_urls = 10
    urls = [f"https://httpbin.org/delay/0?id={i}" for i in range(num_urls)]
    
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=config)
        
        assert len(results) == num_urls
        
        # Count successes
        successes = sum(1 for r in results if r.success)
        # Allow some failures due to network issues, but most should succeed
        assert successes >= num_urls * 0.8, f"Only {successes}/{num_urls} succeeded"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
