"""Regression tests for root-relative URL resolution in fast_urljoin."""

from crawl4ai.markdown_generation_strategy import fast_urljoin


def test_root_relative_path_resolves_against_the_origin():
    assert fast_urljoin("https://example.com/blog/post", "/about") == "https://example.com/about"


def test_root_relative_path_with_trailing_slash_base():
    assert fast_urljoin("https://example.com/blog/", "/about") == "https://example.com/about"


def test_root_relative_path_keeps_the_port():
    assert fast_urljoin("https://example.com:8443/a/b", "/c") == "https://example.com:8443/c"


def test_document_relative_path_still_resolves_against_the_page():
    assert fast_urljoin("https://example.com/blog/post", "other") == "https://example.com/blog/other"


def test_absolute_and_protocol_relative_urls_are_returned_unchanged():
    assert fast_urljoin("https://example.com/blog/post", "https://other.com/x") == "https://other.com/x"
    assert fast_urljoin("https://example.com/blog/post", "//cdn.other.com/x.png") == "//cdn.other.com/x.png"


def test_base_without_scheme_is_not_treated_as_an_origin():
    assert fast_urljoin("example.com/a", "/about") == "/about"
