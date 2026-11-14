import pytest

from crawl4ai.deep_crawling.filters import URLPatternFilter


@pytest.mark.parametrize(
    "pattern, path, expected",
    [
        ("*.tar.gz", "/downloads/archive.tar.gz", True),
        ("*.tar.gz", "/downloads/archive.gz", False),
        ("*.tar.gz", "/downloads/archive.tar.gz?download=1#file", True),
        ("*.tar.gz", "/downloads/archive.tar.gz/", False),
        ("*.html", "/docs/index.html", True),
        ("*.html", "/docs/html", False),
        ("*.html", "/docs/.html", True),
        ("*.html", "/docs/index.HTML", False),
        ("*.html", "/docs/index.html?format=pdf#section", True),
        ("*.html", "/docs/index?format=.html#section.html", False),
    ],
)
@pytest.mark.parametrize("reverse", [False, True])
def test_suffix_patterns_match_complete_path_suffix(pattern, path, expected, reverse):
    filter_ = URLPatternFilter(pattern, reverse=reverse)

    assert filter_.apply("https://example.com" + path) is (expected != reverse)


def test_suffix_patterns_can_be_combined():
    filter_ = URLPatternFilter(["*.tar.gz", "*.pdf"])

    assert filter_.apply("https://example.com/archive.tar.gz")
    assert filter_.apply("https://example.com/document.pdf")
    assert not filter_.apply("https://example.com/pdf")
    assert not filter_.apply("https://example.com/archive.zip")
