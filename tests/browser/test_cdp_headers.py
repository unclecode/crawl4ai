"""Test examples for CDPBrowserStrategy with Authentication Headers.

These examples demonstrate the functionality of CDPBrowserStrategy with Authentication Headers
and serve as functional tests.
"""

import asyncio
import os
import sys

from bedrock_agentcore.tools.browser_client import BrowserClient

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    )

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger

# Create a logger for clear terminal output
logger = AsyncLogger(verbose=True, log_file=None)


async def test_cdp_headers_with_aws():
    """Test launching a browser and connecting via CDP."""
    logger.info("Testing launch and connect via CDP", tag="TEST")

    try:
        client = BrowserClient(region="us-east-1")
        client.start()

        ws_url, headers = client.generate_ws_headers()

        browser_config = BrowserConfig(
            browser_type="chromium",
            cdp_url=ws_url,
            cdp_headers=headers,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url="https://www.nbcnews.com/business",
            )
            print(result.markdown)

        logger.success("CDP headers test passed", tag="TEST")
        return True

    except Exception as e:
        logger.error(f"CDP headers test failed: {str(e)}", tag="TEST")
        return False


async def run_tests():
    """Run all tests sequentially."""
    results = []

    results.append(await test_cdp_headers_with_aws())

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
