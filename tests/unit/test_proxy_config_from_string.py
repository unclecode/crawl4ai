"""ProxyConfig.from_string() with "@" in the password and username-only URLs."""

import pytest

from crawl4ai import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import ProxyConfig


@pytest.mark.parametrize(
    "proxy_str, username, password, server",
    [
        ("http://user:p@ss@host:8080", "user", "p@ss", "http://host:8080"),
        ("socks5://u:a@b@c@10.0.0.1:1080", "u", "a@b@c", "socks5://10.0.0.1:1080"),
        ("http://me@mail.com:pw@host:8080", "me@mail.com", "pw", "http://host:8080"),
        # percent-encoded credentials keep working
        ("http://user:p%40ss@host:8080", "user", "p@ss", "http://host:8080"),
        ("http://user:pass@host:8080", "user", "pass", "http://host:8080"),
        ("http://user:@host:8080", "user", "", "http://host:8080"),
    ],
)
def test_password_and_host_split_at_last_at(proxy_str, username, password, server):
    pc = ProxyConfig.from_string(proxy_str)
    assert pc.server == server
    assert pc.username == username
    assert pc.password == password
    assert pc.ip == server.split("://")[1].split(":")[0]


def test_username_only_url():
    pc = ProxyConfig.from_string("http://user@host:8080")
    assert pc.server == "http://host:8080"
    assert pc.username == "user"
    assert pc.password is None
    assert pc.ip == "host"


def test_config_strings_go_through_from_string():
    proxy_str = "http://user:p@ss@host:8080"
    for pc in (
        BrowserConfig(proxy_config=proxy_str).proxy_config,
        CrawlerRunConfig(proxy_config=proxy_str).proxy_config,
    ):
        assert (pc.server, pc.username, pc.password) == (
            "http://host:8080",
            "user",
            "p@ss",
        )
