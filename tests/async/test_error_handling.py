import asyncio
import sys

import pytest
import pytest_asyncio

from crawl4ai import CacheMode
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.utils import InvalidCSSSelectorError


@pytest_asyncio.fixture
async def crawler():
    async with AsyncWebCrawler(verbose=True, warmup=False) as crawler:
        yield crawler


@pytest.mark.asyncio
async def test_network_error(crawler: AsyncWebCrawler):
    url = "https://www.nonexistentwebsite123456789.com"
    result = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS)
    assert not result.success
    assert result.error_message
    assert "Failed on navigating ACS-GOTO" in result.error_message


@pytest.mark.asyncio
async def test_timeout_error(crawler: AsyncWebCrawler):
    # Simulating a timeout by using a very short timeout value
    url = "https://www.nbcnews.com/business"
    result = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS, page_timeout=0.001)
    assert not result.success
    assert result.error_message
    assert "timeout" in result.error_message.lower()


@pytest.mark.asyncio
@pytest.mark.skip("Invalid CSS selector not raised any more")
async def test_invalid_css_selector(crawler: AsyncWebCrawler):
    url = "https://www.nbcnews.com/business"
    with pytest.raises(InvalidCSSSelectorError):
        await crawler.arun(url=url, cache_mode=CacheMode.BYPASS, css_selector="invalid>>selector")


@pytest.mark.asyncio
async def test_js_execution_error(crawler: AsyncWebCrawler):
    url = "https://www.nbcnews.com/business"
    invalid_js = "This is not valid JavaScript code;"
    result = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS, js_code=invalid_js)
    assert result.success
    assert result.js_execution_result
    assert result.js_execution_result["success"]
    results: list[dict] = result.js_execution_result["results"]
    assert results
    assert not results[0]["success"]
    assert "SyntaxError" in results[0]["error"]


@pytest.mark.asyncio
@pytest.mark.skip("The page is not empty any more")
async def test_empty_page(crawler: AsyncWebCrawler):
    # Use a URL that typically returns an empty page
    url = "http://example.com/empty"
    result = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS)
    assert result.success  # The crawl itself should succeed
    assert result.markdown is not None
    assert not result.markdown.strip()  # The markdown content should be empty or just whitespace


@pytest.mark.asyncio
@pytest.mark.skip("Rate limiting doesn't trigger")
async def test_rate_limiting(crawler: AsyncWebCrawler):
    # Simulate rate limiting by making multiple rapid requests
    url = "https://www.nbcnews.com/business"
    results = await asyncio.gather(*[crawler.arun(url=url, cache_mode=CacheMode.BYPASS) for _ in range(10)])
    assert any(not result.success and result.error_message and "rate limit" in result.error_message.lower() for result in results)


# Entry point for debugging
if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
