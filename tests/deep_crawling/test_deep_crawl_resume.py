"""
Test Suite: Deep Crawl Resume/Crash Recovery Tests

Tests that verify:
1. State export produces valid JSON-serializable data
2. Resume from checkpoint continues without duplicates
3. Simulated crash at various points recovers correctly
4. State callback fires at expected intervals
5. No damage to existing system behavior (regression tests)
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

from crawl4ai.deep_crawling import (
    BFSDeepCrawlStrategy,
    DFSDeepCrawlStrategy,
    BestFirstCrawlingStrategy,
    FilterChain,
    URLPatternFilter,
    DomainFilter,
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer


# ============================================================================
# Helper Functions for Mock Crawler
# ============================================================================

def create_mock_config(stream=False):
    """Create a mock CrawlerRunConfig."""
    config = MagicMock()
    config.clone = MagicMock(return_value=config)
    config.stream = stream
    return config


def create_mock_crawler_with_links(num_links: int = 3, include_keyword: bool = False):
    """Create mock crawler that returns results with links."""
    call_count = 0

    async def mock_arun_many(urls, config):
        nonlocal call_count
        results = []
        for url in urls:
            call_count += 1
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}

            # Generate child links
            links = []
            for i in range(num_links):
                link_url = f"{url}/child{call_count}_{i}"
                if include_keyword:
                    link_url = f"{url}/important-child{call_count}_{i}"
                links.append({"href": link_url})

            result.links = {"internal": links, "external": []}
            results.append(result)

        # For streaming mode, return async generator
        if config.stream:
            async def gen():
                for r in results:
                    yield r
            return gen()
        return results

    crawler = MagicMock()
    crawler.arun_many = mock_arun_many
    return crawler


def create_mock_crawler_tracking(crawl_order: List[str], return_no_links: bool = False):
    """Create mock crawler that tracks crawl order."""

    async def mock_arun_many(urls, config):
        results = []
        for url in urls:
            crawl_order.append(url)
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}
            result.links = {"internal": [], "external": []} if return_no_links else {"internal": [{"href": f"{url}/child"}], "external": []}
            results.append(result)

        # For streaming mode, return async generator
        if config.stream:
            async def gen():
                for r in results:
                    yield r
            return gen()
        return results

    crawler = MagicMock()
    crawler.arun_many = mock_arun_many
    return crawler


def create_simple_mock_crawler():
    """Basic mock crawler returning 1 result with 2 child links."""
    call_count = 0

    async def mock_arun_many(urls, config):
        nonlocal call_count
        results = []
        for url in urls:
            call_count += 1
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}
            result.links = {
                "internal": [
                    {"href": f"{url}/child1"},
                    {"href": f"{url}/child2"},
                ],
                "external": []
            }
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


def create_mock_crawler_unlimited_links():
    """Mock crawler that always returns links (for testing limits)."""
    async def mock_arun_many(urls, config):
        results = []
        for url in urls:
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}
            result.links = {
                "internal": [{"href": f"{url}/link{i}"} for i in range(10)],
                "external": []
            }
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
# TEST SUITE 1: Crash Recovery Tests
# ============================================================================

class TestBFSResume:
    """BFS strategy resume tests."""

    @pytest.mark.asyncio
    async def test_state_export_json_serializable(self):
        """Verify exported state can be JSON serialized."""
        captured_states: List[Dict] = []

        async def capture_state(state: Dict[str, Any]):
            # Verify JSON serializable
            json_str = json.dumps(state)
            parsed = json.loads(json_str)
            captured_states.append(parsed)

        strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=10,
            on_state_change=capture_state,
        )

        # Create mock crawler that returns predictable results
        mock_crawler = create_mock_crawler_with_links(num_links=3)
        mock_config = create_mock_config()

        results = await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        # Verify states were captured
        assert len(captured_states) > 0

        # Verify state structure
        for state in captured_states:
            assert state["strategy_type"] == "bfs"
            assert "visited" in state
            assert "pending" in state
            assert "depths" in state
            assert "pages_crawled" in state
            assert isinstance(state["visited"], list)
            assert isinstance(state["pending"], list)
            assert isinstance(state["depths"], dict)
            assert isinstance(state["pages_crawled"], int)

    @pytest.mark.asyncio
    async def test_resume_continues_from_checkpoint(self):
        """Verify resume starts from saved state, not beginning."""
        # Simulate state from previous crawl (visited 5 URLs, 3 pending)
        saved_state = {
            "strategy_type": "bfs",
            "visited": [
                "https://example.com",
                "https://example.com/page1",
                "https://example.com/page2",
                "https://example.com/page3",
                "https://example.com/page4",
            ],
            "pending": [
                {"url": "https://example.com/page5", "parent_url": "https://example.com/page2"},
                {"url": "https://example.com/page6", "parent_url": "https://example.com/page3"},
                {"url": "https://example.com/page7", "parent_url": "https://example.com/page3"},
            ],
            "depths": {
                "https://example.com": 0,
                "https://example.com/page1": 1,
                "https://example.com/page2": 1,
                "https://example.com/page3": 1,
                "https://example.com/page4": 1,
                "https://example.com/page5": 2,
                "https://example.com/page6": 2,
                "https://example.com/page7": 2,
            },
            "pages_crawled": 5,
        }

        crawled_urls: List[str] = []

        strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=20,
            resume_state=saved_state,
        )

        # Verify internal state was restored
        assert strategy._resume_state == saved_state

        mock_crawler = create_mock_crawler_tracking(crawled_urls, return_no_links=True)
        mock_config = create_mock_config()

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        # Should NOT re-crawl already visited URLs
        for visited_url in saved_state["visited"]:
            assert visited_url not in crawled_urls, f"Re-crawled already visited: {visited_url}"

        # Should crawl pending URLs
        for pending in saved_state["pending"]:
            assert pending["url"] in crawled_urls, f"Did not crawl pending: {pending['url']}"

    @pytest.mark.asyncio
    async def test_simulated_crash_mid_crawl(self):
        """Simulate crash at URL N, verify resume continues from pending URLs."""
        crash_after = 3
        states_before_crash: List[Dict] = []

        async def capture_until_crash(state: Dict[str, Any]):
            states_before_crash.append(state)
            if state["pages_crawled"] >= crash_after:
                raise Exception("Simulated crash!")

        strategy1 = BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=10,
            on_state_change=capture_until_crash,
        )

        mock_crawler = create_mock_crawler_with_links(num_links=5)
        mock_config = create_mock_config()

        # First crawl - crashes
        with pytest.raises(Exception, match="Simulated crash"):
            await strategy1._arun_batch("https://example.com", mock_crawler, mock_config)

        # Get last state before crash
        last_state = states_before_crash[-1]
        assert last_state["pages_crawled"] >= crash_after

        # Calculate which URLs were already crawled vs pending
        pending_urls = {item["url"] for item in last_state["pending"]}
        visited_urls = set(last_state["visited"])
        already_crawled_urls = visited_urls - pending_urls

        # Resume from checkpoint
        crawled_in_resume: List[str] = []

        strategy2 = BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=10,
            resume_state=last_state,
        )

        mock_crawler2 = create_mock_crawler_tracking(crawled_in_resume, return_no_links=True)

        await strategy2._arun_batch("https://example.com", mock_crawler2, mock_config)

        # Verify already-crawled URLs are not re-crawled
        for crawled_url in already_crawled_urls:
            assert crawled_url not in crawled_in_resume, f"Re-crawled already visited: {crawled_url}"

        # Verify pending URLs are crawled
        for pending_url in pending_urls:
            assert pending_url in crawled_in_resume, f"Did not crawl pending: {pending_url}"

    @pytest.mark.asyncio
    async def test_callback_fires_per_url(self):
        """Verify callback fires after each URL for maximum granularity."""
        callback_count = 0
        pages_crawled_sequence: List[int] = []

        async def count_callbacks(state: Dict[str, Any]):
            nonlocal callback_count
            callback_count += 1
            pages_crawled_sequence.append(state["pages_crawled"])

        strategy = BFSDeepCrawlStrategy(
            max_depth=1,
            max_pages=5,
            on_state_change=count_callbacks,
        )

        mock_crawler = create_mock_crawler_with_links(num_links=2)
        mock_config = create_mock_config()

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        # Callback should fire once per successful URL
        assert callback_count == strategy._pages_crawled, \
            f"Callback fired {callback_count} times, expected {strategy._pages_crawled} (per URL)"

        # pages_crawled should increment by 1 each callback
        for i, count in enumerate(pages_crawled_sequence):
            assert count == i + 1, f"Expected pages_crawled={i+1} at callback {i}, got {count}"

    @pytest.mark.asyncio
    async def test_export_state_returns_last_captured(self):
        """Verify export_state() returns last captured state."""
        last_state = None

        async def capture(state):
            nonlocal last_state
            last_state = state

        strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=5, on_state_change=capture)

        mock_crawler = create_mock_crawler_with_links(num_links=2)
        mock_config = create_mock_config()

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        exported = strategy.export_state()
        assert exported == last_state


class TestDFSResume:
    """DFS strategy resume tests."""

    @pytest.mark.asyncio
    async def test_state_export_includes_stack_and_dfs_seen(self):
        """Verify DFS state includes stack structure and _dfs_seen."""
        captured_states: List[Dict] = []

        async def capture_state(state: Dict[str, Any]):
            captured_states.append(state)

        strategy = DFSDeepCrawlStrategy(
            max_depth=3,
            max_pages=10,
            on_state_change=capture_state,
        )

        mock_crawler = create_mock_crawler_with_links(num_links=2)
        mock_config = create_mock_config()

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        assert len(captured_states) > 0

        for state in captured_states:
            assert state["strategy_type"] == "dfs"
            assert "stack" in state
            assert "dfs_seen" in state
            # Stack items should have depth
            for item in state["stack"]:
                assert "url" in item
                assert "parent_url" in item
                assert "depth" in item

    @pytest.mark.asyncio
    async def test_resume_restores_stack_order(self):
        """Verify DFS stack order is preserved on resume."""
        saved_state = {
            "strategy_type": "dfs",
            "visited": ["https://example.com"],
            "stack": [
                {"url": "https://example.com/deep3", "parent_url": "https://example.com/deep2", "depth": 3},
                {"url": "https://example.com/deep2", "parent_url": "https://example.com/deep1", "depth": 2},
                {"url": "https://example.com/page1", "parent_url": "https://example.com", "depth": 1},
            ],
            "depths": {"https://example.com": 0},
            "pages_crawled": 1,
            "dfs_seen": ["https://example.com", "https://example.com/deep3", "https://example.com/deep2", "https://example.com/page1"],
        }

        crawl_order: List[str] = []

        strategy = DFSDeepCrawlStrategy(
            max_depth=3,
            max_pages=10,
            resume_state=saved_state,
        )

        mock_crawler = create_mock_crawler_tracking(crawl_order, return_no_links=True)
        mock_config = create_mock_config()

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        # DFS pops from end of stack, so order should be: page1, deep2, deep3
        assert crawl_order[0] == "https://example.com/page1"
        assert crawl_order[1] == "https://example.com/deep2"
        assert crawl_order[2] == "https://example.com/deep3"


class TestBestFirstResume:
    """Best-First strategy resume tests."""

    @pytest.mark.asyncio
    async def test_state_export_includes_scored_queue(self):
        """Verify Best-First state includes queue with scores."""
        captured_states: List[Dict] = []

        async def capture_state(state: Dict[str, Any]):
            captured_states.append(state)

        scorer = KeywordRelevanceScorer(keywords=["important"], weight=1.0)

        strategy = BestFirstCrawlingStrategy(
            max_depth=2,
            max_pages=10,
            url_scorer=scorer,
            on_state_change=capture_state,
        )

        mock_crawler = create_mock_crawler_with_links(num_links=3, include_keyword=True)
        mock_config = create_mock_config(stream=True)

        async for _ in strategy._arun_stream("https://example.com", mock_crawler, mock_config):
            pass

        assert len(captured_states) > 0

        for state in captured_states:
            assert state["strategy_type"] == "best_first"
            assert "queue_items" in state
            for item in state["queue_items"]:
                assert "score" in item
                assert "depth" in item
                assert "url" in item
                assert "parent_url" in item

    @pytest.mark.asyncio
    async def test_resume_maintains_priority_order(self):
        """Verify priority queue order is maintained on resume."""
        saved_state = {
            "strategy_type": "best_first",
            "visited": ["https://example.com"],
            "queue_items": [
                {"score": -0.9, "depth": 1, "url": "https://example.com/high-priority", "parent_url": "https://example.com"},
                {"score": -0.5, "depth": 1, "url": "https://example.com/medium-priority", "parent_url": "https://example.com"},
                {"score": -0.1, "depth": 1, "url": "https://example.com/low-priority", "parent_url": "https://example.com"},
            ],
            "depths": {"https://example.com": 0},
            "pages_crawled": 1,
        }

        crawl_order: List[str] = []

        strategy = BestFirstCrawlingStrategy(
            max_depth=2,
            max_pages=10,
            resume_state=saved_state,
        )

        mock_crawler = create_mock_crawler_tracking(crawl_order, return_no_links=True)
        mock_config = create_mock_config(stream=True)

        async for _ in strategy._arun_stream("https://example.com", mock_crawler, mock_config):
            pass

        # Higher negative score = higher priority (min-heap)
        # So -0.9 should be crawled first
        assert crawl_order[0] == "https://example.com/high-priority"


class TestCrossStrategyResume:
    """Tests that apply to all strategies."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("strategy_class,strategy_type", [
        (BFSDeepCrawlStrategy, "bfs"),
        (DFSDeepCrawlStrategy, "dfs"),
        (BestFirstCrawlingStrategy, "best_first"),
    ])
    async def test_no_callback_means_no_overhead(self, strategy_class, strategy_type):
        """Verify no state tracking when callback is None."""
        strategy = strategy_class(max_depth=2, max_pages=5)

        # _queue_shadow should be None for Best-First when no callback
        if strategy_class == BestFirstCrawlingStrategy:
            assert strategy._queue_shadow is None

        # _last_state should be None initially
        assert strategy._last_state is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("strategy_class", [
        BFSDeepCrawlStrategy,
        DFSDeepCrawlStrategy,
        BestFirstCrawlingStrategy,
    ])
    async def test_export_state_returns_last_captured(self, strategy_class):
        """Verify export_state() returns last captured state."""
        last_state = None

        async def capture(state):
            nonlocal last_state
            last_state = state

        strategy = strategy_class(max_depth=2, max_pages=5, on_state_change=capture)

        mock_crawler = create_mock_crawler_with_links(num_links=2)

        if strategy_class == BestFirstCrawlingStrategy:
            mock_config = create_mock_config(stream=True)
            async for _ in strategy._arun_stream("https://example.com", mock_crawler, mock_config):
                pass
        else:
            mock_config = create_mock_config()
            await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        exported = strategy.export_state()
        assert exported == last_state


# ============================================================================
# TEST SUITE 2: Regression Tests (No Damage to Current System)
# ============================================================================

class TestBFSRegressions:
    """Ensure BFS works identically when new params not used."""

    @pytest.mark.asyncio
    async def test_default_params_unchanged(self):
        """Constructor with only original params works."""
        strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            include_external=False,
            max_pages=10,
        )

        assert strategy.max_depth == 2
        assert strategy.include_external == False
        assert strategy.max_pages == 10
        assert strategy._resume_state is None
        assert strategy._on_state_change is None

    @pytest.mark.asyncio
    async def test_filter_chain_still_works(self):
        """FilterChain integration unchanged."""
        filter_chain = FilterChain([
            URLPatternFilter(patterns=["*/blog/*"]),
            DomainFilter(allowed_domains=["example.com"]),
        ])

        strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            filter_chain=filter_chain,
        )

        # Test filter still applies
        assert await strategy.can_process_url("https://example.com/blog/post1", 1) == True
        assert await strategy.can_process_url("https://other.com/blog/post1", 1) == False

    @pytest.mark.asyncio
    async def test_url_scorer_still_works(self):
        """URL scoring integration unchanged."""
        scorer = KeywordRelevanceScorer(keywords=["python", "tutorial"], weight=1.0)

        strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            url_scorer=scorer,
            score_threshold=0.5,
        )

        assert strategy.url_scorer is not None
        assert strategy.score_threshold == 0.5

        # Scorer should work
        score = scorer.score("https://example.com/python-tutorial")
        assert score > 0

    @pytest.mark.asyncio
    async def test_batch_mode_returns_list(self):
        """Batch mode still returns List[CrawlResult]."""
        strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=5)

        mock_crawler = create_simple_mock_crawler()
        mock_config = create_mock_config(stream=False)

        results = await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_max_pages_limit_respected(self):
        """max_pages limit still enforced."""
        strategy = BFSDeepCrawlStrategy(max_depth=10, max_pages=3)

        mock_crawler = create_mock_crawler_unlimited_links()
        mock_config = create_mock_config()

        results = await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        # Should stop at max_pages
        assert strategy._pages_crawled <= 3

    @pytest.mark.asyncio
    async def test_max_depth_limit_respected(self):
        """max_depth limit still enforced."""
        strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=100)

        mock_crawler = create_mock_crawler_unlimited_links()
        mock_config = create_mock_config()

        results = await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        # All results should have depth <= max_depth
        for result in results:
            assert result.metadata.get("depth", 0) <= 2

    @pytest.mark.asyncio
    async def test_metadata_depth_still_set(self):
        """Result metadata still includes depth."""
        strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=5)

        mock_crawler = create_simple_mock_crawler()
        mock_config = create_mock_config()

        results = await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        for result in results:
            assert "depth" in result.metadata
            assert isinstance(result.metadata["depth"], int)

    @pytest.mark.asyncio
    async def test_metadata_parent_url_still_set(self):
        """Result metadata still includes parent_url."""
        strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=5)

        mock_crawler = create_simple_mock_crawler()
        mock_config = create_mock_config()

        results = await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        # First result (start URL) should have parent_url = None
        assert results[0].metadata.get("parent_url") is None

        # Child results should have parent_url set
        for result in results[1:]:
            assert "parent_url" in result.metadata


class TestDFSRegressions:
    """Ensure DFS works identically when new params not used."""

    @pytest.mark.asyncio
    async def test_inherits_bfs_params(self):
        """DFS still inherits all BFS parameters."""
        strategy = DFSDeepCrawlStrategy(
            max_depth=3,
            include_external=True,
            max_pages=20,
            score_threshold=0.5,
        )

        assert strategy.max_depth == 3
        assert strategy.include_external == True
        assert strategy.max_pages == 20
        assert strategy.score_threshold == 0.5

    @pytest.mark.asyncio
    async def test_dfs_seen_initialized(self):
        """DFS _dfs_seen set still initialized."""
        strategy = DFSDeepCrawlStrategy(max_depth=2)

        assert hasattr(strategy, '_dfs_seen')
        assert isinstance(strategy._dfs_seen, set)


class TestBestFirstRegressions:
    """Ensure Best-First works identically when new params not used."""

    @pytest.mark.asyncio
    async def test_default_params_unchanged(self):
        """Constructor with only original params works."""
        strategy = BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            max_pages=10,
        )

        assert strategy.max_depth == 2
        assert strategy.include_external == False
        assert strategy.max_pages == 10
        assert strategy._resume_state is None
        assert strategy._on_state_change is None
        assert strategy._queue_shadow is None  # Not initialized without callback

    @pytest.mark.asyncio
    async def test_scorer_integration(self):
        """URL scorer still affects crawl priority."""
        scorer = KeywordRelevanceScorer(keywords=["important"], weight=1.0)

        strategy = BestFirstCrawlingStrategy(
            max_depth=2,
            max_pages=10,
            url_scorer=scorer,
        )

        assert strategy.url_scorer is scorer


class TestAPICompatibility:
    """Ensure API/serialization compatibility."""

    def test_strategy_signature_backward_compatible(self):
        """Old code calling with positional/keyword args still works."""
        # Positional args (old style)
        s1 = BFSDeepCrawlStrategy(2)
        assert s1.max_depth == 2

        # Keyword args (old style)
        s2 = BFSDeepCrawlStrategy(max_depth=3, max_pages=10)
        assert s2.max_depth == 3

        # Mixed (old style)
        s3 = BFSDeepCrawlStrategy(2, FilterChain(), None, False, float('-inf'), 100)
        assert s3.max_depth == 2
        assert s3.max_pages == 100

    def test_no_required_new_params(self):
        """New params are optional, not required."""
        # Should not raise
        BFSDeepCrawlStrategy(max_depth=2)
        DFSDeepCrawlStrategy(max_depth=2)
        BestFirstCrawlingStrategy(max_depth=2)
