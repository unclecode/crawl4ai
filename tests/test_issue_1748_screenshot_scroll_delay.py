"""
Tests for GitHub issue #1748: scroll_delay config is now properly respected
in take_screenshot_scroller().

Three changes were made to async_crawler_strategy.py:
  A) arun call site now passes scroll_delay from config
  B) _generate_media_from_html call site now passes scroll_delay from config
  C) take_screenshot_scroller reads scroll_delay from kwargs (was hardcoded 0.01)

These tests verify that all three paths correctly forward and use scroll_delay.
"""

import pytest
import asyncio
import base64
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch, call

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tiny_jpeg() -> bytes:
    """Create a minimal valid JPEG image for mock screenshot returns."""
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="red")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


TINY_JPEG = _make_tiny_jpeg()

# A tall HTML page that exceeds any reasonable screenshot_height_threshold
TALL_HTML = "<html><body>" + "<p>Line of content</p>" * 200 + "</body></html>"


def _make_mock_page(viewport_width=1280, viewport_height=200):
    """Create a mock Playwright page with the essentials for take_screenshot_scroller."""
    page = MagicMock()
    page.viewport_size = {"width": viewport_width, "height": viewport_height}
    page.set_viewport_size = AsyncMock()
    page.evaluate = AsyncMock(return_value=None)
    page.screenshot = AsyncMock(return_value=TINY_JPEG)
    return page


# ---------------------------------------------------------------------------
# Test 1 — Unit: scroll_delay extracted from kwargs correctly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scroll_delay_custom_value_used():
    """
    When scroll_delay=1.5 is passed in kwargs, asyncio.sleep must be called
    with 1.5 — NOT with the old hardcoded 0.01.
    """
    strategy = AsyncPlaywrightCrawlerStrategy.__new__(AsyncPlaywrightCrawlerStrategy)
    # Minimal attributes needed by take_screenshot_scroller
    strategy.logger = MagicMock()
    strategy.adapter = MagicMock()

    page = _make_mock_page()

    # get_page_dimensions returns a page taller than the viewport
    strategy.get_page_dimensions = AsyncMock(
        return_value={"width": 1280, "height": 600}
    )

    with patch(
        "crawl4ai.async_crawler_strategy.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        result = await strategy.take_screenshot_scroller(
            page, scroll_delay=1.5, screenshot_height_threshold=100
        )

    # asyncio.sleep must have been called with our custom value
    sleep_args = [c.args[0] for c in mock_sleep.call_args_list]
    assert 1.5 in sleep_args, (
        f"Expected asyncio.sleep(1.5) but got calls with: {sleep_args}"
    )
    # The old hardcoded 0.01 must NOT appear
    assert 0.01 not in sleep_args, (
        f"Old hardcoded 0.01 still present in sleep calls: {sleep_args}"
    )
    # Should return a base64-encoded string
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Test 2 — Unit: default scroll_delay is 0.2 when not provided
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scroll_delay_default_value():
    """
    When scroll_delay is NOT provided in kwargs, asyncio.sleep must be called
    with 0.2 (the correct default), NOT 0.01.
    """
    strategy = AsyncPlaywrightCrawlerStrategy.__new__(AsyncPlaywrightCrawlerStrategy)
    strategy.logger = MagicMock()
    strategy.adapter = MagicMock()

    page = _make_mock_page()

    strategy.get_page_dimensions = AsyncMock(
        return_value={"width": 1280, "height": 600}
    )

    with patch(
        "crawl4ai.async_crawler_strategy.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        result = await strategy.take_screenshot_scroller(
            page, screenshot_height_threshold=100
        )

    sleep_args = [c.args[0] for c in mock_sleep.call_args_list]
    assert 0.2 in sleep_args, (
        f"Expected default asyncio.sleep(0.2) but got calls with: {sleep_args}"
    )
    assert 0.01 not in sleep_args, (
        f"Old hardcoded 0.01 still present in sleep calls: {sleep_args}"
    )
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Test 3 — Unit: take_screenshot forwards scroll_delay to take_screenshot_scroller
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_take_screenshot_forwards_scroll_delay():
    """
    When take_screenshot is called with scroll_delay=2.5 in kwargs and the page
    needs scrolling, it must pass that value through to take_screenshot_scroller.
    """
    strategy = AsyncPlaywrightCrawlerStrategy.__new__(AsyncPlaywrightCrawlerStrategy)
    strategy.logger = MagicMock()
    strategy.adapter = MagicMock()

    page = _make_mock_page()

    # page_need_scroll returns True so the scroller path is taken
    strategy.page_need_scroll = AsyncMock(return_value=True)
    strategy.take_screenshot_scroller = AsyncMock(return_value="base64data")

    await strategy.take_screenshot(page, scroll_delay=2.5)

    # Verify take_screenshot_scroller was called with scroll_delay in kwargs
    strategy.take_screenshot_scroller.assert_called_once()
    call_kwargs = strategy.take_screenshot_scroller.call_args
    # kwargs are passed through via **kwargs
    assert call_kwargs.kwargs.get("scroll_delay") == 2.5 or (
        len(call_kwargs.args) > 1 and False
    ), f"scroll_delay=2.5 not forwarded. Call was: {call_kwargs}"


# ---------------------------------------------------------------------------
# Test 4 — Integration: full-page screenshot with custom scroll_delay
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_integration_arun_respects_scroll_delay():
    """
    End-to-end: use AsyncWebCrawler with a raw: tall HTML page and a very low
    screenshot_height_threshold to force the scroller path. Verify asyncio.sleep
    is called with the configured scroll_delay, not 0.01.
    """
    config = CrawlerRunConfig(
        screenshot=True,
        scroll_delay=0.5,
        screenshot_height_threshold=100,  # Very low to force scroller
    )

    with patch(
        "crawl4ai.async_crawler_strategy.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(f"raw:{TALL_HTML}", config=config)

    assert result.success, f"Crawl failed: {result.error_message}"
    assert result.screenshot is not None, "Expected screenshot data"

    # Check that our custom scroll_delay was used during screenshot capture
    sleep_args = [c.args[0] for c in mock_sleep.call_args_list]
    assert 0.5 in sleep_args, (
        f"Expected asyncio.sleep(0.5) in screenshot capture but got: {sleep_args}"
    )
    assert 0.01 not in sleep_args, (
        f"Old hardcoded 0.01 still present in sleep calls: {sleep_args}"
    )


# ---------------------------------------------------------------------------
# Test 5 — Integration: _generate_media_from_html respects scroll_delay
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_integration_generate_media_respects_scroll_delay():
    """
    Call _generate_media_from_html directly with a config that has
    scroll_delay=0.75 and screenshot=True. Verify asyncio.sleep is called
    with 0.75 during screenshot capture.
    """
    config = CrawlerRunConfig(
        screenshot=True,
        scroll_delay=0.75,
        screenshot_height_threshold=100,  # Very low to force scroller
    )

    with patch(
        "crawl4ai.async_crawler_strategy.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        async with AsyncWebCrawler() as crawler:
            (
                screenshot_data,
                pdf_data,
                mhtml_data,
            ) = await crawler.crawler_strategy._generate_media_from_html(
                TALL_HTML, config
            )

    assert screenshot_data is not None, (
        "Expected screenshot data from _generate_media_from_html"
    )

    sleep_args = [c.args[0] for c in mock_sleep.call_args_list]
    assert 0.75 in sleep_args, f"Expected asyncio.sleep(0.75) but got: {sleep_args}"
    assert 0.01 not in sleep_args, (
        f"Old hardcoded 0.01 still present in sleep calls: {sleep_args}"
    )


# ---------------------------------------------------------------------------
# Test 6 — Unit: CrawlerRunConfig default scroll_delay is 0.2
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crawler_run_config_default_scroll_delay():
    """CrawlerRunConfig.scroll_delay defaults to 0.2."""
    config = CrawlerRunConfig()
    assert config.scroll_delay == 0.2, (
        f"Expected default scroll_delay=0.2, got {config.scroll_delay}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
