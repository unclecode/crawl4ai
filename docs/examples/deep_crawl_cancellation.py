"""
Deep Crawl Cancellation Example

This example demonstrates how to implement cancellable deep crawls in Crawl4AI.
Useful for cloud platforms, job management systems, or any scenario where you
need to stop a running crawl mid-execution and retrieve partial results.

Features demonstrated:
1. Callback-based cancellation (check external source like Redis)
2. Direct cancellation via cancel() method
3. Checking cancellation status
4. State tracking with cancelled flag
5. Strategy reuse after cancellation

Requirements:
    pip install crawl4ai redis
"""

import asyncio
import json
from typing import Dict, Any, List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import (
    BFSDeepCrawlStrategy,
    DFSDeepCrawlStrategy,
    BestFirstCrawlingStrategy,
)


# =============================================================================
# Example 1: Basic Cancellation with Callback
# =============================================================================

async def example_callback_cancellation():
    """
    Cancel a crawl after reaching a certain number of pages.
    This simulates checking an external cancellation source.

    Note: We use DFS here because it processes one URL at a time,
    giving precise cancellation control. BFS processes URLs in batches
    (levels), so cancellation happens at level boundaries.
    """
    print("\n" + "="*60)
    print("Example 1: Callback-based Cancellation (DFS)")
    print("="*60)

    pages_crawled = 0
    max_before_cancel = 5

    # This callback is checked before each URL is processed
    async def should_cancel():
        # In production, you might check Redis, a database, or an API:
        # job = await redis.get(f"job:{job_id}")
        # return job.get("status") == "cancelled"
        return pages_crawled >= max_before_cancel

    # Track progress via state changes
    async def on_state_change(state: Dict[str, Any]):
        nonlocal pages_crawled
        pages_crawled = state.get("pages_crawled", 0)
        cancelled = state.get("cancelled", False)
        print(f"  Progress: {pages_crawled} pages | Cancelled: {cancelled}")

    # Use DFS for precise per-URL cancellation control
    strategy = DFSDeepCrawlStrategy(
        max_depth=3,
        max_pages=100,  # Would crawl up to 100, but we'll cancel at 5
        should_cancel=should_cancel,
        on_state_change=on_state_change,
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        verbose=False,
    )

    print(f"Starting crawl (will cancel after {max_before_cancel} pages)...")

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(
            "https://docs.crawl4ai.com",
            config=config
        )

    print(f"\nResults:")
    print(f"  - Crawled {len(results)} pages")
    print(f"  - Strategy cancelled: {strategy.cancelled}")
    print(f"  - Pages crawled counter: {strategy._pages_crawled}")

    return results


# =============================================================================
# Example 2: Direct Cancellation via cancel() Method
# =============================================================================

async def example_direct_cancellation():
    """
    Cancel a crawl directly using the cancel() method.
    This is useful when you have direct access to the strategy instance.
    """
    print("\n" + "="*60)
    print("Example 2: Direct Cancellation via cancel()")
    print("="*60)

    strategy = BFSDeepCrawlStrategy(
        max_depth=3,
        max_pages=100,
    )

    # Cancel after 3 seconds
    async def cancel_after_delay():
        await asyncio.sleep(3)
        print("  Calling strategy.cancel()...")
        strategy.cancel()

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        verbose=False,
    )

    print("Starting crawl (will cancel after 3 seconds)...")

    async with AsyncWebCrawler() as crawler:
        # Start cancellation timer in background
        cancel_task = asyncio.create_task(cancel_after_delay())

        try:
            results = await crawler.arun(
                "https://docs.crawl4ai.com",
                config=config
            )
        finally:
            cancel_task.cancel()
            try:
                await cancel_task
            except asyncio.CancelledError:
                pass

    print(f"\nResults:")
    print(f"  - Crawled {len(results)} pages")
    print(f"  - Strategy cancelled: {strategy.cancelled}")

    return results


# =============================================================================
# Example 3: Streaming Mode with Cancellation
# =============================================================================

async def example_streaming_cancellation():
    """
    Cancel a streaming crawl and process partial results as they arrive.
    """
    print("\n" + "="*60)
    print("Example 3: Streaming Mode with Cancellation")
    print("="*60)

    results_count = 0
    cancel_after = 3

    async def should_cancel():
        return results_count >= cancel_after

    strategy = DFSDeepCrawlStrategy(
        max_depth=5,
        max_pages=50,
        should_cancel=should_cancel,
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,  # Enable streaming
        verbose=False,
    )

    print(f"Starting streaming crawl (will cancel after {cancel_after} results)...")

    results = []
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(
            "https://docs.crawl4ai.com",
            config=config
        ):
            results_count += 1
            results.append(result)
            print(f"  Received result {results_count}: {result.url[:60]}...")

    print(f"\nResults:")
    print(f"  - Received {len(results)} results")
    print(f"  - Strategy cancelled: {strategy.cancelled}")

    return results


# =============================================================================
# Example 4: Strategy Reuse After Cancellation
# =============================================================================

async def example_strategy_reuse():
    """
    Demonstrate that a strategy can be reused after cancellation.
    The cancel flag is automatically reset on the next crawl.
    """
    print("\n" + "="*60)
    print("Example 4: Strategy Reuse After Cancellation")
    print("="*60)

    crawl_number = 0

    async def cancel_first_crawl_only():
        # Only cancel during the first crawl
        return crawl_number == 1

    strategy = BFSDeepCrawlStrategy(
        max_depth=1,
        max_pages=10,
        should_cancel=cancel_first_crawl_only,
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        verbose=False,
    )

    async with AsyncWebCrawler() as crawler:
        # First crawl - will be cancelled immediately
        crawl_number = 1
        print("First crawl (will be cancelled)...")
        results1 = await crawler.arun(
            "https://docs.crawl4ai.com",
            config=config
        )
        print(f"  - Results: {len(results1)}, Cancelled: {strategy.cancelled}")

        # Second crawl - should work normally
        crawl_number = 2
        print("\nSecond crawl (should complete normally)...")
        results2 = await crawler.arun(
            "https://docs.crawl4ai.com",
            config=config
        )
        print(f"  - Results: {len(results2)}, Cancelled: {strategy.cancelled}")

    print(f"\nSummary:")
    print(f"  - First crawl: {len(results1)} results (cancelled)")
    print(f"  - Second crawl: {len(results2)} results (completed)")


# =============================================================================
# Example 5: Best-First Strategy with Cancellation
# =============================================================================

async def example_best_first_cancellation():
    """
    Cancel a Best-First crawl that prioritizes URLs by relevance score.

    Note: Best-First processes URLs in batches (default 10), so cancellation
    happens at batch boundaries. You may see more results than the cancel
    threshold before the crawl stops.
    """
    print("\n" + "="*60)
    print("Example 5: Best-First Strategy with Cancellation")
    print("="*60)

    from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

    pages_crawled = 0
    cancel_threshold = 5

    async def should_cancel():
        return pages_crawled >= cancel_threshold

    async def track_progress(state: Dict[str, Any]):
        nonlocal pages_crawled
        pages_crawled = state.get("pages_crawled", 0)
        print(f"  Pages: {pages_crawled}, Cancelled: {state.get('cancelled', False)}")

    scorer = KeywordRelevanceScorer(
        keywords=["api", "example", "tutorial"],
        weight=0.8
    )

    strategy = BestFirstCrawlingStrategy(
        max_depth=2,
        max_pages=50,
        url_scorer=scorer,
        should_cancel=should_cancel,
        on_state_change=track_progress,
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        verbose=False,
    )

    print(f"Starting Best-First crawl (will cancel after {cancel_threshold} pages)...")
    print("  (Note: Best-First processes in batches, so may crawl slightly more)")

    results = []
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(
            "https://docs.crawl4ai.com",
            config=config
        ):
            results.append(result)
            score = result.metadata.get("score", 0)
            print(f"  Result: {result.url[:50]}... (score: {score:.2f})")

    print(f"\nResults:")
    print(f"  - Crawled {len(results)} high-priority pages")
    print(f"  - Strategy cancelled: {strategy.cancelled}")


# =============================================================================
# Example 6: Production Pattern - Redis-Based Cancellation (Simulated)
# =============================================================================

async def example_production_pattern():
    """
    Simulate a production pattern where cancellation is checked from Redis.
    This pattern is suitable for cloud platforms with job management.
    """
    print("\n" + "="*60)
    print("Example 6: Production Pattern (Simulated Redis)")
    print("="*60)

    # Simulate Redis storage
    redis_storage: Dict[str, str] = {}

    job_id = "crawl-job-12345"

    # Simulate Redis operations
    async def redis_get(key: str) -> str:
        return redis_storage.get(key)

    async def redis_set(key: str, value: str):
        redis_storage[key] = value

    # Initialize job status
    await redis_set(f"{job_id}:status", "running")

    # Cancellation check
    async def check_cancelled():
        status = await redis_get(f"{job_id}:status")
        return status == "cancelled"

    # Progress tracking
    async def save_progress(state: Dict[str, Any]):
        await redis_set(f"{job_id}:state", json.dumps(state))
        await redis_set(f"{job_id}:pages", str(state["pages_crawled"]))
        print(f"  Saved progress: {state['pages_crawled']} pages")

    strategy = BFSDeepCrawlStrategy(
        max_depth=2,
        max_pages=20,
        should_cancel=check_cancelled,
        on_state_change=save_progress,
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        verbose=False,
    )

    # Simulate external cancellation after 2 seconds
    async def external_cancel():
        await asyncio.sleep(2)
        print("\n  [External] Setting job status to 'cancelled'...")
        await redis_set(f"{job_id}:status", "cancelled")

    print("Starting crawl with simulated Redis job management...")

    async with AsyncWebCrawler() as crawler:
        cancel_task = asyncio.create_task(external_cancel())

        try:
            results = await crawler.arun(
                "https://docs.crawl4ai.com",
                config=config
            )
        finally:
            cancel_task.cancel()
            try:
                await cancel_task
            except asyncio.CancelledError:
                pass

    # Final status
    final_status = "cancelled" if strategy.cancelled else "completed"
    await redis_set(f"{job_id}:status", final_status)

    print(f"\nJob completed:")
    print(f"  - Final status: {final_status}")
    print(f"  - Pages crawled: {await redis_get(f'{job_id}:pages')}")
    print(f"  - Results returned: {len(results)}")

    # Show final state
    final_state = json.loads(await redis_get(f"{job_id}:state"))
    print(f"  - State saved: {len(final_state.get('visited', []))} URLs visited")


# =============================================================================
# Main
# =============================================================================

async def main():
    """Run all examples."""
    print("="*60)
    print("Deep Crawl Cancellation Examples")
    print("="*60)

    await example_callback_cancellation()
    await example_direct_cancellation()
    await example_streaming_cancellation()
    await example_strategy_reuse()
    await example_best_first_cancellation()
    await example_production_pattern()

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
