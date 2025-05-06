"""Test examples for CDPBrowserStrategy.

These examples demonstrate the functionality of CDPBrowserStrategy
and serve as functional tests.
"""

import asyncio
import os
import sys

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai.browser import BrowserManager
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger

# Create a logger for clear terminal output
logger = AsyncLogger(verbose=True, log_file=None)

async def test_cdp_launch_connect():
    """Test launching a browser and connecting via CDP."""
    logger.info("Testing launch and connect via CDP", tag="TEST")
    
    browser_config = BrowserConfig(
        use_managed_browser=True,
        browser_mode="cdp",
        headless=True
    )
    
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        await manager.start()
        logger.info("Browser launched and connected via CDP", tag="TEST")
        
        # Test with multiple pages
        pages = []
        for i in range(3):
            crawler_config = CrawlerRunConfig()
            page, context = await manager.get_page(crawler_config)
            await page.goto(f"https://example.com?test={i}")
            pages.append(page)
            logger.info(f"Created page {i+1}", tag="TEST")
        
        # Verify all pages are working
        for i, page in enumerate(pages):
            title = await page.title()
            logger.info(f"Page {i+1} title: {title}", tag="TEST")
        
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await manager.close()
        except:
            pass
        return False

async def test_cdp_with_user_data_dir():
    """Test CDP browser with a user data directory."""
    logger.info("Testing CDP browser with user data directory", tag="TEST")
    
    # Create a temporary user data directory
    import tempfile
    user_data_dir = tempfile.mkdtemp(prefix="crawl4ai-test-")
    logger.info(f"Created temporary user data directory: {user_data_dir}", tag="TEST")
    
    browser_config = BrowserConfig(
        headless=True,
        browser_mode="cdp",
        user_data_dir=user_data_dir
    )
    
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        await manager.start()
        logger.info("Browser launched with user data directory", tag="TEST")
        
        # Navigate to a page and store some data
        crawler_config = CrawlerRunConfig()
        page, context = await manager.get_page(crawler_config)
        
        # Set a cookie
        await context.add_cookies([{
            "name": "test_cookie",
            "value": "test_value",
            "url": "https://example.com"
        }])
        
        # Visit the site
        await page.goto("https://example.com")
        
        # Verify cookie was set
        cookies = await context.cookies(["https://example.com"])
        has_test_cookie = any(cookie["name"] == "test_cookie" for cookie in cookies)
        logger.info(f"Cookie set successfully: {has_test_cookie}", tag="TEST")
        
        # Close the browser
        await manager.close()
        logger.info("First browser session closed", tag="TEST")
        
        # Start a new browser with the same user data directory
        logger.info("Starting second browser session with same user data directory", tag="TEST")
        manager2 = BrowserManager(browser_config=browser_config, logger=logger)
        await manager2.start()
        
        # Get a new page and check if the cookie persists
        page2, context2 = await manager2.get_page(crawler_config)
        await page2.goto("https://example.com")
        
        # Verify cookie persisted
        cookies2 = await context2.cookies(["https://example.com"])
        has_test_cookie2 = any(cookie["name"] == "test_cookie" for cookie in cookies2)
        logger.info(f"Cookie persisted across sessions: {has_test_cookie2}", tag="TEST")
        
        # Clean up
        await manager2.close()
        
        # Remove temporary directory
        import shutil
        shutil.rmtree(user_data_dir, ignore_errors=True)
        logger.info(f"Removed temporary user data directory", tag="TEST")
        
        return has_test_cookie and has_test_cookie2
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await manager.close()
        except:
            pass
            
        # Clean up temporary directory
        try:
            import shutil
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except:
            pass
            
        return False

async def test_cdp_session_management():
    """Test session management with CDP browser."""
    logger.info("Testing session management with CDP browser", tag="TEST")
    
    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True
    )
    
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        await manager.start()
        logger.info("Browser launched successfully", tag="TEST")
        
        # Create two sessions
        session1_id = "test_session_1"
        session2_id = "test_session_2"
        
        # Set up first session
        crawler_config1 = CrawlerRunConfig(session_id=session1_id)
        page1, context1 = await manager.get_page(crawler_config1)
        await page1.goto("https://example.com")
        await page1.evaluate("localStorage.setItem('session1_data', 'test_value')")
        logger.info(f"Set up session 1 with ID: {session1_id}", tag="TEST")
        
        # Set up second session
        crawler_config2 = CrawlerRunConfig(session_id=session2_id)
        page2, context2 = await manager.get_page(crawler_config2)
        await page2.goto("https://example.org")
        await page2.evaluate("localStorage.setItem('session2_data', 'test_value2')")
        logger.info(f"Set up session 2 with ID: {session2_id}", tag="TEST")
        
        # Get first session again
        page1_again, _ = await manager.get_page(crawler_config1)
        
        # Verify it's the same page and data persists
        is_same_page = page1 == page1_again
        data1 = await page1_again.evaluate("localStorage.getItem('session1_data')")
        logger.info(f"Session 1 reuse successful: {is_same_page}, data: {data1}", tag="TEST")
        
        # Kill first session
        await manager.kill_session(session1_id)
        logger.info(f"Killed session 1", tag="TEST")
        
        # Verify second session still works
        data2 = await page2.evaluate("localStorage.getItem('session2_data')")
        logger.info(f"Session 2 still functional after killing session 1, data: {data2}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")
        
        return is_same_page and data1 == "test_value" and data2 == "test_value2"
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await manager.close()
        except:
            pass
        return False

async def run_tests():
    """Run all tests sequentially."""
    results = []
    
    # results.append(await test_cdp_launch_connect())
    results.append(await test_cdp_with_user_data_dir())
    results.append(await test_cdp_session_management())
    
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
