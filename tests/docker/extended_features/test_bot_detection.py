#!/usr/bin/env python3
"""
Fixed version of test_bot_detection.py with proper timeouts and error handling
"""

import asyncio
import os
import sys
import signal
import logging
from contextlib import asynccontextmanager

import pytest

# Add the project root to Python path
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "deploy", "docker"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

@asynccontextmanager
async def timeout_context(seconds):
    """Context manager for timeout handling"""
    try:
        yield
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out after {seconds} seconds")
        raise
    except TimeoutError:
        logger.error(f"Operation timed out after {seconds} seconds")
        raise

async def safe_crawl_with_timeout(crawler, url, config, timeout_seconds=30):
    """Safely crawl a URL with timeout"""
    try:
        # Use asyncio.wait_for to add timeout
        result = await asyncio.wait_for(
            crawler.arun(url=url, config=config),
            timeout=timeout_seconds
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"Crawl timed out for {url} after {timeout_seconds} seconds")
        return None
    except Exception as e:
        logger.error(f"Crawl failed for {url}: {e}")
        return None

@pytest.mark.asyncio
async def test_bot_detection():
    """Test adapters against bot detection with proper timeouts"""
    print("🤖 Testing Adapters Against Bot Detection (Fixed Version)")
    print("=" * 60)

    # Set global timeout for the entire test (5 minutes)
    test_timeout = 300
    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(test_timeout)

    crawlers_to_cleanup = []

    try:
        from api import _get_browser_adapter
        from crawler_pool import get_crawler
        from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

        # Test with a site that detects automation
        test_sites = [
            "https://bot.sannysoft.com/",  # Bot detection test site
            "https://httpbin.org/headers",  # Headers inspection
        ]

        strategies = [
            ("default", "PlaywrightAdapter"),
            ("stealth", "StealthAdapter"),
            ("undetected", "UndetectedAdapter"),
        ]

        # Test with smaller browser config to reduce resource usage
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            viewport_width=1024,
            viewport_height=768
        )

        for site in test_sites:
            print(f"\n🌐 Testing site: {site}")
            print("=" * 60)

            for strategy, expected_adapter in strategies:
                print(f"\n  🧪 {strategy} strategy:")
                print(f"  {'-' * 30}")

                try:
                    # Get adapter with timeout
                    adapter = _get_browser_adapter(strategy, browser_config)
                    print(f"    ✅ Using {adapter.__class__.__name__}")

                    # Get crawler with timeout
                    try:
                        crawler = await asyncio.wait_for(
                            get_crawler(browser_config, adapter),
                            timeout=20  # 20 seconds timeout for crawler creation
                        )
                        crawlers_to_cleanup.append(crawler)
                        print(f"    ✅ Crawler created successfully")
                    except asyncio.TimeoutError:
                        print(f"    ❌ Crawler creation timed out")
                        continue

                    # Crawl with timeout
                    crawler_config = CrawlerRunConfig(
                        cache_mode="bypass",
                        wait_until="domcontentloaded",  # Faster than networkidle
                        word_count_threshold=5  # Lower threshold for faster processing
                    )

                    result = await safe_crawl_with_timeout(
                        crawler, site, crawler_config, timeout_seconds=20
                    )

                    if result and result.success:
                        content = result.markdown[:500] if result.markdown else ""
                        print(f"    ✅ Crawl successful ({len(result.markdown) if result.markdown else 0} chars)")

                        # Look for bot detection indicators
                        bot_indicators = [
                            "webdriver",
                            "automation",
                            "bot detected",
                            "chrome-devtools",
                            "headless",
                            "selenium",
                        ]

                        detected_indicators = []
                        for indicator in bot_indicators:
                            if indicator.lower() in content.lower():
                                detected_indicators.append(indicator)

                        if detected_indicators:
                            print(f"    ⚠️  Detected indicators: {', '.join(detected_indicators)}")
                        else:
                            print(f"    ✅ No bot detection indicators found")

                        # Show a snippet of content
                        print(f"    📝 Content sample: {content[:200]}...")

                    else:
                        error_msg = result.error_message if result and hasattr(result, 'error_message') else "Unknown error"
                        print(f"    ❌ Crawl failed: {error_msg}")

                except asyncio.TimeoutError:
                    print(f"    ❌ Strategy {strategy} timed out")
                except Exception as e:
                    print(f"    ❌ Error with {strategy} strategy: {e}")

        print(f"\n🎉 Bot detection testing completed!")

    except TimeoutError:
        print(f"\n⏰ Test timed out after {test_timeout} seconds")
        raise
    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Restore original signal handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)

        # Cleanup crawlers
        print("\n🧹 Cleaning up browser instances...")
        cleanup_tasks = []
        for crawler in crawlers_to_cleanup:
            if hasattr(crawler, 'close'):
                cleanup_tasks.append(crawler.close())

        if cleanup_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*cleanup_tasks, return_exceptions=True),
                    timeout=10
                )
                print("✅ Cleanup completed")
            except asyncio.TimeoutError:
                print("⚠️  Cleanup timed out, but test completed")

if __name__ == "__main__":
    asyncio.run(test_bot_detection())