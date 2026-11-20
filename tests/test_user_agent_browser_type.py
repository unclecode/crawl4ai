"""UserAgentGenerator.generate must honour browser_type (#2566).

Before the fix it ignored browser_type and picked a random browser stack, so
generate(browser_type="firefox") could return a Chrome user agent.
"""

import re

import pytest

from crawl4ai.user_agent_generator import UserAgentGenerator

# browser_type -> (browsers parse_user_agent must find, tokens the UA must end with)
EXPECTED = {
    "chrome": ({"chrome"}, r"AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/[\d.]+ Safari/537\.36$"),
    "edge": ({"chrome", "edge"}, r"AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/[\d.]+ Safari/537\.36 Edg/[\d.]+$"),
    "safari": ({"safari"}, r"AppleWebKit/605\.1\.15 \(KHTML, like Gecko\) Version/[\d.]+ Safari/605\.1\.15$"),
    "firefox": ({"firefox"}, r"Gecko/20100101 Firefox/[\d.]+$"),
}


@pytest.mark.parametrize("browser_type", EXPECTED)
def test_generate_returns_only_the_requested_browser(browser_type):
    generator = UserAgentGenerator()
    browsers, tail = EXPECTED[browser_type]

    for _ in range(50):
        ua = generator.generate(browser_type=browser_type)
        assert ua.startswith("Mozilla/5.0 (")
        assert re.search(tail, ua), ua
        assert set(generator.parse_user_agent(ua)) == browsers, ua


def test_edge_reports_the_matching_chromium_version():
    generator = UserAgentGenerator()

    for _ in range(20):
        browsers = generator.parse_user_agent(generator.generate(browser_type="edge"))
        assert browsers["chrome"] == browsers["edge"]


def test_client_hints_match_the_requested_browser():
    generator = UserAgentGenerator()

    assert '"Microsoft Edge"' in generator.generate_client_hints(generator.generate(browser_type="edge"))
    assert '"Google Chrome"' in generator.generate_client_hints(generator.generate(browser_type="chrome"))
    assert '"Safari"' in generator.generate_client_hints(generator.generate(browser_type="safari"))


def test_unknown_browser_type_is_rejected():
    with pytest.raises(ValueError):
        UserAgentGenerator().generate(browser_type="opera")


def test_no_browser_type_keeps_the_random_stack(monkeypatch):
    generator = UserAgentGenerator()
    monkeypatch.setattr(generator, "get_browser_stack", lambda num_browsers: ["Firefox/119.0"])

    assert generator.generate(num_browsers=1).endswith("Firefox/119.0")
