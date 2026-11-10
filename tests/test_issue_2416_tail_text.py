"""
Tests for issue #2416: removing an element also dropped the text after it.

lxml keeps the text that follows an element in that element's .tail, and
getparent().remove() throws it away. Every removal in the scraper must keep it.
"""

import pytest
from lxml import html as lhtml

from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

URL = "https://example.com/"


@pytest.fixture
def strategy():
    return LXMLWebScrapingStrategy()


# (input body, scrap options, text inside the removed element)
CASES = {
    "link": ('<p>Before <link rel="x" href="/x"> after it.</p>', {}, None),
    "meta": ('<p>Before <meta name="x" content="y"> after it.</p>', {}, None),
    "style": ("<p>Before <style>.gone{}</style> after it.</p>", {}, ".gone"),
    "noscript": ("<p>Before <noscript>GONE</noscript> after it.</p>", {}, "GONE"),
    "script": ("<p>Before <script>var gone;</script> after it.</p>", {}, "var gone"),
    "remove_comments": ("<p>Before <!-- GONE --> after it.</p>", {"remove_comments": True}, "GONE"),
    "exclude_all_images": ('<p>Before <img src="gone.png"> after it.</p>', {"exclude_all_images": True}, "gone.png"),
    "exclude_external_images": (
        '<p>Before <img src="https://other.com/gone.png"> after it.</p>',
        {"exclude_external_images": True},
        "gone.png",
    ),
    "exclude_external_links": (
        '<p>Before <a href="https://other.com/">GONE</a> after it.</p>',
        {"exclude_external_links": True},
        "GONE",
    ),
    "exclude_domains": (
        '<p>Before <a href="https://other.com/">GONE</a> after it.</p>',
        {"exclude_domains": ["other.com"]},
        "GONE",
    ),
    "excluded_tags": ("<p>Before <span>GONE</span> after it.</p>", {"excluded_tags": ["span"]}, "GONE"),
    "excluded_selector": ('<p>Before <span class="ad">GONE</span> after it.</p>', {"excluded_selector": ".ad"}, "GONE"),
    "remove_forms": ("<div>Before <form><input value=GONE></form> after it.</div>", {"remove_forms": True}, "GONE"),
}


@pytest.mark.parametrize("body, options, removed", CASES.values(), ids=CASES.keys())
def test_text_after_removed_element_is_kept(strategy, body, options, removed):
    result = strategy._scrap(URL, f"<html><body><article>{body}</article></body></html>", **options)
    md = DefaultMarkdownGenerator().generate_markdown(
        input_html=result["cleaned_html"], base_url=URL
    ).raw_markdown
    assert "Before after it." in " ".join(md.split())
    if removed:
        assert removed not in result["cleaned_html"]


def test_tail_moves_onto_previous_sibling(strategy):
    html = "<html><body><p><b>Bold</b><style>.x{}</style> then text.</p></body></html>"
    result = strategy._scrap(URL, html)
    assert "<b>Bold</b> then text." in result["cleaned_html"]


def test_nested_excluded_tags_keep_outer_tail(strategy):
    html = "<html><body><p>Before <span>a <span>b</span> c</span> after it.</p></body></html>"
    result = strategy._scrap(URL, html, excluded_tags=["span"])
    assert "Before  after it." in result["cleaned_html"]


def test_comment_outside_html_does_not_break_remove_comments(strategy):
    html = "<!-- top --><html><body><p>Before <!-- c --> after it.</p></body></html><!-- end -->"
    result = strategy._scrap(URL, html, remove_comments=True)
    assert "Crawl4AI Error" not in result["cleaned_html"]
    assert "Before  after it." in result["cleaned_html"]


@pytest.mark.parametrize(
    "removed, options",
    [
        ("<span>GONE</span>", {"excluded_tags": ["span"]}),
        ("<span>GONE</span>", {"excluded_selector": "span"}),
        ("<form>GONE</form>", {"remove_forms": True}),
    ],
    ids=["excluded_tags", "excluded_selector", "remove_forms"],
)
def test_process_element_keeps_tail(strategy, removed, options):
    root = lhtml.fromstring(f"<div><div>Before {removed} after it.</div></div>")
    strategy.process_element(URL, root, **options)
    out = lhtml.tostring(root, encoding="unicode")
    assert "Before  after it." in out
    assert "GONE" not in out
