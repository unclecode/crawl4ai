"""Test examples for PlaywrightBrowserStrategy.

These examples demonstrate the functionality of PlaywrightBrowserStrategy
and serve as functional tests.
"""

import asyncio
import os
import re
import sys

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai.browser import BrowserManager
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger

# Create a logger for clear terminal output
logger = AsyncLogger(verbose=True, log_file=None)



async def test_start_close():
    # Create browser config for standard Playwright
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800
    )
    
    # Create browser manager with the config
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        for _ in range(4):
            # Start the browser
            await manager.start()
            logger.info("Browser started successfully", tag="TEST")

            # Get a page
            page, context = await manager.get_page(CrawlerRunConfig())
            logger.info("Got page successfully", tag="TEST")
            
            # Navigate to a website
            await page.goto("https://example.com")
            logger.info("Navigated to example.com", tag="TEST")
            
            # Get page title
            title = await page.title()
            logger.info(f"Page title: {title}", tag="TEST")
            
            # Clean up
            await manager.close()
            logger.info("Browser closed successfully", tag="TEST")
   
            await asyncio.sleep(1)  # Wait for a moment before restarting

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            await manager.close()
        except:
            pass
        return False
    return True

async def test_playwright_basic():
    """Test basic Playwright browser functionality."""
    logger.info("Testing standard Playwright browser", tag="TEST")
    
    # Create browser config for standard Playwright
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800
    )
    
    # Create browser manager with the config
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully", tag="TEST")
        
        # Create crawler config
        crawler_config = CrawlerRunConfig(url="https://example.com")
        
        # Get a page
        page, context = await manager.get_page(crawler_config)
        logger.info("Got page successfully", tag="TEST")
        
        # Navigate to a website
        await page.goto("https://example.com")
        logger.info("Navigated to example.com", tag="TEST")
        
        # Get page title
        title = await page.title()
        logger.info(f"Page title: {title}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            await manager.close()
        except:
            pass
        return False

async def test_playwright_text_mode():
    """Test Playwright browser in text-only mode."""
    logger.info("Testing Playwright text mode", tag="TEST")
    
    # Create browser config with text mode enabled
    browser_config = BrowserConfig(
        headless=True,
        text_mode=True  # Enable text-only mode
    )
    
    # Create browser manager with the config
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully in text mode", tag="TEST")
        
        # Get a page
        crawler_config = CrawlerRunConfig(url="https://example.com")
        page, context = await manager.get_page(crawler_config)
        
        # Navigate to a website
        await page.goto("https://example.com")
        logger.info("Navigated to example.com", tag="TEST")
        
        # Get page title
        title = await page.title()
        logger.info(f"Page title: {title}", tag="TEST")
        
        # Check if images are blocked in text mode
        # We'll check if any image requests were made
        has_images = False
        async with page.expect_request("**/*.{png,jpg,jpeg,gif,webp,svg}", timeout=1000) as request_info:
            try:
                # Try to load a page with images
                await page.goto("https://picsum.photos/", wait_until="domcontentloaded")
                request = await request_info.value
                has_images = True
            except:
                # Timeout without image requests means text mode is working
                has_images = False
        
        logger.info(f"Text mode image blocking working: {not has_images}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            await manager.close()
        except:
            pass
        return False

async def test_playwright_context_reuse():
    """Test context caching and reuse with identical configurations."""
    logger.info("Testing context reuse with identical configurations", tag="TEST")
    
    # Create browser config
    browser_config = BrowserConfig(headless=True)
    
    # Create browser manager
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        # Start the browser
        await manager.start()
        logger.info("Browser started successfully", tag="TEST")
        
        # Create identical crawler configs
        crawler_config1 = CrawlerRunConfig(
            css_selector="body",
        )
        
        crawler_config2 = CrawlerRunConfig(
            css_selector="body",
        )
        
        # Get pages with these configs
        page1, context1 = await manager.get_page(crawler_config1)
        page2, context2 = await manager.get_page(crawler_config2)
        
        # Check if contexts are reused
        is_same_context = context1 == context2
        logger.info(f"Contexts reused: {is_same_context}", tag="TEST")
        
        # Now try with a different config
        crawler_config3 = CrawlerRunConfig()
        
        page3, context3 = await manager.get_page(crawler_config3)
        
        # This should be a different context
        is_different_context = context1 != context3
        logger.info(f"Different contexts for different configs: {is_different_context}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")
        
        # Both tests should pass for success
        return is_same_context and is_different_context
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            await manager.close()
        except:
            pass
        return False

async def test_playwright_session_management():
    """Test session management with Playwright browser."""
    logger.info("Testing session management with Playwright browser", tag="TEST")
    
    browser_config = BrowserConfig(
        headless=True
    )
    
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        await manager.start()
        logger.info("Browser launched successfully", tag="TEST")
        
        # Create two sessions
        session1_id = "playwright_session_1"
        session2_id = "playwright_session_2"
        
        # Set up first session
        crawler_config1 = CrawlerRunConfig(session_id=session1_id, url="https://example.com")
        page1, context1 = await manager.get_page(crawler_config1)
        await page1.goto("https://example.com")
        await page1.evaluate("localStorage.setItem('playwright_session1_data', 'test_value1')")
        logger.info(f"Set up session 1 with ID: {session1_id}", tag="TEST")
        
        # Set up second session
        crawler_config2 = CrawlerRunConfig(session_id=session2_id, url="https://example.org")
        page2, context2 = await manager.get_page(crawler_config2)
        await page2.goto("https://example.org")
        await page2.evaluate("localStorage.setItem('playwright_session2_data', 'test_value2')")
        logger.info(f"Set up session 2 with ID: {session2_id}", tag="TEST")
        
        # Get first session again
        page1_again, context1_again = await manager.get_page(crawler_config1)
        
        # Verify it's the same page and data persists
        is_same_page = page1 == page1_again
        is_same_context = context1 == context1_again
        data1 = await page1_again.evaluate("localStorage.getItem('playwright_session1_data')")
        logger.info(f"Session 1 reuse successful: {is_same_page}, data: {data1}", tag="TEST")
        
        # Kill first session
        await manager.kill_session(session1_id)
        logger.info(f"Killed session 1", tag="TEST")
        
        # Verify second session still works
        data2 = await page2.evaluate("localStorage.getItem('playwright_session2_data')")
        logger.info(f"Session 2 still functional after killing session 1, data: {data2}", tag="TEST")
        
        # Clean up
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")
        
        return is_same_page and is_same_context and data1 == "test_value1" and data2 == "test_value2"
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
    
    # results.append(await test_start_close())
    # results.append(await test_playwright_basic())
    # results.append(await test_playwright_text_mode())
    # results.append(await test_playwright_context_reuse())
    results.append(await test_playwright_session_management())
    
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
