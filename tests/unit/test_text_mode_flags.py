"""text_mode must not pass --disable-javascript to Chromium.

Chromium has no --disable-javascript switch and ignores it, so text_mode never
disabled scripting; the entry only suggested it did. Turning JavaScript off is
BrowserConfig(java_script_enabled=False), which sets it on the browser context.

These are flag-construction checks only; no browser or network required.
"""

from crawl4ai import BrowserConfig
from crawl4ai.browser_manager import BrowserManager, ManagedBrowser


def _text_mode_flag_sets():
    config = BrowserConfig(headless=True, text_mode=True)
    return (
        ManagedBrowser.build_browser_flags(config),
        BrowserManager(browser_config=config)._build_browser_args()["args"],
    )


def test_text_mode_omits_the_dead_disable_javascript_switch():
    for flags in _text_mode_flag_sets():
        assert "--disable-javascript" not in flags


def test_text_mode_keeps_the_switches_that_take_effect():
    for flags in _text_mode_flag_sets():
        assert "--blink-settings=imagesEnabled=false" in flags
        assert "--disable-remote-fonts" in flags
