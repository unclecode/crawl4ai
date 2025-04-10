import os, sys
# append 2 parent directories to sys.path to import crawl4ai
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
parent_parent_dir = os.path.dirname(parent_dir)
sys.path.append(parent_parent_dir)

import asyncio
from crawl4ai import *

async def test_crawler():
    # Setup configurations
    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48, 
                threshold_type="fixed", 
                min_word_threshold=0
            )
        ),
    )

    # Test URLs - mix of different sites
    urls = [
        "http://example.com",
        "http://example.org",
        "http://example.net",
    ] * 10  # 15 total URLs

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("\n=== Testing Streaming Mode ===")
        async for result in await crawler.arun_many(
            urls=urls,
            config=crawler_config.clone(stream=True),
        ):
            print(f"Received result for: {result.url} - Success: {result.success}")
            
        print("\n=== Testing Batch Mode ===")
        results = await crawler.arun_many(
            urls=urls,
            config=crawler_config,
        )
        print(f"Received all {len(results)} results at once")
        for result in results:
            print(f"Batch result for: {result.url} - Success: {result.success}")

if __name__ == "__main__":
    asyncio.run(test_crawler())