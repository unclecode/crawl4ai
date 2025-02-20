"""
This example demonstrates how to use the close_after_screenshot parameter
to control whether the page should be closed after taking a screenshot.

Two scenarios are demonstrated:
1. Default behavior: keep the page open after taking a screenshot
2. Automatic closure: close the page immediately after taking a screenshot
"""

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

async def main():
    # Initialize the crawler with default browser config
    browser_config = BrowserConfig(headless=True)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Example 1: Keep page open after screenshot (default behavior)
        # This is useful when you want to perform additional operations on the page
        config1 = CrawlerRunConfig(
            screenshot=True,
            close_after_screenshot=False  # This is the default
        )
        result1 = await crawler.arun("https://example.com", config=config1)
        print("Screenshot taken, page kept open for further operations")

        # Example 2: Close page after screenshot
        # This is useful for memory optimization when you don't need the page anymore
        config2 = CrawlerRunConfig(
            screenshot=True,
            close_after_screenshot=True  # Page will close after screenshot
        )
        result2 = await crawler.arun("https://example.com", config=config2)
        print("Screenshot taken, page closed automatically")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 