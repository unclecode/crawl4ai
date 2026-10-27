"""Regression tests for issue #2242.

1. BFS matched a fetched result back to its parent by re-scanning the whole
   level, which is O(n^2) per level.
2. Best-First only marked a URL visited when it was dequeued, so two pages
   linking to the same third page pushed it onto the priority queue twice.
"""

import asyncio
from collections import Counter
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy


def make_config(stream: bool = False):
    config = MagicMock()
    config.clone = MagicMock(return_value=config)
    config.stream = stream
    return config


class FakeResult:
    """Cheap stand-in for CrawlResult (MagicMock is too slow to time against)."""

    def __init__(self, url: str, children: List[str]):
        self.url = url
        self.success = True
        self.metadata: Dict[str, Any] = {}
        self.links = {
            "internal": [{"href": child} for child in children],
            "external": [],
        }


def make_crawler(link_map: Dict[str, List[str]]):
    """Mock crawler serving a fixed url -> child urls map."""

    async def arun_many(urls, config):
        results = [FakeResult(url, link_map.get(url, [])) for url in urls]

        if config.stream:
            async def gen():
                for result in results:
                    yield result
            return gen()
        return results

    crawler = MagicMock()
    crawler.arun_many = arun_many
    return crawler


ROOT = "https://example.com"


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_bfs_parent_url_is_correct_for_every_child(stream):
    """Parent bookkeeping must stay correct now that it uses a lookup table."""
    children = [f"{ROOT}/p{i}" for i in range(50)]
    link_map = {ROOT: children, **{c: [f"{c}/leaf"] for c in children}}

    strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=100)
    crawler, config = make_crawler(link_map), make_config(stream=stream)

    if stream:
        results = [r async for r in strategy._arun_stream(ROOT, crawler, config)]
    else:
        results = await strategy._arun_batch(ROOT, crawler, config)

    parents = {r.url: r.metadata["parent_url"] for r in results}
    assert parents[ROOT] is None
    assert len(results) == len(children) + 1
    for child in children:
        assert parents[child] == ROOT


@pytest.mark.asyncio
async def test_bfs_level_bookkeeping_scales_linearly():
    """Matching results back to parents must not re-scan the level per result.

    max_depth=0 keeps link discovery out of the loop and resume_state seeds a
    level of arbitrary width, so the only per-result work left is the parent
    lookup. Quadratic bookkeeping shows up as a ~4x cost for 2x the URLs.
    """

    async def run(n: int) -> float:
        urls = [f"{ROOT}/p{i}" for i in range(n)]
        strategy = BFSDeepCrawlStrategy(
            max_depth=0,
            max_pages=n + 1,
            resume_state={
                "visited": urls,
                "pending": [{"url": u, "parent_url": ROOT} for u in urls],
                "depths": {u: 1 for u in urls},
                "pages_crawled": 0,
            },
        )
        crawler, config = make_crawler({}), make_config()
        loop = asyncio.get_running_loop()
        start = loop.time()
        results = await strategy._arun_batch(ROOT, crawler, config)
        elapsed = loop.time() - start
        assert len(results) == n
        return elapsed

    async def best_of(n: int, rounds: int = 3) -> float:
        return min([await run(n) for _ in range(rounds)])

    await run(200)  # warm up
    small = await best_of(2000)
    large = await best_of(4000)

    # 2x the URLs: linear is ~2x, the old full-level scan was ~4x.
    assert large / small < 3, f"level bookkeeping looks superlinear: {large / small:.1f}x"


@pytest.mark.asyncio
async def test_best_first_queues_a_shared_url_once():
    """Two parents at the same depth must enqueue a shared child only once."""
    link_map = {
        ROOT: [f"{ROOT}/a", f"{ROOT}/b"],
        f"{ROOT}/a": [f"{ROOT}/shared"],
        f"{ROOT}/b": [f"{ROOT}/shared"],
        f"{ROOT}/shared": [],
    }

    snapshots: List[List[str]] = []

    async def on_state_change(state: Dict[str, Any]):
        snapshots.append([item["url"] for item in state["queue_items"]])

    strategy = BestFirstCrawlingStrategy(
        max_depth=2, max_pages=10, on_state_change=on_state_change
    )
    crawled = [
        r.url
        async for r in strategy._arun_stream(ROOT, make_crawler(link_map), make_config(stream=True))
    ]

    for queue in snapshots:
        assert not [u for u, n in Counter(queue).items() if n > 1], f"duplicate in queue: {queue}"
    assert sorted(crawled) == sorted(link_map)


@pytest.mark.asyncio
async def test_best_first_keeps_the_shallowest_depth_for_a_shared_url():
    """De-duplicating must not freeze a URL at the depth it was first seen.

    ROOT -> A, B, F0..F11;  A -> C;  C -> X;  B -> X;  X -> LEAF

    The scores crawl C before B, so X is discovered first at depth 3 and only
    later at depth 2. The twelve fillers push B out of the first BATCH_SIZE
    pull, which is what lets C run ahead of B - without them both land in one
    batch and the ordering that exposes this never happens.

    If the shallower re-discovery is dropped as a duplicate, X stays at depth 3
    and link_discovery bails at 4 > max_depth, losing LEAF.
    """
    a, b, c, x, leaf = (f"{ROOT}/{p}" for p in ("a", "b", "c", "x", "leaf"))
    fillers = [f"{ROOT}/f{i}" for i in range(12)]
    link_map = {ROOT: [a, b] + fillers, a: [c], c: [x], b: [x], x: [leaf]}
    scores = {a: 0.9, b: 0.1, c: 0.95, x: 0.5, leaf: 0.5, **{f: 0.8 for f in fillers}}

    class DictScorer:
        def score(self, url):
            return scores.get(url, 0.0)

    strategy = BestFirstCrawlingStrategy(max_depth=3, max_pages=100, url_scorer=DictScorer())
    crawled = {
        r.url: r.metadata["depth"]
        async for r in strategy._arun_stream(ROOT, make_crawler(link_map), make_config(stream=True))
    }

    assert crawled[x] == 2, "X must be crawled at its shallowest depth, not the first one seen"
    assert leaf in crawled, "LEAF is within max_depth once X sits at depth 2"
    assert crawled == {ROOT: 0, a: 1, b: 1, c: 2, x: 2, leaf: 3, **{f: 1 for f in fillers}}
