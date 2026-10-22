"""Text after removed <style>/<link>/<meta>/<noscript> elements must survive.

Regression tests for issue #2416: the scraping strategy removed those elements
with ``element.getparent().remove(element)``, which also drops the element's
``.tail`` -- the text that follows it inside the same parent.  Wikipedia puts
``<link rel="mw:PageProp/Category">`` inside paragraphs, so a kept paragraph
lost everything after such a link, silently (the crawl still reports success).

The tests run fully offline: the strategy and the markdown generator only need
an HTML string and a base URL.
"""

import pytest

from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

BASE_URL = "https://example.com/article"


def scrape_and_markdown(fragment):
    result = LXMLWebScrapingStrategy().scrap(
        BASE_URL,
        "<html><body>" + fragment + "</body></html>",
        word_count_threshold=0,
    )
    assert result.success
    markdown = DefaultMarkdownGenerator().generate_markdown(
        result.cleaned_html, base_url=BASE_URL
    )
    return result.cleaned_html, markdown.raw_markdown


@pytest.mark.parametrize(
    "fragment,expected",
    [
        pytest.param(
            '<p>The port grew quickly, and as of 2020<link rel="mw:PageProp/Category" href="/x">,'
            " it handles more cargo than any other port.</p>",
            "The port grew quickly, and as of 2020, it handles more cargo than any other port.",
            id="link-inside-sentence",
        ),
        pytest.param(
            '<p>The old warehouses stood on the quay<meta property="mw:PageProp/toc">'
            " until the great fire destroyed them.</p>",
            "The old warehouses stood on the quay until the great fire destroyed them.",
            id="meta-inside-sentence",
        ),
        pytest.param(
            "<p>Styled text<style>.a{color:red}</style> continues after a style element.</p>",
            "Styled text continues after a style element.",
            id="style-inside-sentence",
        ),
        pytest.param(
            "<p>Plain text<noscript>Enable JavaScript</noscript> continues after a noscript element.</p>",
            "Plain text continues after a noscript element.",
            id="noscript-inside-sentence",
        ),
        pytest.param(
            '<p><link rel="mw:PageProp/Category" href="/x">Text at the start of the paragraph.</p>',
            "Text at the start of the paragraph.",
            id="element-is-first-child",
        ),
    ],
)
def test_text_after_removed_element_is_kept(fragment, expected):
    cleaned_html, markdown = scrape_and_markdown(fragment)

    assert expected in markdown
    assert expected.replace("&", "&amp;") in cleaned_html
    # The element itself is still gone.
    for tag in ("<style", "<link", "<meta", "<noscript"):
        assert tag not in cleaned_html


def test_removed_element_between_two_sentences():
    fragment = (
        '<p>First sentence.<link rel="mw:PageProp/Category" href="/x">'
        "Second sentence.</p>"
    )
    cleaned_html, markdown = scrape_and_markdown(fragment)

    assert "First sentence.Second sentence." in markdown


def test_neighbouring_inline_markup_is_kept():
    fragment = (
        "<p>Before <strong>bold</strong><style>.a{color:red}</style>"
        " <em>after</em> the style element.</p>"
    )
    _, markdown = scrape_and_markdown(fragment)

    assert "Before **bold**" in markdown
    assert "_after_ the style element." in markdown
