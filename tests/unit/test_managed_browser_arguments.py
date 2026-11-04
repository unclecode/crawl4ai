"""`ManagedBrowser` reads every setting off `browser_config`.

Without one, that raised `AttributeError: 'NoneType' object has no attribute
'browser_type'` for the documented all-arguments form, which is how
`BrowserProfiler.launch_builtin_browser` constructs it — so `crwl browser start`
and `crwl browser restart` could not start a browser at all.
"""

import pytest

from crawl4ai.async_configs import BrowserConfig
from crawl4ai.browser_manager import ManagedBrowser


def test_defaults_construct_without_a_config():
    browser = ManagedBrowser()

    assert browser.browser_type == "chromium"
    assert browser.debugging_port == 9222
    assert browser.host == "localhost"


def test_launch_builtin_browser_argument_shape_constructs():
    """The exact call `BrowserProfiler.launch_builtin_browser` makes."""
    browser = ManagedBrowser(
        browser_type="chromium",
        user_data_dir="/tmp/crawl4ai-builtin",
        headless=True,
        logger=None,
        debugging_port=9333,
    )

    assert browser.user_data_dir == "/tmp/crawl4ai-builtin"
    assert browser.debugging_port == 9333


@pytest.mark.parametrize(
    ("kwargs", "attribute", "expected"),
    [
        ({"browser_type": "firefox"}, "browser_type", "firefox"),
        ({"user_data_dir": "/tmp/profile"}, "user_data_dir", "/tmp/profile"),
        ({"headless": False}, "headless", False),
        ({"host": "0.0.0.0"}, "host", "0.0.0.0"),
        ({"debugging_port": 9333}, "debugging_port", 9333),
        ({"cdp_url": "http://localhost:9444"}, "cdp_url", "http://localhost:9444"),
    ],
)
def test_each_argument_reaches_the_instance(kwargs, attribute, expected):
    assert getattr(ManagedBrowser(**kwargs), attribute) == expected


def test_a_supplied_config_still_wins():
    """Existing callers pass both; the config is the source of truth and stays so."""
    config = BrowserConfig(browser_type="chromium", debugging_port=9222, headless=True)

    browser = ManagedBrowser(
        browser_type="firefox",
        debugging_port=9333,
        headless=False,
        browser_config=config,
    )

    assert browser.browser_type == "chromium"
    assert browser.debugging_port == 9222
    assert browser.headless is True
    assert browser.browser_config is config
