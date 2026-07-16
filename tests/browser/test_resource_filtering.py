"""E2E tests for avoid_ads / avoid_css resource filtering.

These tests launch real browsers and crawl real websites to verify
that route-based resource blocking actually works.

Domains used:
  - books.toscrape.com  (CSS-heavy practice site, designed for scraping)
  - quotes.toscrape.com (simple practice site)
  - httpbin.org/html    (static HTML, no trackers)
  - en.wikipedia.org    (real site with analytics)
"""

import pytest
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


# ---------------------------------------------------------------------------
# Basic success tests — flags should not break crawling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crawl_with_avoid_css_succeeds():
    """Crawl books.toscrape.com with avoid_css=True — page should load fine."""
    browser_config = BrowserConfig(headless=True, avoid_css=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com",
            config=CrawlerRunConfig(cache_mode="bypass"),
        )
        assert result.success, f"Crawl failed: {result.error_message}"
        assert len(result.html) > 500, "Page HTML is suspiciously short"


@pytest.mark.asyncio
async def test_crawl_with_avoid_ads_succeeds():
    """Crawl Wikipedia with avoid_ads=True — content should be intact."""
    browser_config = BrowserConfig(headless=True, avoid_ads=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/Web_scraping",
            config=CrawlerRunConfig(cache_mode="bypass"),
        )
        assert result.success, f"Crawl failed: {result.error_message}"
        # Wikipedia article content must be present
        html_lower = result.html.lower()
        assert "web scraping" in html_lower, "Wikipedia content missing"


@pytest.mark.asyncio
async def test_crawl_with_both_flags_succeeds():
    """Both avoid_css and avoid_ads enabled simultaneously."""
    browser_config = BrowserConfig(headless=True, avoid_css=True, avoid_ads=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://quotes.toscrape.com",
            config=CrawlerRunConfig(cache_mode="bypass"),
        )
        assert result.success, f"Crawl failed: {result.error_message}"
        html_lower = result.html.lower()
        assert "quote" in html_lower or "toscrape" in html_lower


@pytest.mark.asyncio
async def test_avoid_ads_does_not_block_page_content():
    """avoid_ads must not interfere with first-party page content."""
    browser_config = BrowserConfig(headless=True, avoid_ads=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://httpbin.org/html",
            config=CrawlerRunConfig(cache_mode="bypass"),
        )
        assert result.success, f"Crawl failed: {result.error_message}"
        # httpbin.org/html serves a Moby Dick excerpt
        assert "Herman Melville" in result.html, "First-party content missing"


# ---------------------------------------------------------------------------
# Network-level verification — prove routes actually block requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_without_flags_css_loads_normally():
    """Baseline: without avoid_css, CSS responses should appear in network log."""
    browser_config = BrowserConfig(headless=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com",
            config=CrawlerRunConfig(
                cache_mode="bypass",
                capture_network_requests=True,
            ),
        )
        assert result.success
        assert result.network_requests is not None, "Network requests not captured"

        # There should be successful CSS responses
        css_responses = [
            r
            for r in result.network_requests
            if r.get("event_type") == "response" and ".css" in r.get("url", "")
        ]
        assert (
            len(css_responses) > 0
        ), "CSS should load normally without avoid_css flag"


@pytest.mark.asyncio
async def test_avoid_css_blocks_css_requests():
    """With avoid_css=True, CSS requests must be aborted (no successful responses)."""
    browser_config = BrowserConfig(headless=True, avoid_css=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com",
            config=CrawlerRunConfig(
                cache_mode="bypass",
                capture_network_requests=True,
            ),
        )
        assert result.success
        assert result.network_requests is not None, "Network requests not captured"

        # No CSS should have gotten a successful response
        css_responses = [
            r
            for r in result.network_requests
            if r.get("event_type") == "response" and ".css" in r.get("url", "")
        ]
        assert (
            len(css_responses) == 0
        ), f"CSS responses should be blocked, but found: {[r['url'] for r in css_responses]}"

        # There SHOULD be request_failed events for CSS (proves blocking happened)
        css_failures = [
            r
            for r in result.network_requests
            if r.get("event_type") == "request_failed"
            and ".css" in r.get("url", "")
        ]
        assert (
            len(css_failures) > 0
        ), "Expected request_failed events for blocked CSS files"


@pytest.mark.asyncio
async def test_avoid_css_with_text_mode_combines():
    """Both avoid_css and text_mode should combine their blocking rules."""
    browser_config = BrowserConfig(
        headless=True, avoid_css=True, text_mode=True
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com",
            config=CrawlerRunConfig(
                cache_mode="bypass",
                capture_network_requests=True,
            ),
        )
        assert result.success
        assert result.network_requests is not None

        successful = [
            r for r in result.network_requests if r.get("event_type") == "response"
        ]

        # CSS should be blocked (via avoid_css)
        css_hits = [r for r in successful if ".css" in r.get("url", "")]
        assert len(css_hits) == 0, "CSS should be blocked by avoid_css"

        # Images should be blocked (via text_mode)
        img_exts = (".jpg", ".jpeg", ".png", ".gif", ".webp")
        img_hits = [
            r
            for r in successful
            if any(r.get("url", "").lower().endswith(ext) for ext in img_exts)
        ]
        assert len(img_hits) == 0, "Images should be blocked by text_mode"
