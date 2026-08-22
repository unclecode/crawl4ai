import asyncio
from unittest.mock import AsyncMock

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig
from crawl4ai.browser_manager import BrowserManager


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [RuntimeError("launch failed"), pytest.param(None, id="cancelled")])
async def test_browser_manager_stops_playwright_after_failed_launch(monkeypatch, failure):
    if failure is None:
        failure = asyncio.CancelledError()

    playwright = type("FakePlaywright", (), {})()
    playwright.stop = AsyncMock()
    starter = type("FakeStarter", (), {})()
    starter.start = AsyncMock(return_value=playwright)

    monkeypatch.setattr("playwright.async_api.async_playwright", lambda: starter)

    manager = BrowserManager(BrowserConfig(), logger=None)
    manager._launch_browser = AsyncMock(side_effect=failure)

    with pytest.raises(type(failure)):
        await manager.start()

    playwright.stop.assert_awaited_once()
    assert manager.playwright is None


@pytest.mark.asyncio
async def test_async_webcrawler_rolls_back_cancelled_strategy_start(tmp_path):
    class CancelledStrategy:
        def __init__(self):
            self.exit = AsyncMock()

        async def __aenter__(self):
            raise asyncio.CancelledError()

        async def __aexit__(self, exc_type, exc_value, traceback):
            await self.exit(exc_type, exc_value, traceback)

    strategy = CancelledStrategy()
    crawler = AsyncWebCrawler(crawler_strategy=strategy, base_directory=str(tmp_path))

    with pytest.raises(asyncio.CancelledError):
        await crawler.start()

    strategy.exit.assert_awaited_once_with(None, None, None)
    assert crawler.ready is False
