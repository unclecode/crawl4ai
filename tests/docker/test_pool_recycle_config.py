"""The Docker pool must recycle its browser context by pages served (#2231).

The pool's janitor only closes *idle* browsers, so a server under sustained
load never recycles one. Recycling by page count is what bounds the context
state (cookies/localStorage/service workers) that slows navigation down.
"""
import sys
from pathlib import Path

import pytest
import yaml

from crawl4ai import BrowserConfig

CONFIG_PATH = Path(__file__).resolve().parents[2] / "deploy" / "docker" / "config.yml"


@pytest.fixture(scope="module")
def browser_section():
    return yaml.safe_load(CONFIG_PATH.read_text())["crawler"]["browser"]


def test_recycle_is_enabled(browser_section):
    kwargs = browser_section.get("kwargs", {})
    assert kwargs.get("max_pages_before_recycle", 0) > 0, (
        "deploy/docker/config.yml must set crawler.browser.kwargs."
        "max_pages_before_recycle > 0, otherwise pooled browser contexts are "
        "never recycled under sustained load (issue #2231)."
    )


def test_kwargs_reach_browser_config(browser_section):
    """server.py/api.py splat these kwargs straight into BrowserConfig."""
    cfg = BrowserConfig(
        extra_args=browser_section.get("extra_args", []),
        **browser_section.get("kwargs", {}),
    )
    assert cfg.max_pages_before_recycle > 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
