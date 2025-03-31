import sys

import pytest
from _pytest.mark.structures import ParameterSet

from crawl4ai.deep_crawling.scorers import (
    CompositeScorer,
    ContentTypeScorer,
    DomainAuthorityScorer,
    FreshnessScorer,
    KeywordRelevanceScorer,
    PathDepthScorer,
    URLScorer,
)


def scorers_params() -> list[ParameterSet]:
    tests: list[ParameterSet] = []

    def add_tests(name: str, scorer, urls: dict[str, float]):
        for url, expected in urls.items():
            tests.append(pytest.param(scorer, url, expected, id=f"{name} {url}"))

    # Keyword Scorer Tests
    add_tests(
        "keyword-scorer",
        KeywordRelevanceScorer(keywords=["python", "blog"], weight=1.0, case_sensitive=False),
        {
            "https://example.com/python-blog": 1.0,
            "https://example.com/PYTHON-BLOG": 1.0,
            "https://example.com/python-only": 0.5,
            "https://example.com/other": 0.0,
        },
    )

    # Path Depth Scorer Tests
    add_tests(
        "path-depth-scorer",
        PathDepthScorer(optimal_depth=2, weight=1.0),
        {
            "https://example.com/a/b": 1.0,
            "https://example.com/a": 0.5,
            "https://example.com/a/b/c": 0.5,
            "https://example.com": 0.33333333,
        },
    )

    # Content Type Scorer Tests
    add_tests(
        "content-type-scorer",
        ContentTypeScorer(type_weights={".html$": 1.0, ".pdf$": 0.8, ".jpg$": 0.6}, weight=1.0),
        {
            "https://example.com/doc.html": 1.0,
            "https://example.com/doc.pdf": 0.8,
            "https://example.com/img.jpg": 0.6,
            "https://example.com/other.txt": 0.0,
        },
    )

    # Freshness Scorer Tests
    add_tests(
        "freshness-scorer",
        FreshnessScorer(weight=1.0, current_year=2024),
        {
            "https://example.com/2024/01/post": 1.0,
            "https://example.com/2023/12/post": 0.9,
            "https://example.com/2022/post": 0.8,
            "https://example.com/no-date": 0.5,
        },
    )

    # Domain Authority Scorer Tests
    add_tests(
        "domain-authority-scorer",
        DomainAuthorityScorer(
            domain_weights={"python.org": 1.0, "github.com": 0.8, "medium.com": 0.6}, default_weight=0.3, weight=1.0
        ),
        {
            "https://python.org/about": 1.0,
            "https://github.com/repo": 0.8,
            "https://medium.com/post": 0.6,
            "https://unknown.com": 0.3,
        },
    )

    return tests


@pytest.mark.parametrize("scorer,url,expected", scorers_params())
def test_accuracy(scorer: URLScorer, url: str, expected: float):
    score = round(scorer.score(url), 8)
    expected = round(expected, 8)

    assert abs(score - expected) < 0.00001, f"Expected: {expected}, Got: {score}"


def composite_scorer_params() -> list[ParameterSet]:
    composite = CompositeScorer(
        [
            KeywordRelevanceScorer(keywords=["python", "blog"], weight=1.0, case_sensitive=False),
            PathDepthScorer(optimal_depth=2, weight=1.0),
            ContentTypeScorer(type_weights={".html$": 1.0, ".pdf$": 0.8, ".jpg$": 0.6}, weight=1.0),
            FreshnessScorer(weight=1.0, current_year=2024),
            DomainAuthorityScorer(
                domain_weights={"python.org": 1.0, "github.com": 0.8, "medium.com": 0.6}, default_weight=0.3, weight=1.0
            ),
        ],
        normalize=True,
    )

    test_urls = {
        "https://python.org/blog/2024/01/new-release.html": 0.86666667,
        "https://github.com/repo/old-code.pdf": 0.62,
        "https://unknown.com/random": 0.26,
    }

    return [pytest.param(url, expected, composite, id=url) for url, expected in test_urls.items()]


@pytest.mark.parametrize("url,expected,composite", composite_scorer_params())
def test_composite(url: str, expected: float, composite: CompositeScorer):
    score = round(composite.score(url), 8)
    assert abs(score - expected) < 0.00001, f"Expected: {expected}, Got: {score}"


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
