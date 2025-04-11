"""Test examples for BrowserManager.

These examples demonstrate the functionality of BrowserManager
and serve as functional tests.
"""

import sys
from typing import AsyncGenerator, Optional

import pytest
import pytest_asyncio
from playwright.async_api import Page

from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.browser import BrowserManager


@pytest_asyncio.fixture
async def browser_manager() -> AsyncGenerator[BrowserManager, None]:
    """Fixture to create a BrowserManager instance."""
    manager = BrowserManager()
    await manager.start()
    yield manager
    await manager.close()

@pytest.mark.asyncio
async def test_basic_browser_manager(browser_manager: BrowserManager):
    """Test basic BrowserManager functionality with default configuration."""
    # Get a page
    crawler_config = CrawlerRunConfig(url="https://example.com")
    page, context = await browser_manager.get_page(crawler_config)
    assert page is not None, "Failed to create a page"

    # Navigate to a website
    await page.goto("https://example.com")
    title: str = await page.title()
    assert title == "Example Domain", f"Expected title 'Example Domain', got '{title}'"

@pytest.mark.asyncio
async def test_custom_browser_config():
    """Test BrowserManager with custom browser configuration."""
    manager: Optional[BrowserManager] = None
    try:
        # Create a custom browser config
        browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            viewport_width=1280,
            viewport_height=800,
            light_mode=True
        )

        # Create browser manager with the config
        manager = BrowserManager(browser_config=browser_config)

        # Start the browser
        await manager.start()

        # Get a page
        crawler_config = CrawlerRunConfig(url="https://example.com")
        page, context = await manager.get_page(crawler_config)
        assert page is not None, "Failed to create a page"

        # Navigate to a website
        await page.goto("https://example.com")
        title: str = await page.title()
        assert title == "Example Domain", f"Expected title 'Example Domain', got '{title}'"

        # Verify viewport size
        viewport_size = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
        assert viewport_size, "Failed to get viewport size"
        assert viewport_size["width"] == 1280, f"Expected width 1280, got {viewport_size["width"]}"
        assert viewport_size["height"] == 800, f"Expected height 800, got {viewport_size["height"]}"
    finally:
        if manager:
            await manager.close()

@pytest.mark.asyncio
async def test_multiple_pages(browser_manager: BrowserManager):
    """Test BrowserManager with multiple pages."""
    # Create multiple pages
    pages: list[tuple[Page, str]] = []
    urls: list[str] = ["https://example.com", "https://example.org", "https://mozilla.org"]

    for url in urls:
        crawler_config = CrawlerRunConfig(url=url)
        page, _ = await browser_manager.get_page(crawler_config)
        await page.goto(url)
        pages.append((page, url))


    # Verify all pages are loaded correctly
    for page, url in pages:
        title: str = await page.title()
        assert title, f"Failed to get title for {url}"


@pytest.mark.asyncio
async def test_session_management(browser_manager: BrowserManager):
    """Test session management in BrowserManager."""
    # Create a session
    session_id: str = "test_session_1"
    crawler_config = CrawlerRunConfig(url="https://example.com", session_id=session_id)
    page1, context1 = await browser_manager.get_page(crawler_config)
    assert page1 is not None, "Failed to create a page"
    response = await page1.goto("https://example.com")
    assert response, "Failed to navigate to the page"

    # Get the same session again
    page2, context2 = await browser_manager.get_page(crawler_config)
    assert page2 is not None, "Failed to create a page"

    # Verify it's the same page/context
    assert page1 == page2, "Pages are not the same"
    assert context1 == context2, "Contexts are not the same"

    # Kill the session
    await browser_manager.kill_session(session_id)

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))