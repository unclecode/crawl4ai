import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    CrawlResult,
    UndetectedAdapter
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy


async def main():
    # Create browser config
    browser_config = BrowserConfig(
        headless=False,
        verbose=True,
    )
    
    # Create the undetected adapter
    undetected_adapter = UndetectedAdapter()
    
    # Create the crawler strategy with the undetected adapter
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=undetected_adapter
    )
    
    # Create the crawler with our custom strategy
    async with AsyncWebCrawler(
        crawler_strategy=crawler_strategy,
        config=browser_config
    ) as crawler:
        # Configure the crawl
        crawler_config = CrawlerRunConfig(
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter()
            ),
            capture_console_messages=True,  # Enable console capture to test adapter
        )
        
        # Test on a site that typically detects bots
        print("Testing undetected adapter...")
        result: CrawlResult = await crawler.arun(
            url="https://www.helloworld.org", 
            config=crawler_config
        )
        
        print(f"Status: {result.status_code}")
        print(f"Success: {result.success}")
        print(f"Console messages captured: {len(result.console_messages or [])}")
        print(f"Markdown content (first 500 chars):\n{result.markdown.raw_markdown[:500]}")


if __name__ == "__main__":
    asyncio.run(main())