import asyncio
import time
from rich import print
from rich.table import Table
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    MemoryAdaptiveDispatcher,
    SemaphoreDispatcher,
    RateLimiter,
    CrawlerMonitor,
    DisplayMode,
    CacheMode,
    LXMLWebScrapingStrategy,
)


async def memory_adaptive(urls, browser_config, run_config):
    """Memory adaptive crawler with monitoring"""
    start = time.perf_counter()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=70.0,
            max_session_permit=10,
            monitor=CrawlerMonitor(
                max_visible_rows=15, display_mode=DisplayMode.DETAILED
            ),
        )
        results = await crawler.arun_many(
            urls, config=run_config, dispatcher=dispatcher
        )
    duration = time.perf_counter() - start
    return len(results), duration


async def memory_adaptive_with_rate_limit(urls, browser_config, run_config):
    """Memory adaptive crawler with rate limiting"""
    start = time.perf_counter()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=70.0,
            max_session_permit=10,
            rate_limiter=RateLimiter(
                base_delay=(1.0, 2.0), max_delay=30.0, max_retries=2
            ),
            monitor=CrawlerMonitor(
                max_visible_rows=15, display_mode=DisplayMode.DETAILED
            ),
        )
        results = await crawler.arun_many(
            urls, config=run_config, dispatcher=dispatcher
        )
    duration = time.perf_counter() - start
    return len(results), duration


async def semaphore(urls, browser_config, run_config):
    """Basic semaphore crawler"""
    start = time.perf_counter()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        dispatcher = SemaphoreDispatcher(
            semaphore_count=5,
            monitor=CrawlerMonitor(
                max_visible_rows=15, display_mode=DisplayMode.DETAILED
            ),
        )
        results = await crawler.arun_many(
            urls, config=run_config, dispatcher=dispatcher
        )
    duration = time.perf_counter() - start
    return len(results), duration


async def semaphore_with_rate_limit(urls, browser_config, run_config):
    """Semaphore crawler with rate limiting"""
    start = time.perf_counter()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        dispatcher = SemaphoreDispatcher(
            semaphore_count=5,
            rate_limiter=RateLimiter(
                base_delay=(1.0, 2.0), max_delay=30.0, max_retries=2
            ),
            monitor=CrawlerMonitor(
                max_visible_rows=15, display_mode=DisplayMode.DETAILED
            ),
        )
        results = await crawler.arun_many(
            urls, config=run_config, dispatcher=dispatcher
        )
    duration = time.perf_counter() - start
    return len(results), duration


def create_performance_table(results):
    """Creates a rich table showing performance results"""
    table = Table(title="Crawler Strategy Performance Comparison")
    table.add_column("Strategy", style="cyan")
    table.add_column("URLs Crawled", justify="right", style="green")
    table.add_column("Time (seconds)", justify="right", style="yellow")
    table.add_column("URLs/second", justify="right", style="magenta")

    sorted_results = sorted(results.items(), key=lambda x: x[1][1])

    for strategy, (urls_crawled, duration) in sorted_results:
        urls_per_second = urls_crawled / duration
        table.add_row(
            strategy, str(urls_crawled), f"{duration:.2f}", f"{urls_per_second:.2f}"
        )

    return table


async def main():
    urls = [f"https://example.com/page{i}" for i in range(1, 40)]
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, scraping_strategy=LXMLWebScrapingStrategy())

    results = {
        "Memory Adaptive": await memory_adaptive(urls, browser_config, run_config),
        # "Memory Adaptive + Rate Limit": await memory_adaptive_with_rate_limit(
        #     urls, browser_config, run_config
        # ),
        # "Semaphore": await semaphore(urls, browser_config, run_config),
        # "Semaphore + Rate Limit": await semaphore_with_rate_limit(
        #     urls, browser_config, run_config
        # ),
    }

    table = create_performance_table(results)
    print("\nPerformance Summary:")
    print(table)


if __name__ == "__main__":
    asyncio.run(main())
