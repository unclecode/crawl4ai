"""max_pages must count URLs already queued for the next level (#2338)."""

import pytest

from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.models import CrawlResult


def _result(url, links):
    r = CrawlResult(url=url, html="", success=True)
    r.links = {"internal": [{"href": h} for h in links], "external": []}
    return r


@pytest.mark.asyncio
async def test_link_discovery_budget_counts_next_level():
    strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=50)
    strategy._pages_crawled = 36  # 14 pages of budget left

    visited = set()
    next_level = []
    depths = {}
    for p in range(35):
        parent = f"https://example.com/p{p}"
        links = [f"https://example.com/p{p}/c{i}" for i in range(30)]
        await strategy.link_discovery(
            _result(parent, links), parent, 1, visited, next_level, depths
        )

    assert len(next_level) == 14
