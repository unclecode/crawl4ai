"""Regression tests for crawl4ai issue #2493 (part: empty sec-ch-ua).

BrowserConfig(user_agent="") keeps the browser's native User-Agent, but
__init__ used to auto-add an empty "sec-ch-ua" header to every request.
An empty client-hints header must not be sent; a caller-provided value
must still be respected.
"""

from crawl4ai.async_configs import BrowserConfig


class TestEmptySecChUa:
    def test_empty_user_agent_adds_no_sec_ch_ua(self):
        config = BrowserConfig(user_agent="")
        assert config.browser_hint == ""
        assert "sec-ch-ua" not in config.headers

    def test_unparseable_user_agent_adds_no_sec_ch_ua(self):
        config = BrowserConfig(user_agent="MyBot/1.0")
        assert config.browser_hint == ""
        assert "sec-ch-ua" not in config.headers

    def test_default_user_agent_still_adds_sec_ch_ua(self):
        config = BrowserConfig()
        assert config.browser_hint != ""
        assert config.headers["sec-ch-ua"] == config.browser_hint

    def test_caller_provided_sec_ch_ua_is_respected(self):
        config = BrowserConfig(
            user_agent="",
            headers={"sec-ch-ua": '"Chromium";v="156"'},
        )
        assert config.headers["sec-ch-ua"] == '"Chromium";v="156"'
