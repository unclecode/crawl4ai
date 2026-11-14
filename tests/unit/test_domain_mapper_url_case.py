"""Domain mapping must retain case-sensitive URL components when deduplicating."""

from html import escape

import httpx
import pytest

from crawl4ai import DomainMapper, DomainMapperConfig
from crawl4ai.utils import normalize_url


def _result(url, source="sitemap"):
    return {
        "url": url,
        "host": "example.test",
        "source": source,
        "status": "valid",
        "head_data": {},
    }


@pytest.mark.parametrize(
    ("first", "second"),
    [
        pytest.param("/docs/API", "/docs/api", id="path"),
        pytest.param("/article?id=AbC", "/article?id=abc", id="query-value"),
        pytest.param("/search?Topic=crawl", "/search?topic=crawl", id="query-key"),
    ],
)
def test_case_distinct_urls_remain_separate(first, second):
    mapper = DomainMapper.__new__(DomainMapper)
    urls = [f"https://example.test{first}", f"https://example.test{second}"]

    assert [normalize_url(url, "https://example.test/") for url in urls] == urls
    results = mapper._normalize_and_dedup(
        [_result(url) for url in urls], "example.test"
    )

    assert [result["url"] for result in results] == urls


def test_normalized_duplicates_merge_sources_without_reordering():
    mapper = DomainMapper.__new__(DomainMapper)
    first = _result("HTTPS://EXAMPLE.TEST/docs/API?b=2&a=1")
    first["head_data"] = {"title": "First result"}
    other = _result("https://example.test/other")
    duplicate = _result(
        "https://example.test/docs/API?a=1&b=2&utm_source=test#section", "homepage"
    )

    results = mapper._normalize_and_dedup(
        [first, other, duplicate, first], "example.test"
    )

    assert results == [
        {
            **first,
            "url": "https://example.test/docs/API?a=1&b=2",
            "source": "homepage+sitemap",
        },
        other,
    ]
    assert first["source"] == "sitemap"


def test_trailing_slash_equivalence_keeps_first_url():
    mapper = DomainMapper.__new__(DomainMapper)
    first = _result("https://example.test/about/")
    duplicate = _result("https://example.test/about", "homepage")

    results = mapper._normalize_and_dedup([first, duplicate], "example.test")

    assert results == [{**first, "source": "homepage+sitemap"}]


@pytest.mark.asyncio
async def test_public_scan_preserves_case_distinct_homepage_urls(tmp_path):
    urls = [
        "https://example.test/docs/API",
        "https://example.test/docs/api",
        "https://example.test/article?id=AbC",
        "https://example.test/article?id=abc",
        "https://example.test/search?Topic=crawl",
        "https://example.test/search?topic=crawl",
    ]
    links = urls + ["HTTPS://EXAMPLE.TEST/docs/API"]
    page = (
        "<html><head><title>Home</title></head><body>"
        + "".join(f'<a href="{escape(url, quote=True)}">Article</a>' for url in links)
        + "</body></html>"
    )
    requests = []

    def respond(request):
        requests.append((request.method, str(request.url)))
        assert str(request.url) == "https://example.test/"
        assert request.method in {"HEAD", "GET"}
        return httpx.Response(200, text=page, headers={"Content-Type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        async with DomainMapper(client=client, base_directory=tmp_path) as mapper:
            results = await mapper.scan(
                "example.test",
                DomainMapperConfig(
                    source="homepage",
                    include_subdomains=False,
                    soft_404_detection=False,
                    extract_head=False,
                    verbose=False,
                ),
            )

    assert requests == [
        ("HEAD", "https://example.test/"),
        ("GET", "https://example.test/"),
    ]
    assert [result["url"] for result in results] == urls
    assert all(result["source"] == "homepage" for result in results)
