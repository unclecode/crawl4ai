"""
Test script for builtin browser functionality in the browser module.

This script tests:
1. Creating a builtin browser
2. Getting browser information
3. Killing the browser
4. Restarting the browser
5. Testing operations with different browser strategies
6. Testing edge cases
"""

import asyncio
import os
import sys
import time
from typing import List, Dict, Any
from colorama import Fore, Style, init

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import Box, SIMPLE

from crawl4ai.browser import BrowserManager
from crawl4ai.browser.strategies import BuiltinBrowserStrategy
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


async def test_builtin_browser_creation():
    """Test creating a builtin browser using the BrowserManager with BuiltinBrowserStrategy"""
    print(f"\n{INFO}========== Testing Builtin Browser Creation =========={RESET}")

    # Step 1: Create a BrowserManager with builtin mode
    print(f"\n{INFO}1. Creating BrowserManager with builtin mode{RESET}")
    browser_config = BrowserConfig(browser_mode="builtin", headless=True, verbose=True)
    manager = BrowserManager(browser_config=browser_config, logger=logger)

    # Step 2: Check if we have a BuiltinBrowserStrategy
    print(f"\n{INFO}2. Checking if we have a BuiltinBrowserStrategy{RESET}")
    if isinstance(manager.strategy, BuiltinBrowserStrategy):
        print(
            f"{SUCCESS}Correct strategy type: {manager.strategy.__class__.__name__}{RESET}"
        )
    else:
        print(
            f"{ERROR}Wrong strategy type: {manager.strategy.__class__.__name__}{RESET}"
        )
        return None

    # Step 3: Start the manager to launch or connect to builtin browser
    print(f"\n{INFO}3. Starting the browser manager{RESET}")
    try:
        await manager.start()
        print(f"{SUCCESS}Browser manager started successfully{RESET}")
    except Exception as e:
        print(f"{ERROR}Failed to start browser manager: {str(e)}{RESET}")
        return None

    # Step 4: Get browser info from the strategy
    print(f"\n{INFO}4. Getting browser information{RESET}")
    browser_info = manager.strategy.get_browser_info()
    if browser_info:
        print(f"{SUCCESS}Browser info retrieved:{RESET}")
        for key, value in browser_info.items():
            if key != "config":  # Skip the verbose config section
                print(f"  {key}: {value}")

        cdp_url = browser_info.get("cdp_url")
        print(f"{SUCCESS}CDP URL: {cdp_url}{RESET}")
    else:
        print(f"{ERROR}Failed to get browser information{RESET}")
        cdp_url = None

    # Save manager for later tests
    return manager, cdp_url


async def test_page_operations(manager: BrowserManager):
    """Test page operations with the builtin browser"""
    print(
        f"\n{INFO}========== Testing Page Operations with Builtin Browser =========={RESET}"
    )

    # Step 1: Get a single page
    print(f"\n{INFO}1. Getting a single page{RESET}")
    try:
        crawler_config = CrawlerRunConfig()
        page, context = await manager.get_page(crawler_config)
        print(f"{SUCCESS}Got page successfully{RESET}")

        # Navigate to a test URL
        await page.goto("https://example.com")
        title = await page.title()
        print(f"{SUCCESS}Page title: {title}{RESET}")

        # Close the page
        await page.close()
        print(f"{SUCCESS}Page closed successfully{RESET}")
    except Exception as e:
        print(f"{ERROR}Page operation failed: {str(e)}{RESET}")
        return False

    # Step 2: Get multiple pages
    print(f"\n{INFO}2. Getting multiple pages with get_pages(){RESET}")
    try:
        # Request 3 pages
        crawler_config = CrawlerRunConfig()
        pages = await manager.get_pages(crawler_config, count=3)
        print(f"{SUCCESS}Got {len(pages)} pages{RESET}")

        # Test each page
        for i, (page, context) in enumerate(pages):
            await page.goto(f"https://example.com?test={i}")
            title = await page.title()
            print(f"{SUCCESS}Page {i + 1} title: {title}{RESET}")
            await page.close()

        print(f"{SUCCESS}All pages tested and closed successfully{RESET}")
    except Exception as e:
        print(f"{ERROR}Multiple page operation failed: {str(e)}{RESET}")
        return False

    return True


async def test_browser_status_management(manager: BrowserManager):
    """Test browser status and management operations"""
    print(f"\n{INFO}========== Testing Browser Status and Management =========={RESET}")

    # Step 1: Get browser status
    print(f"\n{INFO}1. Getting browser status{RESET}")
    try:
        status = await manager.strategy.get_builtin_browser_status()
        print(f"{SUCCESS}Browser status:{RESET}")
        print(f"  Running: {status['running']}")
        print(f"  CDP URL: {status['cdp_url']}")
    except Exception as e:
        print(f"{ERROR}Failed to get browser status: {str(e)}{RESET}")
        return False

    # Step 2: Test killing the browser
    print(f"\n{INFO}2. Testing killing the browser{RESET}")
    try:
        result = await manager.strategy.kill_builtin_browser()
        if result:
            print(f"{SUCCESS}Browser killed successfully{RESET}")
        else:
            print(f"{ERROR}Failed to kill browser{RESET}")
    except Exception as e:
        print(f"{ERROR}Browser kill operation failed: {str(e)}{RESET}")
        return False

    # Step 3: Check status after kill
    print(f"\n{INFO}3. Checking status after kill{RESET}")
    try:
        status = await manager.strategy.get_builtin_browser_status()
        if not status["running"]:
            print(f"{SUCCESS}Browser is correctly reported as not running{RESET}")
        else:
            print(f"{ERROR}Browser is incorrectly reported as still running{RESET}")
    except Exception as e:
        print(f"{ERROR}Failed to get browser status: {str(e)}{RESET}")
        return False

    # Step 4: Launch a new browser
    print(f"\n{INFO}4. Launching a new browser{RESET}")
    try:
        cdp_url = await manager.strategy.launch_builtin_browser(
            browser_type="chromium", headless=True
        )
        if cdp_url:
            print(f"{SUCCESS}New browser launched at: {cdp_url}{RESET}")
        else:
            print(f"{ERROR}Failed to launch new browser{RESET}")
            return False
    except Exception as e:
        print(f"{ERROR}Browser launch failed: {str(e)}{RESET}")
        return False

    return True


async def test_multiple_managers():
    """Test creating multiple BrowserManagers that use the same builtin browser"""
    print(f"\n{INFO}========== Testing Multiple Browser Managers =========={RESET}")

    # Step 1: Create first manager
    print(f"\n{INFO}1. Creating first browser manager{RESET}")
    browser_config1 = BrowserConfig(browser_mode="builtin", headless=True)
    manager1 = BrowserManager(browser_config=browser_config1, logger=logger)

    # Step 2: Create second manager
    print(f"\n{INFO}2. Creating second browser manager{RESET}")
    browser_config2 = BrowserConfig(browser_mode="builtin", headless=True)
    manager2 = BrowserManager(browser_config=browser_config2, logger=logger)

    # Step 3: Start both managers (should connect to the same builtin browser)
    print(f"\n{INFO}3. Starting both managers{RESET}")
    try:
        await manager1.start()
        print(f"{SUCCESS}First manager started{RESET}")

        await manager2.start()
        print(f"{SUCCESS}Second manager started{RESET}")

        # Check if they got the same CDP URL
        cdp_url1 = manager1.strategy.config.cdp_url
        cdp_url2 = manager2.strategy.config.cdp_url

        if cdp_url1 == cdp_url2:
            print(
                f"{SUCCESS}Both managers connected to the same browser: {cdp_url1}{RESET}"
            )
        else:
            print(
                f"{WARNING}Managers connected to different browsers: {cdp_url1} and {cdp_url2}{RESET}"
            )
    except Exception as e:
        print(f"{ERROR}Failed to start managers: {str(e)}{RESET}")
        return False

    # Step 4: Test using both managers
    print(f"\n{INFO}4. Testing operations with both managers{RESET}")
    try:
        # First manager creates a page
        page1, ctx1 = await manager1.get_page(CrawlerRunConfig())
        await page1.goto("https://example.com")
        title1 = await page1.title()
        print(f"{SUCCESS}Manager 1 page title: {title1}{RESET}")

        # Second manager creates a page
        page2, ctx2 = await manager2.get_page(CrawlerRunConfig())
        await page2.goto("https://example.org")
        title2 = await page2.title()
        print(f"{SUCCESS}Manager 2 page title: {title2}{RESET}")

        # Clean up
        await page1.close()
        await page2.close()
    except Exception as e:
        print(f"{ERROR}Failed to use both managers: {str(e)}{RESET}")
        return False

    # Step 5: Close both managers
    print(f"\n{INFO}5. Closing both managers{RESET}")
    try:
        await manager1.close()
        print(f"{SUCCESS}First manager closed{RESET}")

        await manager2.close()
        print(f"{SUCCESS}Second manager closed{RESET}")
    except Exception as e:
        print(f"{ERROR}Failed to close managers: {str(e)}{RESET}")
        return False

    return True


async def test_edge_cases():
    """Test edge cases like multiple starts, killing browser during operations, etc."""
    print(f"\n{INFO}========== Testing Edge Cases =========={RESET}")

    # Step 1: Test multiple starts with the same manager
    print(f"\n{INFO}1. Testing multiple starts with the same manager{RESET}")
    browser_config = BrowserConfig(browser_mode="builtin", headless=True)
    manager = BrowserManager(browser_config=browser_config, logger=logger)

    try:
        await manager.start()
        print(f"{SUCCESS}First start successful{RESET}")

        # Try to start again
        await manager.start()
        print(f"{SUCCESS}Second start completed without errors{RESET}")

        # Test if it's still functional
        page, context = await manager.get_page(CrawlerRunConfig())
        await page.goto("https://example.com")
        title = await page.title()
        print(
            f"{SUCCESS}Page operations work after multiple starts. Title: {title}{RESET}"
        )
        await page.close()
    except Exception as e:
        print(f"{ERROR}Multiple starts test failed: {str(e)}{RESET}")
        return False
    finally:
        await manager.close()

    # Step 2: Test killing the browser while manager is active
    print(f"\n{INFO}2. Testing killing the browser while manager is active{RESET}")
    manager = BrowserManager(browser_config=browser_config, logger=logger)

    try:
        await manager.start()
        print(f"{SUCCESS}Manager started{RESET}")

        # Kill the browser directly
        print(f"{INFO}Killing the browser...{RESET}")
        await manager.strategy.kill_builtin_browser()
        print(f"{SUCCESS}Browser killed{RESET}")

        # Try to get a page (should fail or launch a new browser)
        try:
            page, context = await manager.get_page(CrawlerRunConfig())
            print(
                f"{WARNING}Page request succeeded despite killed browser (might have auto-restarted){RESET}"
            )
            title = await page.title()
            print(f"{SUCCESS}Got page title: {title}{RESET}")
            await page.close()
        except Exception as e:
            print(
                f"{SUCCESS}Page request failed as expected after browser was killed: {str(e)}{RESET}"
            )
    except Exception as e:
        print(f"{ERROR}Kill during operation test failed: {str(e)}{RESET}")
        return False
    finally:
        await manager.close()

    return True


async def cleanup_browsers():
    """Clean up any remaining builtin browsers"""
    print(f"\n{INFO}========== Cleaning Up Builtin Browsers =========={RESET}")

    browser_config = BrowserConfig(browser_mode="builtin", headless=True)
    manager = BrowserManager(browser_config=browser_config, logger=logger)

    try:
        # No need to start, just access the strategy directly
        strategy = manager.strategy
        if isinstance(strategy, BuiltinBrowserStrategy):
            result = await strategy.kill_builtin_browser()
            if result:
                print(f"{SUCCESS}Successfully killed all builtin browsers{RESET}")
            else:
                print(f"{WARNING}No builtin browsers found to kill{RESET}")
        else:
            print(f"{ERROR}Wrong strategy type: {strategy.__class__.__name__}{RESET}")
    except Exception as e:
        print(f"{ERROR}Cleanup failed: {str(e)}{RESET}")
    finally:
        # Just to be safe
        try:
            await manager.close()
        except:
            pass


async def test_performance_scaling():
    """Test performance with multiple browsers and pages.

    This test creates multiple browsers on different ports,
    spawns multiple pages per browser, and measures performance metrics.
    """
    print(f"\n{INFO}========== Testing Performance Scaling =========={RESET}")

    # Configuration parameters
    num_browsers = 10
    pages_per_browser = 10
    total_pages = num_browsers * pages_per_browser
    base_port = 9222

    # Set up a measuring mechanism for memory
    import psutil
    import gc

    # Force garbage collection before starting
    gc.collect()
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # in MB
    peak_memory = initial_memory

    # Report initial configuration
    print(
        f"{INFO}Test configuration: {num_browsers} browsers × {pages_per_browser} pages = {total_pages} total crawls{RESET}"
    )

    # List to track managers
    managers: List[BrowserManager] = []
    all_pages = []



    # Get crawl4ai home directory
    crawl4ai_home = os.path.expanduser("~/.crawl4ai")
    temp_dir = os.path.join(crawl4ai_home, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Create all managers but don't start them yet
    manager_configs = []
    for i in range(num_browsers):
        port = base_port + i
        browser_config = BrowserConfig(
            browser_mode="builtin",
            headless=True,
            debugging_port=port,
            user_data_dir=os.path.join(temp_dir, f"browser_profile_{i}"),
        )
        manager = BrowserManager(browser_config=browser_config, logger=logger)
        manager.strategy.shutting_down = True
        manager_configs.append((manager, i, port))

    # Define async function to start a single manager
    async def start_manager(manager, index, port):
        try:
            await manager.start()
            return manager
        except Exception as e:
            print(
                f"{ERROR}Failed to start browser {index + 1} on port {port}: {str(e)}{RESET}"
            )
            return None

    # Start all managers in parallel
    start_tasks = [
        start_manager(manager, i, port) for manager, i, port in manager_configs
    ]
    started_managers = await asyncio.gather(*start_tasks)

    # Filter out None values (failed starts) and add to managers list
    managers = [m for m in started_managers if m is not None]

    if len(managers) == 0:
        print(f"{ERROR}All browser managers failed to start. Aborting test.{RESET}")
        return False

    if len(managers) < num_browsers:
        print(
            f"{WARNING}Only {len(managers)} out of {num_browsers} browser managers started successfully{RESET}"
        )

    # Create pages for each browser
    for i, manager in enumerate(managers):
        try:
            pages = await manager.get_pages(CrawlerRunConfig(), count=pages_per_browser)
            all_pages.extend(pages)
        except Exception as e:
            print(f"{ERROR}Failed to create pages for browser {i + 1}: {str(e)}{RESET}")

    # Check memory after page creation
    gc.collect()
    current_memory = process.memory_info().rss / 1024 / 1024
    peak_memory = max(peak_memory, current_memory)

    # Ask for confirmation before loading
    confirmation = input(
        f"{WARNING}Do you want to proceed with loading pages? (y/n): {RESET}"
    )
    # Step 1: Create and start multiple browser managers in parallel
    start_time = time.time()
    
    if confirmation.lower() == "y":
        load_start_time = time.time()

        # Function to load a single page
        async def load_page(page_ctx, index):
            page, _ = page_ctx
            try:
                await page.goto(f"https://example.com/page{index}", timeout=30000)
                title = await page.title()
                return title
            except Exception as e:
                return f"Error: {str(e)}"

        # Load all pages concurrently
        load_tasks = [load_page(page_ctx, i) for i, page_ctx in enumerate(all_pages)]
        load_results = await asyncio.gather(*load_tasks, return_exceptions=True)

        # Count successes and failures
        successes = sum(
            1 for r in load_results if isinstance(r, str) and not r.startswith("Error")
        )
        failures = len(load_results) - successes

        load_time = time.time() - load_start_time
        total_test_time = time.time() - start_time

        # Check memory after loading (peak memory)
        gc.collect()
        current_memory = process.memory_info().rss / 1024 / 1024
        peak_memory = max(peak_memory, current_memory)

        # Calculate key metrics
        memory_per_page = peak_memory / successes if successes > 0 else 0
        time_per_crawl = total_test_time / successes if successes > 0 else 0
        crawls_per_second = successes / total_test_time if total_test_time > 0 else 0
        crawls_per_minute = crawls_per_second * 60
        crawls_per_hour = crawls_per_minute * 60

        # Print simplified performance summary
        from rich.console import Console
        from rich.table import Table

        console = Console()

        # Create a simple summary table
        table = Table(title="CRAWL4AI PERFORMANCE SUMMARY")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Crawls Completed", f"{successes}")
        table.add_row("Total Time", f"{total_test_time:.2f} seconds")
        table.add_row("Time Per Crawl", f"{time_per_crawl:.2f} seconds")
        table.add_row("Crawling Speed", f"{crawls_per_second:.2f} crawls/second")
        table.add_row("Projected Rate (1 minute)", f"{crawls_per_minute:.0f} crawls")
        table.add_row("Projected Rate (1 hour)", f"{crawls_per_hour:.0f} crawls")
        table.add_row("Peak Memory Usage", f"{peak_memory:.2f} MB")
        table.add_row("Memory Per Crawl", f"{memory_per_page:.2f} MB")

        # Display the table
        console.print(table)

    # Ask confirmation before cleanup
    confirmation = input(
        f"{WARNING}Do you want to proceed with cleanup? (y/n): {RESET}"
    )
    if confirmation.lower() != "y":
        print(f"{WARNING}Cleanup aborted by user{RESET}")
        return False

    # Close all pages
    for page, _ in all_pages:
        try:
            await page.close()
        except:
            pass

    # Close all managers
    for manager in managers:
        try:
            await manager.close()
        except:
            pass

    # Remove the temp directory
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    return True


async def test_performance_scaling_lab( num_browsers: int = 10, pages_per_browser: int = 10):
    """Test performance with multiple browsers and pages.

    This test creates multiple browsers on different ports,
    spawns multiple pages per browser, and measures performance metrics.
    """
    print(f"\n{INFO}========== Testing Performance Scaling =========={RESET}")

    # Configuration parameters
    num_browsers = num_browsers
    pages_per_browser = pages_per_browser
    total_pages = num_browsers * pages_per_browser
    base_port = 9222

    # Set up a measuring mechanism for memory
    import psutil
    import gc

    # Force garbage collection before starting
    gc.collect()
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # in MB
    peak_memory = initial_memory

    # Report initial configuration
    print(
        f"{INFO}Test configuration: {num_browsers} browsers × {pages_per_browser} pages = {total_pages} total crawls{RESET}"
    )

    # List to track managers
    managers: List[BrowserManager] = []
    all_pages = []

    # Get crawl4ai home directory
    crawl4ai_home = os.path.expanduser("~/.crawl4ai")
    temp_dir = os.path.join(crawl4ai_home, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Create all managers but don't start them yet
    manager_configs = []
    for i in range(num_browsers):
        port = base_port + i
        browser_config = BrowserConfig(
            browser_mode="builtin",
            headless=True,
            debugging_port=port,
            user_data_dir=os.path.join(temp_dir, f"browser_profile_{i}"),
        )
        manager = BrowserManager(browser_config=browser_config, logger=logger)
        manager.strategy.shutting_down = True
        manager_configs.append((manager, i, port))

    # Define async function to start a single manager
    async def start_manager(manager, index, port):
        try:
            await manager.start()
            return manager
        except Exception as e:
            print(
                f"{ERROR}Failed to start browser {index + 1} on port {port}: {str(e)}{RESET}"
            )
            return None

    # Start all managers in parallel
    start_tasks = [
        start_manager(manager, i, port) for manager, i, port in manager_configs
    ]
    started_managers = await asyncio.gather(*start_tasks)

    # Filter out None values (failed starts) and add to managers list
    managers = [m for m in started_managers if m is not None]

    if len(managers) == 0:
        print(f"{ERROR}All browser managers failed to start. Aborting test.{RESET}")
        return False

    if len(managers) < num_browsers:
        print(
            f"{WARNING}Only {len(managers)} out of {num_browsers} browser managers started successfully{RESET}"
        )

    # Create pages for each browser
    for i, manager in enumerate(managers):
        try:
            pages = await manager.get_pages(CrawlerRunConfig(), count=pages_per_browser)
            all_pages.extend(pages)
        except Exception as e:
            print(f"{ERROR}Failed to create pages for browser {i + 1}: {str(e)}{RESET}")

    # Check memory after page creation
    gc.collect()
    current_memory = process.memory_info().rss / 1024 / 1024
    peak_memory = max(peak_memory, current_memory)

    # Ask for confirmation before loading
    confirmation = input(
        f"{WARNING}Do you want to proceed with loading pages? (y/n): {RESET}"
    )
    # Step 1: Create and start multiple browser managers in parallel
    start_time = time.time()
    
    if confirmation.lower() == "y":
        load_start_time = time.time()

        # Function to load a single page
        async def load_page(page_ctx, index):
            page, _ = page_ctx
            try:
                await page.goto(f"https://example.com/page{index}", timeout=30000)
                title = await page.title()
                return title
            except Exception as e:
                return f"Error: {str(e)}"

        # Load all pages concurrently
        load_tasks = [load_page(page_ctx, i) for i, page_ctx in enumerate(all_pages)]
        load_results = await asyncio.gather(*load_tasks, return_exceptions=True)

        # Count successes and failures
        successes = sum(
            1 for r in load_results if isinstance(r, str) and not r.startswith("Error")
        )
        failures = len(load_results) - successes

        load_time = time.time() - load_start_time
        total_test_time = time.time() - start_time

        # Check memory after loading (peak memory)
        gc.collect()
        current_memory = process.memory_info().rss / 1024 / 1024
        peak_memory = max(peak_memory, current_memory)

        # Calculate key metrics
        memory_per_page = peak_memory / successes if successes > 0 else 0
        time_per_crawl = total_test_time / successes if successes > 0 else 0
        crawls_per_second = successes / total_test_time if total_test_time > 0 else 0
        crawls_per_minute = crawls_per_second * 60
        crawls_per_hour = crawls_per_minute * 60

        # Print simplified performance summary
        from rich.console import Console
        from rich.table import Table

        console = Console()

        # Create a simple summary table
        table = Table(title="CRAWL4AI PERFORMANCE SUMMARY")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Crawls Completed", f"{successes}")
        table.add_row("Total Time", f"{total_test_time:.2f} seconds")
        table.add_row("Time Per Crawl", f"{time_per_crawl:.2f} seconds")
        table.add_row("Crawling Speed", f"{crawls_per_second:.2f} crawls/second")
        table.add_row("Projected Rate (1 minute)", f"{crawls_per_minute:.0f} crawls")
        table.add_row("Projected Rate (1 hour)", f"{crawls_per_hour:.0f} crawls")
        table.add_row("Peak Memory Usage", f"{peak_memory:.2f} MB")
        table.add_row("Memory Per Crawl", f"{memory_per_page:.2f} MB")

        # Display the table
        console.print(table)

    # Ask confirmation before cleanup
    confirmation = input(
        f"{WARNING}Do you want to proceed with cleanup? (y/n): {RESET}"
    )
    if confirmation.lower() != "y":
        print(f"{WARNING}Cleanup aborted by user{RESET}")
        return False

    # Close all pages
    for page, _ in all_pages:
        try:
            await page.close()
        except:
            pass

    # Close all managers
    for manager in managers:
        try:
            await manager.close()
        except:
            pass

    # Remove the temp directory
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    return True



async def main():
    """Run all tests"""
    try:
        print(f"{INFO}Starting builtin browser tests with browser module{RESET}")

        # # Run browser creation test
        # manager, cdp_url = await test_builtin_browser_creation()
        # if not manager:
        #     print(f"{ERROR}Browser creation failed, cannot continue tests{RESET}")
        #     return

        # # Run page operations test
        # await test_page_operations(manager)

        # # Run browser status and management test
        # await test_browser_status_management(manager)

        # # Close manager before multiple manager test
        # await manager.close()

        # Run multiple managers test
        await test_multiple_managers()

        # Run performance scaling test
        await test_performance_scaling()

        # Run cleanup test
        await cleanup_browsers()

        # Run edge cases test
        await test_edge_cases()

        print(f"\n{SUCCESS}All tests completed!{RESET}")

    except Exception as e:
        print(f"\n{ERROR}Test failed with error: {str(e)}{RESET}")
        import traceback

        traceback.print_exc()
    finally:
        # Clean up: kill any remaining builtin browsers
        await cleanup_browsers()
        print(f"{SUCCESS}Test cleanup complete{RESET}")


if __name__ == "__main__":
    asyncio.run(main())
