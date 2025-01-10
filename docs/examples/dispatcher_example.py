import asyncio, time
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, RateLimitConfig
from crawl4ai.dispatcher import DisplayMode

async def crawl_with_rate_limiting(urls):
    """
    Example function demonstrating how to use AsyncWebCrawler with rate limiting and resource monitoring.
    
    Args:
        urls (List[str]): List of URLs to crawl
        
    Returns:
        List[CrawlResult]: List of crawl results for each URL
    """
    # Configure browser settings
    browser_config = BrowserConfig(
        headless=True,  # Run browser in headless mode
        verbose=False   # Minimize browser logging
    )
    
    # Configure crawler settings with rate limiting
    run_config = CrawlerRunConfig(
        # Enable rate limiting
        enable_rate_limiting=True,
        rate_limit_config=RateLimitConfig(
            base_delay=(1.0, 2.0),  # Random delay between 1-2 seconds between requests
            max_delay=30.0,         # Maximum delay after rate limit hits
            max_retries=2,          # Number of retries before giving up
            rate_limit_codes=[429, 503]  # HTTP status codes to trigger rate limiting
        ),
        # Resource monitoring settings
        memory_threshold_percent=70.0,  # Pause crawling if memory usage exceeds this
        check_interval=0.5,            # How often to check resource usage
        max_session_permit=10,          # Maximum concurrent crawls
        display_mode=DisplayMode.DETAILED.value  # Show detailed progress
    )
    
    # Create and use crawler with context manager
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls, config=run_config)
        return results

def main():
    # Example URLs (replace with real URLs)
    urls = [
        f"https://example.com/page{i}" for i in range(1, 40)
    ]
    
    start = time.perf_counter()
    
    # Run the crawler
    results = asyncio.run(crawl_with_rate_limiting(urls))
    
    # Process results
    successful_results = [result for result in results if result.success]
    failed_results = [result for result in results if not result.success]
    
    end = time.perf_counter()
    
    # Print results
    print(f"Successful crawls: {len(successful_results)}")
    print(f"Failed crawls: {len(failed_results)}")
    print(f"Time taken: {end - start:.2f} seconds")

if __name__ == "__main__":
    main()
