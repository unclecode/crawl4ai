"""Offline lifecycle regressions for non-streaming dispatcher batches."""

import asyncio
from unittest.mock import Mock

import pytest

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlResult,
    CrawlerRunConfig,
    MemoryAdaptiveDispatcher,
)


class BlockingCrawler:
    def __init__(self):
        self.started = asyncio.Event()
        self.tasks = {}
        self.cleaned = set()

    async def arun(self, url, config=None, session_id=None):
        self.tasks[url] = asyncio.current_task()
        if len(self.tasks) == 2:
            self.started.set()
        try:
            await asyncio.Event().wait()
        finally:
            # Model asynchronous page/context cleanup, which must finish before
            # the batch returns control to its caller.
            await asyncio.sleep(0)
            self.cleaned.add(url)


class TrackingDispatcher(MemoryAdaptiveDispatcher):
    def __init__(self):
        super().__init__(max_session_permit=2, check_interval=0.001)
        self.memory_task = None
        self.memory_cleaned = False

    async def _memory_monitor_task(self):
        self.memory_task = asyncio.current_task()
        try:
            await super()._memory_monitor_task()
        finally:
            await asyncio.sleep(0)
            self.memory_cleaned = True


@pytest.fixture(autouse=True)
def low_memory(monkeypatch):
    monkeypatch.setattr(
        "crawl4ai.async_dispatcher.get_true_memory_usage_percent", lambda: 0.0
    )


@pytest.mark.parametrize("public_api", [False, True], ids=["dispatcher", "arun_many"])
def test_cancelled_batch_cleans_up_before_dispatcher_reuse(public_api, tmp_path):
    async def scenario():
        dispatcher = TrackingDispatcher()
        crawler = BlockingCrawler()
        config = CrawlerRunConfig()
        if public_api:
            # Use the real public wrapper and dispatcher, replacing only the
            # single-page I/O boundary. No browser is launched.
            webcrawler = AsyncWebCrawler(
                crawler_strategy=object(),
                config=BrowserConfig(verbose=False),
                base_directory=str(tmp_path),
            )
            webcrawler.arun = crawler.arun

            async def run(urls):
                return await webcrawler.arun_many(
                    urls, config=config, dispatcher=dispatcher
                )

        else:

            async def run(urls):
                return await dispatcher.run_urls(urls, crawler, config)

        batch = asyncio.create_task(run(["active-1", "active-2", "queued"]))
        try:
            await asyncio.wait_for(crawler.started.wait(), timeout=1)
            batch.cancel()
            with pytest.raises(asyncio.CancelledError):
                await batch

            # Observe immediately: loop shutdown or a sleep must not perform
            # cleanup on behalf of the API under test.
            after_cancel = {
                "all_cancelled": all(t.cancelled() for t in crawler.tasks.values()),
                "cleaned": set(crawler.cleaned),
                "sessions": dispatcher.concurrent_sessions,
                "queued": dispatcher.task_queue.qsize(),
                "memory_done": dispatcher.memory_task.done(),
                "memory_cleaned": dispatcher.memory_cleaned,
            }
            visited = []

            async def successful_arun(url, config=None, session_id=None):
                visited.append(url)
                return CrawlResult(url=url, html="", success=True, status_code=200)

            if public_api:
                webcrawler.arun = successful_arun
            else:
                crawler.arun = successful_arun
            results = await asyncio.wait_for(run(["new"]), timeout=1)

            assert after_cancel == {
                "all_cancelled": True,
                "cleaned": {"active-1", "active-2"},
                "sessions": 0,
                "queued": 0,
                "memory_done": True,
                "memory_cleaned": True,
            }
            assert visited == ["new"]
            assert [result.url for result in results] == ["new"]
        finally:
            # Keep a failing regression run from leaking the exposed tasks.
            if not batch.done():
                batch.cancel()
            await asyncio.gather(batch, return_exceptions=True)
            for task in crawler.tasks.values():
                if not task.done():
                    task.cancel()
            await asyncio.gather(*crawler.tasks.values(), return_exceptions=True)

    asyncio.run(scenario())


def test_memory_monitor_failure_awaits_crawl_cleanup():
    async def scenario():
        crawler = BlockingCrawler()

        class FailingMonitorDispatcher(MemoryAdaptiveDispatcher):
            async def _memory_monitor_task(self):
                await crawler.started.wait()
                raise MemoryError("controlled memory failure")

        dispatcher = FailingMonitorDispatcher(max_session_permit=2)
        try:
            with pytest.raises(MemoryError, match="controlled memory failure"):
                await asyncio.wait_for(
                    dispatcher.run_urls(
                        ["active-1", "active-2", "queued"],
                        crawler,
                        CrawlerRunConfig(),
                    ),
                    timeout=1,
                )
            assert all(task.cancelled() for task in crawler.tasks.values())
            assert crawler.cleaned == {"active-1", "active-2"}
            assert dispatcher.concurrent_sessions == 0
            assert dispatcher.task_queue.empty()
        finally:
            for task in crawler.tasks.values():
                if not task.done():
                    task.cancel()
            await asyncio.gather(*crawler.tasks.values(), return_exceptions=True)

    asyncio.run(scenario())


def test_queue_setup_failure_preserves_error_and_cleans_up():
    async def scenario():
        monitor = Mock()
        monitor.add_task.side_effect = [None, RuntimeError("queue setup failed")]
        dispatcher = MemoryAdaptiveDispatcher(monitor=monitor)
        tasks_before = asyncio.all_tasks()

        with pytest.raises(RuntimeError, match="queue setup failed"):
            await dispatcher.run_urls(
                ["queued", "never-added"], BlockingCrawler(), CrawlerRunConfig()
            )

        assert dispatcher.task_queue.empty()
        assert asyncio.all_tasks() == tasks_before
        monitor.stop.assert_called_once_with()

    asyncio.run(scenario())


def test_individual_crawl_failure_remains_a_failed_result():
    async def scenario():
        class FailingCrawler:
            async def arun(self, url, config=None, session_id=None):
                raise ValueError("controlled crawl failure")

        results = await MemoryAdaptiveDispatcher().run_urls(
            ["failed"], FailingCrawler(), CrawlerRunConfig()
        )
        assert len(results) == 1
        assert results[0].url == "failed"
        assert results[0].result.success is False
        assert results[0].error_message == "controlled crawl failure"

    asyncio.run(scenario())


@pytest.mark.parametrize("urls", [[], ["one"], ["one", "two", "three"]])
def test_successful_batches_leave_no_background_tasks(urls):
    async def scenario():
        class SuccessfulCrawler:
            async def arun(self, url, config=None, session_id=None):
                return CrawlResult(url=url, html="", success=True, status_code=200)

        dispatcher = TrackingDispatcher()
        tasks_before = asyncio.all_tasks()
        results = await dispatcher.run_urls(
            urls, SuccessfulCrawler(), CrawlerRunConfig()
        )
        assert sorted(result.url for result in results) == sorted(urls)
        assert all(result.result.success for result in results)
        assert dispatcher.concurrent_sessions == 0
        assert dispatcher.task_queue.empty()
        assert asyncio.all_tasks() == tasks_before

    asyncio.run(scenario())
