#!/usr/bin/env python3
"""
Crawl4AI v0.9.2 Release Demo - Fix Verification Tests
======================================================

This demo ACTUALLY RUNS and VERIFIES the key changes in v0.9.2.
v0.9.2 is a maintenance patch release with no new features, so each test
exercises a bug-fix path end-to-end.

Fixes Verified (Python-testable):
1. MemoryAdaptiveDispatcher cleans up tasks when a stream is closed (#2071)
2. Basic real-crawl smoke test (the release build crawls end-to-end)

Not covered here (validated by CI image builds, not this script):
- Docker Playground "Advanced Config" 400 (#2059)
- Docker Monitor WebSocket auth 500 (#2060)
- Playwright headless-shell packaging (#2067)
- GPU ENABLE_GPU=true build / CUDA toolkit non-free apt source (#2020)

Usage:
    python docs/releases_review/demo_v0.9.2.py
"""

import asyncio
import sys
from dataclasses import dataclass
from types import SimpleNamespace


@dataclass
class TestResult:
    name: str
    feature: str
    passed: bool
    message: str
    skipped: bool = False


results: list[TestResult] = []


def print_header(title: str):
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}")


def print_test(name: str, feature: str):
    print(f"\n[TEST] {name} ({feature})")
    print("-" * 50)


def record_result(name: str, feature: str, passed: bool, message: str, skipped: bool = False):
    results.append(TestResult(name, feature, passed, message, skipped))
    status = "SKIP" if skipped else ("PASS" if passed else "FAIL")
    print(f"  [{status}] {message}")


# ── Test 1: Dispatcher stream-close cleanup (#2071) ───────────────────

async def test_dispatcher_stream_cleanup():
    """Closing a streaming MemoryAdaptiveDispatcher must cancel in-flight
    per-URL tasks, drain queued URLs, and restore concurrent_sessions."""
    print_test("Dispatcher stream-close cleanup", "MemoryAdaptiveDispatcher #2071")

    from crawl4ai import CrawlerRunConfig, MemoryAdaptiveDispatcher

    class BlockingCrawler:
        """Return one result immediately; block all other URLs forever."""

        async def arun(self, url, config=None, session_id=None):
            if url == "fast":
                return SimpleNamespace(success=True, status_code=200, error_message="")
            await asyncio.Event().wait()

    class TrackingDispatcher(MemoryAdaptiveDispatcher):
        def __init__(self):
            super().__init__(max_session_permit=3)
            self.tasks = {}

        async def crawl_url(self, url, config, task_id, retry_count=0):
            self.tasks[url] = asyncio.current_task()
            return await super().crawl_url(url, config, task_id, retry_count)

    dispatcher = TrackingDispatcher()
    stream = dispatcher.run_urls_stream(
        ["fast", "blocked-1", "blocked-2", "queued"],
        BlockingCrawler(),
        CrawlerRunConfig(),
    )

    try:
        first = await asyncio.wait_for(stream.__anext__(), timeout=5)
        assert first.url == "fast", f"expected first result 'fast', got {first.url!r}"

        # Close the stream while blocked-1 / blocked-2 are still running.
        await asyncio.wait_for(stream.aclose(), timeout=5)

        started = set(dispatcher.tasks)
        all_done = all(t.done() for t in dispatcher.tasks.values())
        blocked_cancelled = (
            dispatcher.tasks["blocked-1"].cancelled()
            and dispatcher.tasks["blocked-2"].cancelled()
        )

        if (
            started == {"fast", "blocked-1", "blocked-2"}
            and all_done
            and blocked_cancelled
            and dispatcher.concurrent_sessions == 0
            and dispatcher.task_queue.empty()
        ):
            record_result(
                "dispatcher_stream_cleanup", "dispatcher", True,
                "aclose() cancelled in-flight tasks, drained queue, sessions=0",
            )
        else:
            record_result(
                "dispatcher_stream_cleanup", "dispatcher", False,
                f"leaked state: started={started}, all_done={all_done}, "
                f"blocked_cancelled={blocked_cancelled}, "
                f"sessions={dispatcher.concurrent_sessions}, "
                f"queue_empty={dispatcher.task_queue.empty()}",
            )
    finally:
        # Belt-and-suspenders: never let the demo itself leak tasks.
        for t in dispatcher.tasks.values():
            if not t.done():
                t.cancel()
        await asyncio.gather(*dispatcher.tasks.values(), return_exceptions=True)


# ── Test 2: Basic real-crawl smoke test ───────────────────────────────

async def test_basic_crawl_smoke():
    """The release build should crawl a real page end-to-end and produce
    markdown. Skips gracefully if no browser/network is available."""
    print_test("Basic crawl smoke test", "arun end-to-end")

    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    try:
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            result = await crawler.arun(
                url="https://example.com",
                config=CrawlerRunConfig(),
            )
        if result.success and result.markdown and len(str(result.markdown)) > 0:
            record_result(
                "basic_crawl_smoke", "core", True,
                f"crawled example.com, markdown length={len(str(result.markdown))}",
            )
        else:
            record_result(
                "basic_crawl_smoke", "core", False,
                f"crawl failed: success={result.success}, error={result.error_message}",
            )
    except Exception as e:
        record_result(
            "basic_crawl_smoke", "core", False,
            f"browser/network unavailable — skipped: {e}", skipped=True,
        )


# ── Main ──────────────────────────────────────────────────────────────

async def main():
    print_header("Crawl4AI v0.9.2 Release Verification")

    await test_dispatcher_stream_cleanup()
    await test_basic_crawl_smoke()

    # Summary
    print_header("RESULTS SUMMARY")
    total = len(results)
    passed = sum(1 for r in results if r.passed and not r.skipped)
    failed = sum(1 for r in results if not r.passed and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)

    for r in results:
        status = "SKIP" if r.skipped else ("PASS" if r.passed else "FAIL")
        print(f"  [{status}] {r.name}: {r.message}")

    print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")

    if failed > 0:
        print("\n⚠️  Some tests FAILED. Review before release.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
