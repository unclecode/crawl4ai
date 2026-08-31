"""Test examples for BrowserManager.

These examples demonstrate the functionality of BrowserManager
and serve as functional tests.
"""

import asyncio
import os
import sys
from typing import List

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai.browser import BrowserManager
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger

# Create a logger for clear terminal output
logger = AsyncLogger(verbose=True, log_file=None)

async def test_basic_browser_manager():
    """Test basic BrowserManager functionality with default configuration."""
    logger.info("Starting test_basic_browser_manager", tag="TEST")
    
    try:
        # Create a browser manager with default config
        manager = BrowserManager(logger=logger)
        
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully", tag="TEST")
        
        # Get a page
        crawler_config = CrawlerRunConfig(url="https://example.com")
        page, context = await manager.get_page(crawler_config)
        logger.info("Page created successfully", tag="TEST")
        
        # Navigate to a website
        await page.goto("https://example.com")
        title = await page.title()
        logger.info(f"Page title: {title}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.success("test_basic_browser_manager completed successfully", tag="TEST")
        return True
    except Exception as e:
        logger.error(f"test_basic_browser_manager failed: {str(e)}", tag="TEST")
        return False

async def test_custom_browser_config():
    """Test BrowserManager with custom browser configuration."""
    logger.info("Starting test_custom_browser_config", tag="TEST")
    
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
        manager = BrowserManager(browser_config=browser_config, logger=logger)
        
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully with custom config", tag="TEST")
        
        # Get a page
        crawler_config = CrawlerRunConfig(url="https://example.com")
        page, context = await manager.get_page(crawler_config)
        
        # Navigate to a website
        await page.goto("https://example.com")
        title = await page.title()
        logger.info(f"Page title: {title}", tag="TEST")
        
        # Verify viewport size
        viewport_size = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
        logger.info(f"Viewport size: {viewport_size}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.success("test_custom_browser_config completed successfully", tag="TEST")
        return True
    except Exception as e:
        logger.error(f"test_custom_browser_config failed: {str(e)}", tag="TEST")
        return False

async def test_multiple_pages():
    """Test BrowserManager with multiple pages."""
    logger.info("Starting test_multiple_pages", tag="TEST")
    
    try:
        # Create browser manager
        manager = BrowserManager(logger=logger)
        
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully", tag="TEST")
        
        # Create multiple pages
        pages = []
        urls = ["https://example.com", "https://example.org", "https://mozilla.org"]
        
        for i, url in enumerate(urls):
            crawler_config = CrawlerRunConfig(url=url)
            page, context = await manager.get_page(crawler_config)
            await page.goto(url)
            pages.append((page, url))
            logger.info(f"Created page {i+1} for {url}", tag="TEST")
        
        # Verify all pages are loaded correctly
        for i, (page, url) in enumerate(pages):
            title = await page.title()
            logger.info(f"Page {i+1} title: {title}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.success("test_multiple_pages completed successfully", tag="TEST")
        return True
    except Exception as e:
        logger.error(f"test_multiple_pages failed: {str(e)}", tag="TEST")
        return False

async def test_session_management():
    """Test session management in BrowserManager."""
    logger.info("Starting test_session_management", tag="TEST")
    
    try:
        # Create browser manager
        manager = BrowserManager(logger=logger)
        
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully", tag="TEST")
        
        # Create a session
        session_id = "test_session_1"
        crawler_config = CrawlerRunConfig(url="https://example.com", session_id=session_id)
        page1, context1 = await manager.get_page(crawler_config)
        await page1.goto("https://example.com")
        logger.info(f"Created session with ID: {session_id}", tag="TEST")
        
        # Get the same session again
        page2, context2 = await manager.get_page(crawler_config)
        
        # Verify it's the same page/context
        is_same_page = page1 == page2
        is_same_context = context1 == context2
        logger.info(f"Same page: {is_same_page}, Same context: {is_same_context}", tag="TEST")
        
        # Kill the session
        await manager.kill_session(session_id)
        logger.info(f"Killed session with ID: {session_id}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.success("test_session_management completed successfully", tag="TEST")
        return True
    except Exception as e:
        logger.error(f"test_session_management failed: {str(e)}", tag="TEST")
        return False

async def run_tests():
    """Run all tests sequentially."""
    results = []
    
    results.append(await test_basic_browser_manager())
    results.append(await test_custom_browser_config())
    results.append(await test_multiple_pages())
    results.append(await test_session_management())
    
    # Print summary
    total = len(results)
    passed = sum(results)
    logger.info(f"Tests complete: {passed}/{total} passed", tag="SUMMARY")
    
    if passed == total:
        logger.success("All tests passed!", tag="SUMMARY")
    else:
        logger.error(f"{total - passed} tests failed", tag="SUMMARY")

if __name__ == "__main__":
    asyncio.run(run_tests())
