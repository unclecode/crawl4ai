"""Test examples for CDPBrowserStrategy.

These examples demonstrate the functionality of CDPBrowserStrategy
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
async def test_cdp_launch_connect():
    """Test launching a browser and connecting via CDP."""
    browser_config = BrowserConfig(
        use_managed_browser=True, browser_mode="cdp", headless=True
    )

    manager = BrowserManager(browser_config=browser_config, logger=logger)

    await manager.start()

    # Test with multiple pages
    pages = []
    for i in range(3):
        crawler_config = CrawlerRunConfig()
        page, context = await manager.get_page(crawler_config)
        await page.goto(f"https://example.com?test={i}")
        pages.append(page)

    # Verify all pages are working
    for i, page in enumerate(pages):
        title = await page.title()
        assert title, "Page has no title"

    await manager.close()

    assert True


@pytest.mark.skip(reason="Cookie data does not persist via user data dir")
@pytest.mark.asyncio
async def test_cdp_with_user_data_dir():
    """Test CDP browser with a user data directory."""
    # Create a temporary user data directory
    import tempfile

    user_data_dir = tempfile.mkdtemp(prefix="crawl4ai-test-")

    browser_config = BrowserConfig(
        headless=True, browser_mode="cdp", user_data_dir=user_data_dir
    )

    manager = BrowserManager(browser_config=browser_config, logger=logger)

    await manager.start()

    # Navigate to a page and store some data
    crawler_config = CrawlerRunConfig()
    page, context = await manager.get_page(crawler_config)

    # Set a cookie
    await context.add_cookies(
        [
            {
                "name": "test_cookie",
                "value": "test_value",
                "url": "https://example.com",
            }
        ]
    )

    # Visit the site
    await page.goto("https://example.com")

    # Verify cookie was set
    cookies = await context.cookies(["https://example.com"])
    assert any(cookie["name"] == "test_cookie" for cookie in cookies)

    # Close the browser
    await manager.close()

    # Start a new browser with the same user data directory
    manager2 = BrowserManager(browser_config=browser_config, logger=logger)
    await manager2.start()

    # Get a new page and check if the cookie persists
    page2, context2 = await manager2.get_page(crawler_config)
    await page2.goto("https://example.com")

    # Verify cookie persisted
    cookies2 = await context2.cookies(["https://example.com"])

    assert any(cookie["name"] == "test_cookie" for cookie in cookies2), (
        f"test_ccookie not found in {cookies2}"
    )

    # Clean up
    await manager2.close()

    # Remove temporary directory
    import shutil

    shutil.rmtree(user_data_dir, ignore_errors=True)
    assert True


@pytest.mark.skip(reason="Session data does not persist across contexts")
@pytest.mark.asyncio
async def test_cdp_session_management():
    """Test session management with CDP browser."""

    browser_config = BrowserConfig(
        use_managed_browser=True, headless=True, browser_mode="cdp"
    )

    manager = BrowserManager(browser_config=browser_config, logger=logger)

    await manager.start()

    # Create two sessions
    session1_id = "test_session_1"
    session2_id = "test_session_2"

    # Set up first session
    crawler_config1 = CrawlerRunConfig(session_id=session1_id)
    page1, _ = await manager.get_page(crawler_config1)
    await page1.goto("https://example.com")
    await page1.evaluate("localStorage.setItem('session1_data', 'test_value')")

    # Set up second session
    crawler_config2 = CrawlerRunConfig(session_id=session2_id)
    page2, _ = await manager.get_page(crawler_config2)
    await page2.goto("https://example.org")
    await page2.evaluate("localStorage.setItem('session2_data', 'test_value2')")

    # Get first session again
    page1_again, _ = await manager.get_page(crawler_config1)

    # Verify it's the same page and data persists
    assert page1 == page1_again, "Pages for the same session ID do not match"
    data1 = await page1_again.evaluate("localStorage.getItem('session1_data')")
    assert data1 == "test_value", "Session 1 data did not persist"

    # Kill first session
    await manager.kill_session(session1_id)

    # Verify second session still works
    data2 = await page2.evaluate("localStorage.getItem('session2_data')")
    assert data2 == "test_value2", "Session 2 data did not persist"

    await manager.close()
