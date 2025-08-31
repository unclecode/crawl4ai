"""
Undetected Browser Test - Cloudflare Protected Site
Tests the difference between regular and undetected modes on a Cloudflare-protected site
"""

import asyncio
from crawl4ai import (
    AsyncWebCrawler, 
    BrowserConfig, 
    CrawlerRunConfig,
    UndetectedAdapter
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

# Test URL with Cloudflare protection
TEST_URL = "https://nowsecure.nl"

async def test_regular_browser():
    """Test with regular browser - likely to be blocked"""
    print("=" * 60)
    print("Testing with Regular Browser")
    print("=" * 60)
    
    browser_config = BrowserConfig(
        headless=False,
        verbose=True,
        viewport_width=1920,
        viewport_height=1080,
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        config = CrawlerRunConfig(
            delay_before_return_html=2.0,
            simulate_user=True,
            magic=True,  # Try with magic mode too
        )
        
        result = await crawler.arun(url=TEST_URL, config=config)
        
        print(f"\n✓ Success: {result.success}")
        print(f"✓ Status Code: {result.status_code}")
        print(f"✓ HTML Length: {len(result.html)}")
        
        # Check for Cloudflare challenge
        if result.html:
            cf_indicators = [
                "Checking your browser",
                "Please stand by",
                "cloudflare",
                "cf-browser-verification",
                "Access denied",
                "Ray ID"
            ]
            
            detected = False
            for indicator in cf_indicators:
                if indicator.lower() in result.html.lower():
                    print(f"⚠️  Cloudflare Challenge Detected: '{indicator}' found")
                    detected = True
                    break
            
            if not detected and len(result.markdown.raw_markdown) > 100:
                print("✅ Successfully bypassed Cloudflare!")
                print(f"Content preview: {result.markdown.raw_markdown[:200]}...")
            elif not detected:
                print("⚠️  Page loaded but content seems minimal")
        
        return result

async def test_undetected_browser():
    """Test with undetected browser - should bypass Cloudflare"""
    print("\n" + "=" * 60)
    print("Testing with Undetected Browser")
    print("=" * 60)
    
    browser_config = BrowserConfig(
        headless=False,  # Headless is easier to detect
        verbose=True,
        viewport_width=1920,
        viewport_height=1080,
    )
    
    # Create undetected adapter
    undetected_adapter = UndetectedAdapter()
    
    # Create strategy with undetected adapter
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=undetected_adapter
    )
    
    async with AsyncWebCrawler(
        crawler_strategy=crawler_strategy,
        config=browser_config
    ) as crawler:
        config = CrawlerRunConfig(
            delay_before_return_html=2.0,
            simulate_user=True,
        )
        
        result = await crawler.arun(url=TEST_URL, config=config)
        
        print(f"\n✓ Success: {result.success}")
        print(f"✓ Status Code: {result.status_code}")
        print(f"✓ HTML Length: {len(result.html)}")
        
        # Check for Cloudflare challenge
        if result.html:
            cf_indicators = [
                "Checking your browser",
                "Please stand by",
                "cloudflare",
                "cf-browser-verification",
                "Access denied",
                "Ray ID"
            ]
            
            detected = False
            for indicator in cf_indicators:
                if indicator.lower() in result.html.lower():
                    print(f"⚠️  Cloudflare Challenge Detected: '{indicator}' found")
                    detected = True
                    break
            
            if not detected and len(result.markdown.raw_markdown) > 100:
                print("✅ Successfully bypassed Cloudflare!")
                print(f"Content preview: {result.markdown.raw_markdown[:200]}...")
            elif not detected:
                print("⚠️  Page loaded but content seems minimal")
        
        return result

async def main():
    """Compare regular vs undetected browser"""
    print("🤖 Crawl4AI - Cloudflare Bypass Test")
    print(f"Testing URL: {TEST_URL}\n")
    
    # Test regular browser
    regular_result = await test_regular_browser()
    
    # Small delay
    await asyncio.sleep(2)
    
    # Test undetected browser
    undetected_result = await test_undetected_browser()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Regular Browser:")
    print(f"  - Success: {regular_result.success}")
    print(f"  - Content Length: {len(regular_result.markdown.raw_markdown) if regular_result.markdown else 0}")
    
    print(f"\nUndetected Browser:")
    print(f"  - Success: {undetected_result.success}")
    print(f"  - Content Length: {len(undetected_result.markdown.raw_markdown) if undetected_result.markdown else 0}")
    
    if undetected_result.success and len(undetected_result.markdown.raw_markdown) > len(regular_result.markdown.raw_markdown):
        print("\n✅ Undetected browser successfully bypassed protection!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())