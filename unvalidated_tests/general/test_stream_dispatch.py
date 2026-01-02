import os, sys
# append 2 parent directories to sys.path to import crawl4ai
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
parent_parent_dir = os.path.dirname(parent_dir)
sys.path.append(parent_parent_dir)


import asyncio
from typing import List
from crawl4ai import *
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher

async def test_streaming():
    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            # content_filter=PruningContentFilter(
            #     threshold=0.48, 
            #     threshold_type="fixed", 
            #     min_word_threshold=0
            # )
        ),
    )

    urls = ["http://example.com"] * 10
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        dispatcher = MemoryAdaptiveDispatcher(
            max_session_permit=5,
            check_interval=0.5
        )
        
        async for result in dispatcher.run_urls_stream(urls, crawler, crawler_config):
            print(f"Got result for {result.url} - Success: {result.result.success}")

if __name__ == "__main__":
    asyncio.run(test_streaming())