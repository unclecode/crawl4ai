"""Regression coverage for the DFS page budget in batch and streaming crawls."""

import json

import pytest

from crawl4ai import CrawlerRunConfig
from crawl4ai.deep_crawling import DFSDeepCrawlStrategy
from crawl4ai.models import CrawlResult

ROOT = "https://example.com/"
FIRST = ROOT + "a"
DESCENDANT = FIRST + "/a"
SIBLING = ROOT + "b"


class GraphCrawler:
    def __init__(self, *, failed=()):
        self.fetched = []
        self.failed = set(failed)

    async def arun_many(self, urls, config):
        self.fetched.extend(urls)
        graph = {ROOT: [FIRST, SIBLING], FIRST: [DESCENDANT]}
        results = [
            CrawlResult(
                url=url,
                html="",
                success=url not in self.failed,
                links={"internal": [{"href": child} for child in graph.get(url, [])]},
            )
            for url in urls
        ]
        if not config.stream:
            return results

        async def generate():
            for result in results:
                yield result

        return generate()


async def crawl(strategy, crawler, stream):
    result = await strategy.arun(ROOT, crawler, CrawlerRunConfig(stream=stream))
    if stream:
        return [page async for page in result]
    return result


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["batch", "stream"])
@pytest.mark.parametrize("limit", [0, 3, 4])
async def test_dfs_stops_fetching_when_page_budget_is_exhausted(stream, limit):
    crawler = GraphCrawler()
    strategy = DFSDeepCrawlStrategy(max_depth=2, max_pages=limit)

    pages = await crawl(strategy, crawler, stream)

    expected = [ROOT, FIRST, DESCENDANT, SIBLING][:limit]
    assert crawler.fetched == expected
    assert [page.url for page in pages] == expected
    assert [page.metadata["depth"] for page in pages] == [0, 1, 2, 1][:limit]
    assert [page.metadata["parent_url"] for page in pages] == [
        None,
        ROOT,
        FIRST,
        ROOT,
    ][:limit]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["batch", "stream"])
@pytest.mark.parametrize("new_limit", [2, 3, 4])
async def test_dfs_applies_budget_to_saved_progress(stream, new_limit):
    snapshots = []

    async def save(state):
        snapshots.append(json.loads(json.dumps(state)))

    first_crawler = GraphCrawler()
    interrupted = DFSDeepCrawlStrategy(
        max_depth=2,
        max_pages=4,
        on_state_change=save,
        should_cancel=lambda: len(first_crawler.fetched) >= 3,
    )
    assert [p.url for p in await crawl(interrupted, first_crawler, stream)] == [
        ROOT,
        FIRST,
        DESCENDANT,
    ]
    saved = snapshots[-1]
    assert saved["cancelled"] is True
    assert saved["pages_crawled"] == 3
    assert saved["stack"] == [{"url": SIBLING, "parent_url": ROOT, "depth": 1}]

    resumed = DFSDeepCrawlStrategy(max_depth=2, max_pages=new_limit, resume_state=saved)
    next_crawler = GraphCrawler()

    pages = await crawl(resumed, next_crawler, stream)

    expected = [SIBLING] if new_limit == 4 else []
    assert next_crawler.fetched == expected
    assert [page.url for page in pages] == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["batch", "stream"])
async def test_dfs_failed_page_does_not_consume_the_success_budget(stream):
    crawler = GraphCrawler(failed=[DESCENDANT])
    strategy = DFSDeepCrawlStrategy(max_depth=2, max_pages=3)

    pages = await crawl(strategy, crawler, stream)

    assert crawler.fetched == [ROOT, FIRST, DESCENDANT, SIBLING]
    assert [page.url for page in pages if page.success] == [ROOT, FIRST, SIBLING]
    assert [page.url for page in pages if not page.success] == [DESCENDANT]
