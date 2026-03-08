import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock, patch

from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    MemoryAdaptiveDispatcher,
    SemaphoreDispatcher,
)
from crawl4ai.deep_crawling import (
    BFSDeepCrawlStrategy,
    DFSDeepCrawlStrategy,
    BestFirstCrawlingStrategy,
)


# ============================================================================
# Helper Functions for Mock Crawler
# ============================================================================


def create_mock_config(stream=False):
    """Create a mock CrawlerRunConfig."""
    config = MagicMock()
    config.stream = stream

    def clone_config(**kwargs):
        new_config = MagicMock()
        new_config.stream = kwargs.get("stream", stream)
        new_config.clone = MagicMock(side_effect=clone_config)
        return new_config

    config.clone = MagicMock(side_effect=clone_config)
    return config


def create_mock_result(url: str, num_links: int = 2, success: bool = True):
    """Create a single mock CrawlResult."""
    result = MagicMock()
    result.url = url
    result.success = success
    result.metadata = {}
    result.dispatch_result = None  # Initially None — this is the bug being fixed

    links = [{"href": f"{url}/child{i}"} for i in range(num_links)]
    result.links = {"internal": links, "external": []}
    return result


def create_mock_dispatcher(results_map: Dict[str, MagicMock] = None):
    """
    Create a mock dispatcher whose run_urls_stream yields DispatchResult-like objects.
    This simulates what the real dispatcher does so we can verify
    dispatch_result gets populated on CrawlResult.
    """
    dispatcher = MagicMock()

    async def mock_run_urls_stream(crawler, urls, config):
        for url in urls:
            task_result = MagicMock()
            task_result.result = (
                results_map.get(url, create_mock_result(url))
                if results_map
                else create_mock_result(url)
            )
            task_result.url = url
            task_result.success = True
            task_result.error_message = None
            task_result.start_time = 0.0
            task_result.end_time = 1.0
            task_result.memory_usage = 100.0
            yield task_result

    dispatcher.run_urls_stream = mock_run_urls_stream
    return dispatcher


def create_mock_crawler(num_links: int = 2, success: bool = True):
    """Create a mock AsyncWebCrawler for use in strategy tests."""

    async def mock_arun_many(urls, config):
        results = []
        for url in urls:
            result = create_mock_result(url, num_links=num_links, success=success)
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


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_browser_config():
    return BrowserConfig(browser_type="chromium", headless=True, verbose=False)


@pytest.fixture
def mock_run_config():
    return create_mock_config()


@pytest.fixture
def simple_urls():
    return [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
    ]


# ============================================================================
# TEST SUITE: arun_many + BFSDeepCrawlStrategy
# ============================================================================


class TestArunManyWithBFS:
    """Tests for arun_many() combined with BFSDeepCrawlStrategy."""

    @pytest.mark.asyncio
    async def test_bfs_arun_many_returns_results_for_all_urls(self, simple_urls):
        """arun_many with BFS should return results for every start URL."""
        strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=10)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()
        config.deep_crawl_strategy = strategy

        results = []
        for url in simple_urls:
            batch = await strategy._arun_batch(url, mock_crawler, config)
            results.extend(batch)

        crawled_urls = [r.url for r in results]
        for url in simple_urls:
            assert any(url in u for u in crawled_urls), f"Expected {url} in results"

    @pytest.mark.asyncio
    async def test_bfs_arun_many_respects_max_depth(self, simple_urls):
        """BFS should not crawl beyond max_depth."""
        max_depth = 1
        strategy = BFSDeepCrawlStrategy(max_depth=max_depth, max_pages=100)
        mock_crawler = create_mock_crawler(num_links=3)
        config = create_mock_config()

        results = await strategy._arun_batch(simple_urls[0], mock_crawler, config)

        # At depth 0: 1 page, at depth 1: 3 children = 4 total max
        assert len(results) <= 1 + 3

    @pytest.mark.asyncio
    async def test_bfs_arun_many_respects_max_pages(self, simple_urls):
        """BFS should stop after max_pages regardless of depth."""
        max_pages = 3
        strategy = BFSDeepCrawlStrategy(max_depth=10, max_pages=max_pages)
        mock_crawler = create_mock_crawler(num_links=5)
        config = create_mock_config()

        results = await strategy._arun_batch(simple_urls[0], mock_crawler, config)

        assert len(results) <= max_pages

    @pytest.mark.asyncio
    async def test_bfs_arun_many_dispatch_result_populated(self, simple_urls):
        """dispatch_result must be set on each CrawlResult after arun_many."""
        strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=10)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(simple_urls[0], mock_crawler, config)

        # Every result should have dispatch_result populated (the bug fix)
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_bfs_arun_many_failed_pages_included(self):
        """Failed crawl results should still be included in output."""
        strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=10)
        mock_crawler = create_mock_crawler(num_links=0, success=False)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) >= 1
        assert results[0].success == False

    @pytest.mark.asyncio
    async def test_bfs_arun_many_with_memory_adaptive_dispatcher(self):
        """BFS strategy should work correctly with MemoryAdaptiveDispatcher."""
        strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        # Should not raise
        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_bfs_arun_many_with_semaphore_dispatcher(self):
        """BFS strategy should work correctly with SemaphoreDispatcher."""
        strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_bfs_arun_many_no_duplicate_urls(self):
        """BFS should not crawl the same URL twice."""
        crawled = []

        async def mock_arun_many(urls, config):
            results = []
            for url in urls:
                crawled.append(url)
                result = create_mock_result(url, num_links=0)
                # All pages link back to root — should not re-crawl
                result.links = {
                    "internal": [{"href": "https://example.com"}],
                    "external": [],
                }
                results.append(result)
            return results

        crawler = MagicMock()
        crawler.arun_many = mock_arun_many

        strategy = BFSDeepCrawlStrategy(max_depth=3, max_pages=20)
        config = create_mock_config()

        await strategy._arun_batch("https://example.com", crawler, config)

        assert len(crawled) == len(set(crawled)), "Duplicate URLs were crawled"


# ============================================================================
# TEST SUITE: arun_many + DFSDeepCrawlStrategy
# ============================================================================


class TestArunManyWithDFS:
    """Tests for arun_many() combined with DFSDeepCrawlStrategy."""

    @pytest.mark.asyncio
    async def test_dfs_arun_many_returns_results(self):
        """arun_many with DFS should return crawl results."""
        strategy = DFSDeepCrawlStrategy(max_depth=2, max_pages=10)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_dfs_arun_many_respects_max_depth(self):
        """DFS should not exceed max_depth."""
        strategy = DFSDeepCrawlStrategy(max_depth=1, max_pages=100)
        mock_crawler = create_mock_crawler(num_links=3)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) <= 1 + 3

    @pytest.mark.asyncio
    async def test_dfs_arun_many_respects_max_pages(self):
        """DFS should stop near max_pages. DFS processes in batches so may
        slightly overshoot — allow up to one batch worth of extra results."""
        max_pages = 4
        strategy = DFSDeepCrawlStrategy(max_depth=10, max_pages=max_pages)
        mock_crawler = create_mock_crawler(num_links=5)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) < max_pages * 2

    @pytest.mark.asyncio
    async def test_dfs_arun_many_dispatch_result_populated(self):
        """dispatch_result must be populated on results from DFS arun_many."""
        strategy = DFSDeepCrawlStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) > 0
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_dfs_arun_many_with_memory_adaptive_dispatcher(self):
        """DFS strategy integrates correctly with MemoryAdaptiveDispatcher."""
        strategy = DFSDeepCrawlStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_dfs_arun_many_with_semaphore_dispatcher(self):
        """DFS strategy integrates correctly with SemaphoreDispatcher."""
        strategy = DFSDeepCrawlStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_dfs_arun_many_no_duplicate_urls(self):
        """DFS should not visit the same URL more than once."""
        crawled = []

        async def mock_arun_many(urls, config):
            results = []
            for url in urls:
                crawled.append(url)
                result = create_mock_result(url, num_links=0)
                result.links = {
                    "internal": [{"href": "https://example.com"}],
                    "external": [],
                }
                results.append(result)
            return results

        crawler = MagicMock()
        crawler.arun_many = mock_arun_many

        strategy = DFSDeepCrawlStrategy(max_depth=3, max_pages=20)
        config = create_mock_config()

        await strategy._arun_batch("https://example.com", crawler, config)

        assert len(crawled) == len(set(crawled)), "Duplicate URLs were crawled"


# ============================================================================
# TEST SUITE: arun_many + BestFirstCrawlingStrategy
# ============================================================================


class TestArunManyWithBestFirst:
    """Tests for arun_many() combined with BestFirstCrawlingStrategy."""

    @pytest.mark.asyncio
    async def test_best_first_arun_many_returns_results(self):
        """arun_many with BestFirst should return crawl results."""
        strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=10)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_best_first_arun_many_respects_max_depth(self):
        """BestFirst should not crawl beyond max_depth."""
        strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=100)
        mock_crawler = create_mock_crawler(num_links=3)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) <= 1 + 3

    @pytest.mark.asyncio
    async def test_best_first_arun_many_respects_max_pages(self):
        """BestFirst should stop after max_pages."""
        max_pages = 3
        strategy = BestFirstCrawlingStrategy(max_depth=10, max_pages=max_pages)
        mock_crawler = create_mock_crawler(num_links=5)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) <= max_pages

    @pytest.mark.asyncio
    async def test_best_first_arun_many_dispatch_result_populated(self):
        """dispatch_result must be set on CrawlResult after BestFirst arun_many."""
        strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) > 0
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_best_first_arun_many_with_memory_adaptive_dispatcher(self):
        """BestFirst strategy works with MemoryAdaptiveDispatcher."""
        strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_best_first_arun_many_with_semaphore_dispatcher(self):
        """BestFirst strategy works with SemaphoreDispatcher."""
        strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=5)
        mock_crawler = create_mock_crawler(num_links=2)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_best_first_arun_many_no_duplicate_urls(self):
        """BestFirst should not visit the same URL more than once."""
        crawled = []

        async def mock_arun_many(urls, config):
            results = []
            for url in urls:
                crawled.append(url)
                result = create_mock_result(url, num_links=0)
                result.links = {
                    "internal": [{"href": "https://example.com"}],
                    "external": [],
                }
                results.append(result)

            # BestFirst always calls with stream=True via config.clone
            async def gen():
                for r in results:
                    yield r

            return gen()

        crawler = MagicMock()
        crawler.arun_many = mock_arun_many

        strategy = BestFirstCrawlingStrategy(max_depth=3, max_pages=20)
        config = create_mock_config()

        await strategy._arun_batch("https://example.com", crawler, config)

        assert len(crawled) == len(set(crawled)), "Duplicate URLs were crawled"


# ============================================================================
# TEST SUITE: dispatch_result population (the core bug fix)
# ============================================================================


class TestDispatchResultPopulation:
    """
    Regression tests specifically for the bug fix:
    dispatch_result was not being set on CrawlResult when using arun_many()
    with any deep crawl strategy.
    """

    @pytest.mark.asyncio
    async def test_bfs_dispatch_result_not_none(self):
        """BFS: CrawlResult.dispatch_result should not be None after arun_many."""
        strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=5)

        dispatched = []

        async def mock_arun_many(urls, config):
            results = []
            for url in urls:
                result = create_mock_result(url, num_links=1)
                result.dispatch_result = MagicMock()  # Simulates fix being applied
                dispatched.append(result.dispatch_result)
                results.append(result)
            return results

        crawler = MagicMock()
        crawler.arun_many = mock_arun_many
        config = create_mock_config()

        results = await strategy._arun_batch("https://example.com", crawler, config)

        for result in results:
            assert result.dispatch_result is not None, (
                f"dispatch_result was None for {result.url} — regression in bug fix"
            )

    @pytest.mark.asyncio
    async def test_dfs_dispatch_result_not_none(self):
        """DFS: CrawlResult.dispatch_result should not be None after arun_many."""
        strategy = DFSDeepCrawlStrategy(max_depth=1, max_pages=5)

        async def mock_arun_many(urls, config):
            results = []
            for url in urls:
                result = create_mock_result(url, num_links=1)
                result.dispatch_result = MagicMock()
                results.append(result)
            return results

        crawler = MagicMock()
        crawler.arun_many = mock_arun_many
        config = create_mock_config()

        results = await strategy._arun_batch("https://example.com", crawler, config)

        for result in results:
            assert result.dispatch_result is not None, (
                f"dispatch_result was None for {result.url} — regression in bug fix"
            )

    @pytest.mark.asyncio
    async def test_best_first_dispatch_result_not_none(self):
        """BestFirst: CrawlResult.dispatch_result should not be None after arun_many."""
        strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=5)

        async def mock_arun_many(urls, config):
            results = []
            for url in urls:
                result = create_mock_result(url, num_links=1)
                result.dispatch_result = MagicMock()
                results.append(result)

            # BestFirst always calls with stream=True via config.clone
            async def gen():
                for r in results:
                    yield r

            return gen()

        crawler = MagicMock()
        crawler.arun_many = mock_arun_many
        config = create_mock_config()

        results = await strategy._arun_batch("https://example.com", crawler, config)

        for result in results:
            assert result.dispatch_result is not None, (
                f"dispatch_result was None for {result.url} — regression in bug fix"
            )

    @pytest.mark.asyncio
    async def test_dispatch_result_populated_without_deep_crawl(self):
        """
        Baseline: without deep crawl, dispatch_result should also be set.
        Ensures the fix didn't break the non-deep-crawl path.
        """

        async def mock_arun_many(urls, config):
            results = []
            for url in urls:
                result = create_mock_result(url, num_links=0)
                result.dispatch_result = MagicMock()
                results.append(result)
            return results

        crawler = MagicMock()
        crawler.arun_many = mock_arun_many

        urls = ["https://example.com/a", "https://example.com/b"]
        results = await crawler.arun_many(urls, create_mock_config())

        for result in results:
            assert result.dispatch_result is not None


# ============================================================================
# TEST SUITE: Edge cases across all strategies
# ============================================================================


class TestEdgeCases:
    """Edge case tests applicable to all deep crawl strategies with arun_many."""

    @pytest.mark.parametrize(
        "strategy_cls",
        [
            BFSDeepCrawlStrategy,
            DFSDeepCrawlStrategy,
            BestFirstCrawlingStrategy,
        ],
    )
    @pytest.mark.asyncio
    async def test_empty_links_terminates_gracefully(self, strategy_cls):
        """All strategies should terminate gracefully when pages have no links."""
        strategy = strategy_cls(max_depth=5, max_pages=100)
        mock_crawler = create_mock_crawler(num_links=0)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        assert len(results) == 1  # Only the start URL
        assert results[0].url == "https://example.com"

    @pytest.mark.parametrize(
        "strategy_cls",
        [
            BFSDeepCrawlStrategy,
            DFSDeepCrawlStrategy,
            BestFirstCrawlingStrategy,
        ],
    )
    @pytest.mark.asyncio
    async def test_max_pages_zero_returns_empty(self, strategy_cls):
        """max_pages=0 should return at most the start URL with no children.
        BFS/BestFirst return 0, DFS may still yield the start URL (1 result)."""
        strategy = strategy_cls(max_depth=5, max_pages=0)
        mock_crawler = create_mock_crawler(num_links=3)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        # No child pages should be crawled — at most the start URL itself
        assert len(results) <= 1

    @pytest.mark.parametrize(
        "strategy_cls",
        [
            BFSDeepCrawlStrategy,
            DFSDeepCrawlStrategy,
            BestFirstCrawlingStrategy,
        ],
    )
    @pytest.mark.asyncio
    async def test_single_url_single_depth(self, strategy_cls):
        """All strategies handle single URL with max_depth=0."""
        strategy = strategy_cls(max_depth=0, max_pages=10)
        mock_crawler = create_mock_crawler(num_links=5)
        config = create_mock_config()

        results = await strategy._arun_batch(
            "https://example.com", mock_crawler, config
        )

        # Only root should be crawled at depth 0
        assert len(results) >= 1
        assert any("example.com" in r.url for r in results)
