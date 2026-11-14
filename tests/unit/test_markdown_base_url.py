"""Relative base elements resolve against the original document URL."""

import pytest

from crawl4ai import DefaultMarkdownGenerator
from crawl4ai.html2text import CustomHTML2Text, HTML2Text

BASE_CASES = [
    ("../assets/", "https://example.test/assets/"),
    ("assets/", "https://example.test/pages/assets/"),
    ("/docs/", "https://example.test/docs/"),
    ("//cdn.example.test/v1/", "https://cdn.example.test/v1/"),
    ("https://cdn.example.test/v1/", "https://cdn.example.test/v1/"),
    (None, "https://example.test/pages/"),
    ("", "https://example.test/pages/"),
]
PAGE_URL = "https://example.test/pages/index.html"


def _page_html(base_href):
    base_tag = f'<base href="{base_href}">' if base_href is not None else ""
    return (
        f"<html><head>{base_tag}</head><body><p>"
        '<a href="guide.html">Guide</a><img src="logo.png" alt="Logo">'
        "</p></body></html>"
    )


@pytest.mark.parametrize("converter_class", [HTML2Text, CustomHTML2Text])
@pytest.mark.parametrize(("base_href", "expected_prefix"), BASE_CASES)
def test_relative_base_element_resolves_links_and_images(
    converter_class, base_href, expected_prefix
):
    converter = converter_class(baseurl=PAGE_URL, bodywidth=0)

    markdown = converter.handle(_page_html(base_href))

    assert f"[Guide]({expected_prefix}guide.html)" in markdown
    assert f"![Logo]({expected_prefix}logo.png)" in markdown


@pytest.mark.parametrize("citations", [False, True])
@pytest.mark.parametrize(("base_href", "expected_prefix"), BASE_CASES)
def test_markdown_generator_resolves_relative_base_element(
    citations, base_href, expected_prefix
):
    result = DefaultMarkdownGenerator().generate_markdown(
        _page_html(base_href), base_url=PAGE_URL, citations=citations
    )

    assert f"[Guide]({expected_prefix}guide.html)" in result.raw_markdown
    assert f"![Logo]({expected_prefix}logo.png)" in result.raw_markdown
    if citations:
        assert f"{expected_prefix}guide.html" in result.references_markdown
        assert f"{expected_prefix}logo.png" in result.references_markdown
    else:
        assert result.references_markdown == ""
