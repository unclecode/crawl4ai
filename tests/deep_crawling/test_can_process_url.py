"""
Test Suite: can_process_url URL validation for deep crawl strategies

Covers:
1. Single-label (dot-less) hostnames such as intranet hosts, localhost and
   Docker service names are accepted for http(s) URLs.
2. Regular hostnames, IP literals and ports keep working.
3. URLs without a scheme/netloc and non-http(s) schemes are still rejected.
4. The filter chain still applies for depth > 0, while depth 0 bypasses it.
"""

import pytest

from crawl4ai.deep_crawling import (
    BFSDeepCrawlStrategy,
    BestFirstCrawlingStrategy,
)
from crawl4ai.deep_crawling.filters import DomainFilter, FilterChain


@pytest.mark.parametrize(
    "strategy",
    [
        pytest.param(BFSDeepCrawlStrategy(max_depth=1), id="bfs"),
        pytest.param(BestFirstCrawlingStrategy(max_depth=1), id="bff"),
    ],
)
class TestCanProcessUrl:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "url",
        [
            "https://intranet/xyz/",
            "http://name/xyz",
            "https://localhost:8000/docs",
            "http://10.0.0.5:8080/",
            "https://example.com/blog/post1",
        ],
    )
    async def test_accepts_valid_urls(self, strategy, url):
        assert await strategy.can_process_url(url, 0) is True
        assert await strategy.can_process_url(url, 1) is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "url",
        [
            "intranet/xyz",  # missing scheme
            "https:///xyz",  # empty netloc
            "ftp://example.com/file",  # unsupported scheme
        ],
    )
    async def test_rejects_invalid_urls(self, strategy, url):
        assert await strategy.can_process_url(url, 0) is False
        assert await strategy.can_process_url(url, 1) is False

    @pytest.mark.asyncio
    async def test_filter_chain_still_applied_for_deeper_depths(self, strategy):
        strategy.filter_chain = FilterChain(
            [DomainFilter(allowed_domains=["intranet"])]
        )

        # Single-label host inside the allowed domain passes.
        assert await strategy.can_process_url("https://intranet/xyz", 1) is True
        # Host outside the allowed domain is rejected by the filter chain.
        assert await strategy.can_process_url("https://other/xyz", 1) is False
        # Depth 0 bypasses filtering.
        assert await strategy.can_process_url("https://other/xyz", 0) is True
