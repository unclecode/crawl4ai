"""Tests for DomainFilter host extraction (userinfo/port/trailing-dot bypass)."""

from crawl4ai.deep_crawling.filters import DomainFilter


def test_blocked_userinfo_bypass():
    f = DomainFilter(blocked_domains=["evil.com"])
    assert f.apply("https://user@evil.com/") is False


def test_blocked_trailing_dot_bypass():
    f = DomainFilter(blocked_domains=["evil.com"])
    assert f.apply("https://evil.com./") is False


def test_blocked_port_bypass():
    f = DomainFilter(blocked_domains=["evil.com"])
    assert f.apply("https://evil.com:443/") is False


def test_blocked_mixed_case():
    f = DomainFilter(blocked_domains=["evil.com"])
    assert f.apply("https://EVIL.COM/") is False


def test_blocked_subdomain():
    f = DomainFilter(blocked_domains=["evil.com"])
    assert f.apply("https://a.evil.com/") is False


def test_not_blocked_lookalike_domain():
    f = DomainFilter(blocked_domains=["evil.com"])
    assert f.apply("https://notevil.com/") is True


def test_blocked_domain_configured_with_trailing_dot():
    f = DomainFilter(blocked_domains=["evil.com."])
    assert f.apply("https://evil.com/") is False


def test_blocked_domain_configured_uppercase():
    f = DomainFilter(blocked_domains=["EVIL.COM"])
    assert f.apply("https://evil.com/") is False


def test_allowed_with_port():
    f = DomainFilter(allowed_domains=["good.com"])
    assert f.apply("https://good.com:443/") is True


def test_allowed_with_trailing_dot():
    f = DomainFilter(allowed_domains=["good.com"])
    assert f.apply("https://good.com./") is True


def test_allowed_userinfo_spoof_not_allowed():
    # Userinfo "good.com@evil.com" must not fool the allowlist into
    # treating the host as good.com; the real host is evil.com.
    f = DomainFilter(allowed_domains=["good.com"])
    assert f.apply("https://good.com@evil.com/") is False
