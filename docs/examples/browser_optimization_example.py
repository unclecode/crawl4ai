"""
This example demonstrates optimal browser usage patterns in Crawl4AI:
1. Sequential crawling with session reuse
2. Parallel crawling with browser instance reuse
3. Performance optimization settings
"""

import asyncio
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def crawl_sequential(urls: List[str]):
    """
    Sequential crawling using session reuse - most efficient for moderate workloads
    """
    print("\n=== Sequential Crawling with Session Reuse ===")

    # Configure browser with optimized settings
    browser_config = BrowserConfig(
        headless=True,
        browser_args=[
            "--disable-gpu",  # Disable GPU acceleration
            "--disable-dev-shm-usage",  # Disable /dev/shm usage
            "--no-sandbox",  # Required for Docker
        ],
        viewport={
            "width": 800,
            "height": 600,
        },  # Smaller viewport for better performance
    )

    # Configure crawl settings
    crawl_config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            #  content_filter=PruningContentFilter(), In case you need fit_markdown
        ),
    )

    # Create single crawler instance
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        session_id = "session1"  # Use same session for all URLs
        for url in urls:
            result = await crawler.arun(
                url=url,
                config=crawl_config,
                session_id=session_id,  # Reuse same browser tab
            )
            if result.success:
                print(f"Successfully crawled {url}")
                print(f"Content length: {len(result.markdown_v2.raw_markdown)}")
    finally:
        await crawler.close()


async def crawl_parallel(urls: List[str], max_concurrent: int = 3):
    """
    Parallel crawling while reusing browser instance - best for large workloads
    """
    print("\n=== Parallel Crawling with Browser Reuse ===")

    browser_config = BrowserConfig(
        headless=True,
        browser_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
        viewport={"width": 800, "height": 600},
    )

    crawl_config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            #  content_filter=PruningContentFilter(), In case you need fit_markdown
        ),
    )

    # Create single crawler instance for all parallel tasks
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        # Create tasks in batches to control concurrency
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = []

            for j, url in enumerate(batch):
                session_id = (
                    f"parallel_session_{j}"  # Different session per concurrent task
                )
                task = crawler.arun(url=url, config=crawl_config, session_id=session_id)
                tasks.append(task)

            # Wait for batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Error crawling {url}: {str(result)}")
                elif result.success:
                    print(f"Successfully crawled {url}")
                    print(f"Content length: {len(result.markdown_v2.raw_markdown)}")
    finally:
        await crawler.close()


async def main():
    # Example URLs
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
        "https://example.com/page4",
    ]

    # Demo sequential crawling
    await crawl_sequential(urls)

    # Demo parallel crawling
    await crawl_parallel(urls, max_concurrent=2)


if __name__ == "__main__":
    asyncio.run(main())
