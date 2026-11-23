import asyncio

import pytest

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CrawlResult,
    MemoryAdaptiveDispatcher,
)


class MemoryGate:
    def __init__(self, dispatcher, samples_by_url):
        self.dispatcher = dispatcher
        self.samples_by_url = samples_by_url
        self.attempts = []

    async def wait_if_needed(self, url):
        # Sample memory after scheduling and before the worker starts crawling.
        self.attempts.append(url)
        self.dispatcher.current_memory_percent = (
            99.0 if self.attempts.count(url) <= self.samples_by_url.get(url, 0) else 0.0
        )

    def update_delay(self, url, status_code):
        return True


async def collect(crawler, dispatcher, urls, *, stream):
    results = await crawler.arun_many(
        urls, config=CrawlerRunConfig(stream=stream), dispatcher=dispatcher
    )
    if not stream:
        return results
    return [result async for result in results]


@pytest.fixture
def crawler_and_dispatcher(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "crawl4ai.async_dispatcher.get_true_memory_usage_percent", lambda: 0.0
    )
    crawler = AsyncWebCrawler(
        crawler_strategy=object(),
        config=BrowserConfig(verbose=False),
        base_directory=str(tmp_path),
    )
    dispatcher = MemoryAdaptiveDispatcher(check_interval=0.001, max_session_permit=1)
    return crawler, dispatcher


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["batch", "stream"])
@pytest.mark.parametrize("critical_samples", [1, 2])
async def test_memory_retries_only_return_the_terminal_result(
    crawler_and_dispatcher, monkeypatch, stream, critical_samples
):
    crawler, dispatcher = crawler_and_dispatcher
    url = "https://example.test/page"
    gate = MemoryGate(dispatcher, {url: critical_samples})
    dispatcher.rate_limiter = gate
    visited = []

    async def arun(url, *, config, session_id):
        visited.append(url)
        return CrawlResult(url=url, html="", success=True, status_code=200)

    monkeypatch.setattr(crawler, "arun", arun)
    results = await asyncio.wait_for(
        collect(crawler, dispatcher, [url], stream=stream), timeout=1
    )

    assert [(result.url, result.success) for result in results] == [(url, True)]
    assert gate.attempts == [url] * (critical_samples + 1)
    assert visited == [url]
    assert dispatcher.concurrent_sessions == 0
    assert dispatcher.task_queue.empty()


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["batch", "stream"])
async def test_terminal_results_survive_an_interleaved_retry(
    crawler_and_dispatcher, monkeypatch, stream
):
    crawler, dispatcher = crawler_and_dispatcher
    retry_url = "https://example.test/a-retry"
    other_url = "https://example.test/b-unavailable"
    gate = MemoryGate(dispatcher, {retry_url: 1})
    dispatcher.rate_limiter = gate
    visited = []

    async def arun(url, *, config, session_id):
        visited.append(url)
        success = url == retry_url
        return CrawlResult(
            url=url,
            html="",
            success=success,
            status_code=200 if success else 404,
            error_message="" if success else "page unavailable",
        )

    monkeypatch.setattr(crawler, "arun", arun)
    results = await asyncio.wait_for(
        collect(crawler, dispatcher, [retry_url, other_url], stream=stream), timeout=1
    )

    assert [(result.url, result.success) for result in results] == [
        (other_url, False),
        (retry_url, True),
    ]
    assert gate.attempts == [retry_url, other_url, retry_url]
    assert visited == [other_url, retry_url]
    assert dispatcher.concurrent_sessions == 0
    assert dispatcher.task_queue.empty()


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["batch", "stream"])
@pytest.mark.parametrize(
    "success,error_message,metadata",
    [
        (False, "page unavailable", {}),
        (False, "page was requeued upstream", {}),
        (True, "", {"status": "requeued"}),
    ],
    ids=["ordinary-failure", "retry-word-in-error", "retry-word-in-metadata"],
)
async def test_terminal_results_are_not_mistaken_for_internal_retries(
    crawler_and_dispatcher, monkeypatch, stream, success, error_message, metadata
):
    crawler, dispatcher = crawler_and_dispatcher
    url = "https://example.test/page"

    async def arun(url, *, config, session_id):
        return CrawlResult(
            url=url,
            html="",
            success=success,
            error_message=error_message,
            metadata=metadata,
        )

    monkeypatch.setattr(crawler, "arun", arun)
    results = await asyncio.wait_for(
        collect(crawler, dispatcher, [url], stream=stream), timeout=1
    )

    assert [
        (result.url, result.success, result.error_message, result.metadata)
        for result in results
    ] == [(url, success, error_message, metadata)]
    assert dispatcher.concurrent_sessions == 0
    assert dispatcher.task_queue.empty()
