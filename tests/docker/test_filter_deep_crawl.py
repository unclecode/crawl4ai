"""
Test the complete fix for both the filter serialization and JSON serialization issues.
"""

import asyncio
import httpx

from crawl4ai import BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, FilterChain, URLPatternFilter

BASE_URL = "http://localhost:11234/"  # Adjust port as needed

async def test_with_docker_client():
    """Test using the Docker client (same as 1419.py)."""
    from crawl4ai.docker_client import Crawl4aiDockerClient
    
    print("=" * 60)
    print("Testing with Docker Client")
    print("=" * 60)
    
    try:
        async with Crawl4aiDockerClient(
            base_url=BASE_URL,
            verbose=True,
        ) as client:
            
            # Create filter chain - testing the serialization fix
            filter_chain = [
                URLPatternFilter(
                    # patterns=["*about*", "*privacy*", "*terms*"],
                    patterns=["*advanced*"],
                    reverse=True
                ),
            ]
            
            crawler_config = CrawlerRunConfig(
                deep_crawl_strategy=BFSDeepCrawlStrategy(
                    max_depth=2,  # Keep it shallow for testing
                    # max_pages=5,  # Limit pages for testing
                    filter_chain=FilterChain(filter_chain)
                ),
                cache_mode=CacheMode.BYPASS,
            )
            
            print("\n1. Testing crawl with filters...")
            results = await client.crawl(
                ["https://docs.crawl4ai.com"],  # Simple test page
                browser_config=BrowserConfig(headless=True),
                crawler_config=crawler_config,
            )
            
            if results:
                print(f"✅ Crawl succeeded! Type: {type(results)}")
                if hasattr(results, 'success'):
                    print(f"✅ Results success: {results.success}")
                    # Test that we can iterate results without JSON errors
                    if hasattr(results, '__iter__'):
                        for i, result in enumerate(results):
                            if hasattr(result, 'url'):
                                print(f"   Result {i}: {result.url[:50]}...")
                            else:
                                print(f"   Result {i}: {str(result)[:50]}...")
                else:
                    # Handle list of results
                    print(f"✅ Got {len(results)} results")
                    for i, result in enumerate(results[:3]):  # Show first 3
                        print(f"   Result {i}: {result.url[:50]}...")
            else:
                print("❌ Crawl failed - no results returned")
                return False
                
        print("\n✅ Docker client test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Docker client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_rest_api():
    """Test using REST API directly."""
    print("\n" + "=" * 60)
    print("Testing with REST API")
    print("=" * 60)
    
    # Create filter configuration
    deep_crawl_strategy_payload = {
        "type": "BFSDeepCrawlStrategy",
        "params": {
            "max_depth": 2,
            # "max_pages": 5,
            "filter_chain": {
                "type": "FilterChain",
                "params": {
                    "filters": [
                        {
                            "type": "URLPatternFilter",
                            "params": {
                                "patterns": ["*advanced*"],
                                "reverse": True
                            }
                        }
                    ]
                }
            }
        }
    }
    
    crawl_payload = {
        "urls": ["https://docs.crawl4ai.com"],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "deep_crawl_strategy": deep_crawl_strategy_payload,
                "cache_mode": "bypass"
            }
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print("\n1. Sending crawl request to REST API...")
            response = await client.post(
                f"{BASE_URL}crawl",
                json=crawl_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ REST API returned 200 OK")
                data = response.json()
                if data.get("success"):
                    results = data.get("results", [])
                    print(f"✅ Got {len(results)} results")
                    for i, result in enumerate(results[:3]):
                        print(f"   Result {i}: {result.get('url', 'unknown')[:50]}...")
                else:
                    print(f"❌ Crawl not successful: {data}")
                    return False
            else:
                print(f"❌ REST API returned {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
                
        print("\n✅ REST API test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ REST API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n🧪 TESTING COMPLETE FIX FOR DOCKER FILTER AND JSON ISSUES")
    print("=" * 60)
    print("Make sure the server is running with the updated code!")
    print("=" * 60)
    
    results = []
    
    # Test 1: Docker client
    docker_passed = await test_with_docker_client()
    results.append(("Docker Client", docker_passed))
    
    # Test 2: REST API
    rest_passed = await test_with_rest_api()
    results.append(("REST API", rest_passed))
    
    # Summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Both issues are fully resolved!")
        print("\nThe fixes:")
        print("1. Filter serialization: Fixed by not serializing private __slots__")
        print("2. JSON serialization: Fixed by removing property descriptors from model_dump()")
    else:
        print("⚠️ Some tests failed. Please check the server logs for details.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))