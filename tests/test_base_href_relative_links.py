"""Regression test: a relative <base href> must be resolved against the page URL.

A document with ``<base href="/sub/">`` previously produced ``/sub/page.html``
(scheme- and host-less) while the same document without a ``<base>`` element
produced ``https://example.com/app/page.html``.
"""

import pytest

lxml_html = pytest.importorskip("lxml.html")

from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

PAGE_URL = "https://example.com/app/index.html"


def _internal_hrefs(html: str):
    strategy = LXMLWebScrapingStrategy()
    result = strategy.process_element(PAGE_URL, lxml_html.fromstring(html))
    return [link["href"] for link in result["internal_links_dict"].values()]


def test_absolute_base_href_is_kept():
    html = (
        "<html><head><base href='https://cdn.example.com/docs/'></head>"
        "<body><a href='page.html'>Page</a></body></html>"
    )

    assert _internal_hrefs(html) == ["https://cdn.example.com/docs/page.html"]


def test_root_relative_base_href_is_resolved_against_the_page():
    html = (
        "<html><head><base href='/sub/'></head>"
        "<body><a href='page.html'>Page</a></body></html>"
    )

    assert _internal_hrefs(html) == ["https://example.com/sub/page.html"]


def test_document_relative_base_href_is_resolved_against_the_page():
    html = (
        "<html><head><base href='sub/'></head>"
        "<body><a href='page.html'>Page</a></body></html>"
    )

    assert _internal_hrefs(html) == ["https://example.com/app/sub/page.html"]


def test_no_base_href_still_resolves_against_the_page():
    html = "<html><head></head><body><a href='page.html'>Page</a></body></html>"

    assert _internal_hrefs(html) == ["https://example.com/app/page.html"]
