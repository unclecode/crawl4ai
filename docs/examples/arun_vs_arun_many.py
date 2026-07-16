import asyncio
import time
from crawl4ai.async_webcrawler import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher, RateLimiter

VERBOSE = False

async def crawl_sequential(urls):
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=VERBOSE)
    results = []
    start_time = time.perf_counter()
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            result_container = await crawler.arun(url=url, config=config)
            results.append(result_container[0])
    total_time = time.perf_counter() - start_time
    return total_time, results

async def crawl_parallel_dispatcher(urls):
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=VERBOSE)
    # Dispatcher with rate limiter enabled (default behavior)
    dispatcher = MemoryAdaptiveDispatcher(
        rate_limiter=RateLimiter(base_delay=(1.0, 3.0), max_delay=60.0, max_retries=3),
        max_session_permit=50,
    )
    start_time = time.perf_counter()
    async with AsyncWebCrawler() as crawler:
        result_container = await crawler.arun_many(urls=urls, config=config, dispatcher=dispatcher)
        results = []
        if isinstance(result_container, list):
            results = result_container
        else:
            async for res in result_container:
                results.append(res)
    total_time = time.perf_counter() - start_time
    return total_time, results

async def crawl_parallel_no_rate_limit(urls):
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=VERBOSE)
    # Dispatcher with no rate limiter and a high session permit to avoid queuing
    dispatcher = MemoryAdaptiveDispatcher(
        rate_limiter=None,
        max_session_permit=len(urls)  # allow all URLs concurrently
    )
    start_time = time.perf_counter()
    async with AsyncWebCrawler() as crawler:
        result_container = await crawler.arun_many(urls=urls, config=config, dispatcher=dispatcher)
        results = []
        if isinstance(result_container, list):
            results = result_container
        else:
            async for res in result_container:
                results.append(res)
    total_time = time.perf_counter() - start_time
    return total_time, results

async def main():
    urls = ["https://example.com"] * 100
    print(f"Crawling {len(urls)} URLs sequentially...")
    seq_time, seq_results = await crawl_sequential(urls)
    print(f"Sequential crawling took: {seq_time:.2f} seconds\n")
    
    print(f"Crawling {len(urls)} URLs in parallel using arun_many with dispatcher (with rate limit)...")
    disp_time, disp_results = await crawl_parallel_dispatcher(urls)
    print(f"Parallel (dispatcher with rate limiter) took: {disp_time:.2f} seconds\n")
       
    print(f"Crawling {len(urls)} URLs in parallel using dispatcher with no rate limiter...")
    no_rl_time, no_rl_results = await crawl_parallel_no_rate_limit(urls)
    print(f"Parallel (dispatcher without rate limiter) took: {no_rl_time:.2f} seconds\n")
    
    print("Crawl4ai - Crawling Comparison")
    print("--------------------------------------------------------")
    print(f"Sequential crawling took: {seq_time:.2f} seconds")
    print(f"Parallel (dispatcher with rate limiter) took: {disp_time:.2f} seconds")
    print(f"Parallel (dispatcher without rate limiter) took: {no_rl_time:.2f} seconds")
    
if __name__ == "__main__":
    asyncio.run(main())
