from urllib.parse import parse_qsl, urlparse

import pytest

from crawl4ai.utils import normalize_url_for_deep_crawl, quick_extract_links


@pytest.mark.parametrize(
    "query, expected",
    [
        ("q=", [("q", "")]),
        ("download", [("download", "")]),
        ("q=&page=2", [("q", ""), ("page", "2")]),
        ("tag=&tag=python", [("tag", ""), ("tag", "python")]),
        ("utm_source=&q=", [("q", "")]),
    ],
)
def test_deep_crawl_preserves_blank_query_values(query, expected):
    normalized = normalize_url_for_deep_crawl("/search?" + query, "https://example.com")
    assert parse_qsl(urlparse(normalized).query, keep_blank_values=True) == expected


def test_prefetch_keeps_blank_parameter_link_distinct():
    links = quick_extract_links(
        '<a href="/report">view</a><a href="/report?download=">download</a>',
        "https://example.com",
    )
    assert {link["href"] for link in links["internal"]} == {
        "https://example.com/report",
        "https://example.com/report?download=",
    }
