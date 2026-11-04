"""Regression tests for nested/malformed <noscript> discarding the page body.

`<noscript>` may not nest. With scripting enabled its content is raw text, so
a parser never sees an inner `<noscript>` as an element and the *outer* one is
left unclosed — libxml2 then swallows every following node. A WordPress
lazy-load plugin that wraps the Google Tag Manager block in a second
`<noscript>` is enough to lose an entire page:

    312,628 B of rendered HTML -> 97 B of cleaned_html -> 1 B of markdown

at HTTP 200 with success=True, which makes it silent.

Run:  pytest tests/general/test_noscript_body_loss.py -q
"""

import pytest

from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy, strip_noscript

PAGE = """<html><head><title>T</title></head><body>
{ns}
<h1>Contact</h1><p>Phone 010 123 4567, email info@example.com</p>
<div><p>A second paragraph of real content.</p></div>
</body></html>"""

IFRAME = '<iframe src="about:blank"></iframe>'

# The shape emitted by the plugin: the inner element consumes the closing tag,
# so the outer <noscript> is never closed.
NESTED = f"<noscript>{IFRAME}<noscript>{IFRAME}</noscript>"
SINGLE = f"<noscript>{IFRAME}</noscript>"
UNCLOSED = f"<noscript>{IFRAME}"
UPPERCASE = f"<NOSCRIPT>{IFRAME}<NOSCRIPT>{IFRAME}</NOSCRIPT>"
WITH_ATTRS = f'<noscript data-lazyloaded="1">{IFRAME}<noscript>{IFRAME}</noscript>'


def cleaned(html):
    return (
        LXMLWebScrapingStrategy()
        .scrap("https://example.com/", html, word_count_threshold=1)
        .cleaned_html
    )


@pytest.mark.parametrize(
    "region",
    [NESTED, SINGLE, UNCLOSED, UPPERCASE, WITH_ATTRS, ""],
    ids=["nested", "single", "unclosed", "uppercase", "with-attrs", "absent"],
)
def test_body_survives_every_noscript_shape(region):
    out = cleaned(PAGE.format(ns=region))
    assert "Contact" in out
    assert "info@example.com" in out
    assert "A second paragraph" in out


def test_nested_and_single_are_indistinguishable():
    """Before the fix, `nested` produced
    '<html><head><title>T</title></head></html>' (42 B) while `single`
    produced the full 187 B document."""
    assert cleaned(PAGE.format(ns=NESTED)) == cleaned(PAGE.format(ns=SINGLE))


def test_noscript_only_page_is_still_empty():
    """Not a regression: Crawl4AI renders with JavaScript enabled, so
    <noscript> content is by definition not what the page displayed."""
    out = cleaned(
        "<html><head><title>T</title></head><body>"
        "<noscript><p>Enable JavaScript</p></noscript></body></html>"
    )
    assert "Enable JavaScript" not in out


def test_strip_noscript_is_a_noop_without_noscript():
    html = "<html><body><p>hello</p></body></html>"
    assert strip_noscript(html) is html
    assert strip_noscript("") == ""


def test_strip_noscript_removes_element_and_contents():
    assert strip_noscript("<p>a</p><noscript><img src=x></noscript><p>b</p>") == (
        "<p>a</p><p>b</p>"
    )


def test_realistic_gtm_lazyload_markup():
    html = (
        "<html><head><title>Home</title></head><body>"
        '<noscript><iframe data-lazyloaded="1" src="about:blank" '
        'data-src="https://www.googletagmanager.com/ns.html?id=GTM-XXXX"></iframe>'
        '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXX">'
        "</iframe></noscript>"
        '<a class="skip-link" href="#content">Skip to content</a>'
        '<div id="page"><h1>Example Oy</h1><p>We sell packaging. Call 010 000 0000.</p>'
        "</div></body></html>"
    )
    out = cleaned(html)
    assert "Example Oy" in out
    assert "Skip to content" in out
    assert "010 000 0000" in out
