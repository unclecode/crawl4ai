import pytest

from crawl4ai.deep_crawling.scorers import (
    ContentTypeScorer,
    DomainAuthorityScorer,
    PathDepthScorer,
)


@pytest.mark.parametrize(
    "suffix", ["?next=/x/y", "#section/x/y", "?next=https://other.test/x/y"]
)
@pytest.mark.parametrize("path", ["", "/a/b"])
def test_path_depth_ignores_query_and_fragment(path, suffix):
    scorer = PathDepthScorer(optimal_depth=2)
    url = "https://example.com" + path
    assert scorer.score(url + suffix) == scorer.score(url)


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://example.com/report.pdf?next=image.jpg", 1.0),
        ("https://example.com/report.PDF#image.jpg", 1.0),
        ("https://example.com/report.pdf;version=2.jpg", 1.0),
        ("https://reports.pdf/", 0.0),
        ("https://example.com/archive.pdf/readme", 0.0),
        ("https://example.com/download?name=report.pdf", 0.0),
        ("https://example.com/download#report.pdf", 0.0),
        ("https://example.com/report.pdf", 1.0),
    ],
)
def test_content_type_uses_only_filename_extension(url, expected):
    assert ContentTypeScorer({".pdf$": 1.0}).score(url) == expected


@pytest.mark.parametrize(
    "url, domain",
    [
        ("https://example.com?next=/a", "example.com"),
        ("https://example.com#section/a", "example.com"),
        ("https://User:Secret@EXAMPLE.COM:8443/a", "example.com"),
        ("https://[2001:db8::1]:8443/a", "2001:db8::1"),
        ("example.com?next=/a", "example.com"),
        ("https://example.com:8443/a", "example.com"),
    ],
)
def test_domain_authority_uses_hostname(url, domain):
    scorer = DomainAuthorityScorer({domain: 1.0}, default_weight=0.2)
    assert scorer.score(url) == 1.0
