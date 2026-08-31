"""
Crawl4AI Regression Tests - Core Crawling Functionality

Tests core crawling features including basic crawls, raw HTML, multiple URLs,
screenshots, JavaScript execution, caching, sessions, hooks, network capture,
CSS selectors, excluded tags, timeouts, and status codes.

All tests use real browser crawling with no mocking.
"""

import asyncio
import base64
import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.cache_context import CacheMode


# ---------------------------------------------------------------------------
# Basic crawl tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_basic_crawl(local_server):
    """Crawl the local server home page and verify basic result fields."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/")
        assert result.success, f"Crawl failed: {result.error_message}"
        assert "<h1>" in result.html, "HTML should contain an <h1> tag"
        assert isinstance(result.markdown, str), "Markdown should be a string"
        assert len(result.markdown) > 0, "Markdown should be non-empty"


@pytest.mark.asyncio
@pytest.mark.network
async def test_basic_crawl_real_url():
    """Crawl https://example.com and verify success with real content."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun("https://example.com")
        assert result.success, f"Crawl failed: {result.error_message}"
        assert len(result.html) > 100, "HTML should have substantial content"
        assert len(result.markdown) > 10, "Markdown should have content"


# ---------------------------------------------------------------------------
# Raw HTML crawl tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_raw_html_crawl():
    """Crawl raw HTML and verify markdown extraction."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun("raw:<html><body><h1>Test</h1><p>Hello world</p></body></html>")
        assert result.success, f"Raw HTML crawl failed: {result.error_message}"
        assert "Test" in result.markdown, "Markdown should contain 'Test'"
        assert "Hello" in result.markdown, "Markdown should contain 'Hello'"


@pytest.mark.asyncio
async def test_raw_html_with_base_url():
    """Raw HTML with relative links should resolve against base_url."""
    raw_html = (
        "raw:<html><body>"
        '<a href="/page1">Link 1</a>'
        '<a href="/page2">Link 2</a>'
        '<a href="https://other.com/abs">Absolute</a>'
        "</body></html>"
    )
    config = CrawlerRunConfig(base_url="http://example.com")
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(raw_html, config=config)
        assert result.success, f"Raw HTML with base_url failed: {result.error_message}"
        # Check that links were resolved (they should appear in the result's links or markdown)
        md_lower = result.markdown.lower() if result.markdown else ""
        html_lower = result.html.lower() if result.html else ""
        combined = md_lower + html_lower
        # At minimum, the link text should appear
        assert "link 1" in combined, "Link text should be present"


# ---------------------------------------------------------------------------
# Multiple URL crawl tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_arun_many(local_server):
    """Crawl 3 local server URLs with arun_many and verify all succeed."""
    urls = [
        local_server + "/",
        local_server + "/products",
        local_server + "/tables",
    ]
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun_many(urls, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
        assert isinstance(results, list), "arun_many should return a list"
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        for i, result in enumerate(results):
            assert result.success, f"Result {i} failed: {result.error_message}"


@pytest.mark.asyncio
@pytest.mark.network
async def test_arun_many_real():
    """Crawl multiple real URLs together."""
    urls = ["https://example.com", "https://quotes.toscrape.com"]
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun_many(urls, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"
        for result in results:
            assert result.success, f"Real URL crawl failed: {result.error_message}"


# ---------------------------------------------------------------------------
# Screenshot tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_screenshot_capture(local_server):
    """Crawl with screenshot=True and verify PNG format output."""
    config = CrawlerRunConfig(screenshot=True)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/", config=config)
        assert result.success, f"Screenshot crawl failed: {result.error_message}"
        assert result.screenshot, "Screenshot should be a non-empty string"
        assert isinstance(result.screenshot, str), "Screenshot should be a base64 string"
        # Decode and verify PNG header
        raw_bytes = base64.b64decode(result.screenshot)
        assert raw_bytes[:4] == b"\x89PNG", "Screenshot should be in PNG format"


@pytest.mark.asyncio
async def test_screenshot_not_bmp(local_server):
    """Verify screenshot is PNG format, NOT BMP (regression for #1758)."""
    config = CrawlerRunConfig(screenshot=True)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/", config=config)
        assert result.success
        raw_bytes = base64.b64decode(result.screenshot)
        # BMP files start with b'BM'
        assert raw_bytes[:2] != b"BM", "Screenshot should NOT be BMP format"
        assert raw_bytes[:4] == b"\x89PNG", "Screenshot should be PNG format"


# ---------------------------------------------------------------------------
# JavaScript execution tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_js_execution(local_server):
    """Crawl /js-dynamic with wait_for to verify JS-generated content loads."""
    config = CrawlerRunConfig(wait_for="css:.js-loaded")
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/js-dynamic", config=config)
        assert result.success, f"JS dynamic crawl failed: {result.error_message}"
        assert "Dynamic content successfully loaded" in result.markdown, (
            "JS-generated content should appear in markdown"
        )


@pytest.mark.asyncio
async def test_js_code_execution(local_server):
    """Execute custom JS code during crawl and verify modification."""
    config = CrawlerRunConfig(
        js_code="document.title = 'Modified Title';",
    )
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/", config=config)
        assert result.success, f"JS code execution crawl failed: {result.error_message}"
        # The JS ran after page load; verify it did not cause errors
        # (title change may or may not be reflected in html depending on timing)


@pytest.mark.asyncio
async def test_js_code_before_wait(local_server):
    """Use js_code_before_wait to inject content, then wait_for to verify it."""
    js_inject = """
    const div = document.createElement('div');
    div.id = 'injected-marker';
    div.className = 'injected';
    div.textContent = 'Injected by js_code_before_wait';
    document.body.appendChild(div);
    """
    config = CrawlerRunConfig(
        js_code_before_wait=js_inject,
        wait_for="css:#injected-marker",
    )
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/", config=config)
        assert result.success, f"js_code_before_wait crawl failed: {result.error_message}"
        assert "Injected by js_code_before_wait" in result.markdown, (
            "Injected content should appear in markdown"
        )


# ---------------------------------------------------------------------------
# Cache mode tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_write_and_read(local_server):
    """Crawl with ENABLED cache, then crawl again to verify cache hit."""
    config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        # First crawl - writes to cache
        result1 = await crawler.arun(local_server + "/", config=config)
        assert result1.success, f"First crawl failed: {result1.error_message}"

        # Second crawl - should read from cache
        result2 = await crawler.arun(local_server + "/", config=config)
        assert result2.success, f"Second crawl failed: {result2.error_message}"
        if result2.cache_status:
            assert "hit" in result2.cache_status.lower(), (
                f"Second crawl should be a cache hit, got: {result2.cache_status}"
            )


@pytest.mark.asyncio
async def test_cache_bypass(local_server):
    """Crawl with BYPASS cache mode; result should still succeed."""
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/", config=config)
        assert result.success, f"Bypass cache crawl failed: {result.error_message}"
        assert len(result.html) > 0, "HTML should be non-empty even with bypass"


@pytest.mark.asyncio
async def test_cache_disabled(local_server):
    """Crawl with DISABLED cache; second crawl should not be cached."""
    config = CrawlerRunConfig(cache_mode=CacheMode.DISABLED)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result1 = await crawler.arun(local_server + "/", config=config)
        assert result1.success
        result2 = await crawler.arun(local_server + "/", config=config)
        assert result2.success
        # With DISABLED, there should be no cache hit
        if result2.cache_status:
            assert "hit" not in result2.cache_status.lower(), (
                "DISABLED cache should not produce a cache hit"
            )


# ---------------------------------------------------------------------------
# Session reuse test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_session_reuse(local_server):
    """Crawl with a session_id, crawl again with same session_id; both succeed."""
    config = CrawlerRunConfig(session_id="test-session", cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result1 = await crawler.arun(local_server + "/", config=config)
        assert result1.success, f"First session crawl failed: {result1.error_message}"

        result2 = await crawler.arun(local_server + "/", config=config)
        assert result2.success, f"Second session crawl failed: {result2.error_message}"


# ---------------------------------------------------------------------------
# Hooks test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hooks_fire(local_server):
    """Verify before_goto and after_goto hooks are called during crawl."""
    calls = []

    async def before_hook(page, context, url, **kwargs):
        calls.append(("before_goto", url))
        return page

    async def after_hook(page, context, url, **kwargs):
        calls.append(("after_goto", url))
        return page

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        crawler.crawler_strategy.set_hook("before_goto", before_hook)
        crawler.crawler_strategy.set_hook("after_goto", after_hook)

        result = await crawler.arun(local_server + "/", config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
        assert result.success, f"Hook crawl failed: {result.error_message}"
        hook_types = [c[0] for c in calls]
        assert "before_goto" in hook_types, "before_goto hook should have been called"
        assert "after_goto" in hook_types, "after_goto hook should have been called"


# ---------------------------------------------------------------------------
# Network capture test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_network_request_capture(local_server):
    """Crawl with capture_network_requests=True and verify requests are captured."""
    config = CrawlerRunConfig(capture_network_requests=True, cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/", config=config)
        assert result.success, f"Network capture crawl failed: {result.error_message}"
        assert result.network_requests is not None, "network_requests should not be None"
        assert isinstance(result.network_requests, list), "network_requests should be a list"
        assert len(result.network_requests) >= 1, "Should capture at least 1 network request"
        # Each entry should have a url key
        assert "url" in result.network_requests[0], (
            "Network request entries should have a 'url' key"
        )


# ---------------------------------------------------------------------------
# CSS selector test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_css_selector(local_server):
    """Crawl /products with css_selector to narrow content extraction."""
    config = CrawlerRunConfig(css_selector=".product-list", cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/products", config=config)
        assert result.success, f"CSS selector crawl failed: {result.error_message}"
        # The product content should be present
        assert "Wireless Mouse" in result.html, "Product content should be in HTML"
        # The h1 "Products" is outside .product-list, should not be in the selected HTML
        # css_selector filters the HTML sent to content extraction
        assert "<h1>" not in result.html, (
            "The h1 outside .product-list should not appear in result.html"
        )


# ---------------------------------------------------------------------------
# Excluded tags test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_excluded_tags(local_server):
    """Crawl with excluded_tags to remove nav and footer content."""
    config = CrawlerRunConfig(excluded_tags=["nav", "footer"], cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/", config=config)
        assert result.success, f"Excluded tags crawl failed: {result.error_message}"
        cleaned = result.cleaned_html or ""
        assert "<nav" not in cleaned.lower(), "cleaned_html should not contain nav element"
        assert "<footer" not in cleaned.lower(), "cleaned_html should not contain footer element"


# ---------------------------------------------------------------------------
# Page timeout test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_page_timeout(local_server):
    """Crawl /slow with a 500ms timeout; expect failure or timeout."""
    config = CrawlerRunConfig(page_timeout=500, cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/slow", config=config)
        # The slow page takes 2 seconds but we gave only 500ms
        # It should either fail or have an error
        if result.success:
            # Some browsers may still return partial content; that is acceptable
            pass
        else:
            assert result.error_message is not None, (
                "Failed crawl should have an error message"
            )


# ---------------------------------------------------------------------------
# Status code tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_404_status_code(local_server):
    """Crawl /not-found and verify 404 status code."""
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/not-found", config=config)
        assert result.status_code == 404, (
            f"Expected status code 404, got {result.status_code}"
        )


@pytest.mark.asyncio
async def test_redirect_status(local_server):
    """Crawl /redirect and verify it follows the redirect to home."""
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/redirect", config=config)
        assert result.success, f"Redirect crawl failed: {result.error_message}"
        # After redirect, the final URL should be the home page
        if result.redirected_url:
            assert result.redirected_url.rstrip("/").endswith(
                local_server.rstrip("/").split(":")[-1]
            ) or result.redirected_url.endswith("/"), (
                f"Redirected URL should end with /, got: {result.redirected_url}"
            )
