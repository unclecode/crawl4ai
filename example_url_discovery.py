#!/usr/bin/env python3
"""
Runnable example for the /urls/discover endpoint.

This script demonstrates how to use the new URL Discovery API endpoint
to find relevant URLs from a domain before committing to a full crawl.
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any

# Configuration
BASE_URL = "http://localhost:11235"
EXAMPLE_DOMAIN = "nbcnews.com"


async def discover_urls_basic_example():
    """Basic example of URL discovery."""
    print("🔍 Basic URL Discovery Example")
    print("=" * 50)
    
    # Basic discovery request
    request_data = {
        "domain": EXAMPLE_DOMAIN,
        "seeding_config": {
            "source": "sitemap",      # Use sitemap for fast discovery
            "max_urls": 10           # Limit to 10 URLs
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/urls/discover",
                json=request_data,
                timeout=30.0
            )
            response.raise_for_status()
            
            urls = response.json()
            print(f"✅ Found {len(urls)} URLs")
            
            # Display first few URLs
            for i, url_obj in enumerate(urls[:3]):
                print(f"  {i+1}. {url_obj.get('url', 'N/A')}")
                
            return urls
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []


async def discover_urls_advanced_example():
    """Advanced example with filtering and metadata extraction."""
    print("\n🎯 Advanced URL Discovery Example")
    print("=" * 50)
    
    # Advanced discovery with filtering
    request_data = {
        "domain": EXAMPLE_DOMAIN,
        "seeding_config": {
            "source": "sitemap+cc",   # Use both sitemap and Common Crawl
            "pattern": "*/news/*",    # Filter to news articles only
            "extract_head": True,     # Extract page metadata
            "max_urls": 5,
            "live_check": True,       # Verify URLs are accessible
            "verbose": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/urls/discover",
                json=request_data,
                timeout=60.0  # Longer timeout for advanced features
            )
            response.raise_for_status()
            
            urls = response.json()
            print(f"✅ Found {len(urls)} news URLs with metadata")
            
            # Display URLs with metadata
            for i, url_obj in enumerate(urls[:3]):
                print(f"\n  {i+1}. URL: {url_obj.get('url', 'N/A')}")
                print(f"     Status: {url_obj.get('status', 'unknown')}")
                
                head_data = url_obj.get('head_data', {})
                if head_data:
                    title = head_data.get('title', 'No title')
                    description = head_data.get('description', 'No description')
                    print(f"     Title: {title[:60]}...")
                    print(f"     Description: {description[:60]}...")
                
            return urls
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []


async def discover_urls_with_scoring_example():
    """Example using BM25 relevance scoring."""
    print("\n🏆 URL Discovery with Relevance Scoring")
    print("=" * 50)
    
    # Discovery with relevance scoring
    request_data = {
        "domain": EXAMPLE_DOMAIN,
        "seeding_config": {
            "source": "sitemap",
            "extract_head": True,     # Required for BM25 scoring
            "query": "politics election",  # Search for political content
            "scoring_method": "bm25",
            "score_threshold": 0.1,   # Minimum relevance score
            "max_urls": 5
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/urls/discover",
                json=request_data,
                timeout=60.0
            )
            response.raise_for_status()
            
            urls = response.json()
            print(f"✅ Found {len(urls)} relevant URLs")
            
            # Display URLs sorted by relevance score
            for i, url_obj in enumerate(urls[:3]):
                score = url_obj.get('score', 0)
                print(f"\n  {i+1}. Score: {score:.3f}")
                print(f"     URL: {url_obj.get('url', 'N/A')}")
                
                head_data = url_obj.get('head_data', {})
                if head_data:
                    title = head_data.get('title', 'No title')
                    print(f"     Title: {title[:60]}...")
                
            return urls
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []


def demonstrate_request_schema():
    """Show the complete request schema with all options."""
    print("\n📋 Complete Request Schema")
    print("=" * 50)
    
    complete_schema = {
        "domain": "example.com",  # Required: Domain to discover URLs from
        "seeding_config": {       # Optional: Configuration object
            # Discovery sources
            "source": "sitemap+cc",           # "sitemap", "cc", or "sitemap+cc"
            
            # Filtering options
            "pattern": "*/blog/*",            # URL pattern filter (glob style)
            "max_urls": 50,                   # Maximum URLs to return (-1 = no limit)
            "filter_nonsense_urls": True,     # Filter out nonsense URLs
            
            # Metadata and validation
            "extract_head": True,             # Extract <head> metadata
            "live_check": True,               # Verify URL accessibility
            
            # Performance and rate limiting
            "concurrency": 100,               # Concurrent requests
            "hits_per_sec": 10,              # Rate limit (requests/second)
            "force": False,                   # Bypass cache
            
            # Relevance scoring (requires extract_head=True)
            "query": "search terms",          # Query for BM25 scoring
            "scoring_method": "bm25",         # Scoring algorithm
            "score_threshold": 0.2,           # Minimum score threshold
            
            # Debugging
            "verbose": True                   # Enable verbose logging
        }
    }
    
    print("Full request schema:")
    print(json.dumps(complete_schema, indent=2))
    

async def main():
    """Run all examples."""
    print("🚀 URL Discovery API Examples")
    print("=" * 50)
    print(f"Server: {BASE_URL}")
    print(f"Domain: {EXAMPLE_DOMAIN}")
    
    # Check if server is running
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            response.raise_for_status()
            print("✅ Server is running\n")
        except Exception as e:
            print(f"❌ Server not available: {e}")
            print("Please start the Crawl4AI server first:")
            print("  docker compose up crawl4ai -d")
            return
    
    # Run examples
    await discover_urls_basic_example()
    await discover_urls_advanced_example()
    await discover_urls_with_scoring_example()
    
    # Show schema
    demonstrate_request_schema()
    
    print("\n🎉 Examples complete!")
    print("\nNext steps:")
    print("1. Use discovered URLs with the /crawl endpoint")
    print("2. Filter URLs based on your specific needs")
    print("3. Combine with other API endpoints for complete workflows")


if __name__ == "__main__":
    asyncio.run(main())