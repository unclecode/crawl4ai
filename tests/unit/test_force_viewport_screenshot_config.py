"""Viewport-only screenshot settings must survive configuration cloning."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from crawl4ai import CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy


def test_force_viewport_screenshot_defaults_to_false():
    config = CrawlerRunConfig()

    assert config.force_viewport_screenshot is False
    assert config.clone().force_viewport_screenshot is False


@pytest.mark.parametrize("force_viewport", [False, True])
def test_force_viewport_screenshot_to_dict(force_viewport):
    config = CrawlerRunConfig(force_viewport_screenshot=force_viewport)

    assert config.to_dict()["force_viewport_screenshot"] is force_viewport


@pytest.mark.parametrize("force_viewport", [False, True])
def test_force_viewport_screenshot_from_kwargs(force_viewport):
    config = CrawlerRunConfig.from_kwargs({"force_viewport_screenshot": force_viewport})

    assert config.force_viewport_screenshot is force_viewport


@pytest.mark.parametrize("force_viewport", [False, True])
def test_force_viewport_screenshot_dict_roundtrip(force_viewport):
    config = CrawlerRunConfig(force_viewport_screenshot=force_viewport)
    restored = CrawlerRunConfig.from_kwargs(config.to_dict())

    assert restored.force_viewport_screenshot is force_viewport


@pytest.mark.parametrize("updates", [{}, {"stream": True}])
def test_clone_preserves_force_viewport_screenshot(updates):
    config = CrawlerRunConfig(force_viewport_screenshot=True)
    cloned = config.clone(**updates)

    assert cloned is not config
    assert cloned.force_viewport_screenshot is True
    assert cloned.stream is updates.get("stream", False)
    assert config.force_viewport_screenshot is True
    assert config.stream is False


def test_clone_can_disable_force_viewport_screenshot():
    config = CrawlerRunConfig(force_viewport_screenshot=True)
    cloned = config.clone(force_viewport_screenshot=False)

    assert cloned.force_viewport_screenshot is False
    assert config.force_viewport_screenshot is True


@pytest.mark.asyncio
async def test_cloned_config_keeps_viewport_screenshot_when_scanning_full_page():
    config = CrawlerRunConfig(
        screenshot=True,
        scan_full_page=True,
        force_viewport_screenshot=True,
    ).clone(stream=True)
    strategy = object.__new__(AsyncPlaywrightCrawlerStrategy)
    strategy.take_screenshot_naive = AsyncMock(return_value="viewport")
    strategy.take_screenshot_scroller = AsyncMock(return_value="full-page")
    strategy.page_need_scroll = AsyncMock(return_value=True)
    page = MagicMock()

    result = await strategy.take_screenshot(
        page,
        screenshot_height_threshold=config.screenshot_height_threshold,
        force_viewport_screenshot=config.force_viewport_screenshot,
        scan_full_page=config.scan_full_page,
        scroll_delay=config.scroll_delay,
    )

    assert result == "viewport"
    strategy.take_screenshot_naive.assert_awaited_once_with(page)
    strategy.take_screenshot_scroller.assert_not_awaited()
    strategy.page_need_scroll.assert_not_awaited()
