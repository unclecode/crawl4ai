import pytest

from crawl4ai.async_configs import ProxyConfig
from crawl4ai.proxy_strategy import ProxyConfig as LegacyProxyConfig


@pytest.mark.parametrize("config_cls", [ProxyConfig, LegacyProxyConfig])
@pytest.mark.parametrize(
    "server, expected",
    [
        ("http://[2001:db8::1]:8080", "2001:db8::1"),
        ("[2001:db8::2]:8080", "2001:db8::2"),
        ("http://user:password@192.0.2.1:8080", "192.0.2.1"),
        ("socks5://user:password@[2001:db8::1]:1080", "2001:db8::1"),
        ("https://proxy.example.test/", "proxy.example.test"),
        ("http://192.0.2.1:8080", "192.0.2.1"),
        ("proxy.example.test:8080", "proxy.example.test"),
    ],
)
def test_auto_ip_uses_hostname(config_cls, server, expected):
    config = config_cls(server=server)
    assert config.ip == expected
    assert config.server == server
    assert config.to_dict()["ip"] == expected


@pytest.mark.parametrize("config_cls", [ProxyConfig, LegacyProxyConfig])
def test_explicit_verification_ip_is_preserved(config_cls):
    assert config_cls(server="http://[::1]:8080", ip="192.0.2.2").ip == "192.0.2.2"


def test_url_factory_keeps_ipv6_endpoint_and_auth():
    config = ProxyConfig.from_string("socks5://user:password@[2001:db8::1]:1080")
    assert config.ip == "2001:db8::1"
    assert config.server == "socks5://[2001:db8::1]:1080"
    assert (config.username, config.password) == ("user", "password")
