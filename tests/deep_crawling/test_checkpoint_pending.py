"""Per-URL checkpoints must retain the unprocessed part of a fetched batch."""

import json

import pytest

from crawl4ai import CrawlerRunConfig, CrawlResult
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy

ROOT = "https://example.com/"
SIBLINGS = [ROOT + name for name in ("a", "b", "c")]
GRAPH = {ROOT: SIBLINGS, **{url: [url + "/child"] for url in SIBLINGS}}


class GraphCrawler:
    """Keep the real strategy/config/result objects; replace only page fetching."""

    def __init__(self, failures=()):
        self.calls = []
        self.failures = set(failures)

    async def arun_many(self, urls, config, **kwargs):
        self.calls.append(list(urls))
        results = [
            CrawlResult(
                url=url,
                html="<p>fixture</p>",
                success=url not in self.failures,
                links={
                    "internal": [{"href": target} for target in GRAPH.get(url, [])],
                    "external": [],
                },
            )
            for url in urls
        ]

        async def stream():
            for result in reversed(results):
                yield result

        return stream() if config.stream else results


class SimulatedCrash(Exception):
    pass


async def collect(strategy, crawler, stream):
    result = await strategy.arun(ROOT, crawler, CrawlerRunConfig(stream=stream))
    return [item async for item in result] if stream else result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strategy_type", [BFSDeepCrawlStrategy, BestFirstCrawlingStrategy]
)
@pytest.mark.parametrize("stream", [False, True])
async def test_resume_retains_unprocessed_batch_and_discovered_children(
    strategy_type, stream
):
    snapshots = []

    async def persist(state):
        snapshots.append(json.loads(json.dumps(state)))
        if state["pages_crawled"] == 2:
            raise SimulatedCrash

    strategy = strategy_type(max_depth=2, max_pages=20, on_state_change=persist)
    with pytest.raises(SimulatedCrash):
        await collect(strategy, GraphCrawler(), stream)

    checkpoint = snapshots[-1]
    first = (
        SIBLINGS[-1]
        if strategy_type is BFSDeepCrawlStrategy and stream
        else SIBLINGS[0]
    )
    expected_remaining = set(SIBLINGS) - {first}
    expected_remaining.update(url + "/child" for url in SIBLINGS)
    resumed_crawler = GraphCrawler()
    resumed = strategy_type(max_depth=2, max_pages=20, resume_state=checkpoint)
    results = await collect(resumed, resumed_crawler, stream)

    assert {result.url for result in results} == expected_remaining
    assert len(results) == len(expected_remaining)
    assert resumed._pages_crawled == 7
    for result in results:
        expected_parent = (
            result.url.rsplit("/", 1)[0] if result.url.endswith("/child") else ROOT
        )
        assert result.metadata["parent_url"] == expected_parent
        assert result.metadata["depth"] == (2 if result.url.endswith("/child") else 1)
    if strategy_type is BFSDeepCrawlStrategy:
        assert set(resumed_crawler.calls[0]) == set(SIBLINGS) - {first}
        assert set(resumed_crawler.calls[1]) == {url + "/child" for url in SIBLINGS}
    else:
        pending = {item["url"] for item in checkpoint["queue_items"]}
        assert pending.isdisjoint(checkpoint["visited"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strategy_type", [BFSDeepCrawlStrategy, BestFirstCrawlingStrategy]
)
@pytest.mark.parametrize("stream", [False, True])
async def test_without_checkpoint_preserves_ordinary_traversal(strategy_type, stream):
    strategy = strategy_type(max_depth=2, max_pages=20)
    results = await collect(strategy, GraphCrawler(), stream)
    expected = {ROOT, *SIBLINGS, *(url + "/child" for url in SIBLINGS)}
    assert {result.url for result in results} == expected
    assert len(results) == len(expected)
    assert strategy.export_state() is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strategy_type", [BFSDeepCrawlStrategy, BestFirstCrawlingStrategy]
)
@pytest.mark.parametrize("stream", [False, True])
async def test_checkpoint_does_not_retry_completed_failed_result(strategy_type, stream):
    failed = (
        SIBLINGS[-1]
        if strategy_type is BFSDeepCrawlStrategy and stream
        else SIBLINGS[0]
    )
    snapshots = []

    async def persist(state):
        snapshots.append(json.loads(json.dumps(state)))
        if state["pages_crawled"] == 2:
            raise SimulatedCrash

    strategy = strategy_type(max_depth=2, max_pages=20, on_state_change=persist)
    with pytest.raises(SimulatedCrash):
        await collect(strategy, GraphCrawler(failures=[failed]), stream)

    checkpoint = snapshots[-1]
    pending_key = "pending" if strategy_type is BFSDeepCrawlStrategy else "queue_items"
    assert failed not in {item["url"] for item in checkpoint[pending_key]}
    resumed_crawler = GraphCrawler()
    resumed = strategy_type(max_depth=2, max_pages=20, resume_state=checkpoint)
    results = await collect(resumed, resumed_crawler, stream)
    assert failed not in {result.url for result in results}
    assert failed + "/child" not in {result.url for result in results}
    assert resumed._pages_crawled == 5
