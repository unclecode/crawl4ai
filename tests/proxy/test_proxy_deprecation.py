import warnings

import pytest

from crawl4ai.async_configs import BrowserConfig, ProxyConfig


def test_browser_config_proxy_string_emits_deprecation_and_autoconverts():
    warnings.simplefilter("always", DeprecationWarning)

    proxy_str = "23.95.150.145:6114:username:password"
    with warnings.catch_warnings(record=True) as caught:
        cfg = BrowserConfig(proxy=proxy_str, headless=True)

    dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert dep_warnings, "Expected DeprecationWarning when using BrowserConfig(proxy=...)"

    assert cfg.proxy is None, "cfg.proxy should be None after auto-conversion"
    assert isinstance(cfg.proxy_config, ProxyConfig), "cfg.proxy_config should be ProxyConfig instance"
    assert cfg.proxy_config.username == "username"
    assert cfg.proxy_config.password == "password"
    assert cfg.proxy_config.server.startswith("http://")
    assert cfg.proxy_config.server.endswith(":6114")


def test_browser_config_with_proxy_config_emits_no_deprecation():
    warnings.simplefilter("always", DeprecationWarning)

    with warnings.catch_warnings(record=True) as caught:
        cfg = BrowserConfig(
            headless=True,
            proxy_config={
                "server": "http://127.0.0.1:8080",
                "username": "u",
                "password": "p",
            },
        )

    dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert not dep_warnings, "Did not expect DeprecationWarning when using proxy_config"
    assert cfg.proxy is None
    assert isinstance(cfg.proxy_config, ProxyConfig)
