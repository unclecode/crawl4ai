"""Test examples for BrowserManager.

These examples demonstrate the functionality of BrowserManager
and serve as functional tests.
"""

import pytest

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
async def test_basic_browser_manager():
    """Test basic BrowserManager functionality with default configuration."""

    # Create a browser manager with default config
    manager = BrowserManager(logger=logger, browser_config=BrowserConfig(headless=True))

    # Start the browser
    await manager.start()

    # Get a page
    crawler_config = CrawlerRunConfig(url="https://example.com")
    page, _ = await manager.get_page(crawler_config)

    # Navigate to a website
    await page.goto("https://example.com")
    title = await page.title()
    assert title, "Page has no title"
    # Clean up
    await manager.close()
    assert True


@pytest.mark.asyncio
async def test_custom_browser_config():
    """Test BrowserManager with custom browser configuration."""

    # Create a custom browser config
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        light_mode=True,
    )

    # Create browser manager with the config
    manager = BrowserManager(browser_config=browser_config, logger=logger)

    # Start the browser
    await manager.start()

    # Get a page
    crawler_config = CrawlerRunConfig(url="https://example.com")
    page, context = await manager.get_page(crawler_config)

    # Navigate to a website
    await page.goto("https://example.com")
    title = await page.title()
    assert title, "Page has no title"

    # Verify viewport size
    viewport_size = await page.evaluate(
        "() => ({ width: window.innerWidth, height: window.innerHeight })"
    )
    assert viewport_size["width"] == 1280, "Viewport width does not match"
    assert viewport_size["height"] == 800, "Viewport height does not match"

    # Clean up
    await manager.close()
    assert True


@pytest.mark.asyncio
async def test_multiple_pages():
    """Test BrowserManager with multiple pages."""

    # Create browser manager
    manager = BrowserManager(logger=logger, browser_config=BrowserConfig(headless=True))

    # Start the browser
    await manager.start()

    # Create multiple pages
    pages = []
    urls = ["https://example.com", "https://example.org", "https://mozilla.org"]

    for i, url in enumerate(urls):
        crawler_config = CrawlerRunConfig(url=url)
        page, context = await manager.get_page(crawler_config)
        await page.goto(url)
        pages.append((page, url))

    # Verify all pages are loaded correctly
    for page, url in pages:
        title = await page.title()
        assert title, "Page has no title"

    await manager.close()
    assert True


@pytest.mark.asyncio
async def test_session_management():
    """Test session management in BrowserManager."""
    manager = BrowserManager(logger=logger, browser_config=BrowserConfig(headless=True))

    # Start the browser
    await manager.start()

    # Create a session
    session_id = "test_session_1"
    crawler_config = CrawlerRunConfig(url="https://example.com", session_id=session_id)
    page1, context1 = await manager.get_page(crawler_config)
    await page1.goto("https://example.com")

    # Get the same session again
    page2, context2 = await manager.get_page(crawler_config)

    # Verify it's the same page/context
    assert page1 == page2, "Pages do not match for the same session ID"
    assert context1 == context2, "Contexts do not match for the same session ID"

    # Kill the session
    await manager.kill_session(session_id)

    # Clean up
    await manager.close()
    assert True
