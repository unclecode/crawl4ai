from types import SimpleNamespace

import pytest

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig


class ClosingDispatcher:
    closed = False

    async def run_urls_stream(self, **kwargs):
        try:
            yield SimpleNamespace(
                result=SimpleNamespace(),
                task_id="task",
                memory_usage=0,
                peak_memory=0,
                start_time=0,
                end_time=0,
                error_message="",
            )
        finally:
            self.closed = True


@pytest.mark.asyncio
async def test_arun_many_closes_dispatcher_stream():
    dispatcher = ClosingDispatcher()
    stream = await AsyncWebCrawler().arun_many(
        ["url"], config=CrawlerRunConfig(stream=True), dispatcher=dispatcher
    )
    await stream.__anext__()
    await stream.aclose()
    assert dispatcher.closed
