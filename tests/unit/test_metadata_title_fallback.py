"""Empty page titles should fall back to OpenGraph or Twitter title metadata."""

import pytest

from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy


@pytest.mark.parametrize(
    "head, expected",
    [
        pytest.param(
            '<title> \n\t </title><meta property="og:title" content="OpenGraph article">',
            "OpenGraph article",
            id="whitespace-title-uses-opengraph",
        ),
        pytest.param(
            '<title> \n\t </title><meta name="twitter:title" content="Twitter article">',
            "Twitter article",
            id="whitespace-title-uses-twitter",
        ),
        pytest.param(
            '<title> </title><meta property="og:title" content="OpenGraph article">',
            "OpenGraph article",
            id="space-only-title-uses-opengraph",
        ),
        pytest.param(
            '<title>&nbsp;</title><meta property="og:title" content="OpenGraph article">',
            "OpenGraph article",
            id="nonbreaking-space-title-uses-opengraph",
        ),
        pytest.param(
            "<title> \n\t </title>"
            '<meta property="og:title" content="OpenGraph article">'
            '<meta name="twitter:title" content="Twitter article">',
            "OpenGraph article",
            id="whitespace-title-prefers-opengraph",
        ),
        pytest.param("<title> \n\t </title>", None, id="whitespace-title-no-fallback"),
        pytest.param(
            "<title>  HTML article  </title>"
            '<meta property="og:title" content="OpenGraph article">'
            '<meta name="twitter:title" content="Twitter article">',
            "HTML article",
            id="nonempty-html-title-has-priority",
        ),
        pytest.param(
            "<title>  Café 中文  </title>"
            '<meta property="og:title" content="OpenGraph article">',
            "Café 中文",
            id="unicode-html-title-has-priority",
        ),
        pytest.param(
            '<meta property="og:title" content="OpenGraph article">'
            '<meta name="twitter:title" content="Twitter article">',
            "OpenGraph article",
            id="missing-title-prefers-opengraph",
        ),
        pytest.param(
            '<title></title><meta property="og:title" content="OpenGraph article">',
            "OpenGraph article",
            id="empty-title-uses-opengraph",
        ),
        pytest.param(
            '<title></title><meta name="twitter:title" content="Twitter article">',
            "Twitter article",
            id="empty-title-uses-twitter",
        ),
        pytest.param(
            '<meta name="twitter:title" content="Twitter article">',
            "Twitter article",
            id="missing-title-uses-twitter",
        ),
        pytest.param(
            '<title> </title><meta property="og:title" content="  OpenGraph article  ">',
            "OpenGraph article",
            id="fallback-title-is-trimmed",
        ),
        pytest.param("<title></title>", None, id="empty-title-no-fallback"),
        pytest.param("", None, id="missing-title-no-fallback"),
    ],
)
def test_public_scraper_title_fallback(head, expected):
    html = (
        f'<html><head>{head}<meta name="description" content="Keep description">'
        "</head><body><p>Meaningful article content remains available here.</p>"
        "</body></html>"
    )

    result = LXMLWebScrapingStrategy().scrap("https://example.test/article", html)

    assert result.success
    assert result.metadata["description"] == "Keep description"
    assert result.metadata["title"] == expected
