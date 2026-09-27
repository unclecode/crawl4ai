import re

import pytest

from crawl4ai.deep_crawling.filters import URLPatternFilter


@pytest.mark.parametrize(
    "pattern, path, expected",
    [
        (r"/article/[0-9]+", "/article/123", True),
        (r"/article/[0-9]+", "/article/abc", False),
        (r"/docs/.*", "/docs/intro", True),
        (r"/docs/.*", "/other/intro", False),
        (r"\.(pdf|txt)", "/report.pdf", True),
        (r"\.(pdf|txt)", "/report.html", False),
    ],
)
@pytest.mark.parametrize("reverse", [False, True])
def test_explicit_regex_mode(pattern, path, expected, reverse):
    filter_ = URLPatternFilter(pattern, use_glob=False, reverse=reverse)
    assert filter_.apply("https://example.com" + path) is (expected != reverse)


def test_explicit_regex_mode_supports_mixed_pattern_list():
    filter_ = URLPatternFilter(
        [r"/article/[0-9]+", re.compile(r"/DOCS/.*", re.IGNORECASE)],
        use_glob=False,
    )
    assert filter_.apply("https://example.com/article/12")
    assert filter_.apply("https://example.com/docs/intro")
    assert not filter_.apply("https://example.com/other")


def test_default_glob_mode_still_matches_suffixes():
    filter_ = URLPatternFilter("*.pdf")
    assert filter_.apply("https://example.com/report.pdf?download=1")
    assert not filter_.apply("https://example.com/report.html")
