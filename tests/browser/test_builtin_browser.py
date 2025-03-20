"""
Test script for browser_profiler and builtin browser functionality.

This script tests:
1. Creating a builtin browser
2. Getting browser information
3. Killing the browser
4. Restarting the browser
5. Testing crawling with different browser modes
6. Testing edge cases
"""

import asyncio
import os
import sys
import time
from colorama import Fore, init

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai.browser_profiler import BrowserProfiler
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger

# Initialize colorama for cross-platform colored terminal output
init()

# Define colors for pretty output
SUCCESS = Fore.GREEN
WARNING = Fore.YELLOW
ERROR = Fore.RED
INFO = Fore.CYAN
RESET = Fore.RESET

# Create logger
logger = AsyncLogger(verbose=True)

async def test_browser_profiler():
    """Test the BrowserProfiler class functionality"""
    print(f"\n{INFO}========== Testing BrowserProfiler =========={RESET}")
    
    # Initialize browser profiler
    profiler = BrowserProfiler(logger=logger)
    
    # Step 1: Check if builtin browser exists and kill it if it does
    print(f"\n{INFO}1. Checking if builtin browser exists{RESET}")
    browser_info = profiler.get_builtin_browser_info()
    if browser_info:
        print(f"{SUCCESS}Builtin browser found: {browser_info['cdp_url']}{RESET}")
        # Kill it to start with a clean state
        print(f"{INFO}Killing existing browser...{RESET}")
        await profiler.kill_builtin_browser()
        browser_info = profiler.get_builtin_browser_info()
        if not browser_info:
            print(f"{SUCCESS}Browser successfully killed{RESET}")
        else:
            print(f"{ERROR}Failed to kill browser{RESET}")
    else:
        print(f"{WARNING}No builtin browser found{RESET}")
    
    # Step 2: Launch a new builtin browser
    print(f"\n{INFO}2. Launching new builtin browser{RESET}")
    cdp_url = await profiler.launch_builtin_browser(headless=True)
    if cdp_url:
        print(f"{SUCCESS}Builtin browser launched at: {cdp_url}{RESET}")
    else:
        print(f"{ERROR}Failed to launch builtin browser{RESET}")
        return
    
    # Step 3: Get and display browser information
    print(f"\n{INFO}3. Getting browser information{RESET}")
    browser_info = profiler.get_builtin_browser_info()
    if browser_info:
        print(f"{SUCCESS}Browser info retrieved:{RESET}")
        for key, value in browser_info.items():
            if key != 'config':  # Skip the verbose config section
                print(f"  {key}: {value}")
    else:
        print(f"{ERROR}Failed to get browser information{RESET}")
    
    # Step 4: Get browser status
    print(f"\n{INFO}4. Getting browser status{RESET}")
    status = await profiler.get_builtin_browser_status()
    print(f"Running: {status['running']}")
    print(f"CDP URL: {status['cdp_url']}")
    
    # Pause to let the browser run for a moment
    print(f"\n{INFO}Waiting for 2 seconds...{RESET}")
    await asyncio.sleep(2)
    
    return cdp_url  # Return the CDP URL for the crawling tests

async def test_crawling_with_builtin_browser(cdp_url):
    """Test crawling with the builtin browser"""
    print(f"\n{INFO}========== Testing Crawling with Builtin Browser =========={RESET}")
    
    # Step 1: Create a crawler with 'builtin' browser mode
    print(f"\n{INFO}1. Creating crawler with 'builtin' browser mode{RESET}")
    browser_config = BrowserConfig(
        browser_mode="builtin",
        headless=True
    )
    crawler = AsyncWebCrawler(config=browser_config)
    
    # Step 2: Test crawling without explicitly starting (should auto-start)
    print(f"\n{INFO}2. Testing auto-start with arun{RESET}")
    try:
        result = await crawler.arun("https://crawl4ai.com")
        print(f"{SUCCESS}Auto-start crawling successful!{RESET}")
        print(f"  Got {len(result.markdown.raw_markdown)} chars of markdown content")
    except Exception as e:
        print(f"{ERROR}Auto-start crawling failed: {str(e)}{RESET}")
    
    # Close the crawler
    await crawler.close()
    
    # Step 3: Test with explicit start
    print(f"\n{INFO}3. Testing with explicit start{RESET}")
    crawler = AsyncWebCrawler(config=browser_config)
    try:
        await crawler.start()
        print(f"{SUCCESS}Explicit start successful!{RESET}")
        result = await crawler.arun("https://example.com")
        print(f"  Got {len(result.markdown.raw_markdown)} chars of markdown content")
        # Try second time, no start needed
        print(f"{INFO}Testing second arun call without start{RESET}")
        result = await crawler.arun("https://example.com")
        print(f"  Got {len(result.markdown.raw_markdown)} chars of markdown content")
    except Exception as e:
        print(f"{ERROR}Explicit start crawling failed: {str(e)}{RESET}")
    
    # Close the crawler
    await crawler.close()
    
    # Step 4: Test with context manager
    print(f"\n{INFO}4. Testing with context manager{RESET}")
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun("https://httpbin.org/html")
            print(f"{SUCCESS}Context manager crawling successful!{RESET}")
            print(f"  Got {len(result.markdown.raw_markdown)} chars of markdown content")
    except Exception as e:
        print(f"{ERROR}Context manager crawling failed: {str(e)}{RESET}")
    
    return True

async def test_crawling_without_builtin_browser():
    """Test crawling after killing the builtin browser"""
    print(f"\n{INFO}========== Testing Crawling Without Builtin Browser =========={RESET}")
    
    # Step 1: Kill the builtin browser
    print(f"\n{INFO}1. Killing the builtin browser{RESET}")
    profiler = BrowserProfiler(logger=logger)
    await profiler.kill_builtin_browser()
    
    # Step 2: Create a crawler with 'builtin' mode (should fall back to dedicated)
    print(f"\n{INFO}2. Creating crawler with 'builtin' mode (should fall back){RESET}")
    browser_config = BrowserConfig(
        browser_mode="builtin",
        headless=True
    )
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun("https://httpbin.org/get")
            print(f"{SUCCESS}Fallback to dedicated browser successful!{RESET}")
            print(f"  Got {len(result.markdown.raw_markdown)} chars of markdown content")
    except Exception as e:
        print(f"{ERROR}Fallback crawler failed: {str(e)}{RESET}")
    
    # Step 3: Test with direct CDP URL
    print(f"\n{INFO}3. Testing with direct CDP URL connection{RESET}")
    
    # Launch a standalone browser to get a CDP URL
    print(f"{INFO}Launching standalone browser...{RESET}")
    cdp_url = await profiler.launch_standalone_browser(headless=True)
    if not cdp_url:
        print(f"{ERROR}Failed to launch standalone browser{RESET}")
        return
    
    print(f"{SUCCESS}Got CDP URL: {cdp_url}{RESET}")
    
    # Create a crawler with the CDP URL
    browser_config = BrowserConfig(
        browser_mode="dedicated",
        cdp_url=cdp_url,
        use_managed_browser=True,
        headless=True
    )
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun("https://httpbin.org/ip")
            print(f"{SUCCESS}Direct CDP URL crawling successful!{RESET}")
            print(f"  Got {len(result.markdown.raw_markdown)} chars of markdown content")
    except Exception as e:
        print(f"{ERROR}Direct CDP URL crawling failed: {str(e)}{RESET}")
    
    return True

async def test_edge_cases():
    """Test edge cases like multiple starts, killing browser during crawl, etc."""
    print(f"\n{INFO}========== Testing Edge Cases =========={RESET}")
    
    # Step 1: Launch the builtin browser if it doesn't exist
    print(f"\n{INFO}1. Ensuring builtin browser exists{RESET}")
    profiler = BrowserProfiler(logger=logger)
    browser_info = profiler.get_builtin_browser_info()
    if not browser_info:
        cdp_url = await profiler.launch_builtin_browser(headless=True)
        if cdp_url:
            print(f"{SUCCESS}Builtin browser launched at: {cdp_url}{RESET}")
        else:
            print(f"{ERROR}Failed to launch builtin browser{RESET}")
            return
    else:
        print(f"{SUCCESS}Using existing builtin browser: {browser_info['cdp_url']}{RESET}")
    
    # Step 2: Test multiple starts with the same crawler
    print(f"\n{INFO}2. Testing multiple starts with the same crawler{RESET}")
    browser_config = BrowserConfig(browser_mode="builtin", headless=True)
    crawler = AsyncWebCrawler(config=browser_config)
    
    await crawler.start()
    print(f"{SUCCESS}First start successful!{RESET}")
    
    try:
        await crawler.start()
        print(f"{SUCCESS}Second start didn't cause errors!{RESET}")
    except Exception as e:
        print(f"{ERROR}Second start failed: {str(e)}{RESET}")
    
    # Run a crawl to verify functionality
    try:
        result = await crawler.arun("https://httpbin.org/user-agent")
        print(f"{SUCCESS}Crawling after multiple starts successful!{RESET}")
        print(f"  Got {len(result.markdown.raw_markdown)} chars of markdown content")
    except Exception as e:
        print(f"{ERROR}Crawling after multiple starts failed: {str(e)}{RESET}")
    
    await crawler.close()
    
    # Step 3: Test killing browser while crawler is active
    print(f"\n{INFO}3. Testing killing browser while crawler is active{RESET}")
    
    # Create and start a crawler
    browser_config = BrowserConfig(browser_mode="builtin", headless=True)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    
    # Kill the browser
    print(f"{INFO}Killing the browser...{RESET}")
    await profiler.kill_builtin_browser()
    
    # Try to crawl (should fail)
    try:
        result = await crawler.arun("https://httpbin.org/get")
        print(f"{WARNING}Crawling succeeded despite killed browser!{RESET}")
    except Exception as e:
        print(f"{SUCCESS}Crawling failed as expected: {str(e)}{RESET}")
    
    await crawler.close()
    
    return True

async def main():
    """Run all tests"""
    try:
        print(f"{INFO}Starting browser_profiler and builtin browser tests{RESET}")
        
        # Run browser profiler tests
        cdp_url = await test_browser_profiler()
        
        # Run crawling tests with builtin browser
        if cdp_url:
            await test_crawling_with_builtin_browser(cdp_url)
        
        # Run tests without builtin browser
        # await test_crawling_without_builtin_browser()
        
        # Run edge case tests
        # await test_edge_cases()
        
        print(f"\n{SUCCESS}All tests completed!{RESET}")
        
    except Exception as e:
        print(f"\n{ERROR}Test failed with error: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up: kill any remaining builtin browser
        print(f"\n{INFO}Cleaning up: killing any remaining builtin browser{RESET}")
        profiler = BrowserProfiler(logger=logger)
        await profiler.kill_builtin_browser()
        print(f"{SUCCESS}Test cleanup complete{RESET}")

if __name__ == "__main__":
    asyncio.run(main())