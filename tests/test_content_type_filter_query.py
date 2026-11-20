"""Regression test: ContentTypeFilter must ignore query strings and fragments.

``_extract_extension("https://example.com/page.html?v=2")`` used to return
``"html?v=2"``, which is not in the extension map, so every URL with a query
string or fragment was rejected even for an allowed type.
"""

import pytest

from crawl4ai.deep_crawling.filters import ContentTypeFilter

URLS = [
    "https://example.com/page.html",
    "https://example.com/page.html?v=2",
    "https://example.com/page.html#section",
    "https://example.com/page.html?utm_source=test#section",
]


def test_extract_extension_drops_query_and_fragment():
    assert ContentTypeFilter._extract_extension("https://example.com/page.html?v=2") == "html"
    assert ContentTypeFilter._extract_extension("https://example.com/page.html#top") == "html"
    assert ContentTypeFilter._extract_extension("https://example.com/a/b.pdf?x=1#y") == "pdf"


def test_content_type_filter_allows_query_and_fragment_urls():
    content_filter = ContentTypeFilter(allowed_types=["text/html"])

    for url in URLS:
        assert content_filter.apply(url) is True, url


def test_content_type_filter_still_rejects_other_extensions():
    content_filter = ContentTypeFilter(allowed_types=["text/html"])

    assert content_filter.apply("https://example.com/page.pdf?v=2") is False
    assert content_filter.apply("https://example.com/image.png#top") is False


def test_content_type_filter_allows_urls_without_extension():
    content_filter = ContentTypeFilter(allowed_types=["text/html"])

    assert content_filter.apply("https://example.com/docs/") is True
    assert content_filter.apply("https://example.com/docs/?page=2") is True
