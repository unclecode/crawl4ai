#!/usr/bin/env python3
"""
Simple smoke test for CDP concurrency fixes.
This can be run without pytest to quickly validate the changes.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


async def test_basic_cdp():
    """Basic test that CDP browser works"""
    print("Test 1: Basic CDP browser test...")
    
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url="https://example.com",
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            assert result.success, f"Failed: {result.error_message}"
            assert len(result.html) > 0, "Empty HTML"
            print("  ✓ Basic CDP test passed")
            return True
    except Exception as e:
        print(f"  ✗ Basic CDP test failed: {e}")
        return False


async def test_arun_many_cdp():
    """Test arun_many with CDP browser - the key concurrency fix"""
    print("\nTest 2: arun_many with CDP browser...")
    
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://www.example.org",
    ]
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun_many(
                urls=urls,
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            
            assert len(results) == len(urls), f"Expected {len(urls)} results, got {len(results)}"
            
            success_count = sum(1 for r in results if r.success)
            print(f"  ✓ Crawled {success_count}/{len(urls)} URLs successfully")
            
            if success_count >= len(urls) * 0.8:  # Allow 20% failure for network issues
                print("  ✓ arun_many CDP test passed")
                return True
            else:
                print(f"  ✗ Too many failures: {len(urls) - success_count}/{len(urls)}")
                return False
                
    except Exception as e:
        print(f"  ✗ arun_many CDP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_arun_many():
    """Test concurrent arun_many calls - stress test for page lock"""
    print("\nTest 3: Concurrent arun_many calls...")
    
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        verbose=False
    )
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Run two arun_many calls concurrently
            task1 = crawler.arun_many(
                urls=["https://example.com", "https://httpbin.org/html"],
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            
            task2 = crawler.arun_many(
                urls=["https://www.example.org", "https://example.com"],
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            
            results1, results2 = await asyncio.gather(task1, task2, return_exceptions=True)
            
            # Check for exceptions
            if isinstance(results1, Exception):
                print(f"  ✗ Task 1 raised exception: {results1}")
                return False
            if isinstance(results2, Exception):
                print(f"  ✗ Task 2 raised exception: {results2}")
                return False
            
            total_success = sum(1 for r in results1 if r.success) + sum(1 for r in results2 if r.success)
            total_requests = len(results1) + len(results2)
            
            print(f"  ✓ {total_success}/{total_requests} concurrent requests succeeded")
            
            if total_success >= total_requests * 0.7:  # Allow 30% failure for concurrent stress
                print("  ✓ Concurrent arun_many test passed")
                return True
            else:
                print(f"  ✗ Too many concurrent failures")
                return False
                
    except Exception as e:
        print(f"  ✗ Concurrent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("CDP Concurrency Smoke Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests sequentially
    results.append(await test_basic_cdp())
    results.append(await test_arun_many_cdp())
    results.append(await test_concurrent_arun_many())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} smoke tests passed!")
        print("=" * 60)
        return 0
    else:
        print(f"✗ {total - passed}/{total} smoke tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
