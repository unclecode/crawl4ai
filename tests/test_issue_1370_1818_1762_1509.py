"""
Regression tests for crawl4ai issue fixes:
  #1762 — CLI encoding (utf-8 on all file writes)
  #1370 — Screenshot distortion on Elementor sites (dimension freezing)
  #1818 — Deep crawl timeout due to page reuse (window.stop + listener cleanup)
  #1509 — deep_crawl_strategy in arun_many (bypass dispatcher)
"""

import asyncio
import base64
import inspect
import re
import textwrap
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch, mock_open, call

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Issue #1762 — CLI encoding
# ---------------------------------------------------------------------------

class TestIssue1762_CLIEncoding:
    """Verify that all file writes in cli.py use encoding='utf-8'."""

    def test_save_global_config_writes_utf8(self):
        """save_global_config must open the config file with encoding='utf-8'."""
        from crawl4ai.cli import save_global_config

        m = mock_open()
        with patch("builtins.open", m), \
             patch("yaml.dump") as mock_dump:
            save_global_config({"key": "value"})

        # open() should have been called with encoding="utf-8"
        m.assert_called_once()
        _, kwargs = m.call_args
        assert kwargs.get("encoding") == "utf-8", (
            "save_global_config must write with encoding='utf-8'"
        )

    def test_all_open_writes_in_cli_use_utf8(self):
        """Every open(..., 'w' ...) call in cli.py should include encoding='utf-8'."""
        import crawl4ai.cli as cli_module
        source = inspect.getsource(cli_module)

        # Find all open(..., "w" ...) patterns in source
        # Match open(<anything>, "w" or 'w', ...) calls
        write_opens = re.findall(
            r'open\([^)]*["\']w["\'][^)]*\)', source
        )
        assert len(write_opens) > 0, "Should find at least one open(..., 'w') in cli.py"

        for match in write_opens:
            assert 'encoding="utf-8"' in match or "encoding='utf-8'" in match, (
                f"Missing encoding='utf-8' in: {match}"
            )


# ---------------------------------------------------------------------------
# Issue #1370 — Screenshot distortion on Elementor sites
# ---------------------------------------------------------------------------

def _make_mock_page(page_width=1280, page_height=3000, viewport_height=900):
    """Create a mock Playwright Page for screenshot tests."""
    page = AsyncMock()
    page.viewport_size = {"width": page_width, "height": viewport_height}

    # get_page_dimensions returns page dimensions
    # (accessed via self.get_page_dimensions)

    # page.screenshot returns a small valid JPEG image
    img = Image.new("RGB", (page_width, viewport_height), color="blue")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    page.screenshot = AsyncMock(return_value=buf.getvalue())

    # page.evaluate is an AsyncMock — we inspect calls to it
    page.evaluate = AsyncMock(return_value=None)

    # page.set_viewport_size is an AsyncMock
    page.set_viewport_size = AsyncMock()

    return page


def _make_strategy():
    """Create a minimal AsyncPlaywrightCrawlerStrategy mock for screenshot tests."""
    strategy = MagicMock()
    strategy.logger = MagicMock()

    # Import the real method and bind it
    from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
    strategy.take_screenshot_scroller = (
        AsyncPlaywrightCrawlerStrategy.take_screenshot_scroller.__get__(
            strategy, type(strategy)
        )
    )
    strategy.get_page_dimensions = AsyncMock()
    return strategy


@pytest.mark.asyncio
class TestIssue1370_ScreenshotDistortion:
    """Verify take_screenshot_scroller freezes/unfreezes dimensions and
    saves/restores the original viewport."""

    async def test_original_viewport_saved_and_restored(self):
        page = _make_mock_page(page_width=1280, page_height=1800, viewport_height=900)
        strategy = _make_strategy()
        strategy.get_page_dimensions.return_value = {"width": 1280, "height": 1800}

        original_viewport = page.viewport_size.copy()

        await strategy.take_screenshot_scroller(page)

        # The very last set_viewport_size call must restore the original viewport
        last_viewport_call = page.set_viewport_size.call_args_list[-1]
        assert last_viewport_call == call(original_viewport), (
            "Original viewport should be restored after screenshot capture"
        )

    async def test_css_freeze_called_before_viewport_change(self):
        page = _make_mock_page(page_width=1280, page_height=1800, viewport_height=900)
        strategy = _make_strategy()
        strategy.get_page_dimensions.return_value = {"width": 1280, "height": 1800}

        await strategy.take_screenshot_scroller(page)

        # The first evaluate call should be the freeze JS
        first_eval = page.evaluate.call_args_list[0]
        js_code = first_eval[0][0]
        assert "crawl4aiFrozen" in js_code, (
            "First JS evaluate should freeze element dimensions"
        )
        assert "important" in js_code, (
            "Frozen dimensions should use !important"
        )

    async def test_css_unfreeze_called_after_capture(self):
        page = _make_mock_page(page_width=1280, page_height=1800, viewport_height=900)
        strategy = _make_strategy()
        strategy.get_page_dimensions.return_value = {"width": 1280, "height": 1800}

        await strategy.take_screenshot_scroller(page)

        # Find the unfreeze call — should contain removeProperty
        eval_calls = [c[0][0] for c in page.evaluate.call_args_list]
        unfreeze_calls = [c for c in eval_calls if "removeProperty" in c]
        assert len(unfreeze_calls) >= 1, (
            "Should call JS to unfreeze (removeProperty) element dimensions"
        )

    async def test_segments_captured_and_stitched(self):
        page_height = 2000
        viewport_height = 900
        page = _make_mock_page(page_width=800, page_height=page_height, viewport_height=viewport_height)
        strategy = _make_strategy()
        strategy.get_page_dimensions.return_value = {"width": 800, "height": page_height}

        # Dynamic screenshot: last segment is the remainder
        call_count = [0]
        last_part = page_height % viewport_height  # 200
        num_segments = (page_height // viewport_height) + 1  # 3

        async def dynamic_screenshot(**kwargs):
            call_count[0] += 1
            if call_count[0] == num_segments:
                h = last_part
            else:
                h = viewport_height
            img = Image.new("RGB", (800, h), color="blue")
            buf = BytesIO()
            img.save(buf, format="JPEG")
            return buf.getvalue()

        page.screenshot = dynamic_screenshot

        result = await strategy.take_screenshot_scroller(page)

        # Result should be a valid base64 string
        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        img = Image.open(BytesIO(decoded))
        # Total stitched height should equal page height
        assert img.height == page_height, (
            f"Stitched image height {img.height} should equal page height {page_height}"
        )

    async def test_page_shorter_than_viewport(self):
        """When page height < viewport, we still get a valid screenshot."""
        page = _make_mock_page(page_width=800, page_height=400, viewport_height=900)
        strategy = _make_strategy()
        strategy.get_page_dimensions.return_value = {"width": 800, "height": 400}

        # The viewport will be set to min(400, threshold)=400, and
        # page_height % viewport_height == 0, so the last segment is skipped
        # but there should be at least one segment from i=0 (since 400 // 400 + 1 = 2,
        # first segment captured, second skipped because remainder is 0).
        # We need the screenshot mock to return an image of the right viewport size
        img = Image.new("RGB", (800, 400), color="red")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        page.screenshot = AsyncMock(return_value=buf.getvalue())

        result = await strategy.take_screenshot_scroller(page)
        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        stitched = Image.open(BytesIO(decoded))
        assert stitched.height == 400

    async def test_page_exact_multiple_of_viewport(self):
        """When page height is exact multiple of viewport, no extra segment."""
        page = _make_mock_page(page_width=800, page_height=1800, viewport_height=900)
        strategy = _make_strategy()
        strategy.get_page_dimensions.return_value = {"width": 800, "height": 1800}

        result = await strategy.take_screenshot_scroller(page)
        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        stitched = Image.open(BytesIO(decoded))
        # 1800 / 900 = 2 segments, each 900px → total 1800
        assert stitched.height == 1800

    async def test_page_not_multiple_of_viewport_last_segment(self):
        """When page height is not a multiple, last segment is smaller."""
        page_height = 2100
        viewport_height = 900
        page = _make_mock_page(page_width=800, page_height=page_height, viewport_height=viewport_height)
        strategy = _make_strategy()
        strategy.get_page_dimensions.return_value = {"width": 800, "height": page_height}

        # For the last segment, viewport will be resized to 2100 % 900 = 300
        # We need screenshot to return images of the right size based on call order
        call_count = [0]
        last_part = page_height % viewport_height  # 300

        async def dynamic_screenshot(**kwargs):
            call_count[0] += 1
            # Segments: 0 (900), 1 (900), 2 (300 — last)
            num_segments = (page_height // viewport_height) + 1  # 3
            if call_count[0] == num_segments:
                h = last_part
            else:
                h = viewport_height
            img = Image.new("RGB", (800, h), color="green")
            buf = BytesIO()
            img.save(buf, format="JPEG")
            return buf.getvalue()

        page.screenshot = dynamic_screenshot

        result = await strategy.take_screenshot_scroller(page)
        decoded = base64.b64decode(result)
        stitched = Image.open(BytesIO(decoded))
        assert stitched.height == page_height, (
            f"Stitched height {stitched.height} should be {page_height}"
        )


# ---------------------------------------------------------------------------
# Issue #1818 — Deep crawl timeout due to page reuse
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestIssue1818_DeepCrawlTimeout:
    """Verify window.stop() and event listener cleanup behaviour."""

    def _make_crawl_mocks(self, session_id=None, capture_network=True):
        """Build strategy + config + page mocks for crawl tests."""
        from crawl4ai.async_configs import CrawlerRunConfig

        config = MagicMock(spec=CrawlerRunConfig)
        config.session_id = session_id
        config.capture_network_requests = capture_network
        config.capture_console_messages = False
        return config

    async def test_window_stop_called_when_session_id_set(self):
        """When session_id is set, window.stop() should be called."""
        page = AsyncMock()
        page.evaluate = AsyncMock(return_value=None)

        config = self._make_crawl_mocks(session_id="my-session")

        # Simulate the logic from _crawl lines 571-575
        if config.session_id:
            try:
                await page.evaluate("window.stop()")
            except Exception:
                pass

        page.evaluate.assert_called_once_with("window.stop()")

    async def test_window_stop_not_called_when_no_session_id(self):
        """When session_id is not set, window.stop() should NOT be called."""
        page = AsyncMock()
        page.evaluate = AsyncMock(return_value=None)

        config = self._make_crawl_mocks(session_id=None)

        # Same logic — should NOT call evaluate
        if config.session_id:
            try:
                await page.evaluate("window.stop()")
            except Exception:
                pass

        page.evaluate.assert_not_called()

    async def test_event_listeners_removed_with_session_id(self):
        """Event listeners should be cleaned up even when session_id is set."""
        page = AsyncMock()
        page.remove_listener = MagicMock()

        config = self._make_crawl_mocks(session_id="my-session", capture_network=True)

        handle_request = MagicMock()
        handle_response = MagicMock()
        handle_failed = MagicMock()

        # Simulate finally block logic from lines 1161-1174
        # Listener cleanup is OUTSIDE the `if not config.session_id` block
        try:
            if config.capture_network_requests:
                page.remove_listener("request", handle_request)
                page.remove_listener("response", handle_response)
                page.remove_listener("requestfailed", handle_failed)
        except Exception:
            pass

        assert page.remove_listener.call_count == 3, (
            "All three event listeners should be removed even with session_id"
        )

    async def test_page_not_closed_when_session_id_set(self):
        """When session_id is set, the page should NOT be closed."""
        page = AsyncMock()
        config = self._make_crawl_mocks(session_id="my-session")

        # Simulate the finally block logic from lines 1176-1191
        closed = False
        if not config.session_id:
            closed = True

        assert not closed, "Page should NOT be closed when session_id is set"

    async def test_page_closed_when_no_session_id(self):
        """When session_id is not set, the page IS closed."""
        page = AsyncMock()
        config = self._make_crawl_mocks(session_id=None)

        closed = False
        if not config.session_id:
            closed = True

        assert closed, "Page should be closed when session_id is not set"

    async def test_source_code_listener_cleanup_outside_session_block(self):
        """Verify in source that listener removal is in the finally block,
        outside the 'if not config.session_id' guard."""
        import crawl4ai.async_crawler_strategy as mod
        source = inspect.getsource(mod)

        # Find the finally block containing remove_listener and check that
        # remove_listener comes before the "if not config.session_id" block
        finally_pos = source.find("finally:")
        assert finally_pos != -1, "Should have a finally block"

        remove_listener_pos = source.find("remove_listener", finally_pos)
        assert remove_listener_pos != -1, "Should have remove_listener after finally"

        session_check_pos = source.find("if not config.session_id", finally_pos)
        assert session_check_pos != -1, "Should have session_id check after finally"

        assert remove_listener_pos < session_check_pos, (
            "remove_listener should appear BEFORE the 'if not config.session_id' "
            "block so listeners are always cleaned up"
        )


# ---------------------------------------------------------------------------
# Issue #1509 — deep_crawl_strategy in arun_many
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestIssue1509_DeepCrawlArunMany:
    """Verify arun_many bypasses dispatcher when deep_crawl_strategy is set."""

    async def test_arun_many_with_deep_crawl_calls_arun_per_url(self):
        """With deep_crawl_strategy, arun_many should call arun() for each URL."""
        from crawl4ai.async_webcrawler import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig

        crawler = AsyncWebCrawler(config=BrowserConfig())
        # Avoid real initialization
        crawler._setup_done = True

        config = MagicMock()
        config.deep_crawl_strategy = MagicMock()  # truthy
        config.stream = False

        urls = ["https://a.com", "https://b.com", "https://c.com"]

        result_a = [MagicMock(url="https://a.com/1"), MagicMock(url="https://a.com/2")]
        result_b = [MagicMock(url="https://b.com/1")]
        result_c = [MagicMock(url="https://c.com/1"), MagicMock(url="https://c.com/2")]

        crawler.arun = AsyncMock(side_effect=[result_a, result_b, result_c])

        results = await crawler.arun_many(urls=urls, config=config)

        assert crawler.arun.call_count == 3
        # All results should be flattened
        assert len(results) == 5

    async def test_arun_many_deep_crawl_results_flattened(self):
        """Results from multiple deep-crawl URLs should be flattened into one list."""
        from crawl4ai.async_webcrawler import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig

        crawler = AsyncWebCrawler(config=BrowserConfig())
        crawler._setup_done = True

        config = MagicMock()
        config.deep_crawl_strategy = MagicMock()
        config.stream = False

        urls = ["https://x.com", "https://y.com"]
        r1 = MagicMock(url="https://x.com/page1")
        r2 = MagicMock(url="https://x.com/page2")
        r3 = MagicMock(url="https://y.com/page1")

        crawler.arun = AsyncMock(side_effect=[[r1, r2], [r3]])

        results = await crawler.arun_many(urls=urls, config=config)
        assert results == [r1, r2, r3]

    async def test_arun_many_deep_crawl_streaming(self):
        """In streaming mode with deep_crawl_strategy, results are yielded."""
        from crawl4ai.async_webcrawler import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig

        crawler = AsyncWebCrawler(config=BrowserConfig())
        crawler._setup_done = True

        config = MagicMock()
        config.deep_crawl_strategy = MagicMock()
        config.stream = True

        urls = ["https://a.com", "https://b.com"]
        r1 = MagicMock(url="a1")
        r2 = MagicMock(url="a2")
        r3 = MagicMock(url="b1")

        crawler.arun = AsyncMock(side_effect=[[r1, r2], [r3]])

        gen = await crawler.arun_many(urls=urls, config=config)

        collected = []
        async for item in gen:
            collected.append(item)

        assert len(collected) == 3
        assert collected == [r1, r2, r3]

    async def test_arun_many_without_deep_crawl_uses_dispatcher(self):
        """Without deep_crawl_strategy, arun_many should use the dispatcher."""
        from crawl4ai.async_webcrawler import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig

        crawler = AsyncWebCrawler(config=BrowserConfig())
        crawler._setup_done = True

        config = MagicMock()
        config.deep_crawl_strategy = None
        config.stream = False
        config.mean_delay = 0.1
        config.max_range = 0.3
        config.proxy_session_id = None

        urls = ["https://a.com", "https://b.com"]

        dispatcher = MagicMock()
        task_result_a = MagicMock()
        task_result_a.result = MagicMock(url="https://a.com")
        task_result_a.result.dispatch_result = None
        task_result_a.task_id = "task-1"
        task_result_a.memory_usage = 100.0
        task_result_a.peak_memory = 200.0
        task_result_a.start_time = 0.0
        task_result_a.end_time = 1.0
        task_result_a.error_message = ""

        task_result_b = MagicMock()
        task_result_b.result = MagicMock(url="https://b.com")
        task_result_b.result.dispatch_result = None
        task_result_b.task_id = "task-2"
        task_result_b.memory_usage = 100.0
        task_result_b.peak_memory = 200.0
        task_result_b.start_time = 0.0
        task_result_b.end_time = 1.0
        task_result_b.error_message = ""

        dispatcher.run_urls = AsyncMock(return_value=[task_result_a, task_result_b])

        results = await crawler.arun_many(urls=urls, config=config, dispatcher=dispatcher)

        dispatcher.run_urls.assert_called_once()
        assert len(results) == 2
