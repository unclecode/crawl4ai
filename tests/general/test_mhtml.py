# test_mhtml_capture.py

import pytest
import asyncio
import re  # For more robust MHTML checks

# Assuming these can be imported directly from the crawl4ai library
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CrawlResult

# A reliable, simple static HTML page for testing
# Using httpbin as it's designed for testing clients
TEST_URL_SIMPLE = "https://httpbin.org/html"
EXPECTED_CONTENT_SIMPLE = "Herman Melville - Moby-Dick"

# A slightly more complex page that might involve JS (good secondary test)
TEST_URL_JS = "https://quotes.toscrape.com/js/"
EXPECTED_CONTENT_JS = "Quotes to Scrape" # Title of the page, which should be present in MHTML

# Removed the custom event_loop fixture as pytest-asyncio provides a default one.

@pytest.mark.asyncio
async def test_mhtml_capture_when_enabled():
    """
    Verify that when CrawlerRunConfig has capture_mhtml=True,
    the CrawlResult contains valid MHTML content.
    """
    # Create a fresh browser config and crawler instance for this test
    browser_config = BrowserConfig(headless=True) # Use headless for testing CI/CD
    # --- Key: Enable MHTML capture in the run config ---
    run_config = CrawlerRunConfig(capture_mhtml=True)

    # Create a fresh crawler instance
    crawler = AsyncWebCrawler(config=browser_config)

    try:
        # Start the browser
        await crawler.start()
        
        # Perform the crawl with the MHTML-enabled config
        result: CrawlResult = await crawler.arun(TEST_URL_SIMPLE, config=run_config)

        # --- Assertions ---
        assert result is not None, "Crawler should return a result object"
        assert result.success is True, f"Crawling {TEST_URL_SIMPLE} should succeed. Error: {result.error_message}"

        # 1. Check if the mhtml attribute exists (will fail if CrawlResult not updated)
        assert hasattr(result, 'mhtml'), "CrawlResult object must have an 'mhtml' attribute"

        # 2. Check if mhtml is populated
        assert result.mhtml is not None, "MHTML content should be captured when enabled"
        assert isinstance(result.mhtml, str), "MHTML content should be a string"
        assert len(result.mhtml) > 500, "MHTML content seems too short, likely invalid" # Basic sanity check

        # 3. Check for MHTML structure indicators (more robust than simple string contains)
        # MHTML files are multipart MIME messages
        assert re.search(r"Content-Type: multipart/related;", result.mhtml, re.IGNORECASE), \
            "MHTML should contain 'Content-Type: multipart/related;'"
        # Should contain a boundary definition
        assert re.search(r"boundary=\"----MultipartBoundary", result.mhtml), \
            "MHTML should contain a multipart boundary"
        # Should contain the main HTML part
        assert re.search(r"Content-Type: text/html", result.mhtml, re.IGNORECASE), \
            "MHTML should contain a 'Content-Type: text/html' part"

        # 4. Check if the *actual page content* is within the MHTML string
        # This confirms the snapshot captured the rendered page
        assert EXPECTED_CONTENT_SIMPLE in result.mhtml, \
            f"Expected content '{EXPECTED_CONTENT_SIMPLE}' not found within the captured MHTML"

        # 5. Ensure standard HTML is still present and correct
        assert result.html is not None, "Standard HTML should still be present"
        assert isinstance(result.html, str), "Standard HTML should be a string"
        assert EXPECTED_CONTENT_SIMPLE in result.html, \
            f"Expected content '{EXPECTED_CONTENT_SIMPLE}' not found within the standard HTML"

    finally:
        # Important: Ensure browser is completely closed even if assertions fail
        await crawler.close()
        # Help the garbage collector clean up
        crawler = None


@pytest.mark.asyncio
async def test_mhtml_capture_when_disabled_explicitly():
    """
    Verify that when CrawlerRunConfig explicitly has capture_mhtml=False,
    the CrawlResult.mhtml attribute is None.
    """
    # Create a fresh browser config and crawler instance for this test
    browser_config = BrowserConfig(headless=True)
    # --- Key: Explicitly disable MHTML capture ---
    run_config = CrawlerRunConfig(capture_mhtml=False)

    # Create a fresh crawler instance
    crawler = AsyncWebCrawler(config=browser_config)

    try:
        # Start the browser
        await crawler.start()
        result: CrawlResult = await crawler.arun(TEST_URL_SIMPLE, config=run_config)

        assert result is not None
        assert result.success is True, f"Crawling {TEST_URL_SIMPLE} should succeed. Error: {result.error_message}"

        # 1. Check attribute existence (important for TDD start)
        assert hasattr(result, 'mhtml'), "CrawlResult object must have an 'mhtml' attribute"

        # 2. Check mhtml is None
        assert result.mhtml is None, "MHTML content should be None when explicitly disabled"

        # 3. Ensure standard HTML is still present
        assert result.html is not None
        assert EXPECTED_CONTENT_SIMPLE in result.html

    finally:
        # Important: Ensure browser is completely closed even if assertions fail
        await crawler.close()
        # Help the garbage collector clean up
        crawler = None


@pytest.mark.asyncio
async def test_mhtml_capture_when_disabled_by_default():
    """
    Verify that if capture_mhtml is not specified (using its default),
    the CrawlResult.mhtml attribute is None.
    (This assumes the default value for capture_mhtml in CrawlerRunConfig is False)
    """
    # Create a fresh browser config and crawler instance for this test
    browser_config = BrowserConfig(headless=True)
    # --- Key: Use default run config ---
    run_config = CrawlerRunConfig() # Do not specify capture_mhtml

    # Create a fresh crawler instance
    crawler = AsyncWebCrawler(config=browser_config)

    try:
        # Start the browser
        await crawler.start()
        result: CrawlResult = await crawler.arun(TEST_URL_SIMPLE, config=run_config)

        assert result is not None
        assert result.success is True, f"Crawling {TEST_URL_SIMPLE} should succeed. Error: {result.error_message}"

        # 1. Check attribute existence
        assert hasattr(result, 'mhtml'), "CrawlResult object must have an 'mhtml' attribute"

        # 2. Check mhtml is None (assuming default is False)
        assert result.mhtml is None, "MHTML content should be None when using default config (assuming default=False)"

        # 3. Ensure standard HTML is still present
        assert result.html is not None
        assert EXPECTED_CONTENT_SIMPLE in result.html

    finally:
        # Important: Ensure browser is completely closed even if assertions fail
        await crawler.close()
        # Help the garbage collector clean up
        crawler = None

# Optional: Add a test for a JS-heavy page if needed
@pytest.mark.asyncio
async def test_mhtml_capture_on_js_page_when_enabled():
    """
    Verify MHTML capture works on a page requiring JavaScript execution.
    """
    # Create a fresh browser config and crawler instance for this test
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        capture_mhtml=True,
        # Add a small wait or JS execution if needed for the JS page to fully render
        # For quotes.toscrape.com/js/, it renders quickly, but a wait might be safer
        # wait_for_timeout=2000 # Example: wait up to 2 seconds
        js_code="await new Promise(r => setTimeout(r, 500));" # Small delay after potential load
    )

    # Create a fresh crawler instance
    crawler = AsyncWebCrawler(config=browser_config)

    try:
        # Start the browser
        await crawler.start()
        result: CrawlResult = await crawler.arun(TEST_URL_JS, config=run_config)

        assert result is not None
        assert result.success is True, f"Crawling {TEST_URL_JS} should succeed. Error: {result.error_message}"
        assert hasattr(result, 'mhtml'), "CrawlResult object must have an 'mhtml' attribute"
        assert result.mhtml is not None, "MHTML content should be captured on JS page when enabled"
        assert isinstance(result.mhtml, str), "MHTML content should be a string"
        assert len(result.mhtml) > 500, "MHTML content from JS page seems too short"

        # Check for MHTML structure
        assert re.search(r"Content-Type: multipart/related;", result.mhtml, re.IGNORECASE)
        assert re.search(r"Content-Type: text/html", result.mhtml, re.IGNORECASE)

        # Check for content rendered by JS within the MHTML
        assert EXPECTED_CONTENT_JS in result.mhtml, \
            f"Expected JS-rendered content '{EXPECTED_CONTENT_JS}' not found within the captured MHTML"

        # Check standard HTML too
        assert result.html is not None
        assert EXPECTED_CONTENT_JS in result.html, \
             f"Expected JS-rendered content '{EXPECTED_CONTENT_JS}' not found within the standard HTML"

    finally:
        # Important: Ensure browser is completely closed even if assertions fail
        await crawler.close()
        # Help the garbage collector clean up
        crawler = None

if __name__ == "__main__":
    # Use pytest for async tests
    pytest.main(["-xvs", __file__])
