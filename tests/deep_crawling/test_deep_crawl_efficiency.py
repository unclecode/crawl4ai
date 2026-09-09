"""
Regression tests for GH issue #2242:

1. BFSDeepCrawlStrategy re-scanned the entire current level (a Python list)
   once per fetched result to find that result's parent URL, making the
   per-level bookkeeping O(n^2) instead of O(n).
2. BestFirstCrawlingStrategy.link_discovery only checked `visited` without
   updating it, so a URL discovered by two sibling pages in the same batch
   was scored and enqueued twice instead of once.
"""

import asyncio
import time

import pytest
from unittest.mock import MagicMock

from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy


def create_mock_config(stream=False):
    config = MagicMock()
    config.stream = stream

    def clone_config(**kwargs):
        new_config = MagicMock()
        new_config.stream = kwargs.get("stream", stream)
        new_config.clone = MagicMock(side_effect=clone_config)
        return new_config

    config.clone = MagicMock(side_effect=clone_config)
    return config


def create_fanout_crawler(start_url, num_children):
    """Mock crawler where `start_url` links to `num_children` leaf pages."""

    async def mock_arun_many(urls, config):
        results = []
        for url in urls:
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}
            if url == start_url:
                links = [
                    {"href": f"{start_url}/child{i}"} for i in range(num_children)
                ]
            else:
                links = []
            result.links = {"internal": links, "external": []}
            results.append(result)
        return results

    crawler = MagicMock()
    crawler.arun_many = mock_arun_many
    return crawler


class TestBFSParentLookupPerformance:
    """
    The parent lookup used to be `next((parent for (u, parent) in
    current_level if u == url), None)`, executed once per result in the
    level: O(n) work per result, O(n^2) for the whole level. Measure the
    strategy's own wall-clock growth between a small and a large level -
    a self-relative check that doesn't depend on absolute machine speed.
    Linear behavior keeps the ratio close to the level-size ratio (8x);
    quadratic behavior pushes it towards its square (64x).
    """

    @pytest.mark.asyncio
    async def test_parent_lookup_scales_linearly_with_level_size(self):
        start_url = "https://example.com/start"
        small_n, large_n = 2500, 20000

        async def timed_run(num_children):
            strategy = BFSDeepCrawlStrategy(max_depth=2)
            crawler = create_fanout_crawler(start_url, num_children)
            config = create_mock_config(stream=False)
            t0 = time.perf_counter()
            results = await strategy._arun_batch(start_url, crawler, config)
            elapsed = time.perf_counter() - t0
            assert len(results) == num_children + 1
            return elapsed

        small_time = await timed_run(small_n)
        large_time = await timed_run(large_n)

        growth = large_time / small_time
        # Level size grows 8x; O(n) bookkeeping keeps growth near 8x while
        # O(n^2) bookkeeping pushes it towards 64x. 12x cleanly separates
        # the two on this workload (measured ~8.3x fixed, ~16.9x unfixed).
        assert growth < 12, (
            f"per-level bookkeeping does not scale linearly: {small_n} "
            f"URLs took {small_time:.3f}s, {large_n} URLs took "
            f"{large_time:.3f}s ({growth:.1f}x for an {large_n / small_n:.0f}x "
            "increase in level size)"
        )


class CountingScorer:
    """Records how many times each URL is scored."""

    def __init__(self):
        self.call_counts = {}

    def score(self, url):
        self.call_counts[url] = self.call_counts.get(url, 0) + 1
        return 0.0


class TestBestFirstDuplicateEnqueue:
    """
    `link_discovery` checked `if base_url in visited: continue` but never
    added newly discovered URLs to `visited`. When two sibling pages in the
    same batch link to the same third URL, that URL was scored and pushed
    onto the priority queue twice before either copy was ever dequeued.
    """

    @pytest.mark.asyncio
    async def test_shared_link_is_scored_and_enqueued_once(self):
        start_url = "https://example.com/start"
        page_a = "https://example.com/a"
        page_b = "https://example.com/b"
        shared = "https://example.com/shared"

        async def mock_arun_many(urls, config):
            async def gen():
                for url in urls:
                    result = MagicMock()
                    result.url = url
                    result.success = True
                    result.metadata = {}
                    if url == start_url:
                        links = [{"href": page_a}, {"href": page_b}]
                    elif url in (page_a, page_b):
                        links = [{"href": shared}]
                    else:
                        links = []
                    result.links = {"internal": links, "external": []}
                    yield result

            return gen()

        crawler = MagicMock()
        crawler.arun_many = mock_arun_many
        config = create_mock_config(stream=True)

        scorer = CountingScorer()
        strategy = BestFirstCrawlingStrategy(max_depth=2, url_scorer=scorer)

        results = []
        async for result in strategy._arun_best_first(start_url, crawler, config):
            results.append(result)

        assert scorer.call_counts.get(shared, 0) == 1
        assert sum(1 for r in results if r.url == shared) == 1
