"""
Test Suite: configurable `batch_size` (BestFirstCrawlingStrategy) and
`dispatcher` (BFSDeepCrawlStrategy, BestFirstCrawlingStrategy) parameters.

Covers:
1. `batch_size` defaults to the previous hardcoded value (10) and, when
   overridden, actually changes how many URLs are pulled from the priority
   queue per round.
2. `dispatcher` defaults to None and is NOT forwarded to arun_many() in that
   case, so the call shape is unchanged for existing callers/test doubles.
3. `dispatcher`, when explicitly set, is forwarded to arun_many() for both
   BFSDeepCrawlStrategy and BestFirstCrawlingStrategy.
"""

import pytest
from unittest.mock import MagicMock

from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy


def create_mock_config(stream=False):
    config = MagicMock()
    config.clone = MagicMock(return_value=config)
    config.stream = stream
    return config


def create_mock_crawler_old_signature():
    """Mock crawler whose arun_many() only accepts (urls, config) — the
    signature every caller used before `dispatcher` existed. If our strategy
    code unconditionally passed `dispatcher=`, this would raise TypeError."""

    async def mock_arun_many(urls, config):
        results = []
        for url in urls:
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}
            result.links = {"internal": [], "external": []}
            results.append(result)
        if config.stream:

            async def gen():
                for r in results:
                    yield r

            return gen()
        return results

    crawler = MagicMock()
    crawler.arun_many = mock_arun_many
    return crawler


def create_mock_crawler_capturing(recorder: dict):
    """Mock crawler that records the `dispatcher` kwarg and each batch of
    urls it was called with (accepts the new signature)."""

    async def mock_arun_many(urls, config, dispatcher=None):
        recorder.setdefault("dispatcher_calls", []).append(dispatcher)
        recorder.setdefault("batches", []).append(list(urls))
        results = []
        for url in urls:
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}
            result.links = {"internal": [], "external": []}
            results.append(result)
        if config.stream:

            async def gen():
                for r in results:
                    yield r

            return gen()
        return results

    crawler = MagicMock()
    crawler.arun_many = mock_arun_many
    return crawler


def make_queue_items(n: int):
    return [
        {
            "score": -i,
            "depth": 0,
            "url": f"https://example.com/p{i}",
            "parent_url": None,
        }
        for i in range(n)
    ]


class TestBatchSizeDefaults:
    def test_defaults_to_previous_hardcoded_value(self):
        strategy = BestFirstCrawlingStrategy(max_depth=1)
        assert strategy.batch_size == 10

    def test_overridable_via_constructor(self):
        strategy = BestFirstCrawlingStrategy(max_depth=1, batch_size=100)
        assert strategy.batch_size == 100


class TestBatchSizeBehavior:
    @pytest.mark.asyncio
    async def test_custom_batch_size_changes_round_size(self):
        """With 12 queued URLs and batch_size=5, rounds should be 5, 5, 2 —
        not the previous fixed 10, 2."""
        resume_state = {
            "visited": [],
            "depths": {},
            "pages_crawled": 0,
            "queue_items": make_queue_items(12),
        }
        strategy = BestFirstCrawlingStrategy(
            max_depth=1, max_pages=12, batch_size=5, resume_state=resume_state
        )
        recorder = {}
        mock_crawler = create_mock_crawler_capturing(recorder)
        # BestFirstCrawlingStrategy always treats its internal arun_many call as
        # a stream generator (its own batch_config hardcodes stream=True),
        # regardless of the outer config — so the mock config must say stream=True
        # for the mock's async-generator branch to be used, matching reality.
        mock_config = create_mock_config(stream=True)

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        batch_sizes = [len(b) for b in recorder["batches"]]
        assert batch_sizes == [5, 5, 2]

    @pytest.mark.asyncio
    async def test_default_batch_size_matches_old_behavior(self):
        """With no batch_size override, rounds should still be 10, 2 (old default)."""
        resume_state = {
            "visited": [],
            "depths": {},
            "pages_crawled": 0,
            "queue_items": make_queue_items(12),
        }
        strategy = BestFirstCrawlingStrategy(
            max_depth=1, max_pages=12, resume_state=resume_state
        )
        recorder = {}
        mock_crawler = create_mock_crawler_capturing(recorder)
        # BestFirstCrawlingStrategy always treats its internal arun_many call as
        # a stream generator (its own batch_config hardcodes stream=True),
        # regardless of the outer config — so the mock config must say stream=True
        # for the mock's async-generator branch to be used, matching reality.
        mock_config = create_mock_config(stream=True)

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        batch_sizes = [len(b) for b in recorder["batches"]]
        assert batch_sizes == [10, 2]


class TestDispatcherDefaultOmitted:
    """Regression: arun_many() must NOT be called with `dispatcher=` when the
    strategy's own dispatcher is None, so existing (old-signature) test
    doubles/integrations keep working."""

    @pytest.mark.asyncio
    async def test_bfs_batch_mode_works_with_old_signature_mock(self):
        strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler_old_signature()
        mock_config = create_mock_config(stream=False)

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, mock_config
        )
        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_bfs_stream_mode_works_with_old_signature_mock(self):
        strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler_old_signature()
        mock_config = create_mock_config(stream=True)

        results = [
            r
            async for r in strategy._arun_stream(
                "https://example.com", mock_crawler, mock_config
            )
        ]
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_best_first_works_with_old_signature_mock(self):
        strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler_old_signature()
        mock_config = create_mock_config(
            stream=True
        )  # BestFirst always streams internally

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, mock_config
        )
        assert isinstance(results, list)
        assert len(results) > 0


class TestDispatcherForwarded:
    """When a dispatcher IS set, it must actually reach arun_many()."""

    @pytest.mark.asyncio
    async def test_bfs_batch_mode_forwards_dispatcher(self):
        sentinel_dispatcher = object()
        strategy = BFSDeepCrawlStrategy(
            max_depth=1, max_pages=5, dispatcher=sentinel_dispatcher
        )
        recorder = {}
        mock_crawler = create_mock_crawler_capturing(recorder)
        mock_config = create_mock_config(stream=False)

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        assert recorder["dispatcher_calls"]
        assert all(d is sentinel_dispatcher for d in recorder["dispatcher_calls"])

    @pytest.mark.asyncio
    async def test_bfs_stream_mode_forwards_dispatcher(self):
        sentinel_dispatcher = object()
        strategy = BFSDeepCrawlStrategy(
            max_depth=1, max_pages=5, dispatcher=sentinel_dispatcher
        )
        recorder = {}
        mock_crawler = create_mock_crawler_capturing(recorder)
        mock_config = create_mock_config(stream=True)

        results = [
            r
            async for r in strategy._arun_stream(
                "https://example.com", mock_crawler, mock_config
            )
        ]
        assert len(results) > 0
        assert recorder["dispatcher_calls"]
        assert all(d is sentinel_dispatcher for d in recorder["dispatcher_calls"])

    @pytest.mark.asyncio
    async def test_best_first_forwards_dispatcher(self):
        sentinel_dispatcher = object()
        strategy = BestFirstCrawlingStrategy(
            max_depth=1, max_pages=5, dispatcher=sentinel_dispatcher
        )
        recorder = {}
        mock_crawler = create_mock_crawler_capturing(recorder)
        mock_config = create_mock_config(
            stream=True
        )  # BestFirst always streams internally

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        assert recorder["dispatcher_calls"]
        assert all(d is sentinel_dispatcher for d in recorder["dispatcher_calls"])
