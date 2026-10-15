"""Offline public scraping-to-markdown regressions for excluded-link tails."""

import pytest

from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

BASE_URL = "https://example.com/article"
EXTERNAL_URL = "https://example.net/ad"
EXCLUDED_TEXT = "EXCLUDED ANCHOR TEXT"
TAIL = ", important prose after the excluded link must remain."


def scrape_and_markdown(fragment, options):
    result = LXMLWebScrapingStrategy().scrap(
        BASE_URL,
        "<html><body>" + fragment + "</body></html>",
        word_count_threshold=0,
        **options,
    )
    markdown = DefaultMarkdownGenerator().generate_markdown(
        result.cleaned_html, base_url=BASE_URL
    )
    assert result.success
    return result, markdown


@pytest.mark.parametrize(
    "fragment,options,expected_tails,expected_internal",
    [
        pytest.param(
            f'<p><a href="{EXTERNAL_URL}">{EXCLUDED_TEXT}</a>{TAIL}</p>',
            {"exclude_external_links": True},
            [TAIL],
            0,
            id="first-child-and-punctuation",
        ),
        pytest.param(
            f'<p>Before <strong>retained sibling</strong><a href="{EXTERNAL_URL}">{EXCLUDED_TEXT}</a>{TAIL}</p>',
            {"exclude_external_links": True},
            [TAIL],
            0,
            id="previous-sibling",
        ),
        pytest.param(
            f'<p>Before <a href="{EXTERNAL_URL}">{EXCLUDED_TEXT}</a> first tail, '
            f'<a href="https://another.example.net/ad">{EXCLUDED_TEXT}</a>{TAIL}</p>',
            {"exclude_external_links": True},
            [" first tail, ", TAIL],
            0,
            id="adjacent-excluded-anchors",
        ),
        pytest.param(
            '<p>Before <a href="https://example.com/keep">KEEP INTERNAL</a> internal tail; '
            f'<a href="{EXTERNAL_URL}">{EXCLUDED_TEXT}</a>{TAIL}</p>',
            {"exclude_external_links": True},
            [" internal tail; ", TAIL],
            1,
            id="mixed-internal-external-links",
        ),
        pytest.param(
            f'<p>Before <span><a href="{EXTERNAL_URL}"><em>{EXCLUDED_TEXT}</em></a>{TAIL}</span> After.</p>',
            {"exclude_external_links": True},
            [TAIL],
            0,
            id="nested-inline-anchor",
        ),
        pytest.param(
            f'<p>Before <a href="{EXTERNAL_URL}">{EXCLUDED_TEXT}</a>{TAIL}</p>',
            {"exclude_domains": ["example.net"]},
            [TAIL],
            0,
            id="explicit-domain-exclusion",
        ),
        pytest.param(
            f'<p>Before <a href="https://facebook.com/share">{EXCLUDED_TEXT}</a>{TAIL}</p>',
            {"exclude_social_media_links": True},
            [TAIL],
            0,
            id="social-domain-exclusion",
        ),
    ],
)
def test_exclusion_preserves_prose(
    fragment, options, expected_tails, expected_internal
):
    result, markdown = scrape_and_markdown(fragment, options)
    assert not result.links.external
    assert len(result.links.internal) == expected_internal
    # Preserve current exclusion behavior: the anchor and its own text disappear.
    assert EXCLUDED_TEXT not in result.cleaned_html
    assert EXCLUDED_TEXT not in markdown.raw_markdown
    for tail in expected_tails:
        assert tail in result.cleaned_html
        assert tail in markdown.raw_markdown


@pytest.mark.parametrize(
    "options",
    [{}, {"exclude_domains": ["unrelated.org"]}],
    ids=["exclusions-disabled", "nonmatching-domain-rule"],
)
def test_unexcluded_link_control(options):
    result, markdown = scrape_and_markdown(
        f'<p>Before <a href="{EXTERNAL_URL}">{EXCLUDED_TEXT}</a>{TAIL}</p>',
        options,
    )
    assert len(result.links.external) == 1
    assert result.links.external[0].href == EXTERNAL_URL
    assert EXCLUDED_TEXT in result.cleaned_html
    assert EXCLUDED_TEXT in markdown.raw_markdown
    assert TAIL in result.cleaned_html
    assert TAIL in markdown.raw_markdown
