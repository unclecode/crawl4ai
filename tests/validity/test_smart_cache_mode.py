"""
Test SMART cache mode functionality in crawl4ai.

This test demonstrates:
1. Initial crawl with caching enabled
2. Re-crawl with SMART mode on static content (should use cache)
3. Re-crawl with SMART mode on dynamic content (should re-crawl)
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.cache_context import CacheMode
import time
from datetime import datetime


async def test_smart_cache_mode():
    """Test the SMART cache mode with both static and dynamic URLs"""
    
    print("=" * 60)
    print("Testing SMART Cache Mode")
    print("=" * 60)
    
    # URLs for testing
    static_url = "https://example.com"  # Rarely changes
    dynamic_url = "https://httpbin.org/uuid"  # Changes every request
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        
        # Test 1: Initial crawl with caching enabled
        print("\n1️⃣ Initial crawl with ENABLED cache mode")
        print("-" * 40)
        
        # Crawl static URL
        config_static = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            verbose=True
        )
        result_static_1 = await crawler.arun(url=static_url, config=config_static)
        print(f"✓ Static URL crawled: {len(result_static_1.html)} bytes")
        print(f"  Response headers: {list(result_static_1.response_headers.keys())[:5]}...")
        
        # Crawl dynamic URL
        config_dynamic = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            verbose=True
        )
        result_dynamic_1 = await crawler.arun(url=dynamic_url, config=config_dynamic)
        print(f"✓ Dynamic URL crawled: {len(result_dynamic_1.html)} bytes")
        dynamic_content_1 = result_dynamic_1.html
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Test 2: Re-crawl static URL with SMART mode
        print("\n2️⃣ Re-crawl static URL with SMART cache mode")
        print("-" * 40)
        
        config_smart = CrawlerRunConfig(
            cache_mode=CacheMode.SMART,  # This will be our new mode
            verbose=True
        )
        
        start_time = time.time()
        result_static_2 = await crawler.arun(url=static_url, config=config_smart)
        elapsed = time.time() - start_time
        
        print(f"✓ Static URL with SMART mode completed in {elapsed:.2f}s")
        print(f"  Should use cache (content unchanged)")
        print(f"  HTML length: {len(result_static_2.html)} bytes")
        
        # Test 3: Re-crawl dynamic URL with SMART mode
        print("\n3️⃣ Re-crawl dynamic URL with SMART cache mode")
        print("-" * 40)
        
        start_time = time.time()
        result_dynamic_2 = await crawler.arun(url=dynamic_url, config=config_smart)
        elapsed = time.time() - start_time
        dynamic_content_2 = result_dynamic_2.html
        
        print(f"✓ Dynamic URL with SMART mode completed in {elapsed:.2f}s")
        print(f"  Should re-crawl (content changes every request)")
        print(f"  HTML length: {len(result_dynamic_2.html)} bytes")
        print(f"  Content changed: {dynamic_content_1 != dynamic_content_2}")
        
        # Test 4: Test with a news website (content changes frequently)
        print("\n4️⃣ Testing with news website")
        print("-" * 40)
        
        news_url = "https://news.ycombinator.com"
        
        # First crawl
        result_news_1 = await crawler.arun(
            url=news_url, 
            config=CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
        )
        print(f"✓ News site initial crawl: {len(result_news_1.html)} bytes")
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # Re-crawl with SMART mode
        start_time = time.time()
        result_news_2 = await crawler.arun(
            url=news_url,
            config=CrawlerRunConfig(cache_mode=CacheMode.SMART)
        )
        elapsed = time.time() - start_time
        
        print(f"✓ News site SMART mode completed in {elapsed:.2f}s")
        print(f"  Content length changed: {len(result_news_1.html) != len(result_news_2.html)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print("✅ SMART cache mode should:")
        print("   - Use cache for static content (example.com)")
        print("   - Re-crawl dynamic content (httpbin.org/uuid)")
        print("   - Make intelligent decisions based on HEAD requests")
        print("   - Save bandwidth on unchanged content")


async def test_smart_cache_edge_cases():
    """Test edge cases for SMART cache mode"""
    
    print("\n" + "=" * 60)
    print("Testing SMART Cache Mode Edge Cases")
    print("=" * 60)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        
        # Test with URL that doesn't support HEAD
        print("\n🔧 Testing URL with potential HEAD issues")
        print("-" * 40)
        
        # Some servers don't handle HEAD well
        problematic_url = "https://httpbin.org/status/200"
        
        # Initial crawl
        await crawler.arun(
            url=problematic_url,
            config=CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
        )
        
        # Try SMART mode
        result = await crawler.arun(
            url=problematic_url,
            config=CrawlerRunConfig(cache_mode=CacheMode.SMART)
        )
        print(f"✓ Handled potentially problematic URL: {result.success}")
        
        # Test with URL that has no caching headers
        print("\n🔧 Testing URL with no cache headers")
        print("-" * 40)
        
        no_cache_url = "https://httpbin.org/html"
        
        # Initial crawl
        await crawler.arun(
            url=no_cache_url,
            config=CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
        )
        
        # SMART mode should handle gracefully
        result = await crawler.arun(
            url=no_cache_url,
            config=CrawlerRunConfig(cache_mode=CacheMode.SMART)
        )
        print(f"✓ Handled URL with no cache headers: {result.success}")


async def main():
    """Run all tests"""
    try:
        # Run main test
        await test_smart_cache_mode()
        
        # Run edge case tests
        await test_smart_cache_edge_cases()
        
        print("\n✨ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Note: This test will fail until SMART mode is implemented
    print("⚠️  Note: This test expects CacheMode.SMART to be implemented")
    print("⚠️  It will fail with AttributeError until the feature is added\n")
    
    asyncio.run(main())