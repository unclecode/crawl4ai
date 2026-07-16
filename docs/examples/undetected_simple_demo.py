"""
Simple Undetected Browser Demo
Demonstrates the basic usage of undetected browser mode
"""

import asyncio
from crawl4ai import (
    AsyncWebCrawler, 
    BrowserConfig, 
    CrawlerRunConfig,
    UndetectedAdapter
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

async def crawl_with_regular_browser(url: str):
    """Crawl with regular browser"""
    print("\n[Regular Browser Mode]")
    browser_config = BrowserConfig(
        headless=False,
        verbose=True,
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                delay_before_return_html=2.0
            )
        )
        
        print(f"Success: {result.success}")
        print(f"Status: {result.status_code}")
        print(f"Content length: {len(result.markdown.raw_markdown)}")
        
        # Check for bot detection keywords
        content = result.markdown.raw_markdown.lower()
        if any(word in content for word in ["cloudflare", "checking your browser", "please wait"]):
            print("⚠️  Bot detection triggered!")
        else:
            print("✅ Page loaded successfully")
        
        return result

async def crawl_with_undetected_browser(url: str):
    """Crawl with undetected browser"""
    print("\n[Undetected Browser Mode]")
    browser_config = BrowserConfig(
        headless=False,
        verbose=True,
    )
    
    # Create undetected adapter and strategy
    undetected_adapter = UndetectedAdapter()
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=undetected_adapter
    )
    
    async with AsyncWebCrawler(
        crawler_strategy=crawler_strategy,
        config=browser_config
    ) as crawler:
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                delay_before_return_html=2.0
            )
        )
        
        print(f"Success: {result.success}")
        print(f"Status: {result.status_code}")
        print(f"Content length: {len(result.markdown.raw_markdown)}")
        
        # Check for bot detection keywords
        content = result.markdown.raw_markdown.lower()
        if any(word in content for word in ["cloudflare", "checking your browser", "please wait"]):
            print("⚠️  Bot detection triggered!")
        else:
            print("✅ Page loaded successfully")
        
        return result

async def main():
    """Demo comparing regular vs undetected modes"""
    print("🤖 Crawl4AI Undetected Browser Demo")
    print("="*50)
    
    # Test URLs - you can change these
    test_urls = [
        "https://www.example.com",  # Simple site
        "https://httpbin.org/headers",  # Shows request headers
    ]
    
    for url in test_urls:
        print(f"\n📍 Testing URL: {url}")
        
        # Test with regular browser
        regular_result = await crawl_with_regular_browser(url)
        
        # Small delay
        await asyncio.sleep(2)
        
        # Test with undetected browser
        undetected_result = await crawl_with_undetected_browser(url)
        
        # Compare results
        print(f"\n📊 Comparison for {url}:")
        print(f"Regular browser content: {len(regular_result.markdown.raw_markdown)} chars")
        print(f"Undetected browser content: {len(undetected_result.markdown.raw_markdown)} chars")
        
        if url == "https://httpbin.org/headers":
            # Show headers for comparison
            print("\nHeaders seen by server:")
            print("Regular:", regular_result.markdown.raw_markdown[:500])
            print("\nUndetected:", undetected_result.markdown.raw_markdown[:500])

if __name__ == "__main__":
    asyncio.run(main())