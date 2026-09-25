"""
Tests for pages whose body ends up nested inside an unclosed <noscript>.

A page that nests <noscript> (for example a lazy-load plugin wrapping Google Tag
Manager's own noscript) loses its outer closing tag when a scripting-enabled
browser serializes it. Re-parsed by lxml, the rest of the document becomes a
child of the still-open <noscript>, and the scraper's noscript removal used to
delete the entire page, leaving cleaned_html with an empty body.
"""

import pytest

from crawl4ai.content_scraping_strategy import (
    LXMLWebScrapingStrategy,
    unwrap_orphaned_noscript,
)

# Shape of page.content() for such a page: two opening tags, one closing tag.
DAMAGED_CAPTURE = """
<html>
<head><title>Example shop</title></head>
<body>
<noscript><iframe src="about:blank" height="0" width="0"></iframe><noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-TEST" height="0" width="0"></iframe></noscript>
<div class="site-content">
    <h1>Unstunned. Hand slaughtered. Halal certified.</h1>
    <p>Our entire assortment is strictly halal, prepared by qualified staff.</p>
</div>
</body>
</html>
"""


@pytest.fixture
def strategy():
    return LXMLWebScrapingStrategy()


def test_body_nested_in_unclosed_noscript_is_kept(strategy):
    result = strategy.scrap("https://example.com/", DAMAGED_CAPTURE)

    assert "Unstunned. Hand slaughtered. Halal certified." in result.cleaned_html
    assert "strictly halal" in result.cleaned_html


def test_balanced_noscript_is_still_removed(strategy):
    html = (
        "<html><body>"
        "<noscript><p>Please enable JavaScript</p></noscript>"
        "<p>Real page copy that should be kept.</p>"
        "</body></html>"
    )

    result = strategy.scrap("https://example.com/", html)

    assert "Please enable JavaScript" not in result.cleaned_html
    assert "Real page copy that should be kept." in result.cleaned_html


def test_unwrap_leaves_well_formed_documents_untouched():
    html = "<html><body><noscript><p>fallback</p></noscript><p>copy</p></body></html>"

    assert unwrap_orphaned_noscript(html) == html


def test_unwrap_removes_tags_but_keeps_contents():
    unwrapped = unwrap_orphaned_noscript(DAMAGED_CAPTURE)

    assert "noscript" not in unwrapped
    assert "<h1>Unstunned. Hand slaughtered. Halal certified.</h1>" in unwrapped
