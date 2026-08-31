#!/usr/bin/env python3
"""
Builtin Browser Example

This example demonstrates how to use Crawl4AI's builtin browser feature,
which simplifies the browser management process. With builtin mode:

- No need to manually start or connect to a browser
- No need to manage CDP URLs or browser processes
- Automatically connects to an existing browser or launches one if needed
- Browser persists between script runs, reducing startup time
- No explicit cleanup or close() calls needed

The example also demonstrates "auto-starting" where you don't need to explicitly
call start() method on the crawler.
"""

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import time

async def crawl_with_builtin_browser():
    """
    Simple example of crawling with the builtin browser.
    
    Key features:
    1. browser_mode="builtin" in BrowserConfig
    2. No explicit start() call needed
    3. No explicit close() needed
    """
    print("\n=== Crawl4AI Builtin Browser Example ===\n")
    
    # Create a browser configuration with builtin mode
    browser_config = BrowserConfig(
        browser_mode="builtin",  # This is the key setting!
        headless=True            # Can run headless for background operation
    )
    
    # Create crawler run configuration
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,  # Skip cache for this demo
        screenshot=True,              # Take a screenshot
        verbose=True                  # Show verbose logging
    )
    
    # Create the crawler instance
    # Note: We don't need to use "async with" context manager
    crawler = AsyncWebCrawler(config=browser_config)
    
    # Start crawling several URLs - no explicit start() needed!
    # The crawler will automatically connect to the builtin browser
    print("\n➡️ Crawling first URL...")
    t0 = time.time()
    result1 = await crawler.arun(
        url="https://crawl4ai.com",
        config=crawler_config
    )
    t1 = time.time()
    print(f"✅ First URL crawled in {t1-t0:.2f} seconds")
    print(f"   Got {len(result1.markdown.raw_markdown)} characters of content")
    print(f"   Title: {result1.metadata.get('title', 'No title')}")
    
    # Try another URL - the browser is already running, so this should be faster
    print("\n➡️ Crawling second URL...")
    t0 = time.time()
    result2 = await crawler.arun(
        url="https://example.com",
        config=crawler_config
    )
    t1 = time.time()
    print(f"✅ Second URL crawled in {t1-t0:.2f} seconds")
    print(f"   Got {len(result2.markdown.raw_markdown)} characters of content")
    print(f"   Title: {result2.metadata.get('title', 'No title')}")
    
    # The builtin browser continues running in the background
    # No need to explicitly close it
    print("\n🔄 The builtin browser remains running for future use")
    print("   You can use 'crwl browser status' to check its status")
    print("   or 'crwl browser stop' to stop it when completely done")

async def main():
    """Run the example"""
    await crawl_with_builtin_browser()

if __name__ == "__main__":
    asyncio.run(main())