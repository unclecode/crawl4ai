# demo_browser_hub.py

import asyncio
from typing import List

from crawl4ai.browser.browser_hub import BrowserHub
from pipeline import create_pipeline
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.models import CrawlResultContainer
from crawl4ai.cache_context import CacheMode
from crawl4ai import DefaultMarkdownGenerator
from crawl4ai import PruningContentFilter

async def create_prewarmed_browser_hub(urls_to_crawl: List[str]):
    """Create a pre-warmed browser hub with 10 browsers and 5 pages each."""
    # Set up logging
    logger = AsyncLogger(verbose=True)
    logger.info("Setting up pre-warmed browser hub", tag="DEMO")
    
    # Create browser configuration
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,  # Set to False to see the browsers in action
        viewport_width=1280,
        viewport_height=800,
        light_mode=True,  # Optimize for performance
        java_script_enabled=True
    )
    
    # Create crawler configurations for pre-warming with different user agents
    # This allows pages to be ready for different scenarios
    crawler_configs = [
        CrawlerRunConfig(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            wait_until="networkidle"
        ),
        # CrawlerRunConfig(
        #     user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
        #     wait_until="networkidle"
        # ),
        # CrawlerRunConfig(
        #     user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        #     wait_until="networkidle"
        # )
    ]
    
    # Number of browsers and pages per browser
    num_browsers = 1
    pages_per_browser = 1
    
    # Distribute pages across configurations
    # We'll create a total of 50 pages (10 browsers × 5 pages)
    page_configs = []
    total_pages = num_browsers * pages_per_browser
    pages_per_config = total_pages // len(crawler_configs)
    
    for i, config in enumerate(crawler_configs):
        # For the last config, add any remaining pages
        if i == len(crawler_configs) - 1:
            remaining = total_pages - (pages_per_config * (len(crawler_configs) - 1))
            page_configs.append((browser_config, config, remaining))
        else:
            page_configs.append((browser_config, config, pages_per_config))
    
    # Create browser hub with pre-warmed pages
    start_time = asyncio.get_event_loop().time()
    logger.info("Initializing browser hub with pre-warmed pages...", tag="DEMO")
    
    hub = await BrowserHub.get_browser_manager(
        config=browser_config,
        hub_id="demo_hub",
        logger=logger,
        max_browsers_per_config=num_browsers,
        max_pages_per_browser=pages_per_browser,
        initial_pool_size=num_browsers,
        page_configs=page_configs
    )
    
    end_time = asyncio.get_event_loop().time()
    logger.success(
        message="Browser hub initialized with {total_pages} pre-warmed pages in {duration:.2f} seconds",
        tag="DEMO",
        params={
            "total_pages": total_pages,
            "duration": end_time - start_time
        }
    )
    
    # Get and display pool status
    status = await hub.get_pool_status()
    logger.info(
        message="Browser pool status: {status}",
        tag="DEMO",
        params={"status": status}
    )
    
    return hub

async def crawl_urls_with_hub(hub, urls: List[str]) -> List[CrawlResultContainer]:
    """Crawl a list of URLs using a pre-warmed browser hub."""
    logger = AsyncLogger(verbose=True)
    
    # Create crawler configuration
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=0
            )
        ),
        wait_until="networkidle",
        screenshot=True
    )
    
    # Create pipeline with the browser hub
    pipeline = await create_pipeline(
        browser_hub=hub,
        logger=logger
    )
    
    results = []
    
    # Crawl all URLs in parallel
    async def crawl_url(url):
        logger.info(f"Crawling {url}...", tag="CRAWL")
        result = await pipeline.crawl(url=url, config=crawler_config)
        logger.success(f"Completed crawl of {url}", tag="CRAWL")
        return result
    
    # Create tasks for all URLs
    tasks = [crawl_url(url) for url in urls]
    
    # Execute all tasks in parallel and collect results
    results = await asyncio.gather(*tasks)
    
    return results

async def main():
    """Main demo function."""
    # List of URLs to crawl
    urls_to_crawl = [
        "https://example.com",
        # "https://www.python.org",
        # "https://httpbin.org/html",
        # "https://news.ycombinator.com",
        # "https://github.com",
        # "https://pypi.org",
        # "https://docs.python.org/3/",
        # "https://opensource.org",
        # "https://whatismyipaddress.com",
        # "https://en.wikipedia.org/wiki/Web_scraping"
    ]
    
    # Set up logging
    logger = AsyncLogger(verbose=True)
    logger.info("Starting browser hub demo", tag="DEMO")
    
    try:
        # Create pre-warmed browser hub
        hub = await create_prewarmed_browser_hub(urls_to_crawl)
        
        # Use hub to crawl URLs
        logger.info("Crawling URLs in parallel...", tag="DEMO")
        start_time = asyncio.get_event_loop().time()
        
        results = await crawl_urls_with_hub(hub, urls_to_crawl)
        
        end_time = asyncio.get_event_loop().time()
        
        # Display results
        logger.success(
            message="Crawled {count} URLs in {duration:.2f} seconds (average: {avg:.2f} seconds per URL)",
            tag="DEMO",
            params={
                "count": len(results),
                "duration": end_time - start_time,
                "avg": (end_time - start_time) / len(results)
            }
        )
        
        # Print summary of results
        logger.info("Crawl results summary:", tag="DEMO")
        for i, result in enumerate(results):
            logger.info(
                message="{idx}. {url}: Success={success}, Content length={length}",
                tag="RESULT",
                params={
                    "idx": i+1,
                    "url": result.url,
                    "success": result.success,
                    "length": len(result.html) if result.html else 0
                }
            )
            
            if result.success and result.markdown and result.markdown.raw_markdown:
                # Print a snippet of the markdown
                markdown_snippet = result.markdown.raw_markdown[:150] + "..."
                logger.info(
                    message="   Markdown: {snippet}",
                    tag="RESULT",
                    params={"snippet": markdown_snippet}
                )
        
        # Display final browser pool status
        status = await hub.get_pool_status()
        logger.info(
            message="Final browser pool status: {status}",
            tag="DEMO",
            params={"status": status}
        )
        
    finally:
        # Clean up
        logger.info("Shutting down browser hub...", tag="DEMO")
        await BrowserHub.shutdown_all()
        logger.success("Demo completed", tag="DEMO")

if __name__ == "__main__":
    asyncio.run(main())