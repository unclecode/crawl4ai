"""
Health Check Example - Crawl4AI
===============================

This example demonstrates how to use the health_check method to validate URLs
before crawling them. This is useful for:

1. Pre-crawl validation of URL lists
2. Filtering out dead URLs from batch operations
3. Network troubleshooting
4. Resource optimization

Basic usage examples for the new health_check feature.
"""

import asyncio
from crawl4ai import AsyncWebCrawler


async def basic_health_check():
    """Basic health check example"""
    print("=== Basic Health Check ===")
    
    async with AsyncWebCrawler() as crawler:
        # Test a working URL
        print("\n1. Testing accessible URL:")
        result = await crawler.health_check("https://httpbin.org/get")
        print(f"   Accessible: {result['accessible']}")
        print(f"   Status Code: {result['status_code']}")
        print(f"   Response Time: {result['response_time_ms']}ms")
        print(f"   Content Type: {result['content_type']}")
        
        # Test a URL that redirects
        print("\n2. Testing redirect URL:")
        result = await crawler.health_check("https://httpbin.org/redirect/1") 
        print(f"   Accessible: {result['accessible']}")
        print(f"   Redirected: {result['redirected']}")
        print(f"   Final URL: {result['final_url']}")
        
        # Test a broken URL
        print("\n3. Testing inaccessible URL:")
        result = await crawler.health_check("https://httpbin.org/status/404")
        print(f"   Accessible: {result['accessible']}")
        print(f"   Status Code: {result['status_code']}")


async def conditional_crawling():
    """Example of using health check for conditional crawling"""
    print("\n=== Conditional Crawling ===")
    
    urls_to_test = [
        "https://httpbin.org/get",              # Should work
        "https://httpbin.org/status/404",       # 404 error
        "https://httpbin.org/status/500",       # 500 error  
        "https://example.com",                  # Should work
    ]
    
    async with AsyncWebCrawler() as crawler:
        for url in urls_to_test:
            print(f"\nChecking: {url}")
            health = await crawler.health_check(url)
            
            if health["accessible"]:
                print(f"  ✅ Accessible ({health['status_code']}) - proceeding with crawl")
                try:
                    # Only crawl if health check passes
                    result = await crawler.arun(url)
                    print(f"  📄 Crawled successfully: {len(result.html)} chars")
                except Exception as e:
                    print(f"  ❌ Crawl failed despite health check: {e}")
            else:
                print(f"  ❌ Not accessible - skipping crawl")
                if "error" in health:
                    print(f"     Error: {health['error']}")


async def batch_url_validation():
    """Example of filtering a batch of URLs"""
    print("\n=== Batch URL Validation ===")
    
    # Simulate a list of URLs from various sources
    url_list = [
        "https://httpbin.org/get",
        "https://httpbin.org/html", 
        "https://httpbin.org/status/404",
        "https://httpbin.org/status/500",
        "https://example.com",
        "https://invalid-domain-12345.com",  # Should fail
        "https://httpbin.org/delay/1",       # Should work but slow
    ]
    
    async with AsyncWebCrawler() as crawler:
        print(f"Validating {len(url_list)} URLs...")
        
        accessible_urls = []
        failed_urls = []
        
        for url in url_list:
            health = await crawler.health_check(url)
            
            if health["accessible"]:
                accessible_urls.append({
                    "url": url,
                    "status_code": health["status_code"],
                    "response_time_ms": health["response_time_ms"]
                })
                print(f"  ✅ {url} - {health['status_code']} ({health['response_time_ms']}ms)")
            else:
                error_msg = health.get("error", f"HTTP {health['status_code']}")
                failed_urls.append({
                    "url": url,
                    "error": error_msg
                })
                print(f"  ❌ {url} - {error_msg}")
        
        print(f"\nSummary:")
        print(f"  Accessible URLs: {len(accessible_urls)}")
        print(f"  Failed URLs: {len(failed_urls)}")
        
        # Now crawl only the accessible URLs
        if accessible_urls:
            print(f"\nCrawling {len(accessible_urls)} accessible URLs...")
            crawl_urls = [item["url"] for item in accessible_urls]
            
            # Use arun_many for batch crawling
            results = await crawler.arun_many(crawl_urls)
            success_count = sum(1 for r in results if r.success)
            print(f"Successfully crawled: {success_count}/{len(crawl_urls)} URLs")


async def health_check_with_custom_timeout():
    """Example of using custom timeouts"""
    print("\n=== Custom Timeout Example ===")
    
    async with AsyncWebCrawler() as crawler:
        # Quick health check with short timeout
        print("Quick health check (1 second timeout):")
        result = await crawler.health_check("https://httpbin.org/delay/2", timeout=1.0)
        print(f"  Result: {result['accessible']} - {result.get('error', 'Success')}")
        
        # More patient health check 
        print("\nPatient health check (5 second timeout):")
        result = await crawler.health_check("https://httpbin.org/delay/2", timeout=5.0)
        print(f"  Result: {result['accessible']} - Status: {result.get('status_code', 'Error')}")


async def main():
    """Run all examples"""
    print("Crawl4AI Health Check Examples")
    print("=" * 40)
    
    await basic_health_check()
    await conditional_crawling()
    await batch_url_validation()
    await health_check_with_custom_timeout()
    
    print("\n" + "=" * 40)
    print("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
