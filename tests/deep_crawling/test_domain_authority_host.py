import pytest

from crawl4ai.deep_crawling.scorers import DomainAuthorityScorer


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/path",
        "https://EXAMPLE.COM:8443/path",
        "https://example.com?next=/docs",
        "https://example.com#section/docs",
        "https://user:password@example.com/path",
        "example.com/path",
    ],
)
def test_domain_authority_uses_hostname(url):
    scorer = DomainAuthorityScorer({"example.com": 0.9}, default_weight=0.1)
    assert scorer.score(url) == pytest.approx(0.9)


def test_domain_authority_supports_ipv6_and_ignores_query_hosts():
    scorer = DomainAuthorityScorer({"::1": 0.9}, default_weight=0.1)
    assert scorer.score("http://[::1]:8080/docs") == pytest.approx(0.9)
    assert scorer.score("https://other.test?next=http://[::1]/") == pytest.approx(0.1)


def test_malformed_host_uses_default_authority():
    scorer = DomainAuthorityScorer({"example.com": 0.9}, default_weight=0.1)
    assert scorer.score("https://[invalid]/") == pytest.approx(0.1)
