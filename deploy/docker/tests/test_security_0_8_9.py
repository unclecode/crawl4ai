"""
Behavioral tests for the 0.8.9 non-breaking security patch.

Closes the proxy-injection SSRF class in the Docker server: an unauthenticated
/crawl could set a proxy (or proxy-redirecting Chromium flag) pointing at an
internal IP and route the browser through it, reaching internal services and
cloud metadata. The crawl-target URL was validated; the proxy address was not.

All fixes are backward compatible: a legitimate public proxy still works; only
non-global proxy hosts are rejected and dangerous --proxy/--host-resolver flags
are stripped from extra_args.
"""

import os
import sys

import pytest

DOCKER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if DOCKER_DIR not in sys.path:
    sys.path.insert(0, DOCKER_DIR)


class TestValidateProxyDestination:
    # IP literals so getaddrinfo is numeric (no network needed).
    @pytest.mark.parametrize("server", [
        "http://169.254.169.254:8080",   # cloud metadata
        "http://127.0.0.1:8888",
        "http://10.0.0.5:3128",
        "http://192.168.1.10:3128",
        "169.254.169.254:8080",          # bare host:port (no scheme)
        "socks5://10.1.2.3:1080",
        "http://[::1]:8080",             # ipv6 loopback
        "http://[::ffff:169.254.169.254]:80",  # v4-mapped metadata
    ])
    def test_internal_proxy_rejected(self, server):
        import utils
        with pytest.raises(ValueError):
            utils.validate_proxy_destination(server)

    @pytest.mark.parametrize("server", [
        "http://8.8.8.8:3128",
        "https://1.1.1.1:443",
        "8.8.8.8:3128",
    ])
    def test_public_proxy_allowed(self, server):
        import utils
        utils.validate_proxy_destination(server)  # no raise

    def test_empty_is_noop(self):
        import utils
        utils.validate_proxy_destination("")  # no raise
        utils.validate_proxy_destination(None)  # no raise


class TestScrubExtraArgs:
    def test_strips_dangerous_flags(self):
        import utils
        args = [
            "--headless",
            "--proxy-server=http://10.0.0.1:3128",
            "--host-resolver-rules=MAP * 169.254.169.254",
            "--proxy-bypass-list=*",
            "--proxy-pac-url=http://evil/p.pac",
            "--disable-gpu",
        ]
        out = utils.scrub_browser_extra_args(args)
        assert out == ["--headless", "--disable-gpu"]

    def test_keeps_benign(self):
        import utils
        args = ["--headless", "--no-sandbox", "--disable-dev-shm-usage"]
        assert utils.scrub_browser_extra_args(args) == args

    def test_empty(self):
        import utils
        assert utils.scrub_browser_extra_args([]) == []
        assert utils.scrub_browser_extra_args(None) is None


class TestEnforceProxySafety:
    def test_browser_proxy_config_internal_400(self):
        import api
        from fastapi import HTTPException
        from crawl4ai import BrowserConfig, ProxyConfig
        b = BrowserConfig(proxy_config=ProxyConfig(server="http://169.254.169.254:8080"))
        with pytest.raises(HTTPException) as e:
            api._enforce_proxy_safety(b, None)
        assert e.value.status_code == 400
        assert "169.254" not in str(e.value.detail)  # opaque

    def test_deprecated_proxy_field_internal_400(self):
        import api
        from fastapi import HTTPException
        from crawl4ai import BrowserConfig
        b = BrowserConfig(proxy="http://10.0.0.9:3128")
        with pytest.raises(HTTPException):
            api._enforce_proxy_safety(b, None)

    def test_crawler_proxy_config_internal_400(self):
        import api
        from fastapi import HTTPException
        from crawl4ai import BrowserConfig, CrawlerRunConfig, ProxyConfig
        c = CrawlerRunConfig(proxy_config=ProxyConfig(server="http://192.168.0.2:3128"))
        with pytest.raises(HTTPException):
            api._enforce_proxy_safety(BrowserConfig(), c)

    def test_extra_args_proxy_scrubbed(self):
        import api
        from crawl4ai import BrowserConfig
        b = BrowserConfig(extra_args=["--proxy-server=http://10.0.0.1", "--headless"])
        api._enforce_proxy_safety(b, None)  # no raise (scrub, not block)
        assert b.extra_args == ["--headless"]

    def test_public_proxy_passes(self):
        import api
        from crawl4ai import BrowserConfig, ProxyConfig
        b = BrowserConfig(proxy_config=ProxyConfig(server="http://8.8.8.8:3128"))
        api._enforce_proxy_safety(b, None)  # no raise
