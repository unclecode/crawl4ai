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
from aiohttp import web
from httpx import codes
from pytest_aiohttp import AiohttpServer
from aiohttp.test_utils import TestServer

from typing import Any, AsyncGenerator, List, Optional, Tuple
from pathlib import Path

import psutil
import pytest
import pytest_asyncio
from colorama import Fore, init
from playwright.async_api import Page, Response

from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
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
    def __init__(self, num_browsers: int = 10, pages_per_browser: int = 10):
        self.num_browsers: int = num_browsers
        self.pages_per_browser: int = pages_per_browser
        self.managers: List[BrowserManager] = []
        self.all_pages: List[Tuple[Page, Any]] = []
        self.peak_memory: float = 0.0
        self.total_pages: int = num_browsers * pages_per_browser
        self.process: psutil.Process = psutil.Process()
        print(
            f"{INFO}Test configuration: {num_browsers} browsers × {pages_per_browser} pages = {self.total_pages} total crawls{RESET}"
        )

    async def run(self, tmp_path: Path):
        """Run the BrowsersManager to start multiple browser instances."""
        self.check_memory()

        logger: AsyncLogger = AsyncLogger()
         # Create all managers but don't start them yet
        managers: List[BrowserManager] = []
        for i in range(self.num_browsers):
            browser_config: BrowserConfig = BrowserConfig(
                browser_mode="builtin",
                headless=True,
                debugging_port=0,
                user_data_dir=str(tmp_path / f"browser_profile_{i}"),
            )
            manager: BrowserManager = BrowserManager(browser_config=browser_config, logger=logger)
            assert isinstance(manager._strategy, BuiltinBrowserStrategy), f"Wrong strategy type {manager._strategy.__class__.__name__}"
            manager._strategy.shutting_down = True
            managers.append(manager)

        # Define async function to start a single manager
        async def start_manager(manager: BrowserManager, index: int) -> Optional[BrowserManager]:
            try:
                await manager.start()
                try:
                    pages = await manager.get_pages(CrawlerRunConfig(), count=self.pages_per_browser)
                    self.all_pages.extend(pages)
                except Exception as e:
                    print(f"{ERROR}Failed to create pages for browser {index}: {str(e)}{RESET}")

                return manager
            except Exception as e:
                print(
                    f"{ERROR}Failed to start browser {index}: {str(e)}{RESET}"
                )
                await self._safe_close(manager)
                return None

        # Start all managers and create pages in parallel
        start_tasks = [
            start_manager(manager, i + 1) for i, manager in enumerate(managers)
        ]

        # Filter out None values (failed starts) and add to managers list
        self.managers = [m for m in await asyncio.gather(*start_tasks) if m is not None]
        self.check_memory()

        if len(self.managers) < self.num_browsers:
            print(
                f"{WARNING}Only {len(self.managers)} out of {self.num_browsers} browser managers started successfully{RESET}"
            )

    async def _safe_close(self, manager: BrowserManager):
        try:
            await manager.close()
        except Exception as e:
            print(f"{ERROR}Failed to close browser manager: {str(e)}{RESET}")

    async def close(self):
        """Close all browser instances managed by this manager."""
        await asyncio.gather(*[self._safe_close(manager) for manager in self.managers]
)

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
async def test_server(aiohttp_server: AiohttpServer) -> TestServer:
    async def handler(request):
        return web.Response(text="""<!doctype html>
<html>
<head>
    <title>Example Domain</title>

    <meta charset="utf-8" />
    <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style type="text/css">
    body {
        background-color: #f0f0f2;
        margin: 0;
        padding: 0;
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", "Open Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;

    }
    div {
        width: 600px;
        margin: 5em auto;
        padding: 2em;
        background-color: #fdfdff;
        border-radius: 0.5em;
        box-shadow: 2px 3px 7px 2px rgba(0,0,0,0.02);
    }
    a:link, a:visited {
        color: #38488f;
        text-decoration: none;
    }
    @media (max-width: 700px) {
        div {
            margin: 0 auto;
            width: auto;
        }
    }
    </style>
</head>

<body>
<div>
    <h1>Example Domain</h1>
    <p>This domain is for use in illustrative examples in documents. You may use this
    domain in literature without prior coordination or asking for permission.</p>
    <p><a href="https://www.iana.org/domains/example">More information...</a></p>
</div>
</body>
</html>""")

    app = web.Application()
    app.router.add_get("/{route}", handler)
    return await aiohttp_server(app)

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
@pytest.mark.parametrize("browser_type", ["webkit", "firefox"])
async def test_not_supported(tmp_path: Path, browser_type: str):
    browser_config: BrowserConfig = BrowserConfig(
        browser_mode="builtin",
        browser_type=browser_type,
        headless=True,
        debugging_port=0,
        user_data_dir=str(tmp_path),
    )
    logger: AsyncLogger = AsyncLogger()
    manager: BrowserManager = BrowserManager(browser_config=browser_config, logger=logger)
    assert isinstance(manager._strategy, BuiltinBrowserStrategy), f"Wrong strategy type {manager._strategy.__class__.__name__}"
    manager._strategy.shutting_down = True
    with pytest.raises(Exception):
        await manager.start()

@pytest.mark.asyncio
@pytest.mark.parametrize("browser_type", ["chromium"])
async def test_ephemeral_port(tmp_path: Path, browser_type: str):
    browser_config: BrowserConfig = BrowserConfig(
        browser_mode="builtin",
        browser_type=browser_type,
        headless=True,
        debugging_port=0,
        user_data_dir=str(tmp_path),
    )
    logger: AsyncLogger = AsyncLogger()
    manager: BrowserManager = BrowserManager(browser_config=browser_config, logger=logger)
    assert isinstance(manager._strategy, BuiltinBrowserStrategy), f"Wrong strategy type {manager._strategy.__class__.__name__}"
    manager._strategy.shutting_down = True
    try:
        await manager.start()
        assert manager._strategy.config.debugging_port != 0, "Ephemeral port not assigned"
    finally:
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
@pytest.mark.timeout(30)
async def test_performance_scaling(browsers_manager: BrowsersManager, test_server: TestServer):
    """Test performance with multiple browsers and pages.

    This test creates multiple browsers on different ports,
    spawns multiple pages per browser, and measures performance metrics.
    """
    assert browsers_manager.managers, "Failed to start any browser managers"

    # Ask for confirmation before loading
    confirmation = input(
        f"{WARNING}Do you want to proceed with loading pages? (y/n): {RESET}"
    ) if sys.stdin.isatty() else "y"

    assert confirmation.lower() == "y", "User aborted the test"

    # Step 1: Create and start multiple browser managers in parallel
    start_time = time.time()

    # Function to load a single page
    url = test_server.make_url("/page")
    async def load_page(page_ctx: Tuple[Page, Any], index):
        page, _ = page_ctx
        try:
            response: Optional[Response] = await page.goto(f"{url}{index}", timeout=5000) # example.com tends to hang connections under load.
            if response is None:
                print(f"{ERROR}Failed to load page {index}: No response{RESET}")
                return "Error: No response"

            if response.status != codes.OK:
                print(f"{ERROR}Failed to load page {index}: {response.status}{RESET}")
                return f"Error: {response.status}"

            return await page.title()
        except Exception as e:
            print(f"{ERROR}Failed to load page {index}: {str(e)}{RESET}")
            return f"Error: {str(e)}"

    # Load all pages concurrently
    load_tasks = [load_page(page_ctx, i + 1) for i, page_ctx in enumerate(browsers_manager.all_pages)]
    load_results = await asyncio.gather(*load_tasks)

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

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
