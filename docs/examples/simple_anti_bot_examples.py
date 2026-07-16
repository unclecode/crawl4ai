import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

# Example 1: Stealth Mode
async def stealth_mode_example():
    browser_config = BrowserConfig(
        enable_stealth=True,
        headless=False
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun("https://example.com")
        return result.html[:500]

# Example 2: Undetected Browser
async def undetected_browser_example():
    browser_config = BrowserConfig(
        headless=False
    )
    
    adapter = UndetectedAdapter()
    strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=adapter
    )
    
    async with AsyncWebCrawler(
        crawler_strategy=strategy,
        config=browser_config
    ) as crawler:
        result = await crawler.arun("https://example.com")
        return result.html[:500]

# Example 3: Both Combined
async def combined_example():
    browser_config = BrowserConfig(
        enable_stealth=True,
        headless=False
    )
    
    adapter = UndetectedAdapter()
    strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=adapter
    )
    
    async with AsyncWebCrawler(
        crawler_strategy=strategy,
        config=browser_config
    ) as crawler:
        result = await crawler.arun("https://example.com")
        return result.html[:500]

# Run examples
if __name__ == "__main__":
    asyncio.run(stealth_mode_example())
    asyncio.run(undetected_browser_example())
    asyncio.run(combined_example())