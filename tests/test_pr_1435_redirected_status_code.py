"""Tests for PR #1435: redirected_status_code in CrawlResult."""

import pytest
import pytest_asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.models import CrawlResult, AsyncCrawlResponse


class TestRedirectedStatusCodeModel:
    """Test that the field exists and defaults correctly on both models."""

    def test_crawl_result_default_none(self):
        result = CrawlResult(url="http://example.com", html="", success=True)
        assert result.redirected_status_code is None

    def test_crawl_result_set_value(self):
        result = CrawlResult(url="http://example.com", html="", success=True, redirected_status_code=200)
        assert result.redirected_status_code == 200

    def test_async_crawl_response_default_none(self):
        resp = AsyncCrawlResponse(html="<html></html>", response_headers={}, status_code=200)
        assert resp.redirected_status_code is None

    def test_async_crawl_response_set_value(self):
        resp = AsyncCrawlResponse(html="<html></html>", response_headers={}, status_code=200, redirected_status_code=301)
        assert resp.redirected_status_code == 301


@pytest.mark.asyncio
async def test_redirected_status_code_on_direct_request():
    """A non-redirected request should have redirected_status_code equal to the final status."""
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun("https://httpbin.org/get", config=run_config)

    assert result.success
    # Direct request — redirected_status_code should be the final response status (200)
    assert result.redirected_status_code == 200


@pytest.mark.asyncio
async def test_redirected_status_code_on_redirect():
    """A redirected request should capture the final destination's status code."""
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig()

    # httpbin /redirect/1 does a 302 redirect to /get (which returns 200)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun("https://httpbin.org/redirect/1", config=run_config)

    assert result.success
    # status_code should be 302 (the first hop, per crawl4ai's redirect chain walking)
    assert result.status_code == 302
    # redirected_status_code should be 200 (the final destination)
    assert result.redirected_status_code == 200
    # redirected_url should point to the final destination
    assert "/get" in (result.redirected_url or "")


@pytest.mark.asyncio
async def test_redirected_status_code_on_raw_html():
    """Raw HTML input should have redirected_status_code = None (no network request)."""
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun("raw:<html><body>test</body></html>", config=run_config)

    assert result.success
    assert result.redirected_status_code is None
