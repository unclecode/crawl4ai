"""The default chromium channel is skipped on Windows only (#2382).

On Windows, channel="chromium" makes Playwright look for a system Chrome, so
it is left out there. Elsewhere it must be passed, otherwise Playwright
launches chrome-headless-shell instead of the full Chromium.
"""

import pytest

from crawl4ai import BrowserConfig
from crawl4ai.browser_manager import BrowserManager


def _channel(monkeypatch, platform, **config):
    monkeypatch.setattr("crawl4ai.browser_manager.sys.platform", platform)
    return BrowserManager(browser_config=BrowserConfig(**config))._build_browser_args().get("channel")


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_default_channel_is_passed_outside_windows(monkeypatch, platform):
    assert _channel(monkeypatch, platform) == "chromium"


def test_default_channel_is_skipped_on_windows(monkeypatch):
    assert _channel(monkeypatch, "win32") is None


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_explicit_channel_is_passed_everywhere(monkeypatch, platform):
    assert _channel(monkeypatch, platform, chrome_channel="chrome") == "chrome"
