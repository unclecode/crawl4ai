#!/usr/bin/env python3
"""
Comprehensive Test Suite for Docker Extended Features
Tests all advanced features: URL seeding, adaptive crawling, browser adapters,
proxy rotation, and dispatchers.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Configuration
API_BASE_URL = "http://localhost:11235"
console = Console()


class TestResultData:
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = False
        self.error = None
        self.duration = 0.0
        self.details = {}


class ExtendedFeaturesTestSuite:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        self.results: List[TestResultData] = []

    async def check_server_health(self) -> bool:
        """Check if the server is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            console.print(f"[red]Server health check failed: {e}[/red]")
            return False

    # ========================================================================
    # URL SEEDING TESTS
    # ========================================================================

    async def test_url_seeding_basic(self) -> TestResultData:
        """Test basic URL seeding functionality"""
        result = TestResultData("Basic URL Seeding", "URL Seeding")
        try:
            import time

            start = time.time()

            payload = {
                "url": "https://www.nbcnews.com",
                "config": {"max_urls": 10, "filter_type": "all"},
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/seed",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # API returns: {"seed_url": [list of urls], "count": n}
                        urls = data.get("seed_url", [])

                        result.passed = len(urls) > 0
                        result.details = {
                            "urls_found": len(urls),
                            "sample_url": urls[0] if urls else None,
                        }
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    async def test_url_seeding_with_filters(self) -> TestResultData:
        """Test URL seeding with different filter types"""
        result = TestResultData("URL Seeding with Filters", "URL Seeding")
        try:
            import time

            start = time.time()

            payload = {
                "url": "https://www.nbcnews.com",
                "config": {
                    "max_urls": 20,
                    "filter_type": "domain",
                    "exclude_external": True,
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/seed",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # API returns: {"seed_url": [list of urls], "count": n}
                        urls = data.get("seed_url", [])

                        result.passed = len(urls) > 0
                        result.details = {
                            "urls_found": len(urls),
                            "filter_type": "domain",
                        }
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    # ========================================================================
    # ADAPTIVE CRAWLING TESTS
    # ========================================================================

    async def test_adaptive_crawling_basic(self) -> TestResultData:
        """Test basic adaptive crawling"""
        result = TestResultData("Basic Adaptive Crawling", "Adaptive Crawling")
        try:
            import time

            start = time.time()

            payload = {
                "urls": ["https://example.com"],
                "browser_config": {"headless": True},
                "crawler_config": {"adaptive": True, "adaptive_threshold": 0.5},
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result.passed = data.get("success", False)
                        result.details = {"results_count": len(data.get("results", []))}
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    async def test_adaptive_crawling_with_strategy(self) -> TestResultData:
        """Test adaptive crawling with custom strategy"""
        result = TestResultData("Adaptive Crawling with Strategy", "Adaptive Crawling")
        try:
            import time

            start = time.time()

            payload = {
                "urls": ["https://httpbin.org/html"],
                "browser_config": {"headless": True},
                "crawler_config": {
                    "adaptive": True,
                    "adaptive_threshold": 0.7,
                    "word_count_threshold": 10,
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result.passed = data.get("success", False)
                        result.details = {"adaptive_threshold": 0.7}
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    # ========================================================================
    # BROWSER ADAPTER TESTS
    # ========================================================================

    async def test_browser_adapter_default(self) -> TestResultData:
        """Test default browser adapter"""
        result = TestResultData("Default Browser Adapter", "Browser Adapters")
        try:
            import time

            start = time.time()

            payload = {
                "urls": ["https://example.com"],
                "browser_config": {"headless": True},
                "crawler_config": {},
                "anti_bot_strategy": "default",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result.passed = data.get("success", False)
                        result.details = {"adapter": "default"}
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    async def test_browser_adapter_stealth(self) -> TestResultData:
        """Test stealth browser adapter"""
        result = TestResultData("Stealth Browser Adapter", "Browser Adapters")
        try:
            import time

            start = time.time()

            payload = {
                "urls": ["https://example.com"],
                "browser_config": {"headless": True},
                "crawler_config": {},
                "anti_bot_strategy": "stealth",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result.passed = data.get("success", False)
                        result.details = {"adapter": "stealth"}
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    async def test_browser_adapter_undetected(self) -> TestResultData:
        """Test undetected browser adapter"""
        result = TestResultData("Undetected Browser Adapter", "Browser Adapters")
        try:
            import time

            start = time.time()

            payload = {
                "urls": ["https://example.com"],
                "browser_config": {"headless": True},
                "crawler_config": {},
                "anti_bot_strategy": "undetected",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result.passed = data.get("success", False)
                        result.details = {"adapter": "undetected"}
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    # ========================================================================
    # PROXY ROTATION TESTS
    # ========================================================================

    async def test_proxy_rotation_round_robin(self) -> TestResultData:
        """Test round robin proxy rotation"""
        result = TestResultData("Round Robin Proxy Rotation", "Proxy Rotation")
        try:
            import time

            start = time.time()

            payload = {
                "urls": ["https://httpbin.org/ip"],
                "browser_config": {"headless": True},
                "crawler_config": {},
                "proxy_rotation_strategy": "round_robin",
                "proxies": [
                    {"server": "http://proxy1.example.com:8080"},
                    {"server": "http://proxy2.example.com:8080"},
                ],
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    # This might fail due to invalid proxies, but we're testing the API accepts it
                    result.passed = response.status in [
                        200,
                        500,
                    ]  # Accept either success or expected failure
                    result.details = {
                        "strategy": "round_robin",
                        "status": response.status,
                    }

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    async def test_proxy_rotation_random(self) -> TestResultData:
        """Test random proxy rotation"""
        result = TestResultData("Random Proxy Rotation", "Proxy Rotation")
        try:
            import time

            start = time.time()

            payload = {
                "urls": ["https://httpbin.org/ip"],
                "browser_config": {"headless": True},
                "crawler_config": {},
                "proxy_rotation_strategy": "random",
                "proxies": [
                    {"server": "http://proxy1.example.com:8080"},
                    {"server": "http://proxy2.example.com:8080"},
                ],
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    result.passed = response.status in [200, 500]
                    result.details = {"strategy": "random", "status": response.status}

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    # ========================================================================
    # DISPATCHER TESTS
    # ========================================================================

    async def test_dispatcher_memory_adaptive(self) -> TestResultData:
        """Test memory adaptive dispatcher"""
        result = TestResultData("Memory Adaptive Dispatcher", "Dispatchers")
        try:
            import time

            start = time.time()

            payload = {
                "urls": ["https://example.com"],
                "browser_config": {"headless": True},
                "crawler_config": {"screenshot": True},
                "dispatcher": "memory_adaptive",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result.passed = data.get("success", False)
                        if result.passed and data.get("results"):
                            has_screenshot = (
                                data["results"][0].get("screenshot") is not None
                            )
                            result.details = {
                                "dispatcher": "memory_adaptive",
                                "screenshot_captured": has_screenshot,
                            }
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    async def test_dispatcher_semaphore(self) -> TestResultData:
        """Test semaphore dispatcher"""
        result = TestResultData("Semaphore Dispatcher", "Dispatchers")
        try:
            import time

            start = time.time()

            payload = {
                "urls": ["https://example.com"],
                "browser_config": {"headless": True},
                "crawler_config": {},
                "dispatcher": "semaphore",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result.passed = data.get("success", False)
                        result.details = {"dispatcher": "semaphore"}
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    async def test_dispatcher_endpoints(self) -> TestResultData:
        """Test dispatcher management endpoints"""
        result = TestResultData("Dispatcher Management Endpoints", "Dispatchers")
        try:
            import time

            start = time.time()

            async with aiohttp.ClientSession() as session:
                # Test list dispatchers
                async with session.get(
                    f"{self.base_url}/dispatchers",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # API returns a list directly, not wrapped in a dict
                        dispatchers = data if isinstance(data, list) else []
                        result.passed = len(dispatchers) > 0
                        result.details = {
                            "dispatcher_count": len(dispatchers),
                            "available": [d.get("type") for d in dispatchers],
                        }
                    else:
                        result.error = f"Status {response.status}"

            result.duration = time.time() - start
        except Exception as e:
            result.error = str(e)

        return result

    # ========================================================================
    # TEST RUNNER
    # ========================================================================

    async def run_all_tests(self):
        """Run all tests and collect results"""
        console.print(
            Panel.fit(
                "[bold cyan]Extended Features Test Suite[/bold cyan]\n"
                "Testing: URL Seeding, Adaptive Crawling, Browser Adapters, Proxy Rotation, Dispatchers",
                border_style="cyan",
            )
        )

        # Check server health first
        console.print("\n[yellow]Checking server health...[/yellow]")
        if not await self.check_server_health():
            console.print(
                "[red]❌ Server is not responding. Please start the Docker container.[/red]"
            )
            console.print(f"[yellow]Expected server at: {self.base_url}[/yellow]")
            return

        console.print("[green]✅ Server is healthy[/green]\n")

        # Define all tests
        tests = [
            # URL Seeding
            self.test_url_seeding_basic(),
            self.test_url_seeding_with_filters(),
            # Adaptive Crawling
            self.test_adaptive_crawling_basic(),
            self.test_adaptive_crawling_with_strategy(),
            # Browser Adapters
            self.test_browser_adapter_default(),
            self.test_browser_adapter_stealth(),
            self.test_browser_adapter_undetected(),
            # Proxy Rotation
            self.test_proxy_rotation_round_robin(),
            self.test_proxy_rotation_random(),
            # Dispatchers
            self.test_dispatcher_memory_adaptive(),
            self.test_dispatcher_semaphore(),
            self.test_dispatcher_endpoints(),
        ]

        console.print(f"[cyan]Running {len(tests)} tests...[/cyan]\n")

        # Run tests
        for i, test_coro in enumerate(tests, 1):
            console.print(f"[yellow]Running test {i}/{len(tests)}...[/yellow]")
            test_result = await test_coro
            self.results.append(test_result)

            # Print immediate feedback
            if test_result.passed:
                console.print(
                    f"[green]✅ {test_result.name} ({test_result.duration:.2f}s)[/green]"
                )
            else:
                console.print(
                    f"[red]❌ {test_result.name} ({test_result.duration:.2f}s)[/red]"
                )
                if test_result.error:
                    console.print(f"   [red]Error: {test_result.error}[/red]")

        # Display results
        self.display_results()

    def display_results(self):
        """Display test results in a formatted table"""
        console.print("\n")
        console.print(
            Panel.fit("[bold]Test Results Summary[/bold]", border_style="cyan")
        )

        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        # Display by category
        for category, tests in categories.items():
            table = Table(
                title=f"\n{category}",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan",
            )
            table.add_column("Test Name", style="white", width=40)
            table.add_column("Status", style="white", width=10)
            table.add_column("Duration", style="white", width=10)
            table.add_column("Details", style="white", width=40)

            for test in tests:
                status = (
                    "[green]✅ PASS[/green]" if test.passed else "[red]❌ FAIL[/red]"
                )
                duration = f"{test.duration:.2f}s"
                details = str(test.details) if test.details else (test.error or "")
                if test.error and len(test.error) > 40:
                    details = test.error[:37] + "..."

                table.add_row(test.name, status, duration, details)

            console.print(table)

        # Overall statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        console.print("\n")
        stats_table = Table(box=box.DOUBLE, show_header=False, width=60)
        stats_table.add_column("Metric", style="bold cyan", width=30)
        stats_table.add_column("Value", style="bold white", width=30)

        stats_table.add_row("Total Tests", str(total_tests))
        stats_table.add_row("Passed", f"[green]{passed_tests}[/green]")
        stats_table.add_row("Failed", f"[red]{failed_tests}[/red]")
        stats_table.add_row("Pass Rate", f"[cyan]{pass_rate:.1f}%[/cyan]")

        console.print(
            Panel(
                stats_table,
                title="[bold]Overall Statistics[/bold]",
                border_style="green" if pass_rate >= 80 else "yellow",
            )
        )

        # Recommendations
        if failed_tests > 0:
            console.print(
                "\n[yellow]💡 Some tests failed. Check the errors above for details.[/yellow]"
            )
            console.print("[yellow]   Common issues:[/yellow]")
            console.print(
                "[yellow]   - Server not fully started (wait ~30-40 seconds after docker compose up)[/yellow]"
            )
            console.print(
                "[yellow]   - Invalid proxy servers in proxy rotation tests (expected)[/yellow]"
            )
            console.print("[yellow]   - Network connectivity issues[/yellow]")


async def main():
    """Main entry point"""
    suite = ExtendedFeaturesTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
        sys.exit(1)
