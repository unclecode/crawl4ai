"""
Undetected vs Regular Browser Comparison
This example demonstrates the difference between regular and undetected browser modes
when accessing sites with bot detection services.

Based on tested anti-bot services:
- Cloudflare
- Kasada
- Akamai
- DataDome
- Bet365
- And others
"""

import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    PlaywrightAdapter,
    UndetectedAdapter,
    CrawlResult
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy


# Test URLs for various bot detection services
TEST_SITES = {
    "Cloudflare Protected": "https://nowsecure.nl",
    # "Bot Detection Test": "https://bot.sannysoft.com",
    # "Fingerprint Test": "https://fingerprint.com/products/bot-detection",
    # "Browser Scan": "https://browserscan.net",
    # "CreepJS": "https://abrahamjuliot.github.io/creepjs",
}


async def test_with_adapter(url: str, adapter_name: str, adapter):
    """Test a URL with a specific adapter"""
    browser_config = BrowserConfig(
        headless=False,  # Better for avoiding detection
        viewport_width=1920,
        viewport_height=1080,
        verbose=True,
    )
    
    # Create the crawler strategy with the adapter
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=adapter
    )
    
    print(f"\n{'='*60}")
    print(f"Testing with {adapter_name} adapter")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        async with AsyncWebCrawler(
            crawler_strategy=crawler_strategy,
            config=browser_config
        ) as crawler:
            crawler_config = CrawlerRunConfig(
                delay_before_return_html=3.0,  # Give page time to load
                wait_for_images=True,
                screenshot=True,
                simulate_user=True,  # Add user simulation
            )
            
            result: CrawlResult = await crawler.arun(
                url=url,
                config=crawler_config
            )
            
            # Check results
            print(f"✓ Status Code: {result.status_code}")
            print(f"✓ Success: {result.success}")
            print(f"✓ HTML Length: {len(result.html)}")
            print(f"✓ Markdown Length: {len(result.markdown.raw_markdown)}")
            
            # Check for common bot detection indicators
            detection_indicators = [
                "Access denied",
                "Please verify you are human",
                "Checking your browser",
                "Enable JavaScript",
                "captcha",
                "403 Forbidden",
                "Bot detection",
                "Security check"
            ]
            
            content_lower = result.markdown.raw_markdown.lower()
            detected = False
            for indicator in detection_indicators:
                if indicator.lower() in content_lower:
                    print(f"⚠️  Possible detection: Found '{indicator}'")
                    detected = True
                    break
            
            if not detected:
                print("✅ No obvious bot detection triggered!")
                # Show first 200 chars of content
                print(f"Content preview: {result.markdown.raw_markdown[:200]}...")
            
            return result.success and not detected
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def compare_adapters(url: str, site_name: str):
    """Compare regular and undetected adapters on the same URL"""
    print(f"\n{'#'*60}")
    print(f"# Testing: {site_name}")
    print(f"{'#'*60}")
    
    # Test with regular adapter
    regular_adapter = PlaywrightAdapter()
    regular_success = await test_with_adapter(url, "Regular", regular_adapter)
    
    # Small delay between tests
    await asyncio.sleep(2)
    
    # Test with undetected adapter
    undetected_adapter = UndetectedAdapter()
    undetected_success = await test_with_adapter(url, "Undetected", undetected_adapter)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary for {site_name}:")
    print(f"Regular Adapter: {'✅ Passed' if regular_success else '❌ Blocked/Detected'}")
    print(f"Undetected Adapter: {'✅ Passed' if undetected_success else '❌ Blocked/Detected'}")
    print(f"{'='*60}")
    
    return regular_success, undetected_success


async def main():
    """Run comparison tests on multiple sites"""
    print("🤖 Crawl4AI Browser Adapter Comparison")
    print("Testing regular vs undetected browser modes\n")
    
    results = {}
    
    # Test each site
    for site_name, url in TEST_SITES.items():
        regular, undetected = await compare_adapters(url, site_name)
        results[site_name] = {
            "regular": regular,
            "undetected": undetected
        }
        
        # Delay between different sites
        await asyncio.sleep(3)
    
    # Final summary
    print(f"\n{'#'*60}")
    print("# FINAL RESULTS")
    print(f"{'#'*60}")
    print(f"{'Site':<30} {'Regular':<15} {'Undetected':<15}")
    print(f"{'-'*60}")
    
    for site, result in results.items():
        regular_status = "✅ Passed" if result["regular"] else "❌ Blocked"
        undetected_status = "✅ Passed" if result["undetected"] else "❌ Blocked"
        print(f"{site:<30} {regular_status:<15} {undetected_status:<15}")
    
    # Calculate success rates
    regular_success = sum(1 for r in results.values() if r["regular"])
    undetected_success = sum(1 for r in results.values() if r["undetected"])
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"Success Rates:")
    print(f"Regular Adapter: {regular_success}/{total} ({regular_success/total*100:.1f}%)")
    print(f"Undetected Adapter: {undetected_success}/{total} ({undetected_success/total*100:.1f}%)")
    print(f"{'='*60}")


if __name__ == "__main__":
    # Note: This example may take a while to run as it tests multiple sites
    # You can comment out sites in TEST_SITES to run faster tests
    asyncio.run(main())