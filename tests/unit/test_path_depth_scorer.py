import pytest

from crawl4ai.deep_crawling.scorers import PathDepthScorer


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.com/docs/guide", 1.0),
        ("https://example.com/docs/guide?next=/a/b/c", 1.0),
        ("https://example.com/docs/guide#/a/b/c", 1.0),
        ("https://example.com?next=https://other.test/a", 1.0 / 3),
        ("https://example.com#/a/b/c", 1.0 / 3),
        ("https://example.com/docs?next=/a/b/c", 0.5),
        ("https://example.com/docs/guide?mode=print#/a/b/c", 1.0),
        ("https://example.com/docs//guide/", 1.0),
        ("https://example.com/docs/guide?next=%2Fa%2Fb", 1.0),
        ("https://example.com/docs/guide%2Fpart", 1.0),
        ("https://example.com/docs/guide?ref=guide#overview", 1.0),
    ],
)
def test_path_depth_ignores_query_and_fragment(url, expected):
    scorer = PathDepthScorer(optimal_depth=2)
    assert scorer.score(url) == pytest.approx(expected)


def test_path_depth_weight_with_url_suffixes():
    scorer = PathDepthScorer(optimal_depth=2, weight=2.5)
    url = "https://example.com/docs/guide?next=/a/b/c#/section"
    assert scorer.score(url) == pytest.approx(2.5)
    assert scorer.score(url) == pytest.approx(2.5)
