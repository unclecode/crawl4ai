"""
Tests for redirected_url handling with raw: URLs.

This test file verifies the fix for the issue where redirected_url was incorrectly
set to the entire raw HTML content (potentially 300KB+) instead of None or base_url.

Issue: In raw: mode, async_crawler_strategy.py was setting redirected_url = config.base_url or url,
which fell back to the raw HTML string when base_url wasn't provided.
"""

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    # Create a dummy decorator
    class pytest:
        class mark:
            @staticmethod
            def asyncio(fn):
                return fn

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig


# ============================================================================
# Core fix tests: redirected_url should NOT be the raw HTML string
# ============================================================================

@pytest.mark.asyncio
async def test_raw_html_redirected_url_is_none_without_base_url():
    """Test that redirected_url is None for raw: URLs when no base_url is provided."""
    html = "<html><body><div id='test'>Test Content</div></body></html>"

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig()
        result = await crawler.arun(f"raw:{html}", config=config)

    assert result.success
    # Key assertion: redirected_url should be None, NOT the raw HTML string
    assert result.redirected_url is None, (
        f"redirected_url should be None for raw: URLs without base_url, "
        f"but got: {result.redirected_url[:100] if result.redirected_url else None}..."
    )


@pytest.mark.asyncio
async def test_raw_html_redirected_url_not_huge():
    """Test that redirected_url is not a huge string (the raw HTML content)."""
    # Create a large HTML (100KB+)
    items = "".join([f'<div class="item">Item {i} with some content</div>\n' for i in range(2000)])
    large_html = f"<html><body>{items}</body></html>"
    assert len(large_html) > 100000, "Test HTML should be >100KB"

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig()
        result = await crawler.arun(f"raw:{large_html}", config=config)

    assert result.success
    # Key assertion: redirected_url should NOT be the huge HTML string
    if result.redirected_url is not None:
        assert len(result.redirected_url) < 1000, (
            f"redirected_url should not be the raw HTML! "
            f"Got {len(result.redirected_url)} chars: {result.redirected_url[:100]}..."
        )


@pytest.mark.asyncio
async def test_raw_html_with_base_url_sets_redirected_url():
    """Test that redirected_url is set to base_url when provided."""
    html = "<html><body><div id='test'>Test Content</div></body></html>"
    base_url = "https://example.com/page"

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(base_url=base_url)
        result = await crawler.arun(f"raw:{html}", config=config)

    assert result.success
    # Key assertion: redirected_url should be the base_url
    assert result.redirected_url == base_url, (
        f"redirected_url should be '{base_url}', got: {result.redirected_url}"
    )


@pytest.mark.asyncio
async def test_raw_double_slash_prefix_redirected_url():
    """Test redirected_url handling with raw:// prefix."""
    html = "<html><body>Content</body></html>"

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig()
        result = await crawler.arun(f"raw://{html}", config=config)

    assert result.success
    # Should be None, not the HTML
    assert result.redirected_url is None


# ============================================================================
# Browser path tests (with js_code, screenshot, etc.)
# ============================================================================

@pytest.mark.asyncio
async def test_raw_html_browser_path_redirected_url_none():
    """Test redirected_url is None for raw: URLs in browser path (with js_code)."""
    html = "<html><body><div id='test'>Original</div></body></html>"

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            js_code="document.getElementById('test').innerText = 'Modified'"
        )
        result = await crawler.arun(f"raw:{html}", config=config)

    assert result.success
    assert "Modified" in result.html
    # Key assertion: even with browser path, redirected_url should be None
    assert result.redirected_url is None, (
        f"redirected_url should be None, got: {result.redirected_url}"
    )


@pytest.mark.asyncio
async def test_raw_html_browser_path_with_base_url():
    """Test redirected_url is base_url for raw: URLs in browser path."""
    html = "<html><body><div id='test'>Original</div></body></html>"
    base_url = "https://mysite.com/processed"

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            base_url=base_url,
            js_code="document.getElementById('test').innerText = 'Modified'"
        )
        result = await crawler.arun(f"raw:{html}", config=config)

    assert result.success
    assert "Modified" in result.html
    assert result.redirected_url == base_url


@pytest.mark.asyncio
async def test_raw_html_screenshot_redirected_url():
    """Test redirected_url with screenshot (browser path)."""
    html = "<html><body><h1>Screenshot Test</h1></body></html>"

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(screenshot=True)
        result = await crawler.arun(f"raw:{html}", config=config)

    assert result.success
    assert result.screenshot is not None
    # redirected_url should still be None
    assert result.redirected_url is None


# ============================================================================
# Compatibility tests: HTTP URLs should still work correctly
# ============================================================================

@pytest.mark.asyncio
async def test_http_url_redirected_url_still_works():
    """Ensure HTTP URLs still set redirected_url correctly."""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")

    assert result.success
    # For HTTP URLs, redirected_url should be the final URL (or original if no redirect)
    assert result.redirected_url is not None
    assert "example.com" in result.redirected_url


@pytest.mark.asyncio
async def test_http_url_with_redirect_preserves_redirected_url():
    """Test that HTTP redirects still capture the final URL."""
    # httpbin.org/redirect-to redirects to the specified URL
    async with AsyncWebCrawler() as crawler:
        # Use a URL that redirects
        result = await crawler.arun("https://httpbin.org/redirect-to?url=https://example.com")

    assert result.success
    # Should capture the final redirected URL
    assert result.redirected_url is not None
    assert "example.com" in result.redirected_url


# ============================================================================
# Edge cases
# ============================================================================

@pytest.mark.asyncio
async def test_raw_html_with_url_like_content():
    """Test raw HTML containing URLs doesn't confuse redirected_url."""
    html = """
    <html><body>
        <a href="https://example.com">Link</a>
        <p>Visit https://google.com for more</p>
        <div>raw:https://fake.com</div>
    </body></html>
    """

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(f"raw:{html}")

    assert result.success
    # redirected_url should be None, not any URL from the content
    assert result.redirected_url is None


@pytest.mark.asyncio
async def test_raw_html_empty_base_url():
    """Test raw HTML with empty string base_url."""
    html = "<html><body>Content</body></html>"

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(base_url="")
        result = await crawler.arun(f"raw:{html}", config=config)

    assert result.success
    # Empty string is falsy, so redirected_url should be None
    assert result.redirected_url is None or result.redirected_url == ""


@pytest.mark.asyncio
async def test_raw_html_process_in_browser_redirected_url():
    """Test redirected_url with process_in_browser=True."""
    html = "<html><body>Test</body></html>"

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(process_in_browser=True)
        result = await crawler.arun(f"raw:{html}", config=config)

    assert result.success
    assert result.redirected_url is None


# ============================================================================
# Regression test: specific issue scenario
# ============================================================================

@pytest.mark.asyncio
async def test_regression_321kb_html_redirected_url():
    """
    Regression test for the specific issue:
    - raw:{321KB HTML} should NOT have redirected_url = "raw:{321KB HTML}"
    - This was causing massive memory/logging issues
    """
    # Create ~321KB of HTML content
    content = "X" * 300000  # ~300KB of content
    html = f"<html><body><div>{content}</div></body></html>"
    assert len(html) > 300000, "Should be >300KB"

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(f"raw:{html}")

    assert result.success

    # The bug was: redirected_url = "raw:{321KB HTML}"
    # After fix: redirected_url = None
    assert result.redirected_url is None, (
        "REGRESSION: redirected_url contains the raw HTML! "
        f"Length: {len(result.redirected_url) if result.redirected_url else 0}"
    )


if __name__ == "__main__":
    async def run_tests():
        tests = [
            ("redirected_url None without base_url", test_raw_html_redirected_url_is_none_without_base_url),
            ("redirected_url not huge", test_raw_html_redirected_url_not_huge),
            ("redirected_url with base_url", test_raw_html_with_base_url_sets_redirected_url),
            ("raw:// prefix", test_raw_double_slash_prefix_redirected_url),
            ("browser path None", test_raw_html_browser_path_redirected_url_none),
            ("browser path with base_url", test_raw_html_browser_path_with_base_url),
            ("HTTP URL still works", test_http_url_redirected_url_still_works),
            ("321KB regression", test_regression_321kb_html_redirected_url),
        ]

        passed = 0
        failed = 0

        for name, test_fn in tests:
            print(f"\n=== {name} ===")
            try:
                await test_fn()
                print(f"PASSED")
                passed += 1
            except Exception as e:
                print(f"FAILED: {e}")
                import traceback
                traceback.print_exc()
                failed += 1

        print(f"\n{'='*50}")
        print(f"Results: {passed} passed, {failed} failed")
        return failed == 0

    import sys
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
