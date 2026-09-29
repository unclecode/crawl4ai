import pytest

from crawl4ai.deep_crawling.filters import DomainFilter


@pytest.mark.parametrize(
    "url",
    [
        "https://example.test/path",
        "https://example.test:8443/path",
        "https://user:pass@example.test/path",
        "https://example.test?next=page",
        "https://example.test#section",
        "https://sub.EXAMPLE.test:443/path",
        "https://example.test./path",
    ],
)
def test_host_components_do_not_change_domain_policy(url):
    allowed = DomainFilter(allowed_domains="example.test")
    blocked = DomainFilter(blocked_domains="example.test")
    assert allowed.apply(url) is True
    assert blocked.apply(url) is False
    assert allowed.stats.passed_urls == 1
    assert blocked.stats.rejected_urls == 1


@pytest.mark.parametrize(
    "url",
    [
        "https://example.test@evil.test/path",
        "https://example.test.evil.test/path",
        "https://notexample.test/path",
    ],
)
def test_domain_boundaries_remain_enforced(url):
    assert DomainFilter(allowed_domains="example.test").apply(url) is False
    assert DomainFilter(blocked_domains="example.test").apply(url) is True


def test_ipv6_host_and_normalized_config():
    url = "https://[2001:db8::1]:8443/"
    assert DomainFilter(allowed_domains="2001:db8::1").apply(url) is True
    assert DomainFilter(blocked_domains="2001:db8::1").apply(url) is False
    assert (
        DomainFilter(allowed_domains=["EXAMPLE.test."]).apply("https://example.test/")
        is True
    )
