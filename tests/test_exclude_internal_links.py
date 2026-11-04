"""Documented internal-link exclusion through the public scraping strategy."""

import pytest

from crawl4ai import CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

PAGE_URL = "https://example.com/page"
EXTERNAL_URL = "https://outside.test/out"


@pytest.mark.parametrize(
    "href",
    [
        "/inside",
        "https://example.com/inside",
        "https://sub.example.com/inside",
        "#part",
    ],
    ids=["relative", "same-host", "subdomain", "fragment"],
)
@pytest.mark.parametrize(
    "exclude_internal", [None, False, True], ids=["default", "false", "true"]
)
def test_exclude_internal_links_from_results(href, exclude_internal):
    """The flag filters internal links without changing existing URL classification."""
    options = (
        {} if exclude_internal is None else {"exclude_internal_links": exclude_internal}
    )
    config = CrawlerRunConfig(word_count_threshold=0, **options)
    params = config.__dict__.copy()
    params.pop("url", None)
    html = (
        f'<html><body><p>Before <a href="{href}">Internal destination</a> after. '
        f'<a href="{EXTERNAL_URL}">External destination</a> end.</p></body></html>'
    )

    result = config.scraping_strategy.scrap(PAGE_URL, html, **params)

    assert result.success
    assert len(result.links.internal) == (0 if exclude_internal else 1)
    assert [link.href for link in result.links.external] == [EXTERNAL_URL]
    assert result.cleaned_html == html


@pytest.mark.parametrize("exclude_internal", [False, True])
def test_internal_exclusion_with_external_exclusion(exclude_internal):
    """The internal flag remains independent of the existing external-link exclusion."""
    config = CrawlerRunConfig(
        word_count_threshold=0,
        exclude_internal_links=exclude_internal,
        exclude_external_links=True,
    )
    params = config.__dict__.copy()
    params.pop("url", None)
    html = (
        '<html><body><p><a href="/inside">Internal destination</a> '
        f'<a href="{EXTERNAL_URL}">External destination</a></p></body></html>'
    )

    result = config.scraping_strategy.scrap(PAGE_URL, html, **params)

    assert result.success
    assert result.links.external == []
    assert len(result.links.internal) == (0 if exclude_internal else 1)
    assert result.cleaned_html == (
        '<html><body><p><a href="/inside">Internal destination</a> </p></body></html>'
    )


def test_internal_exclusion_preserves_markdown():
    """Filtering the link inventory must not delete linked text or its Markdown link."""
    html = '<html><body><p>Before <a href="/inside">Internal destination</a> after.</p></body></html>'
    generator = DefaultMarkdownGenerator()
    markdown_results = []

    for exclude_internal in (False, True):
        config = CrawlerRunConfig(
            word_count_threshold=0, exclude_internal_links=exclude_internal
        )
        params = config.__dict__.copy()
        params.pop("url", None)
        result = config.scraping_strategy.scrap(PAGE_URL, html, **params)
        assert result.cleaned_html == html
        markdown_results.append(
            generator.generate_markdown(result.cleaned_html, PAGE_URL)
        )

    assert markdown_results[0] == markdown_results[1]
    assert (
        "[Internal destination](https://example.com/inside)"
        in markdown_results[1].raw_markdown
    )
