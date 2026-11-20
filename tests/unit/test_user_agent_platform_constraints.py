import pytest

from crawl4ai.user_agent_generator import (
    DEFAULT_USER_AGENT,
    OnlineUAGenerator,
    UserAgentGenerator,
)


def test_device_brand_is_honored_without_os_type():
    gen = UserAgentGenerator()
    for _ in range(30):
        ua_iphone = gen.generate(device_brand="iphone", browser_type="safari")
        assert "iPhone" in ua_iphone

        ua_pixel = gen.generate(
            device_type="mobile", device_brand="pixel", browser_type="chrome"
        )
        assert "Pixel 6" in ua_pixel

        ua_ubuntu = gen.generate(device_brand="ubuntu", browser_type="firefox")
        assert "Ubuntu" in ua_ubuntu


def test_conflicting_or_unknown_platform_constraints_raise_value_error():
    gen = UserAgentGenerator()

    with pytest.raises(ValueError):
        gen.generate(device_type="tablet")

    with pytest.raises(ValueError):
        gen.generate(os_type="freebsd")

    with pytest.raises(ValueError):
        gen.generate(device_type="desktop", os_type="android")

    with pytest.raises(ValueError):
        gen.generate(os_type="ios", device_brand="pixel")

    with pytest.raises(ValueError):
        gen.generate(device_brand="blackberry")


def test_macos_non_firefox_uas_omit_gecko_rv_token_and_gecko_date_is_8_digits():
    gen = UserAgentGenerator()
    for browser in ("chrome", "edge", "safari"):
        for _ in range(30):
            ua = gen.generate(os_type="macos", browser_type=browser)
            assert "Macintosh" in ua
            assert "rv:" not in ua

    assert all(token == "Gecko/20100101" for token in gen.rendering_engines["gecko"])


def test_online_ua_generator_filters_browsers_platforms_and_min_version(monkeypatch):
    sample_agents = [
        {
            "ua": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            ),
            "pct": 35.0,
        },
        {
            "ua": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76"
            ),
            "pct": 12.0,
        },
        {
            "ua": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) Version/17.1 Safari/605.1.15"
            ),
            "pct": 9.0,
        },
        {
            "ua": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
            ),
            "pct": 15.0,
        },
        {
            "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
            "pct": 4.0,
        },
        {
            "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "pct": 5.0,
        },
    ]

    monkeypatch.setattr(OnlineUAGenerator, "_fetch_agents", lambda self: None)
    gen = OnlineUAGenerator()
    gen.agents = list(sample_agents)

    edge = gen.generate(browsers=["edge"])
    assert "Edg/118." in edge["ua"]

    safari_desktop = gen.generate(browsers=["safari"], platforms="desktop")
    assert "Version/17.1 Safari/605.1.15" in safari_desktop["ua"]
    assert "Chrome/" not in safari_desktop["ua"]

    mobile = gen.generate(platforms=["mobile"], browsers=["safari"])
    assert "iPhone" in mobile["ua"]

    chrome_only = gen.generate(browsers=["chrome"], min_version=120.0)
    assert chrome_only == {"ua": DEFAULT_USER_AGENT, "pct": 0}

    modern_ff = gen.generate(browsers=["firefox"], min_version=120.0)
    assert "Firefox/121.0" in modern_ff["ua"]
