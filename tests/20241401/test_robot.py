import sys

import pytest
from _pytest.mark.structures import ParameterSet

from crawl4ai import BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.async_webcrawler import AsyncWebCrawler

TEST_CASES = [
    # Public sites that should be allowed
    ("https://example.com", True),  # Simple public site
    ("https://httpbin.org/get", True),  # API endpoint
    # Sites with known strict robots.txt
    ("https://www.facebook.com/robots.txt", False),  # Social media
    ("https://www.google.com/search", False),  # Search pages
    # Edge cases
    ("https://api.github.com", True),  # API service
    ("https://raw.githubusercontent.com", True),  # Content delivery
    # Non-existent/error cases
    ("https://thisisnotarealwebsite123.com", False),  # Non-existent domain
    ("https://localhost:12345", False),  # Invalid port
]


def website_params() -> list[ParameterSet]:
    return [pytest.param(url, expected, id=url) for url, expected in TEST_CASES]


@pytest.mark.asyncio
@pytest.mark.parametrize("url, expected", website_params())
async def test_real_websites(url: str, expected: bool):
    print("\n=== Testing Real Website Robots.txt Compliance ===\n")

    browser_config = BrowserConfig(headless=True, verbose=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            check_robots_txt=True,  # Enable robots.txt checking
            verbose=True,
        )

        result = await crawler.arun(url=url, config=config)
        allowed = result.success and not result.error_message

        print(f"Expected: {'allowed' if expected else 'denied'}")
        print(f"Actual: {'allowed' if allowed else 'denied'}")
        print(f"Status Code: {result.status_code}")
        if result.error_message:
            print(f"Error: {result.error_message}")

        assert expected == allowed, f"Expected {expected} but got {allowed} for {url}"

        # Optional: Print robots.txt content if available
        if result.metadata and 'robots_txt' in result.metadata:
            print(f"Robots.txt rules:\n{result.metadata['robots_txt']}")


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
