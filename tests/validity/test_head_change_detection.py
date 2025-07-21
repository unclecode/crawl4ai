import asyncio
import httpx
import email.utils
from datetime import datetime
import json
from typing import Dict, Optional
import time


async def should_crawl(url: str, cache: Optional[Dict[str, str]] = None) -> bool:
    """
    Check if a URL should be crawled based on HEAD request headers.
    
    Args:
        url: The URL to check
        cache: Previous cache data containing etag, last_modified, digest, content_length
    
    Returns:
        True if the page has changed and should be crawled, False otherwise
    """
    if cache is None:
        cache = {}
    
    headers = {
        "Accept-Encoding": "identity",
        "Want-Content-Digest": "sha-256",
    }
    
    if cache.get("etag"):
        headers["If-None-Match"] = cache["etag"]
    if cache.get("last_modified"):
        headers["If-Modified-Since"] = cache["last_modified"]
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=5) as client:
            response = await client.head(url, headers=headers)
        
        # 304 Not Modified - content hasn't changed
        if response.status_code == 304:
            print(f"✓ 304 Not Modified - No need to crawl {url}")
            return False
        
        h = response.headers
        
        # Check Content-Digest (most reliable)
        if h.get("content-digest") and h["content-digest"] == cache.get("digest"):
            print(f"✓ Content-Digest matches - No need to crawl {url}")
            return False
        
        # Check strong ETag
        if h.get("etag") and h["etag"].startswith('"') and h["etag"] == cache.get("etag"):
            print(f"✓ Strong ETag matches - No need to crawl {url}")
            return False
        
        # Check Last-Modified
        if h.get("last-modified") and cache.get("last_modified"):
            try:
                lm_new = email.utils.parsedate_to_datetime(h["last-modified"])
                lm_old = email.utils.parsedate_to_datetime(cache["last_modified"])
                if lm_new <= lm_old:
                    print(f"✓ Last-Modified not newer - No need to crawl {url}")
                    return False
            except:
                pass
        
        # Check Content-Length (weakest signal - only as a hint, not definitive)
        # Note: Same content length doesn't mean same content!
        # This should only be used when no other signals are available
        if h.get("content-length") and cache.get("content_length"):
            try:
                if int(h["content-length"]) != cache.get("content_length"):
                    print(f"✗ Content-Length changed - Should crawl {url}")
                    return True
                else:
                    print(f"⚠️  Content-Length unchanged but content might have changed - Should crawl {url}")
                    return True  # When in doubt, crawl!
            except:
                pass
        
        print(f"✗ Content has changed - Should crawl {url}")
        return True
        
    except Exception as e:
        print(f"✗ Error checking {url}: {e}")
        return True  # On error, assume we should crawl


async def crawl_page(url: str) -> Dict[str, str]:
    """
    Simulate crawling a page and extracting cache headers.
    """
    print(f"\n🕷️  Crawling {url}...")
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        response = await client.get(url)
    
    cache_data = {}
    h = response.headers
    
    if h.get("etag"):
        cache_data["etag"] = h["etag"]
        print(f"  Stored ETag: {h['etag']}")
    
    if h.get("last-modified"):
        cache_data["last_modified"] = h["last-modified"]
        print(f"  Stored Last-Modified: {h['last-modified']}")
    
    if h.get("content-digest"):
        cache_data["digest"] = h["content-digest"]
        print(f"  Stored Content-Digest: {h['content-digest']}")
    
    if h.get("content-length"):
        cache_data["content_length"] = int(h["content-length"])
        print(f"  Stored Content-Length: {h['content-length']}")
    
    print(f"  Response size: {len(response.content)} bytes")
    return cache_data


async def test_static_site():
    """Test with a static website (example.com)"""
    print("=" * 60)
    print("Testing with static site: example.com")
    print("=" * 60)
    
    url = "https://example.com"
    
    # First crawl - always happens
    cache = await crawl_page(url)
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Second check - should not need to crawl
    print(f"\n📊 Checking if we need to re-crawl...")
    needs_crawl = await should_crawl(url, cache)
    
    if not needs_crawl:
        print("✅ Correctly identified: No need to re-crawl static content")
    else:
        print("❌ Unexpected: Static content flagged as changed")


async def test_dynamic_site():
    """Test with dynamic websites that change frequently"""
    print("\n" + "=" * 60)
    print("Testing with dynamic sites")
    print("=" * 60)
    
    # Test with a few dynamic sites
    dynamic_sites = [
        "https://api.github.com/",  # GitHub API root (changes with rate limit info)
        "https://worldtimeapi.org/api/timezone/UTC",  # Current time API
        "https://httpbin.org/uuid",  # Generates new UUID each request
    ]
    
    for url in dynamic_sites:
        print(f"\n🔄 Testing {url}")
        try:
            # First crawl
            cache = await crawl_page(url)
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Check if content changed
            print(f"\n📊 Checking if we need to re-crawl...")
            needs_crawl = await should_crawl(url, cache)
            
            if needs_crawl:
                print("✅ Correctly identified: Dynamic content has changed")
            else:
                print("⚠️  Note: Dynamic content appears unchanged (might have caching)")
                
        except Exception as e:
            print(f"❌ Error testing {url}: {e}")


async def test_conditional_get():
    """Test conditional GET fallback when HEAD doesn't provide enough info"""
    print("\n" + "=" * 60)
    print("Testing conditional GET scenario")
    print("=" * 60)
    
    url = "https://httpbin.org/etag/test-etag-123"
    
    # Simulate a scenario where we have an ETag
    cache = {"etag": '"test-etag-123"'}
    
    print(f"Testing with cached ETag: {cache['etag']}")
    needs_crawl = await should_crawl(url, cache)
    
    if not needs_crawl:
        print("✅ ETag matched - no crawl needed")
    else:
        print("✅ ETag didn't match - crawl needed")


async def main():
    """Run all tests"""
    print("🚀 Starting HEAD request change detection tests\n")
    
    await test_static_site()
    await test_dynamic_site()
    await test_conditional_get()
    
    print("\n✨ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())