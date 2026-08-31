"""
Tests for issue #1750: Screenshot size should respect scan_full_page setting.

When scan_full_page=False, screenshots should capture only the viewport,
not the entire scrollable page.
"""

import asyncio
import base64
import pytest
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_image_dimensions(screenshot_b64: str) -> tuple:
    """Decode a base64 screenshot and return (width, height)."""
    from PIL import Image
    img_data = base64.b64decode(screenshot_b64)
    img = Image.open(BytesIO(img_data))
    return img.width, img.height


# ---------------------------------------------------------------------------
# Unit tests (mock-based, no browser needed)
# ---------------------------------------------------------------------------

class TestTakeScreenshotRouting:
    """Unit tests for take_screenshot routing logic."""

    @pytest.fixture
    def strategy(self):
        """Create a minimal AsyncPlaywrightCrawlerStrategy with mocked methods."""
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        s = object.__new__(AsyncPlaywrightCrawlerStrategy)
        s.logger = MagicMock()
        s.take_screenshot_naive = AsyncMock(return_value="naive_b64")
        s.take_screenshot_scroller = AsyncMock(return_value="scroller_b64")
        s.page_need_scroll = AsyncMock(return_value=True)
        return s

    @pytest.mark.asyncio
    async def test_scan_full_page_false_uses_naive(self, strategy):
        """scan_full_page=False should always use viewport (naive) screenshot."""
        page = MagicMock()
        result = await strategy.take_screenshot(page, scan_full_page=False)
        assert result == "naive_b64"
        strategy.take_screenshot_naive.assert_awaited_once_with(page)
        strategy.take_screenshot_scroller.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_scan_full_page_true_scrollable_uses_scroller(self, strategy):
        """scan_full_page=True on a scrollable page should use scroller."""
        page = MagicMock()
        result = await strategy.take_screenshot(page, scan_full_page=True)
        assert result == "scroller_b64"
        strategy.take_screenshot_scroller.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_scan_full_page_true_short_page_uses_naive(self, strategy):
        """scan_full_page=True on a short page should still use naive."""
        strategy.page_need_scroll = AsyncMock(return_value=False)
        page = MagicMock()
        result = await strategy.take_screenshot(page, scan_full_page=True)
        assert result == "naive_b64"

    @pytest.mark.asyncio
    async def test_default_scan_full_page_is_true(self, strategy):
        """When scan_full_page is not passed, default to True (full page)."""
        page = MagicMock()
        result = await strategy.take_screenshot(page)
        # Should go to scroller since page_need_scroll=True and default is True
        assert result == "scroller_b64"

    @pytest.mark.asyncio
    async def test_force_viewport_overrides_scan_full_page_true(self, strategy):
        """force_viewport_screenshot=True should use naive even with scan_full_page=True."""
        page = MagicMock()
        result = await strategy.take_screenshot(
            page, force_viewport_screenshot=True, scan_full_page=True
        )
        assert result == "naive_b64"

    @pytest.mark.asyncio
    async def test_scan_full_page_false_on_short_page(self, strategy):
        """scan_full_page=False on a short page should use naive (no regression)."""
        strategy.page_need_scroll = AsyncMock(return_value=False)
        page = MagicMock()
        result = await strategy.take_screenshot(page, scan_full_page=False)
        assert result == "naive_b64"

    @pytest.mark.asyncio
    async def test_scan_full_page_false_does_not_call_page_need_scroll(self, strategy):
        """When scan_full_page=False, we should skip the scroll check entirely."""
        page = MagicMock()
        await strategy.take_screenshot(page, scan_full_page=False)
        strategy.page_need_scroll.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_force_viewport_false_scan_full_page_false(self, strategy):
        """force_viewport=False + scan_full_page=False should still use naive."""
        page = MagicMock()
        result = await strategy.take_screenshot(
            page, force_viewport_screenshot=False, scan_full_page=False
        )
        assert result == "naive_b64"


# ---------------------------------------------------------------------------
# Integration tests (real browser)
# ---------------------------------------------------------------------------

TALL_PAGE_HTML = """
<html>
<body style="margin:0; padding:0;">
<div style="width:100%; height:5000px; background: linear-gradient(red, blue);">
    <h1>Tall page for screenshot testing</h1>
</div>
</body>
</html>
"""

SHORT_PAGE_HTML = """
<html>
<body style="margin:0; padding:0;">
<div style="width:100%; height:200px; background: green;">
    <h1>Short page</h1>
</div>
</body>
</html>
"""


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestScreenshotIntegration:
    """Integration tests using real browser with raw:// HTML pages."""

    VIEWPORT_W = 800
    VIEWPORT_H = 600

    @pytest.fixture(scope="class")
    def browser_config(self):
        return BrowserConfig(
            viewport_width=self.VIEWPORT_W,
            viewport_height=self.VIEWPORT_H,
            headless=True,
        )

    @pytest.mark.asyncio
    async def test_tall_page_scan_full_page_false(self, browser_config):
        """Tall page + scan_full_page=False -> viewport-sized screenshot."""
        config = CrawlerRunConfig(screenshot=True, scan_full_page=False)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw://{TALL_PAGE_HTML}", config=config)
        assert result.screenshot is not None
        w, h = get_image_dimensions(result.screenshot)
        assert w == self.VIEWPORT_W
        assert h == self.VIEWPORT_H, (
            f"Expected viewport height {self.VIEWPORT_H}, got {h}"
        )

    @pytest.mark.asyncio
    async def test_tall_page_scan_full_page_true(self, browser_config):
        """Tall page + scan_full_page=True -> full page screenshot (taller than viewport)."""
        config = CrawlerRunConfig(screenshot=True, scan_full_page=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw://{TALL_PAGE_HTML}", config=config)
        assert result.screenshot is not None
        w, h = get_image_dimensions(result.screenshot)
        assert h > self.VIEWPORT_H, (
            f"Expected full-page screenshot taller than {self.VIEWPORT_H}, got {h}"
        )

    @pytest.mark.asyncio
    async def test_tall_page_default_scan_full_page(self, browser_config):
        """Default config (scan_full_page=False by default) -> viewport-sized screenshot."""
        config = CrawlerRunConfig(screenshot=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw://{TALL_PAGE_HTML}", config=config)
        assert result.screenshot is not None
        w, h = get_image_dimensions(result.screenshot)
        # Default scan_full_page is False, so screenshot should be viewport-sized
        assert h == self.VIEWPORT_H

    @pytest.mark.asyncio
    async def test_short_page_scan_full_page_false(self, browser_config):
        """Short page + scan_full_page=False -> viewport-sized screenshot."""
        config = CrawlerRunConfig(screenshot=True, scan_full_page=False)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw://{SHORT_PAGE_HTML}", config=config)
        assert result.screenshot is not None
        w, h = get_image_dimensions(result.screenshot)
        assert h == self.VIEWPORT_H

    @pytest.mark.asyncio
    async def test_short_page_scan_full_page_true(self, browser_config):
        """Short page + scan_full_page=True -> should still be viewport-sized (no scroll needed)."""
        config = CrawlerRunConfig(screenshot=True, scan_full_page=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw://{SHORT_PAGE_HTML}", config=config)
        assert result.screenshot is not None
        w, h = get_image_dimensions(result.screenshot)
        # Short page doesn't need scrolling, so screenshot should be viewport-sized
        assert h <= self.VIEWPORT_H + 50  # small tolerance

    @pytest.mark.asyncio
    async def test_force_viewport_overrides_on_tall_page(self, browser_config):
        """force_viewport_screenshot=True should give viewport size even with scan_full_page=True."""
        config = CrawlerRunConfig(
            screenshot=True,
            scan_full_page=True,
            force_viewport_screenshot=True,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw://{TALL_PAGE_HTML}", config=config)
        assert result.screenshot is not None
        w, h = get_image_dimensions(result.screenshot)
        assert h == self.VIEWPORT_H

    @pytest.mark.asyncio
    async def test_screenshot_width_always_matches_viewport(self, browser_config):
        """Width should always match viewport regardless of scan_full_page setting."""
        for scan_full in [True, False]:
            config = CrawlerRunConfig(screenshot=True, scan_full_page=scan_full)
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=f"raw://{TALL_PAGE_HTML}", config=config)
            w, h = get_image_dimensions(result.screenshot)
            assert w == self.VIEWPORT_W, (
                f"scan_full_page={scan_full}: width {w} != viewport {self.VIEWPORT_W}"
            )

    @pytest.mark.asyncio
    async def test_no_screenshot_when_disabled(self, browser_config):
        """screenshot=False should return no screenshot regardless of scan_full_page."""
        config = CrawlerRunConfig(screenshot=False, scan_full_page=False)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw://{TALL_PAGE_HTML}", config=config)
        assert not result.screenshot
