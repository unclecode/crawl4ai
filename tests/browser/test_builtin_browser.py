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
import sys
import time
import gc

from typing import Any, AsyncGenerator, List, Optional, Tuple
from pathlib import Path

import psutil
import pytest
import pytest_asyncio
from colorama import Fore, init
from playwright.async_api import Page

from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.browser import BrowserManager
from crawl4ai.browser.strategies import BuiltinBrowserStrategy

# Initialize colorama for cross-platform colored terminal output
init()

# Define colors for pretty output
SUCCESS = Fore.GREEN
WARNING = Fore.YELLOW
ERROR = Fore.RED
INFO = Fore.CYAN
RESET = Fore.RESET


class BrowsersManager:
    """Class to manage multiple browser instances for performance testing."""
    def __init__(self, num_browsers: int = 10, pages_per_browser: int = 10, base_port: int = 9222):
        self.num_browsers: int = num_browsers
        self.pages_per_browser: int = pages_per_browser
        self.base_port: int = base_port
        self.managers: List[BrowserManager] = []
        self.initial_memory: float = 0.0
        self.peak_memory: float = 0.0
        self.total_pages: int = num_browsers * pages_per_browser
        self.process: psutil.Process = psutil.Process()
        print(
            f"{INFO}Test configuration: {num_browsers} browsers × {pages_per_browser} pages = {self.total_pages} total crawls{RESET}"
        )

    async def run(self, tmp_path: Path):
        """Run the BrowsersManager to start multiple browser instances."""
        # Force garbage collection before starting
        gc.collect()

        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # in MB
        self.peak_memory = self.initial_memory

         # Create all managers but don't start them yet
        manager_configs = []
        for i in range(self.num_browsers):
            port = self.base_port + i
            browser_config = BrowserConfig(
                browser_mode="builtin",
                headless=True,
                debugging_port=port,
                user_data_dir=str(tmp_path / f"browser_profile_{i}"),
            )
            manager = BrowserManager(browser_config=browser_config)
            assert isinstance(manager._strategy, BuiltinBrowserStrategy), f"Wrong strategy type {manager._strategy.__class__.__name__}"
            manager._strategy.shutting_down = True
            manager_configs.append((manager, i, port))

        # Define async function to start a single manager
        async def start_manager(manager: BrowserManager, index: int, port: int) -> Optional[BrowserManager]:
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

        # Filter out None values (failed starts) and add to managers list
        self.managers = [m for m in await asyncio.gather(*start_tasks) if m is not None]

        if len(self.managers) < self.num_browsers:
            print(
                f"{WARNING}Only {len(self.managers)} out of {self.num_browsers} browser managers started successfully{RESET}"
            )

    async def close(self):
        """Close all browser instances managed by this manager."""
        for manager in self.managers:
            try:
                await manager.close()
            except Exception:
                pass

    def check_memory(self) -> float:
        """Checks the current memory usage.

        Updates the peak memory usage if the current memory is higher.

        Returns:
            float: Current memory usage in MB.
        """
        gc.collect()
        current_memory: float = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = max(self.peak_memory, current_memory)
        return current_memory

@pytest_asyncio.fixture
async def browsers_manager(tmp_path: Path) -> AsyncGenerator[BrowsersManager, None]:
    manager: BrowsersManager = BrowsersManager()
    await manager.run(tmp_path)
    yield manager
    await manager.close()


@pytest_asyncio.fixture
async def manager() -> AsyncGenerator[BrowserManager, None]:
    browser_config: BrowserConfig = BrowserConfig(browser_mode="builtin", headless=True, verbose=True)
    manager: BrowserManager = BrowserManager(browser_config=browser_config)
    await manager.start()
    yield manager
    await manager.close()

@pytest.mark.asyncio
async def test_builtin_browser_creation(manager: BrowserManager):
    """Test creating a builtin browser using the BrowserManager with BuiltinBrowserStrategy"""
    # Check if we have a BuiltinBrowserStrategy
    assert isinstance(manager._strategy, BuiltinBrowserStrategy), f"Wrong strategy type {manager._strategy.__class__.__name__}"

    # Check we can get browser info from the strategy
    strategy: BuiltinBrowserStrategy = manager._strategy
    browser_info = strategy.get_browser_info()
    assert browser_info, "Failed to get browser info"

@pytest.mark.asyncio
async def test_page_operations(manager: BrowserManager):
    """Test page operations with the builtin browser"""

    # Step 1: Get a single page
    crawler_config = CrawlerRunConfig()
    page, context = await manager.get_page(crawler_config)

    # Navigate to a test URL
    await page.goto("https://example.com")
    title = await page.title()

    # Close the page
    await page.close()

    # Step 2: Get multiple pages

    # Request 3 pages
    crawler_config = CrawlerRunConfig()
    pages = await manager.get_pages(crawler_config, count=3)

    # Test each page
    for i, (page, context) in enumerate(pages):
        response = await page.goto(f"https://example.com?test={i}")
        assert response, f"Failed to load page {i + 1}"
        title: str = await page.title()
        assert title == "Example Domain", f"Expected title 'Example Domain', got '{title}'"
        await page.close()

@pytest.mark.asyncio
async def test_browser_status_management(manager: BrowserManager):
    """Test browser status and management operations"""
    assert isinstance(manager._strategy, BuiltinBrowserStrategy), f"Wrong strategy type {manager._strategy.__class__.__name__}"
    status = await manager._strategy.get_builtin_browser_status()

    # Step 2: Test killing the browser
    result = await manager._strategy.kill_builtin_browser()
    assert result, "Failed to kill the browser"

    # Step 3: Check status after kill
    status = await manager._strategy.get_builtin_browser_status()
    assert status, "Failed to get browser status after kill"
    assert not status["running"], "Browser is still running after kill"

    # Step 4: Launch a new browser
    cdp_url = await manager._strategy.launch_builtin_browser(
        browser_type="chromium", headless=True
    )
    assert cdp_url, "Failed to launch a new browser"

@pytest.mark.asyncio
async def test_multiple_managers():
    """Test creating multiple BrowserManagers that use the same builtin browser"""

    # Step 1: Create first manager
    browser_config1: BrowserConfig = BrowserConfig(browser_mode="builtin", headless=True)
    manager1: BrowserManager = BrowserManager(browser_config=browser_config1)

    # Step 2: Create second manager
    browser_config2: BrowserConfig = BrowserConfig(browser_mode="builtin", headless=True)
    manager2: BrowserManager = BrowserManager(browser_config=browser_config2)

    # Step 3: Start both managers (should connect to the same builtin browser)
    page1: Optional[Page] = None
    page2: Optional[Page] = None
    try:
        await manager1.start()
        await manager2.start()

        # Check if they got the same CDP URL
        cdp_url1 = manager1._strategy.config.cdp_url
        cdp_url2 = manager2._strategy.config.cdp_url

        assert cdp_url1 == cdp_url2, "CDP URLs do not match between managers"

        # Step 4: Test using both managers
        # First manager creates a page
        page1, ctx1 = await manager1.get_page(CrawlerRunConfig())
        await page1.goto("https://example.com")
        title1: str = await page1.title()
        assert title1 == "Example Domain", f"Expected title 'Example Domain', got '{title1}'"

        # Second manager creates a page
        page2, ctx2 = await manager2.get_page(CrawlerRunConfig())
        await page2.goto("https://example.org")
        title2: str = await page2.title()
        assert title2 == "Example Domain", f"Expected title 'Example Domain', got '{title2}'"
    finally:
        if page1:
            await page1.close()
        if page2:
            await page2.close()
        # Close both managers
        await manager1.close()
        await manager2.close()


@pytest.mark.asyncio
async def test_multiple_starts(manager: BrowserManager):
    """Test multiple starts with the same manager."""
    page: Optional[Page] = None
    try:
        # Try to start again
        await manager.start()

        # Test if it's still functional
        page, context = await manager.get_page(CrawlerRunConfig())
        assert page is not None, "Failed to create a page after multiple starts"
        await page.goto("https://example.com")
        title: str = await page.title()
        assert title == "Example Domain", f"Expected title 'Example Domain', got '{title}'"
    finally:
        if page:
            await page.close()
        await manager.close()

@pytest.mark.asyncio
async def test_kill_while_active(manager: BrowserManager):
    """Test killing the browser while manager is active."""
    assert isinstance(manager._strategy, BuiltinBrowserStrategy), f"Wrong strategy type {manager._strategy.__class__.__name__}"
    await manager._strategy.kill_builtin_browser()

    with pytest.raises(Exception):
        # Try to get a page should fail
        await manager.get_page(CrawlerRunConfig())

@pytest.mark.asyncio
@pytest.mark.timeout(80)
async def test_performance_scaling(browsers_manager: BrowsersManager):
    """Test performance with multiple browsers and pages.

    This test creates multiple browsers on different ports,
    spawns multiple pages per browser, and measures performance metrics.
    """
    assert browsers_manager.managers, "Failed to start any browser managers"

    # Create pages for each browser
    all_pages: List[Tuple[Page, Any]] = []
    for i, manager in enumerate(browsers_manager.managers):
        try:
            pages = await manager.get_pages(CrawlerRunConfig(), count=browsers_manager.pages_per_browser)
            all_pages.extend(pages)
        except Exception as e:
            print(f"{ERROR}Failed to create pages for browser {i + 1}: {str(e)}{RESET}")

    # Check memory after page creation
    browsers_manager.check_memory()

    # Ask for confirmation before loading
    confirmation = input(
        f"{WARNING}Do you want to proceed with loading pages? (y/n): {RESET}"
    ) if sys.stdin.isatty() else "y"

    assert confirmation.lower() == "y", "User aborted the test"

    # Step 1: Create and start multiple browser managers in parallel
    start_time = time.time()

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

    try:
        # Count successes and failures
        successes = sum(
            1 for r in load_results if isinstance(r, str) and not r.startswith("Error")
        )
        failures = len(load_results) - successes

        assert not failures, f"Failed to load {failures} pages"

        total_test_time = time.time() - start_time

        # Check memory after loading (peak memory)
        browsers_manager.check_memory()

        # Calculate key metrics
        memory_per_page = browsers_manager.peak_memory / successes if successes > 0 else 0
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
        table.add_row("Peak Memory Usage", f"{browsers_manager.peak_memory:.2f} MB")
        table.add_row("Memory Per Crawl", f"{memory_per_page:.2f} MB")

        # Display the table
        console.print(table)
    finally:
        # Close all pages
        for page, _ in all_pages:
            try:
                await page.close()
            except Exception:
                pass


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
