import sys

from typing import List, Union
from _pytest.mark.structures import ParameterSet
import pytest
from re import Pattern

from crawl4ai.deep_crawling.filters import (
    ContentRelevanceFilter,
    ContentTypeFilter,
    DomainFilter,
    SEOFilter,
    URLPatternFilter,
)


def pattern_filter_params() -> list[ParameterSet]:
    params: list[ParameterSet] = []
    def build_params(
        name: str,
        pattern: Union[str, Pattern, List[Union[str, Pattern]]],
        test_urls: dict[str, bool],
    ):
        for url, expected in test_urls.items():
            params.append(pytest.param(pattern, url, expected, id=f"{name} {url}"))

    # Simple suffix patterns (*.html)
    build_params(
        "simple-suffix",
        "*.html", {
            "https://example.com/page.html": True,
            "https://example.com/path/doc.html": True,
            "https://example.com/page.htm": False,
            "https://example.com/page.html?param=1": True,
        },
    )

    # Path prefix patterns (/foo/*)
    build_params(
        "path-prefix",
        "*/article/*", {
            "https://example.com/article/123": True,
            "https://example.com/blog/article/456": True,
            "https://example.com/articles/789": False,
            "https://example.com/article": False,
        }
    )

    # Complex patterns
    build_params(
        "complex-pattern",
        "blog-*-[0-9]", {
            "https://example.com/blog-post-1": True,
            "https://example.com/blog-test-9": True,
            "https://example.com/blog-post": False,
            "https://example.com/blog-post-x": False,
        }
    )

    # Multiple patterns case
    build_params(
        "multiple-patterns",
        ["*.pdf", "*/download/*"], {
            "https://example.com/doc.pdf": True,
            "https://example.com/download/file.txt": True,
            "https://example.com/path/download/doc": True,
            "https://example.com/uploads/file.txt": False,
        }
    )

    # Edge cases
    build_params(
        "edge-cases",
        "*", {
            "https://example.com": True,
            "": True,
            "http://test.com/path": True,
        },
    )

    # Complex regex
    build_params(
        "complex-regex",
        r"^https?://.*\.example\.com/\d+", {
            "https://sub.example.com/123": True,
            "http://test.example.com/456": True,
            "https://example.com/789": False,
            "https://sub.example.com/abc": False,
        },
    )
    return params

@pytest.mark.asyncio
@pytest.mark.parametrize("pattern,url,expected", pattern_filter_params())
async def test_pattern_filter(pattern: Union[str, Pattern, List[Union[str, Pattern]]], url: str, expected: bool):
    filter_obj = URLPatternFilter(pattern)
    result = filter_obj.apply(url)
    assert result == expected


def domain_filter_params() -> list[ParameterSet]:
    params: list[ParameterSet] = []
    def build_params(
        name: str,
        filter: DomainFilter,
        test_urls: dict[str, bool],
    ):
        for url, expected in test_urls.items():
            params.append(pytest.param(filter, url, expected, id=f"{name} {url}"))

    # Allowed domains
    build_params(
        "allowed-domains",
        DomainFilter(allowed_domains="example.com"), {
            "https://example.com/page": True,
            "http://example.com": True,
            "https://sub.example.com": True,
            "https://other.com": False,
        }
    )

    build_params(
        "allowed-domains-list",
        DomainFilter(allowed_domains=["example.com", "test.com"]), {
            "https://example.com/page": True,
            "https://test.com/home": True,
            "https://other.com": False,
        }
    )

    # Blocked domains
    build_params(
        "blocked-domains",
        DomainFilter(blocked_domains="malicious.com"), {
            "https://malicious.com": False,
            "https://safe.com": True,
            "http://malicious.com/login": False,
        }
    )

    build_params(
        "blocked-domains-list",
        DomainFilter(blocked_domains=["spam.com", "ads.com"]), {
            "https://spam.com": False,
            "https://ads.com/banner": False,
            "https://example.com": True,
        }
    )

    # Allowed and Blocked combination
    build_params(
        "allowed-and-blocked",
        DomainFilter(
            allowed_domains="example.com",
            blocked_domains="sub.example.com"
        ), {
            "https://example.com": True,
            "https://sub.example.com": False,
            "https://other.com": False,
        }
    )

    return params

@pytest.mark.asyncio
@pytest.mark.parametrize("filter,url,expected", domain_filter_params())
async def test_domain_filter(filter: DomainFilter, url: str, expected: bool):
    result = filter.apply(url)
    assert result == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("url,expected", [
    ("https://en.wikipedia.org/wiki/Cricket", False),
    ("https://en.wikipedia.org/wiki/American_Civil_War", True),
])
async def test_content_relevance_filter(url: str, expected: bool):
    relevance_filter = ContentRelevanceFilter(
        query="What was the cause of american civil war?", threshold=1
    )

    result = await relevance_filter.apply(url)
    assert result == expected


def content_type_filter_params() -> list[ParameterSet]:
    params: list[ParameterSet] = []
    def build_params(
        name: str,
        filter: ContentTypeFilter,
        test_urls: dict[str, bool],
    ):
        for url, expected in test_urls.items():
            params.append(pytest.param(filter, url, expected, id=f"{name} {url}"))

    # Allowed single type
    build_params(
        "content-type-filter",
        ContentTypeFilter(allowed_types="image/png"), {
            "https://example.com/image.png": True,
            "https://example.com/photo.jpg": False,
            "https://example.com/document.pdf": False,
        },
    )

    # Multiple allowed types
    build_params(
        "multiple-content-types",
        ContentTypeFilter(allowed_types=["image/jpeg", "application/pdf"]), {
            "https://example.com/photo.jpg": True,
            "https://example.com/document.pdf": True,
            "https://example.com/script.js": False,
        }
    )

    # No extension should be allowed
    build_params(
        "no-extension-allowed",
        ContentTypeFilter(allowed_types="application/json"), {
            "https://example.com/api/data": True,
            "https://example.com/data.json": True,
            "https://example.com/page.html": False,
        }
    )

    # Unknown extensions should not be allowed
    build_params(
        "unknown-extension-not-allowed",
        ContentTypeFilter(allowed_types="application/octet-stream"), {
            "https://example.com/file.unknown": True,
            "https://example.com/archive.zip": False,
            "https://example.com/software.exe": False,
        }
    )

    return params

@pytest.mark.asyncio
@pytest.mark.parametrize("filter,url,expected", content_type_filter_params())
async def test_content_type_filter(filter: ContentTypeFilter, url:str, expected: bool):
    result = filter.apply(url)
    assert result == expected, f"URL: {url}, Expected: {expected}, Got: {result}"

@pytest.mark.asyncio
@pytest.mark.parametrize("url,expected", [
    ("https://en.wikipedia.org/wiki/Search_engine_optimization", True),
    ("https://en.wikipedia.org/wiki/Randomness", False),
])
async def test_seo_filter(url: str, expected: bool):
    seo_filter = SEOFilter(
        threshold=0.5, keywords=["SEO", "search engines", "Optimization"]
    )
    result = await seo_filter.apply(url)
    assert result == expected

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
