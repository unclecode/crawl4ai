import pytest

from crawl4ai.deep_crawling.filters import ContentTypeFilter


@pytest.mark.parametrize(
    "url, allowed",
    [
        ("https://example.test/page.html?version=2", True),
        ("https://example.test/page.HTML#section", True),
        ("https://example.test/page.html?next=/file.pdf", True),
        ("https://example.test/file.pdf?next=/page.html", False),
        ("https://example.test/file.pdf#page.html", False),
        ("example.test/page.html?version=2", True),
        ("https://example.test/download?file=report.pdf", True),
        ("https://example.test/page.html", True),
        ("https://example.test/file.pdf", False),
    ],
)
def test_extension_filter_uses_only_url_path(url, allowed):
    filter_ = ContentTypeFilter("text/html")
    assert filter_.apply(url) is allowed
    assert filter_.stats.total_urls == 1


def test_custom_extension_map_is_used_without_changing_defaults():
    custom = ContentTypeFilter("text/html", ext_map={"page": "text/html"})
    assert custom.apply("https://example.test/index.page") is True
    assert custom.apply("https://example.test/index.html") is False
    assert (
        ContentTypeFilter("text/html").apply("https://example.test/index.html") is True
    )


def test_empty_extension_map_and_disabled_extension_check():
    assert (
        ContentTypeFilter("text/html", ext_map={}).apply("https://x.test/a.html")
        is False
    )
    assert (
        ContentTypeFilter("text/html", check_extension=False).apply(
            "https://x.test/a.pdf"
        )
        is True
    )
