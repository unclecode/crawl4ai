import asyncio
import inspect

import pytest

from crawl4ai.deep_crawling.filters import FilterChain, URLFilter


class CallbackFilter(URLFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def apply(self, url):
        return self.callback()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["coroutine", "task", "future"])
@pytest.mark.parametrize("raises", [False, True])
async def test_sync_exit_cleans_up_prior_awaitables(kind, raises):
    async def wait_forever():
        await asyncio.Event().wait()

    if kind == "coroutine":
        pending = wait_forever()
    elif kind == "task":
        pending = asyncio.create_task(wait_forever())
    else:
        pending = asyncio.get_running_loop().create_future()

    def reject():
        if raises:
            raise ValueError("filter failed")
        return False

    chain = FilterChain([CallbackFilter(lambda: pending), CallbackFilter(reject)])
    try:
        if raises:
            with pytest.raises(ValueError, match="filter failed"):
                await chain.apply("https://example.com")
        else:
            assert not await chain.apply("https://example.com")

        if inspect.iscoroutine(pending):
            assert inspect.getcoroutinestate(pending) == inspect.CORO_CLOSED
        else:
            assert pending.cancelled()
    finally:
        if inspect.iscoroutine(pending):
            pending.close()
        else:
            pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)


@pytest.mark.asyncio
async def test_async_failure_waits_for_sibling_cleanup():
    started = asyncio.Event()
    cleaned = asyncio.Event()

    async def slow_filter():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()

    async def fail_filter():
        await started.wait()
        raise ValueError("async filter failed")

    pending = asyncio.create_task(slow_filter())
    chain = FilterChain([CallbackFilter(lambda: pending), CallbackFilter(fail_filter)])
    try:
        with pytest.raises(ValueError, match="async filter failed"):
            await chain.apply("https://example.com")
        assert cleaned.is_set()
        assert pending.cancelled()
    finally:
        pending.cancel()
        await asyncio.gather(pending, return_exceptions=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [False, True])
async def test_async_filter_result_is_preserved(result):
    async def apply():
        return result

    assert (
        await FilterChain([CallbackFilter(apply)]).apply("https://example.com")
        is result
    )
