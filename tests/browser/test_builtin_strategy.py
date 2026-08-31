"""Test examples for BuiltinBrowserStrategy.

These examples demonstrate the functionality of BuiltinBrowserStrategy
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

async def test_builtin_browser():
    """Test using a builtin browser that persists between sessions."""
    logger.info("Testing builtin browser", tag="TEST")
    
    browser_config = BrowserConfig(
        browser_mode="builtin",
        headless=True
    )
    
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        # Start should connect to existing builtin browser or create one
        await manager.start()
        logger.info("Connected to builtin browser", tag="TEST")
        
        # Test page creation
        crawler_config = CrawlerRunConfig()
        page, context = await manager.get_page(crawler_config)
        
        # Test navigation
        await page.goto("https://example.com")
        title = await page.title()
        logger.info(f"Page title: {title}", tag="TEST")
        
        # Close manager (should not close the builtin browser)
        await manager.close()
        logger.info("First session closed", tag="TEST")
        
        # Create a second manager to verify browser persistence
        logger.info("Creating second session to verify persistence", tag="TEST")
        manager2 = BrowserManager(browser_config=browser_config, logger=logger)
        
        await manager2.start()
        logger.info("Connected to existing builtin browser", tag="TEST")
        
        page2, context2 = await manager2.get_page(crawler_config)
        await page2.goto("https://example.org")
        title2 = await page2.title()
        logger.info(f"Second session page title: {title2}", tag="TEST")
        
        await manager2.close()
        logger.info("Second session closed successfully", tag="TEST")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await manager.close()
        except:
            pass
        return False

async def test_builtin_browser_status():
    """Test getting status of the builtin browser."""
    logger.info("Testing builtin browser status", tag="TEST")
    
    from crawl4ai.browser.strategies import BuiltinBrowserStrategy
    
    browser_config = BrowserConfig(
        browser_mode="builtin",
        headless=True
    )
    
    # Create strategy directly to access its status methods
    strategy = BuiltinBrowserStrategy(browser_config, logger)
    
    try:
        # Get status before starting (should be not running)
        status_before = await strategy.get_builtin_browser_status()
        logger.info(f"Initial status: {status_before}", tag="TEST")
        
        # Start the browser
        await strategy.start()
        logger.info("Browser started successfully", tag="TEST")
        
        # Get status after starting
        status_after = await strategy.get_builtin_browser_status()
        logger.info(f"Status after start: {status_after}", tag="TEST")
        
        # Create a page to verify functionality
        crawler_config = CrawlerRunConfig()
        page, context = await strategy.get_page(crawler_config)
        await page.goto("https://example.com")
        title = await page.title()
        logger.info(f"Page title: {title}", tag="TEST")
        
        # Close strategy (should not kill the builtin browser)
        await strategy.close()
        logger.info("Strategy closed successfully", tag="TEST")
        
        # Create a new strategy object
        strategy2 = BuiltinBrowserStrategy(browser_config, logger)
        
        # Get status again (should still be running)
        status_final = await strategy2.get_builtin_browser_status()
        logger.info(f"Final status: {status_final}", tag="TEST")
        
        # Verify that the status shows the browser is running
        is_running = status_final.get('running', False)
        logger.info(f"Builtin browser persistence confirmed: {is_running}", tag="TEST")
        
        # Kill the builtin browser to clean up
        logger.info("Killing builtin browser", tag="TEST")
        success = await strategy2.kill_builtin_browser()
        logger.info(f"Killed builtin browser successfully: {success}", tag="TEST")
        
        return is_running and success
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await strategy.close()
            
            # Try to kill the builtin browser to clean up
            strategy2 = BuiltinBrowserStrategy(browser_config, logger)
            await strategy2.kill_builtin_browser()
        except:
            pass
        return False

async def run_tests():
    """Run all tests sequentially."""
    results = []
    
    results.append(await test_builtin_browser())
    results.append(await test_builtin_browser_status())
    
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
