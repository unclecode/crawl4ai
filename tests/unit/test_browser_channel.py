"""Default chromium channel (#2382).

channel="chromium" launches the bundled full Chromium. Without it, headless
Playwright launches chrome-headless-shell, which behaves differently. When full
Chromium can't start, the launch falls back to the shell instead of failing.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from crawl4ai import BrowserConfig
from crawl4ai.browser_manager import BrowserManager


def _manager(**config):
    return BrowserManager(browser_config=BrowserConfig(**config), logger=MagicMock())


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_default_channel_is_passed(monkeypatch, platform):
    monkeypatch.setattr("crawl4ai.browser_manager.sys.platform", platform)
    assert _manager()._build_browser_args()["channel"] == "chromium"


def test_explicit_channel_is_passed():
    assert _manager(chrome_channel="chrome")._build_browser_args()["channel"] == "chrome"


@pytest.mark.parametrize("browser_type", ["firefox", "webkit"])
def test_no_channel_for_other_browsers(browser_type):
    assert "channel" not in _manager(browser_type=browser_type)._build_browser_args()


@pytest.mark.asyncio
async def test_launch_uses_full_chromium_when_it_starts():
    manager = _manager()
    manager.playwright = MagicMock()
    manager.playwright.chromium.launch = AsyncMock(return_value="browser")

    assert await manager._launch_chromium({"headless": True, "channel": "chromium"}) == "browser"
    manager.playwright.chromium.launch.assert_awaited_once_with(headless=True, channel="chromium")
    manager.logger.warning.assert_not_called()


@pytest.mark.asyncio
async def test_launch_falls_back_to_shell_when_full_chromium_fails():
    manager = _manager()
    manager.playwright = MagicMock()
    manager.playwright.chromium.launch = AsyncMock(
        side_effect=[Exception("Executable doesn't exist at /x/chromium-1179"), "shell"]
    )

    assert await manager._launch_chromium({"headless": True, "channel": "chromium"}) == "shell"
    assert manager.playwright.chromium.launch.await_args_list[1].kwargs == {"headless": True}
    manager.logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test_launch_does_not_fall_back_for_explicit_channel():
    manager = _manager()
    manager.playwright = MagicMock()
    manager.playwright.chromium.launch = AsyncMock(side_effect=Exception("chrome not found"))

    with pytest.raises(Exception, match="chrome not found"):
        await manager._launch_chromium({"headless": True, "channel": "chrome"})
    manager.playwright.chromium.launch.assert_awaited_once()
