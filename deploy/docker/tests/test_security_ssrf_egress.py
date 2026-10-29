"""
R3 egress-broker behavioral tests (fully offline via the conftest DNS fixtures).

One rule: reject any resolved IP where not ip.is_global, on every transition
form (v4-mapped / NAT64 / 6to4 / v4-compat). Resolve once and pin, so DNS
rebinding never reaches the second (internal) answer. Errors are opaque.
"""

import socket

import pytest

from egress_broker import (
    EgressBlocked,
    check_redirect,
    is_forbidden_ip,
    resolve_and_pin,
)

pytestmark = pytest.mark.posture


class TestForbiddenIp:
    @pytest.mark.parametrize("ip", [
        "127.0.0.1", "169.254.169.254", "10.0.0.5", "192.168.1.1",
        "172.16.0.1", "100.64.0.1", "0.0.0.0",
        "::1", "::", "fc00::1", "fe80::1",
        "::ffff:127.0.0.1",          # v4-mapped loopback
        "::ffff:169.254.169.254",    # v4-mapped metadata
        "64:ff9b::a9fe:a9fe",        # NAT64 -> 169.254.169.254
        "2002:a9fe:a9fe::1",         # 6to4 embedding 169.254.169.254
    ])
    def test_internal_forms_forbidden(self, ip):
        assert is_forbidden_ip(ip) is True

    @pytest.mark.parametrize("ip", ["8.8.8.8", "1.1.1.1", "2606:4700:4700::1111"])
    def test_global_allowed(self, ip):
        assert is_forbidden_ip(ip) is False


class TestResolveAndPin:
    def test_public_host_pins_ip(self, offline_dns):
        offline_dns.set("good.example", "93.184.216.34")
        t = resolve_and_pin("https://good.example/path")
        assert t.ip == "93.184.216.34" and t.host == "good.example" and t.port == 443

    def test_metadata_blocked(self, offline_dns):
        offline_dns.set("meta.example", "169.254.169.254")
        with pytest.raises(EgressBlocked):
            resolve_and_pin("http://meta.example/latest/meta-data/")

    def test_nat64_metadata_blocked(self, offline_dns):
        offline_dns.set("nat64.example", "64:ff9b::a9fe:a9fe")
        with pytest.raises(EgressBlocked):
            resolve_and_pin("http://nat64.example/")

    def test_localhost_name_blocked(self, offline_dns):
        with pytest.raises(EgressBlocked):
            resolve_and_pin("http://localhost/")

    def test_non_http_scheme_blocked(self):
        with pytest.raises(EgressBlocked):
            resolve_and_pin("file:///etc/passwd")
        with pytest.raises(EgressBlocked):
            resolve_and_pin("gopher://x/")

    def test_error_is_opaque(self, offline_dns):
        offline_dns.set("meta.example", "169.254.169.254")
        try:
            resolve_and_pin("http://meta.example/")
            assert False
        except EgressBlocked as e:
            # must not leak the resolved IP or hostname
            assert "169.254" not in e.reason
            assert "meta.example" not in e.reason
            assert e.reason == "URL blocked"

    def test_multi_record_one_internal_rejects_host(self, monkeypatch):
        def fake(host, port, *a, **k):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 0)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port or 0)),
            ]
        monkeypatch.setattr(socket, "getaddrinfo", fake)
        with pytest.raises(EgressBlocked):
            resolve_and_pin("http://mixed.example/")


class TestDnsRebinding:
    def test_pins_first_answer_never_reresolves_internal(self, rebinding_dns):
        r = rebinding_dns("rebind.example", "93.184.216.34", "169.254.169.254")
        t = resolve_and_pin("http://rebind.example/")
        # Pinned to the public answer; the caller dials t.ip, not the host, so
        # the internal second answer is never used.
        assert t.ip == "93.184.216.34"
        assert r.calls == 1  # resolved exactly once


class TestEnforceEgress:
    def test_tls_verification_forced_on(self, monkeypatch):
        import egress_broker
        monkeypatch.setattr(egress_broker, "ALLOW_INSECURE_TLS", False)
        from crawl4ai import BrowserConfig
        b = BrowserConfig(ignore_https_errors=True)
        egress_broker.enforce_egress(b)
        assert b.ignore_https_errors is False

    def test_proxy_nulled(self):
        import egress_broker
        from crawl4ai import BrowserConfig
        b = BrowserConfig()
        b.proxy_config = object()
        egress_broker.enforce_egress(b)
        assert b.proxy_config is None

    def test_dangerous_args_stripped(self):
        import egress_broker
        from crawl4ai import BrowserConfig
        b = BrowserConfig(extra_args=["--proxy-server=http://evil", "--ignore-certificate-errors", "--headless"])
        egress_broker.enforce_egress(b)
        assert b.extra_args == ["--headless"]


class TestRedirectRevalidation:
    def test_redirect_to_internal_blocked(self, offline_dns):
        offline_dns.set("evil-redirect.example", "169.254.169.254")
        with pytest.raises(EgressBlocked):
            check_redirect("http://evil-redirect.example/")


class TestWebhookValidatorUsesBroker:
    def test_webhook_internal_blocked_opaque(self, offline_dns):
        from utils import validate_webhook_url
        offline_dns.set("hook.example", "10.0.0.9")
        with pytest.raises(ValueError) as exc:
            validate_webhook_url("http://hook.example/cb")
        assert "10.0.0" not in str(exc.value)  # no IP leak

    def test_webhook_public_ok(self, offline_dns):
        from utils import validate_webhook_url
        offline_dns.set("hook.example", "93.184.216.34")
        validate_webhook_url("http://hook.example/cb")  # no raise
