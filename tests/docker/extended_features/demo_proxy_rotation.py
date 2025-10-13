#!/usr/bin/env python3
"""
Proxy Rotation Demo Script

This script demonstrates real-world usage scenarios for the proxy rotation feature.
It simulates actual user workflows and shows how to integrate proxy rotation
into your crawling tasks.

Usage:
    python demo_proxy_rotation.py

Note: Update the proxy configuration with your actual proxy servers for real testing.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List

import requests
from rich import print as rprint
from rich.console import Console

# Initialize rich console for colored output
console = Console()

# Configuration
API_BASE_URL = "http://localhost:11235"

# Import real proxy configuration
try:
    from real_proxy_config import (
        PROXY_POOL_LARGE,
        PROXY_POOL_MEDIUM,
        PROXY_POOL_SMALL,
        REAL_PROXIES,
    )

    USE_REAL_PROXIES = True
    console.print(
        f"[green]✅ Loaded {len(REAL_PROXIES)} real proxies from configuration[/green]"
    )
except ImportError:
    # Fallback to demo proxies if real_proxy_config.py not found
    REAL_PROXIES = [
        {
            "server": "http://proxy1.example.com:8080",
            "username": "user1",
            "password": "pass1",
        },
        {
            "server": "http://proxy2.example.com:8080",
            "username": "user2",
            "password": "pass2",
        },
        {
            "server": "http://proxy3.example.com:8080",
            "username": "user3",
            "password": "pass3",
        },
    ]
    PROXY_POOL_SMALL = REAL_PROXIES[:2]
    PROXY_POOL_MEDIUM = REAL_PROXIES[:2]
    PROXY_POOL_LARGE = REAL_PROXIES
    USE_REAL_PROXIES = False
    console.print(
        f"[yellow]⚠️  Using demo proxies (real_proxy_config.py not found)[/yellow]"
    )

# Alias for backward compatibility
DEMO_PROXIES = REAL_PROXIES

# Set to True to test with actual proxies, False for demo mode (no proxies, just shows API)
USE_REAL_PROXIES = False

# Test URLs that help verify proxy rotation
TEST_URLS = [
    "https://httpbin.org/ip",  # Shows origin IP
    "https://httpbin.org/headers",  # Shows all headers
    "https://httpbin.org/user-agent",  # Shows user agent
]


def print_header(text: str):
    """Print a formatted header"""
    console.print(f"\n[cyan]{'=' * 60}[/cyan]")
    console.print(f"[cyan]{text.center(60)}[/cyan]")
    console.print(f"[cyan]{'=' * 60}[/cyan]\n")


def print_success(text: str):
    """Print success message"""
    console.print(f"[green]✅ {text}[/green]")


def print_info(text: str):
    """Print info message"""
    console.print(f"[blue]ℹ️  {text}[/blue]")


def print_warning(text: str):
    """Print warning message"""
    console.print(f"[yellow]⚠️  {text}[/yellow]")


def print_error(text: str):
    """Print error message"""
    console.print(f"[red]❌ {text}[/red]")


def check_server_health() -> bool:
    """Check if the Crawl4AI server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Crawl4AI server is running")
            return True
        else:
            print_error(f"Server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to server: {e}")
        print_warning("Make sure the Crawl4AI server is running on localhost:11235")
        return False


def demo_1_basic_round_robin():
    """Demo 1: Basic proxy rotation with round robin strategy"""
    print_header("Demo 1: Basic Round Robin Rotation")

    print_info("Use case: Even distribution across proxies for general crawling")
    print_info("Strategy: Round Robin - cycles through proxies sequentially\n")

    if USE_REAL_PROXIES:
        payload = {
            "urls": [TEST_URLS[0]],  # Just checking IP
            "proxy_rotation_strategy": "round_robin",
            "proxies": PROXY_POOL_SMALL,  # Use small pool (3 proxies)
            "headless": True,
            "browser_config": {
                "type": "BrowserConfig",
                "params": {"headless": True, "verbose": False},
            },
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {"cache_mode": "bypass", "verbose": False},
            },
        }
    else:
        print_warning(
            "Demo mode: Showing API structure without actual proxy connections"
        )
        payload = {
            "urls": [TEST_URLS[0]],
            "headless": True,
            "browser_config": {
                "type": "BrowserConfig",
                "params": {"headless": True, "verbose": False},
            },
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {"cache_mode": "bypass", "verbose": False},
            },
        }

    console.print(f"[yellow]Request payload:[/yellow]")
    print(json.dumps(payload, indent=2))

    if USE_REAL_PROXIES:
        print()
        print_info("With real proxies, the request would:")
        print_info("  1. Initialize RoundRobinProxyStrategy")
        print_info("  2. Cycle through proxy1 → proxy2 → proxy1...")
        print_info("  3. Each request uses the next proxy in sequence")

    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/crawl", json=payload, timeout=30)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print_success(f"Request completed in {elapsed:.2f} seconds")
            print_info(f"Results: {len(data.get('results', []))} URL(s) crawled")

            # Show first result summary
            if data.get("results"):
                result = data["results"][0]
                print_info(f"Success: {result.get('success')}")
                print_info(f"URL: {result.get('url')}")

            if not USE_REAL_PROXIES:
                print()
                print_success(
                    "✨ API integration works! Add real proxies to test rotation."
                )
        else:
            print_error(f"Request failed: {response.status_code}")
            if "PROXY_CONNECTION_FAILED" in response.text:
                print_warning(
                    "Proxy connection failed - this is expected with example proxies"
                )
                print_info(
                    "Update DEMO_PROXIES and set USE_REAL_PROXIES = True to test with real proxies"
                )
            else:
                print(response.text)

    except Exception as e:
        print_error(f"Error: {e}")


def demo_2_random_stealth():
    """Demo 2: Random proxy rotation with stealth mode"""
    print_header("Demo 2: Random Rotation + Stealth Mode")

    print_info("Use case: Unpredictable traffic pattern with anti-bot evasion")
    print_info("Strategy: Random - unpredictable proxy selection")
    print_info("Feature: Combined with stealth anti-bot strategy\n")

    payload = {
        "urls": [TEST_URLS[1]],  # Check headers
        "proxy_rotation_strategy": "random",
        "anti_bot_strategy": "stealth",  # Combined with anti-bot
        "proxies": PROXY_POOL_MEDIUM,  # Use medium pool (5 proxies)
        "headless": True,
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True, "enable_stealth": True, "verbose": False},
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"cache_mode": "bypass"},
        },
    }

    console.print(f"[yellow]Request payload (key parts):[/yellow]")
    print(
        json.dumps(
            {
                "urls": payload["urls"],
                "proxy_rotation_strategy": payload["proxy_rotation_strategy"],
                "anti_bot_strategy": payload["anti_bot_strategy"],
                "proxies": f"{len(payload['proxies'])} proxies configured",
            },
            indent=2,
        )
    )

    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/crawl", json=payload, timeout=30)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print_success(f"Request completed in {elapsed:.2f} seconds")
            print_success("Random proxy + stealth mode working together!")
        else:
            print_error(f"Request failed: {response.status_code}")

    except Exception as e:
        print_error(f"Error: {e}")


def demo_3_least_used_multiple_urls():
    """Demo 3: Least used strategy with multiple URLs"""
    print_header("Demo 3: Least Used Strategy (Load Balancing)")

    print_info("Use case: Optimal load distribution across multiple requests")
    print_info("Strategy: Least Used - balances load across proxy pool")
    print_info("Feature: Crawling multiple URLs efficiently\n")

    payload = {
        "urls": TEST_URLS,  # All test URLs
        "proxy_rotation_strategy": "least_used",
        "proxies": PROXY_POOL_LARGE,  # Use full pool (all proxies)
        "headless": True,
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True, "verbose": False},
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "bypass",
                "wait_for_images": False,  # Speed up crawling
                "verbose": False,
            },
        },
    }

    console.print(
        f"[yellow]Crawling {len(payload['urls'])} URLs with load balancing:[/yellow]"
    )
    for i, url in enumerate(payload["urls"], 1):
        print(f"  {i}. {url}")

    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/crawl", json=payload, timeout=60)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print_success(f"Completed {len(results)} URLs in {elapsed:.2f} seconds")
            print_info(f"Average time per URL: {elapsed / len(results):.2f}s")

            # Show success rate
            successful = sum(1 for r in results if r.get("success"))
            print_info(
                f"Success rate: {successful}/{len(results)} ({successful / len(results) * 100:.1f}%)"
            )
        else:
            print_error(f"Request failed: {response.status_code}")

    except Exception as e:
        print_error(f"Error: {e}")


def demo_4_failure_aware_production():
    """Demo 4: Failure-aware strategy for production use"""
    print_header("Demo 4: Failure-Aware Strategy (Production)")

    print_info("Use case: High-availability crawling with automatic recovery")
    print_info("Strategy: Failure Aware - tracks proxy health")
    print_info("Feature: Auto-recovery after failures\n")

    payload = {
        "urls": [TEST_URLS[0]],
        "proxy_rotation_strategy": "failure_aware",
        "proxy_failure_threshold": 2,  # Mark unhealthy after 2 failures
        "proxy_recovery_time": 120,  # 2 minutes recovery time
        "proxies": PROXY_POOL_MEDIUM,  # Use medium pool (5 proxies)
        "headless": True,
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True, "verbose": False},
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"cache_mode": "bypass"},
        },
    }

    console.print(f"[yellow]Configuration:[/yellow]")
    print(f"  Failure threshold: {payload['proxy_failure_threshold']} failures")
    print(f"  Recovery time: {payload['proxy_recovery_time']} seconds")
    print(f"  Proxy pool size: {len(payload['proxies'])} proxies")

    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/crawl", json=payload, timeout=30)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print_success(f"Request completed in {elapsed:.2f} seconds")
            print_success("Failure-aware strategy initialized successfully")
            print_info("The strategy will now track proxy health automatically")
        else:
            print_error(f"Request failed: {response.status_code}")

    except Exception as e:
        print_error(f"Error: {e}")


def demo_5_streaming_with_proxies():
    """Demo 5: Streaming endpoint with proxy rotation"""
    print_header("Demo 5: Streaming with Proxy Rotation")

    print_info("Use case: Real-time results with proxy rotation")
    print_info("Strategy: Random - varies proxies across stream")
    print_info("Feature: Streaming endpoint support\n")

    payload = {
        "urls": TEST_URLS[:2],  # First 2 URLs
        "proxy_rotation_strategy": "random",
        "proxies": PROXY_POOL_SMALL,  # Use small pool (3 proxies)
        "headless": True,
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True, "verbose": False},
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"stream": True, "cache_mode": "bypass", "verbose": False},
        },
    }

    print_info("Streaming 2 URLs with random proxy rotation...")

    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/crawl/stream", json=payload, timeout=60, stream=True
        )

        if response.status_code == 200:
            results_count = 0
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if data.get("status") == "processing":
                            print_info(f"Processing: {data.get('url', 'unknown')}")
                        elif data.get("status") == "completed":
                            results_count += 1
                            print_success(f"Completed: {data.get('url', 'unknown')}")
                    except json.JSONDecodeError:
                        pass

            elapsed = time.time() - start_time
            print_success(
                f"\nStreaming completed: {results_count} results in {elapsed:.2f}s"
            )
        else:
            print_error(f"Streaming failed: {response.status_code}")

    except Exception as e:
        print_error(f"Error: {e}")


def demo_6_error_handling():
    """Demo 6: Error handling demonstration"""
    print_header("Demo 6: Error Handling")

    print_info("Demonstrating how the system handles errors gracefully\n")

    # Test 1: Invalid strategy
    console.print(f"[yellow]Test 1: Invalid strategy name[/yellow]")
    payload = {
        "urls": [TEST_URLS[0]],
        "proxy_rotation_strategy": "invalid_strategy",
        "proxies": [PROXY_POOL_SMALL[0]],  # Use just 1 proxy
        "headless": True,
    }

    try:
        response = requests.post(f"{API_BASE_URL}/crawl", json=payload, timeout=10)
        if response.status_code != 200:
            print_error(
                f"Expected error: {response.json().get('detail', 'Unknown error')}"
            )
        else:
            print_warning("Unexpected: Request succeeded")
    except Exception as e:
        print_error(f"Error: {e}")

    print()

    # Test 2: Missing server field
    console.print(f"[yellow]Test 2: Invalid proxy configuration[/yellow]")
    payload = {
        "urls": [TEST_URLS[0]],
        "proxy_rotation_strategy": "round_robin",
        "proxies": [{"username": "user1"}],  # Missing server
        "headless": True,
    }

    try:
        response = requests.post(f"{API_BASE_URL}/crawl", json=payload, timeout=10)
        if response.status_code != 200:
            print_error(
                f"Expected error: {response.json().get('detail', 'Unknown error')}"
            )
        else:
            print_warning("Unexpected: Request succeeded")
    except Exception as e:
        print_error(f"Error: {e}")

    print()
    print_success("Error handling working as expected!")


def demo_7_real_world_scenario():
    """Demo 7: Real-world e-commerce price monitoring scenario"""
    print_header("Demo 7: Real-World Scenario - Price Monitoring")

    print_info("Scenario: Monitoring multiple product pages with high availability")
    print_info("Requirements: Anti-detection + Proxy rotation + Fault tolerance\n")

    # Simulated product URLs (using httpbin for demo)
    product_urls = [
        "https://httpbin.org/delay/1",  # Simulates slow page
        "https://httpbin.org/html",  # Simulates product page
        "https://httpbin.org/json",  # Simulates API endpoint
    ]

    payload = {
        "urls": product_urls,
        "anti_bot_strategy": "stealth",
        "proxy_rotation_strategy": "failure_aware",
        "proxy_failure_threshold": 2,
        "proxy_recovery_time": 180,
        "proxies": PROXY_POOL_LARGE,  # Use full pool for high availability
        "headless": True,
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True, "enable_stealth": True, "verbose": False},
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "bypass",
                "page_timeout": 30000,
                "wait_for_images": False,
                "verbose": False,
            },
        },
    }

    console.print(f"[yellow]Configuration:[/yellow]")
    print(f"  URLs to monitor: {len(product_urls)}")
    print(f"  Anti-bot strategy: stealth")
    print(f"  Proxy strategy: failure_aware")
    print(f"  Proxy pool: {len(DEMO_PROXIES)} proxies")
    print()

    print_info("Starting price monitoring crawl...")

    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/crawl", json=payload, timeout=90)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            print_success(f"Monitoring completed in {elapsed:.2f} seconds\n")

            # Detailed results
            console.print(f"[yellow]Results Summary:[/yellow]")
            for i, result in enumerate(results, 1):
                url = result.get("url", "unknown")
                success = result.get("success", False)
                status = "✅ Success" if success else "❌ Failed"
                print(f"  {i}. {status} - {url}")

            successful = sum(1 for r in results if r.get("success"))
            print()
            print_info(
                f"Success rate: {successful}/{len(results)} ({successful / len(results) * 100:.1f}%)"
            )
            print_info(f"Average time per product: {elapsed / len(results):.2f}s")

            print()
            print_success("✨ Real-world scenario completed successfully!")
            print_info("This configuration is production-ready for:")
            print_info("  - E-commerce price monitoring")
            print_info("  - Competitive analysis")
            print_info("  - Market research")
            print_info("  - Any high-availability crawling needs")
        else:
            print_error(f"Request failed: {response.status_code}")
            print(response.text)

    except Exception as e:
        print_error(f"Error: {e}")


def show_python_integration_example():
    """Show Python integration code example"""
    print_header("Python Integration Example")

    code = '''
import requests
import json

class ProxyCrawler:
    """Example class for integrating proxy rotation into your application"""
    
    def __init__(self, api_url="http://localhost:11235"):
        self.api_url = api_url
        self.proxies = [
            {"server": "http://proxy1.com:8080", "username": "user", "password": "pass"},
            {"server": "http://proxy2.com:8080", "username": "user", "password": "pass"},
        ]
    
    def crawl_with_proxies(self, urls, strategy="round_robin"):
        """Crawl URLs with proxy rotation"""
        payload = {
            "urls": urls,
            "proxy_rotation_strategy": strategy,
            "proxies": self.proxies,
            "headless": True,
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {"cache_mode": "bypass"}
            }
        }
        
        response = requests.post(f"{self.api_url}/crawl", json=payload, timeout=60)
        return response.json()
    
    def monitor_prices(self, product_urls):
        """Monitor product prices with high availability"""
        payload = {
            "urls": product_urls,
            "anti_bot_strategy": "stealth",
            "proxy_rotation_strategy": "failure_aware",
            "proxy_failure_threshold": 2,
            "proxies": self.proxies,
            "headless": True
        }
        
        response = requests.post(f"{self.api_url}/crawl", json=payload, timeout=120)
        return response.json()

# Usage
crawler = ProxyCrawler()

# Simple crawling
results = crawler.crawl_with_proxies(
    urls=["https://example.com"],
    strategy="round_robin"
)

# Price monitoring
product_results = crawler.monitor_prices(
    product_urls=["https://shop.example.com/product1", "https://shop.example.com/product2"]
)
'''

    console.print(f"[green]{code}[/green]")
    print_info("Copy this code to integrate proxy rotation into your application!")


def demo_0_proxy_setup_guide():
    """Demo 0: Guide for setting up real proxies"""
    print_header("Proxy Setup Guide")

    print_info("This demo can run in two modes:\n")

    console.print(f"[yellow]1. DEMO MODE (Current):[/yellow]")
    print("   - Tests API integration without proxies")
    print("   - Shows request/response structure")
    print("   - Safe to run without proxy servers\n")

    console.print(f"[yellow]2. REAL PROXY MODE:[/yellow]")
    print("   - Tests actual proxy rotation")
    print("   - Requires valid proxy servers")
    print("   - Shows real proxy switching in action\n")

    console.print(f"[green]To enable real proxy testing:[/green]")
    print("   1. Update DEMO_PROXIES with your actual proxy servers:")
    print()
    console.print("[cyan]      DEMO_PROXIES = [")
    console.print(
        "          {'server': 'http://your-proxy1.com:8080', 'username': 'user', 'password': 'pass'},"
    )
    console.print(
        "          {'server': 'http://your-proxy2.com:8080', 'username': 'user', 'password': 'pass'},"
    )
    console.print("      ][/cyan]")
    print()
    console.print(f"   2. Set: [cyan]USE_REAL_PROXIES = True[/cyan]")
    print()

    console.print(f"[yellow]Popular Proxy Providers:[/yellow]")
    print("   - Bright Data (formerly Luminati)")
    print("   - Oxylabs")
    print("   - Smartproxy")
    print("   - ProxyMesh")
    print("   - Your own proxy servers")
    print()

    if USE_REAL_PROXIES:
        print_success("Real proxy mode is ENABLED")
        print_info(f"Using {len(DEMO_PROXIES)} configured proxies")
    else:
        print_info("Demo mode is active (USE_REAL_PROXIES = False)")
        print_info(
            "API structure will be demonstrated without actual proxy connections"
        )


def main():
    """Main demo runner"""
    console.print(f"""
[cyan]╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          Crawl4AI Proxy Rotation Demo Suite             ║
║                                                          ║
║  Demonstrating real-world proxy rotation scenarios      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝[/cyan]
""")

    if USE_REAL_PROXIES:
        print_success(f"✨ Using {len(REAL_PROXIES)} real Webshare proxies")
        print_info(f"📊 Proxy pools configured:")
        print_info(f"   • Small pool: {len(PROXY_POOL_SMALL)} proxies (quick tests)")
        print_info(f"   • Medium pool: {len(PROXY_POOL_MEDIUM)} proxies (balanced)")
        print_info(
            f"   • Large pool: {len(PROXY_POOL_LARGE)} proxies (high availability)"
        )
    else:
        print_warning("⚠️  Using demo proxy configuration (won't connect)")
        print_info("To use real proxies, create real_proxy_config.py with your proxies")
    print()

    # Check server health
    if not check_server_health():
        print()
        print_error("Please start the Crawl4AI server first:")
        print_info("cd deploy/docker && docker-compose up")
        print_info("or run: ./dev.sh")
        return

    print()
    input(f"[yellow]Press Enter to start the demos...[/yellow]")

    # Run all demos
    demos = [
        demo_0_proxy_setup_guide,
        demo_1_basic_round_robin,
        demo_2_random_stealth,
        demo_3_least_used_multiple_urls,
        demo_4_failure_aware_production,
        demo_5_streaming_with_proxies,
        demo_6_error_handling,
        demo_7_real_world_scenario,
    ]

    for i, demo in enumerate(demos, 1):
        try:
            demo()
            if i < len(demos):
                print()
                input(f"[yellow]Press Enter to continue to next demo...[/yellow]")
        except KeyboardInterrupt:
            print()
            print_warning("Demo interrupted by user")
            break
        except Exception as e:
            print_error(f"Demo failed: {e}")
            import traceback

            traceback.print_exc()

    # Show integration example
    print()
    show_python_integration_example()

    # Summary
    print_header("Demo Suite Complete!")
    print_success("You've seen all major proxy rotation features!")
    print()
    print_info("Next steps:")
    print_info("  1. Update DEMO_PROXIES with your actual proxy servers")
    print_info("  2. Run: python test_proxy_rotation_strategies.py (full test suite)")
    print_info("  3. Read: PROXY_ROTATION_STRATEGY_DOCS.md (complete documentation)")
    print_info("  4. Integrate into your application using the examples above")
    print()
    console.print(f"[cyan]Happy crawling! 🚀[/cyan]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("\nDemo interrupted. Goodbye!")
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
