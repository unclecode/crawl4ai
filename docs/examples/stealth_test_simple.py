"""
Simple test to verify stealth mode is working
"""

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


async def test_stealth():
    """Test stealth mode effectiveness"""
    
    # Test WITHOUT stealth
    print("=== WITHOUT Stealth ===")
    config1 = BrowserConfig(
        headless=False,
        enable_stealth=False
    )
    
    async with AsyncWebCrawler(config=config1) as crawler:
        result = await crawler.arun(
            url="https://bot.sannysoft.com",
            config=CrawlerRunConfig(
                wait_until="networkidle",
                screenshot=True
            )
        )
        print(f"Success: {result.success}")
        # Take screenshot
        if result.screenshot:
            with open("without_stealth.png", "wb") as f:
                import base64
                f.write(base64.b64decode(result.screenshot))
            print("Screenshot saved: without_stealth.png")
    
    # Test WITH stealth
    print("\n=== WITH Stealth ===")
    config2 = BrowserConfig(
        headless=False,
        enable_stealth=True
    )
    
    async with AsyncWebCrawler(config=config2) as crawler:
        result = await crawler.arun(
            url="https://bot.sannysoft.com",
            config=CrawlerRunConfig(
                wait_until="networkidle",
                screenshot=True
            )
        )
        print(f"Success: {result.success}")
        # Take screenshot
        if result.screenshot:
            with open("with_stealth.png", "wb") as f:
                import base64
                f.write(base64.b64decode(result.screenshot))
            print("Screenshot saved: with_stealth.png")
    
    print("\nCheck the screenshots to see the difference in bot detection results!")


if __name__ == "__main__":
    asyncio.run(test_stealth())