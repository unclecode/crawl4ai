"""
Test examples for parallel crawling with the browser module.

These examples demonstrate the functionality of parallel page creation
and serve as functional tests for multi-page crawling performance.
"""

import pytest

import asyncio
import os
import sys

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    )

from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.browser_manager import BrowserManager

# Create a logger for clear terminal output
logger = AsyncLogger(verbose=True, log_file=None)


@pytest.mark.asyncio
async def test_get_page_basic():
    browser_config = BrowserConfig(headless=True)
    manager = BrowserManager(browser_config=browser_config, logger=logger)

    await manager.start()

    # Request 3 pages
    crawler_config = CrawlerRunConfig()
    page, context = await manager.get_page(crawler_config)

    await page.goto("https://crawl4ai.com")
    title = await page.title()
    assert title, "Page has no title"

    await manager.close()
    assert True


@pytest.mark.asyncio
async def test_parallel_approaches_comparison():
    """Compare two parallel crawling approaches:
    1. Create a page for each URL on-demand (get_page + gather)
    2. Get all pages upfront with get_pages, then use them (get_pages + gather)
    """

    urls = [
        "https://example.com/page1",
        "https://crawl4ai.com",
        "https://kidocode.com",
        "https://bbc.com",
    ]

    browser_config = BrowserConfig(headless=True)
    manager = BrowserManager(browser_config=browser_config, logger=logger)

    await manager.start()

    async def fetch_title(url):
        """Create a new page for each URL, go to the URL, and get title"""
        crawler_config = CrawlerRunConfig(url=url)
        page, context = await manager.get_page(crawler_config)
        try:
            await page.goto(url)
            return await page.title()
        finally:
            await page.close()

    # Run fetch_title for each URL in parallel
    tasks = [fetch_title(url) for url in urls]
    results = await asyncio.gather(*tasks)

    assert len(results) == 4, "Missing results"

    await manager.close()
    assert True


@pytest.mark.asyncio
async def test_multi_browser_scaling(num_browsers=3, pages_per_browser=5):
    """Test performance with multiple browsers and pages per browser.
    Compares two approaches:
    1. On-demand page creation (get_page + gather)
    2. Pre-created pages (get_pages + gather)
    """

    # Generate test URLs
    total_pages = num_browsers * pages_per_browser
    urls = [f"https://example.com/page_{i}" for i in range(total_pages)]

    # Create browser managers
    managers = []

    # Start all browsers in parallel
    start_tasks = []
    for i in range(num_browsers):
        browser_config = BrowserConfig(
            headless=True  # Using default browser mode like in test_parallel_approaches_comparison
        )
        manager = BrowserManager(browser_config=browser_config, logger=logger)
        start_tasks.append(manager.start())
        managers.append(manager)

    await asyncio.gather(*start_tasks)

    # Distribute URLs among managers
    urls_per_manager = {}
    for i, manager in enumerate(managers):
        start_idx = i * pages_per_browser
        end_idx = min(start_idx + pages_per_browser, len(urls))
        urls_per_manager[manager] = urls[start_idx:end_idx]

    async def fetch_title_approach1(manager, url):
        """Create a new page for the URL, go to the URL, and get title"""
        crawler_config = CrawlerRunConfig(url=url)
        page, context = await manager.get_page(crawler_config)
        try:
            await page.goto(url)
            return await page.title()
        finally:
            await page.close()

    # Run fetch_title_approach1 for each URL in parallel
    tasks = []
    for manager, manager_urls in urls_per_manager.items():
        for url in manager_urls:
            tasks.append(fetch_title_approach1(manager, url))

    results = await asyncio.gather(*tasks)

    # Close all managers
    for manager in managers:
        await manager.close()

    assert len(results) == total_pages, "Missing results"
