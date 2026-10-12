"""BFS deep crawl must not fetch more than max_pages pages (#2338)."""

from collections import Counter

import pytest

from crawl4ai import CrawlerRunConfig
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


# A home page that links to 35 pages, each of which links to 30 more.
ROOT = "https://example.com/"


def _tree_links(url):
    if url == ROOT:
        return [f"https://example.com/p{i}" for i in range(35)]
    if url.count("/") == 3:
        return [f"{url}/c{j}" for j in range(30)]
    return []


# Every page links to a shared 10-link menu plus 3 pages of its own.
MENU = [f"https://example.com/m{i}" for i in range(10)]


def _menu_links(url):
    return MENU + [f"{url.rstrip('/')}/n{j}" for j in range(3)]


class FakeCrawler:
    def __init__(self, links=_tree_links):
        self.links = links
        self.fetched = 0

    def _results(self, urls):
        self.fetched += len(urls)
        return [_result(u, self.links(u)) for u in urls]

    async def arun_many(self, urls, config):
        results = self._results(urls)
        if not config.stream:
            return results

        async def gen():
            for r in results:
                yield r

        return gen()


@pytest.mark.asyncio
async def test_batch_crawl_stops_at_max_pages():
    strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=50)
    crawler = FakeCrawler()
    results = await strategy._arun_batch(ROOT, crawler, CrawlerRunConfig())
    assert crawler.fetched == 50
    assert len(results) == 50
    depths = Counter(r.metadata["depth"] for r in results)
    assert depths == {0: 1, 1: 35, 2: 14}


@pytest.mark.asyncio
async def test_batch_crawl_stops_at_max_pages_shared_menu():
    strategy = BFSDeepCrawlStrategy(max_depth=3, max_pages=50)
    crawler = FakeCrawler(_menu_links)
    results = await strategy._arun_batch(ROOT, crawler, CrawlerRunConfig())
    assert crawler.fetched == 50
    assert len(results) == 50


@pytest.mark.asyncio
async def test_stream_crawl_fetches_at_most_max_pages():
    strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=50)
    crawler = FakeCrawler()
    config = CrawlerRunConfig(stream=True)
    [r async for r in strategy._arun_stream(ROOT, crawler, config)]
    assert crawler.fetched == 50


@pytest.mark.asyncio
async def test_batch_crawl_without_max_pages_crawls_everything():
    strategy = BFSDeepCrawlStrategy(max_depth=2)
    crawler = FakeCrawler()
    results = await strategy._arun_batch(ROOT, crawler, CrawlerRunConfig())
    assert len(results) == 1 + 35 + 35 * 30
