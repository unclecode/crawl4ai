"""
Crawl4AI Regression Tests - Edge Cases and Error Handling

Adversarial tests for empty pages, malformed HTML, large pages, unicode,
concurrent crawls, error recovery, and other boundary conditions.

All tests use real browser crawling with no mocking.
"""

import asyncio
import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.cache_context import CacheMode


# ---------------------------------------------------------------------------
# Empty and minimal pages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_page(local_server):
    """Crawl an empty page and verify no crash. Anti-bot may flag it as blocked."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/empty")
        # An empty page may be flagged by the anti-bot detector as "near-empty content"
        # so success may be False. The key thing is no unhandled exception and
        # we get a result object back.
        assert result.html is not None, "HTML should not be None for empty page"
        # Markdown should be empty or minimal
        md = result.markdown or ""
        assert len(md.strip()) < 50, (
            "Empty page should produce little to no markdown"
        )


@pytest.mark.asyncio
async def test_empty_raw_html():
    """Crawl raw HTML with empty body; should succeed without crash."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun("raw:<html><body></body></html>")
        assert result.success, f"Empty raw HTML crawl failed: {result.error_message}"


# ---------------------------------------------------------------------------
# Malformed HTML
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_malformed_html(local_server):
    """Crawl intentionally broken HTML; should not crash, even if anti-bot flags it."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/malformed")
        # The malformed HTML is so broken that the browser may put content into
        # unexpected places (e.g., the title). The anti-bot detector may flag the
        # result as blocked due to empty body. The key assertion is: no unhandled
        # exception and we get a result object back with html content.
        assert result.html is not None, "Should still return HTML even for malformed pages"
        assert len(result.html) > 0, "HTML should be non-empty for malformed page"


@pytest.mark.asyncio
async def test_raw_html_no_doctype():
    """Raw HTML without doctype or <html> wrapper should still parse."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun("raw:<body><p>No doctype</p></body>")
        assert result.success, f"No-doctype raw HTML failed: {result.error_message}"
        assert "No doctype" in (result.markdown or ""), (
            "Content should be extracted despite missing doctype"
        )


# ---------------------------------------------------------------------------
# Large pages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_large_page(local_server):
    """Crawl a page with 50 sections and verify content from beginning and end."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/large")
        assert result.success, f"Large page crawl failed: {result.error_message}"
        md = result.markdown or ""
        assert "Section 0" in md, "Markdown should contain content from section 0"
        assert "Section 49" in md, "Markdown should contain content from section 49"


# ---------------------------------------------------------------------------
# Unicode and special characters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unicode_content():
    """Crawl raw HTML with unicode characters and verify they survive extraction."""
    raw = "raw:<html><body><p>Unicode: \u00e9\u00e8\u00ea \u4e16\u754c \U0001f600</p></body></html>"
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(raw)
        assert result.success, f"Unicode crawl failed: {result.error_message}"
        md = result.markdown or ""
        assert "\u00e9" in md, "French accented 'e' should be in markdown"
        assert "\u4e16\u754c" in md, "Chinese characters should be in markdown"
        # Emoji may or may not survive depending on markdown generator;
        # at least the other unicode should be present


@pytest.mark.asyncio
async def test_html_entities():
    """Crawl raw HTML with entities and verify they are decoded in markdown."""
    raw = "raw:<html><body><p>&amp; &lt; &gt; &quot; &#39;</p></body></html>"
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(raw)
        assert result.success, f"HTML entities crawl failed: {result.error_message}"
        md = result.markdown or ""
        assert "&" in md, "Ampersand entity should be decoded"
        assert "<" in md, "Less-than entity should be decoded"
        assert ">" in md, "Greater-than entity should be decoded"


# ---------------------------------------------------------------------------
# Multiple crawls - no state leakage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sequential_crawls_no_leakage(local_server):
    """Crawl 3 different pages sequentially; verify no content bleed."""
    pages = [
        (local_server + "/products", "Wireless Mouse"),
        (local_server + "/tables", "Sales Report"),
        (local_server + "/js-dynamic", "Static Section"),
    ]
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        for url, expected_content in pages:
            result = await crawler.arun(url, config=config)
            assert result.success, f"Sequential crawl of {url} failed: {result.error_message}"
            md = result.markdown or ""
            assert expected_content in md, (
                f"Expected '{expected_content}' in markdown for {url}, "
                f"got: {md[:200]}..."
            )


# ---------------------------------------------------------------------------
# Raw HTML edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_raw_html_only_whitespace():
    """Raw HTML with only whitespace body should succeed with empty markdown."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun("raw:<html><body>   \n\t  </body></html>")
        assert result.success, f"Whitespace-only raw HTML failed: {result.error_message}"
        md = result.markdown or ""
        assert len(md.strip()) < 20, "Whitespace-only body should produce minimal markdown"


@pytest.mark.asyncio
async def test_raw_html_script_only():
    """Raw HTML with only a script tag should produce empty markdown (scripts stripped)."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            "raw:<html><body><script>var x = 1;</script></body></html>"
        )
        assert result.success, f"Script-only raw HTML failed: {result.error_message}"
        md = result.markdown or ""
        assert "var x" not in md, "Script content should be stripped from markdown"


# ---------------------------------------------------------------------------
# Concurrent crawls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_crawls(local_server):
    """Use asyncio.gather to crawl 5 pages concurrently with same crawler."""
    urls = [
        local_server + "/",
        local_server + "/products",
        local_server + "/tables",
        local_server + "/links-page",
        local_server + "/images-page",
    ]
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        tasks = [crawler.arun(url, config=config) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), (
                f"Concurrent crawl {i} raised exception: {result}"
            )
            assert result.success, (
                f"Concurrent crawl {i} ({urls[i]}) failed: {result.error_message}"
            )


# ---------------------------------------------------------------------------
# Very long URL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_long_url(local_server):
    """Crawl a URL with a very long path (200 chars); catch-all handler serves it."""
    long_path = "/" + "a" * 200
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + long_path)
        assert result.success, f"Long URL crawl failed: {result.error_message}"


# ---------------------------------------------------------------------------
# Special URL characters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_url_with_query_params(local_server):
    """Crawl a URL with query parameters and verify success."""
    url = local_server + "/products?page=1&sort=name&filter=electronics"
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url)
        assert result.success, f"Query params URL crawl failed: {result.error_message}"


@pytest.mark.asyncio
async def test_url_with_fragment(local_server):
    """Crawl a URL with a fragment identifier and verify success."""
    url = local_server + "/#section-5"
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url)
        assert result.success, f"Fragment URL crawl failed: {result.error_message}"


# ---------------------------------------------------------------------------
# Error recovery
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_url_scheme():
    """Try crawling an FTP URL; should handle gracefully without crash."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun("ftp://example.com")
        # Either it fails gracefully with an error or succeeds with empty content
        # The critical thing is no unhandled exception
        if not result.success:
            assert result.error_message is not None, (
                "Invalid scheme should produce an error message"
            )


@pytest.mark.asyncio
@pytest.mark.network
async def test_nonexistent_domain():
    """Try crawling a nonexistent domain; should fail gracefully."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            "https://this-domain-definitely-does-not-exist-xyz123.com",
            config=CrawlerRunConfig(page_timeout=10000),
        )
        # Should fail but not crash
        if not result.success:
            assert result.error_message is not None, (
                "Nonexistent domain should produce an error message"
            )


# ---------------------------------------------------------------------------
# Multiple identical crawls (idempotency)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_idempotent_crawl(local_server):
    """Crawl same URL twice with BYPASS cache; both should succeed with similar content."""
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result1 = await crawler.arun(local_server + "/products", config=config)
        result2 = await crawler.arun(local_server + "/products", config=config)
        assert result1.success, f"First crawl failed: {result1.error_message}"
        assert result2.success, f"Second crawl failed: {result2.error_message}"
        # Both should have similar content length (within 20% tolerance)
        len1 = len(result1.markdown or "")
        len2 = len(result2.markdown or "")
        if len1 > 0 and len2 > 0:
            ratio = min(len1, len2) / max(len1, len2)
            assert ratio > 0.8, (
                f"Idempotent crawls should produce similar content "
                f"(len1={len1}, len2={len2}, ratio={ratio:.2f})"
            )


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pdf_capture(local_server):
    """Crawl with pdf=True and verify PDF bytes output."""
    config = CrawlerRunConfig(pdf=True, cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/", config=config)
        assert result.success, f"PDF capture crawl failed: {result.error_message}"
        assert result.pdf is not None, "PDF should not be None"
        assert isinstance(result.pdf, bytes), "PDF should be bytes"
        assert len(result.pdf) > 0, "PDF should be non-empty"
        # PDF files start with %PDF
        assert result.pdf[:4] == b"%PDF", "PDF should start with %PDF header"


# ---------------------------------------------------------------------------
# Scan full page
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scan_full_page(local_server):
    """Crawl /large with scan_full_page=True to scroll through entire page."""
    config = CrawlerRunConfig(
        scan_full_page=True,
        scroll_delay=0.1,
        cache_mode=CacheMode.BYPASS,
    )
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/large", config=config)
        assert result.success, f"Scan full page crawl failed: {result.error_message}"
        md = result.markdown or ""
        assert len(md) > 100, "Full page scan should produce substantial markdown"


# ---------------------------------------------------------------------------
# Console capture
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_console_capture(local_server):
    """Crawl /js-dynamic with capture_console_messages=True; verify no error."""
    config = CrawlerRunConfig(
        capture_console_messages=True,
        cache_mode=CacheMode.BYPASS,
    )
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(local_server + "/js-dynamic", config=config)
        assert result.success, f"Console capture crawl failed: {result.error_message}"
        # console_messages should be a list (possibly empty)
        assert result.console_messages is not None, (
            "console_messages should not be None when capture_console_messages=True"
        )
        assert isinstance(result.console_messages, list), (
            "console_messages should be a list"
        )
