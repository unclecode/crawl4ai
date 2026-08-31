"""
Test Suite: Deep Crawl ContextVar Safety (Issue #1917)

Tests that DeepCrawlDecorator's ContextVar (deep_crawl_active) works correctly
when the async generator is consumed in a different asyncio context, as happens
with Starlette's StreamingResponse in the Docker API.

The bug: base_strategy.py used ContextVar.reset(token) in the generator's finally
block, but reset() requires the same Context that created the token. When Starlette
consumes the generator in a different Task, the Context changes -> ValueError.

The fix: use ContextVar.set(False) instead of reset(token), which works across
context boundaries.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from crawl4ai.deep_crawling.base_strategy import DeepCrawlDecorator


# ============================================================================
# Helpers
# ============================================================================

def create_mock_result(url="https://example.com"):
    result = MagicMock()
    result.url = url
    result.success = True
    result.metadata = {}
    result.links = {"internal": [], "external": []}
    return result


def create_streaming_strategy(results):
    """Create a mock deep crawl strategy that streams results."""
    strategy = MagicMock()

    async def mock_arun(start_url, crawler, config):
        async def gen():
            for r in results:
                yield r
        return gen()

    strategy.arun = mock_arun
    return strategy


def create_batch_strategy(results):
    """Create a mock deep crawl strategy that returns results as a list."""
    strategy = MagicMock()

    async def mock_arun(start_url, crawler, config):
        return results

    strategy.arun = mock_arun
    return strategy


def create_config(stream=False, strategy=None):
    config = MagicMock()
    config.stream = stream
    config.deep_crawl_strategy = strategy
    return config


# ============================================================================
# Tests: ContextVar cross-context safety (the core #1917 bug)
# ============================================================================

class TestContextVarCrossContext:
    """Tests that deep_crawl_active ContextVar works across task boundaries."""

    @pytest.mark.asyncio
    async def test_streaming_generator_consumed_in_different_task(self):
        """
        Core reproduction of issue #1917:
        Create the generator in one task, consume it in another.
        Before the fix, this raised ValueError.
        """
        mock_results = [create_mock_result(f"https://example.com/{i}") for i in range(3)]
        strategy = create_streaming_strategy(mock_results)
        config = create_config(stream=True, strategy=strategy)

        crawler = MagicMock()
        decorator = DeepCrawlDecorator(crawler)

        async def original_arun(url, config=None, **kwargs):
            return create_mock_result(url)

        wrapped = decorator(original_arun)

        # Call wrapped_arun in the current task — sets the token
        gen = await wrapped("https://example.com", config=config)

        # Consume in a DIFFERENT task (simulates Starlette's StreamingResponse)
        collected = []

        async def consume_in_new_task():
            async for result in gen:
                collected.append(result)

        task = asyncio.create_task(consume_in_new_task())
        await task

        assert len(collected) == 3

    @pytest.mark.asyncio
    async def test_batch_mode_in_different_task(self):
        """Non-streaming mode should also work across task boundaries."""
        mock_results = [create_mock_result("https://example.com")]
        strategy = create_batch_strategy(mock_results)
        config = create_config(stream=False, strategy=strategy)

        crawler = MagicMock()
        decorator = DeepCrawlDecorator(crawler)

        async def original_arun(url, config=None, **kwargs):
            return create_mock_result(url)

        wrapped = decorator(original_arun)
        result = await wrapped("https://example.com", config=config)

        assert result == mock_results


# ============================================================================
# Tests: ContextVar state management
# ============================================================================

class TestContextVarState:
    """Tests that deep_crawl_active is properly managed."""

    @pytest.mark.asyncio
    async def test_flag_is_false_after_streaming_completes(self):
        """deep_crawl_active should be False after the generator is exhausted."""
        strategy = create_streaming_strategy([create_mock_result()])
        config = create_config(stream=True, strategy=strategy)

        crawler = MagicMock()
        decorator = DeepCrawlDecorator(crawler)

        async def original_arun(url, config=None, **kwargs):
            return create_mock_result(url)

        wrapped = decorator(original_arun)
        gen = await wrapped("https://example.com", config=config)

        async for _ in gen:
            pass

        assert decorator.deep_crawl_active.get() == False

    @pytest.mark.asyncio
    async def test_flag_is_false_after_batch_completes(self):
        """deep_crawl_active should be False after batch mode completes."""
        strategy = create_batch_strategy([create_mock_result()])
        config = create_config(stream=False, strategy=strategy)

        crawler = MagicMock()
        decorator = DeepCrawlDecorator(crawler)

        async def original_arun(url, config=None, **kwargs):
            return create_mock_result(url)

        wrapped = decorator(original_arun)
        await wrapped("https://example.com", config=config)

        assert decorator.deep_crawl_active.get() == False

    @pytest.mark.asyncio
    async def test_flag_is_true_during_deep_crawl(self):
        """deep_crawl_active should be True while the generator is being consumed."""
        flag_during_yield = None

        async def capturing_arun(start_url, crawler, config):
            async def gen():
                nonlocal flag_during_yield
                flag_during_yield = DeepCrawlDecorator.deep_crawl_active.get()
                yield create_mock_result(start_url)
            return gen()

        strategy = MagicMock()
        strategy.arun = capturing_arun
        config = create_config(stream=True, strategy=strategy)

        crawler = MagicMock()
        decorator = DeepCrawlDecorator(crawler)

        async def original_arun(url, config=None, **kwargs):
            return create_mock_result(url)

        wrapped = decorator(original_arun)
        gen = await wrapped("https://example.com", config=config)

        async for _ in gen:
            pass

        assert flag_during_yield == True

    @pytest.mark.asyncio
    async def test_flag_prevents_recursive_deep_crawl(self):
        """When deep_crawl_active is True, nested calls should skip deep crawl."""
        crawler = MagicMock()
        decorator = DeepCrawlDecorator(crawler)

        inner_call_hit = False

        async def original_arun(url, config=None, **kwargs):
            nonlocal inner_call_hit
            inner_call_hit = True
            return create_mock_result(url)

        wrapped = decorator(original_arun)

        # Manually set the flag to simulate being inside a deep crawl
        decorator.deep_crawl_active.set(True)
        try:
            strategy = create_batch_strategy([create_mock_result()])
            config = create_config(stream=False, strategy=strategy)
            # Should call original_arun directly, NOT go through strategy
            result = await wrapped("https://example.com", config=config)
            assert inner_call_hit == True
        finally:
            decorator.deep_crawl_active.set(False)

    @pytest.mark.asyncio
    async def test_flag_reset_after_streaming_error(self):
        """deep_crawl_active should be reset even if the generator raises."""
        strategy = MagicMock()

        async def failing_arun(start_url, crawler, config):
            async def gen():
                yield create_mock_result("https://example.com")
                raise RuntimeError("simulated error")
            return gen()

        strategy.arun = failing_arun
        config = create_config(stream=True, strategy=strategy)

        crawler = MagicMock()
        decorator = DeepCrawlDecorator(crawler)

        async def original_arun(url, config=None, **kwargs):
            return create_mock_result(url)

        wrapped = decorator(original_arun)
        gen = await wrapped("https://example.com", config=config)

        with pytest.raises(RuntimeError, match="simulated error"):
            async for _ in gen:
                pass

        assert decorator.deep_crawl_active.get() == False

    @pytest.mark.asyncio
    async def test_flag_reset_after_streaming_error_in_different_task(self):
        """
        Combines #1917 fix with error handling: generator raises in a different task.
        Both the cross-context issue and error cleanup must work together.
        """
        strategy = MagicMock()

        async def failing_arun(start_url, crawler, config):
            async def gen():
                yield create_mock_result("https://example.com")
                raise RuntimeError("simulated error")
            return gen()

        strategy.arun = failing_arun
        config = create_config(stream=True, strategy=strategy)

        crawler = MagicMock()
        decorator = DeepCrawlDecorator(crawler)

        async def original_arun(url, config=None, **kwargs):
            return create_mock_result(url)

        wrapped = decorator(original_arun)
        gen = await wrapped("https://example.com", config=config)

        error_caught = False

        async def consume_in_new_task():
            nonlocal error_caught
            try:
                async for _ in gen:
                    pass
            except RuntimeError:
                error_caught = True

        task = asyncio.create_task(consume_in_new_task())
        await task

        assert error_caught == True


# ============================================================================
# Tests: Concurrent requests
# ============================================================================

class TestConcurrentRequests:
    """Tests that multiple concurrent streaming deep crawls don't interfere."""

    @pytest.mark.asyncio
    async def test_concurrent_streaming_in_separate_tasks(self):
        """
        Multiple concurrent streaming requests consumed in separate tasks.
        This simulates multiple clients hitting /crawl/stream simultaneously.
        """
        crawler = MagicMock()
        decorator = DeepCrawlDecorator(crawler)

        async def original_arun(url, config=None, **kwargs):
            return create_mock_result(url)

        wrapped = decorator(original_arun)
        results_per_request = {}

        async def simulate_request(request_id):
            mock_results = [create_mock_result(f"https://example.com/{request_id}/{i}") for i in range(2)]
            strategy = create_streaming_strategy(mock_results)
            config = create_config(stream=True, strategy=strategy)

            gen = await wrapped(f"https://example.com/{request_id}", config=config)
            results = []
            async for result in gen:
                results.append(result)
                await asyncio.sleep(0.01)  # Interleave with other requests
            results_per_request[request_id] = results

        tasks = [asyncio.create_task(simulate_request(i)) for i in range(3)]
        await asyncio.gather(*tasks)

        assert len(results_per_request) == 3
        for request_id, results in results_per_request.items():
            assert len(results) == 2

        assert decorator.deep_crawl_active.get() == False
