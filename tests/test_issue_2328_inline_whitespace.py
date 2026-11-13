"""
Tests for issue #2328: whitespace-only inline elements removed from
cleaned_html, merging words in raw_markdown.
"""

import pytest
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.fixture
def strategy():
    return LXMLWebScrapingStrategy()


SPLIT_HTML = (
    "<html><body><p><span>H</span><span>i</span><span> </span>"
    "<span>t</span><span>h</span><span>e</span><span>r</span><span>e</span></p>"
    "<p>plain text stays fine</p></body></html>"
)


def test_whitespace_span_between_words_is_kept_in_markdown(strategy):
    result = strategy._scrap("http://test.com", SPLIT_HTML)
    md = DefaultMarkdownGenerator().generate_markdown(
        input_html=result["cleaned_html"], base_url="http://test.com"
    )
    assert "Hi there" in md.raw_markdown
    assert "plain text stays fine" in md.raw_markdown


def test_whitespace_spans_between_several_words(strategy):
    html = "<html><body><p><span>one</span><span> </span><span>two</span><span> </span><span>three</span></p></body></html>"
    result = strategy._scrap("http://test.com", html)
    md = DefaultMarkdownGenerator().generate_markdown(
        input_html=result["cleaned_html"], base_url="http://test.com"
    )
    assert "one two three" in md.raw_markdown
