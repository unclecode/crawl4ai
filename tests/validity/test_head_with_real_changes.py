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
    """
    if cache is None:
        cache = {}
    
    headers = {
        "Accept-Encoding": "identity",
        "Want-Content-Digest": "sha-256",
        "User-Agent": "Mozilla/5.0 (compatible; crawl4ai/1.0)"
    }
    
    if cache.get("etag"):
        headers["If-None-Match"] = cache["etag"]
    if cache.get("last_modified"):
        headers["If-Modified-Since"] = cache["last_modified"]
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=5) as client:
            response = await client.head(url, headers=headers)
        
        print(f"\nHEAD Response Status: {response.status_code}")
        print(f"Headers received: {dict(response.headers)}")
        
        # 304 Not Modified
        if response.status_code == 304:
            return False
        
        h = response.headers
        
        # Check headers in order of reliability
        if h.get("content-digest") and h["content-digest"] == cache.get("digest"):
            return False
        
        if h.get("etag") and h["etag"].startswith('"') and h["etag"] == cache.get("etag"):
            return False
        
        if h.get("last-modified") and cache.get("last_modified"):
            try:
                lm_new = email.utils.parsedate_to_datetime(h["last-modified"])
                lm_old = email.utils.parsedate_to_datetime(cache["last_modified"])
                if lm_new <= lm_old:
                    return False
            except:
                pass
        
        # Check Content-Length (weakest signal - only as a hint, not definitive)
        # Note: Same content length doesn't mean same content!
        if h.get("content-length") and cache.get("content_length"):
            try:
                if int(h["content-length"]) != cache.get("content_length"):
                    return True  # Length changed, likely content changed
                # If length is same, we can't be sure - default to crawling
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"Error during HEAD request: {e}")
        return True


async def test_with_changing_content():
    """Test with a real changing website"""
    print("=" * 60)
    print("Testing with real changing content")
    print("=" * 60)
    
    # Using httpbin's cache endpoint that changes after specified seconds
    url = "https://httpbin.org/cache/1"  # Cache for 1 second
    
    print(f"\n1️⃣ First request to {url}")
    async with httpx.AsyncClient() as client:
        response1 = await client.get(url)
        cache = {}
        if response1.headers.get("etag"):
            cache["etag"] = response1.headers["etag"]
        if response1.headers.get("last-modified"):
            cache["last_modified"] = response1.headers["last-modified"]
        print(f"Cached ETag: {cache.get('etag', 'None')}")
        print(f"Cached Last-Modified: {cache.get('last_modified', 'None')}")
    
    # Check immediately (should not need crawl)
    print(f"\n2️⃣ Checking immediately after first request...")
    needs_crawl = await should_crawl(url, cache)
    print(f"Result: {'NEED TO CRAWL' if needs_crawl else 'NO NEED TO CRAWL'}")
    
    # Wait for cache to expire
    print(f"\n⏳ Waiting 2 seconds for cache to expire...")
    await asyncio.sleep(2)
    
    # Check again (should need crawl now)
    print(f"\n3️⃣ Checking after cache expiry...")
    needs_crawl = await should_crawl(url, cache)
    print(f"Result: {'NEED TO CRAWL' if needs_crawl else 'NO NEED TO CRAWL'}")


async def test_news_website():
    """Test with a news website that updates frequently"""
    print("\n" + "=" * 60)
    print("Testing with news website (BBC)")
    print("=" * 60)
    
    url = "https://www.bbc.com"
    
    print(f"\n1️⃣ First crawl of {url}")
    async with httpx.AsyncClient() as client:
        response1 = await client.get(url)
        cache = {}
        h = response1.headers
        
        if h.get("etag"):
            cache["etag"] = h["etag"]
            print(f"Stored ETag: {h['etag'][:50]}...")
        if h.get("last-modified"):
            cache["last_modified"] = h["last-modified"]
            print(f"Stored Last-Modified: {h['last-modified']}")
        if h.get("content-length"):
            cache["content_length"] = int(h["content-length"])
            print(f"Stored Content-Length: {h['content-length']}")
    
    # Check multiple times
    for i in range(3):
        await asyncio.sleep(5)
        print(f"\n📊 Check #{i+2} - {datetime.now().strftime('%H:%M:%S')}")
        needs_crawl = await should_crawl(url, cache)
        print(f"Result: {'NEED TO CRAWL ✓' if needs_crawl else 'NO NEED TO CRAWL ✗'}")


async def test_api_endpoint():
    """Test with an API that provides proper caching headers"""
    print("\n" + "=" * 60)
    print("Testing with GitHub API")
    print("=" * 60)
    
    # GitHub user API (updates when user data changes)
    url = "https://api.github.com/users/github"
    
    headers = {"User-Agent": "crawl4ai-test"}
    
    print(f"\n1️⃣ First request to {url}")
    async with httpx.AsyncClient() as client:
        response1 = await client.get(url, headers=headers)
        cache = {}
        h = response1.headers
        
        if h.get("etag"):
            cache["etag"] = h["etag"]
            print(f"Stored ETag: {h['etag']}")
        if h.get("last-modified"):
            cache["last_modified"] = h["last-modified"]
            print(f"Stored Last-Modified: {h['last-modified']}")
        
        # Print rate limit info
        print(f"Rate Limit Remaining: {h.get('x-ratelimit-remaining', 'N/A')}")
    
    # Check if content changed
    print(f"\n2️⃣ Checking if content changed...")
    needs_crawl = await should_crawl(url, cache)
    print(f"Result: {'NEED TO CRAWL' if needs_crawl else 'NO NEED TO CRAWL (content unchanged)'}")


async def main():
    """Run all tests"""
    print("🚀 Testing HEAD request change detection with real websites\n")
    
    await test_with_changing_content()
    await test_news_website()
    await test_api_endpoint()
    
    print("\n✨ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())