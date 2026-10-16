from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import crawl4ai.async_dispatcher as dispatcher


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", [0.0, 100.0])
async def test_first_request_is_immediate_and_next_request_waits(monkeypatch, origin):
    clock = Mock(side_effect=[origin, origin, origin + 0.25, origin + 2.0])
    sleep = AsyncMock()
    monkeypatch.setattr(
        dispatcher, "time", SimpleNamespace(time=clock, monotonic=clock)
    )
    monkeypatch.setattr(dispatcher.asyncio, "sleep", sleep)
    limiter = dispatcher.RateLimiter(base_delay=(2.0, 2.0))

    await limiter.wait_if_needed("https://example.com/first")
    sleep.assert_not_awaited()

    await limiter.wait_if_needed("https://example.com/second")
    sleep.assert_awaited_once_with(1.75)
    assert limiter.domains["example.com"].last_request_time == origin + 2.0


@pytest.mark.asyncio
@pytest.mark.parametrize("jump", [-3600.0, 3600.0])
async def test_wall_clock_changes_do_not_change_request_spacing(monkeypatch, jump):
    wall_clock = Mock(side_effect=[1000.0, 1000.0, 1000.5 + jump, 1002.0 + jump])
    clock = Mock(side_effect=[100.0, 100.0, 100.5, 102.0])
    sleep = AsyncMock()
    monkeypatch.setattr(
        dispatcher, "time", SimpleNamespace(time=wall_clock, monotonic=clock)
    )
    monkeypatch.setattr(dispatcher.asyncio, "sleep", sleep)
    limiter = dispatcher.RateLimiter(base_delay=(2.0, 2.0))

    await limiter.wait_if_needed("https://example.com/first")
    await limiter.wait_if_needed("https://example.com/second")

    sleep.assert_awaited_once_with(1.5)
    wall_clock.assert_not_called()


@pytest.mark.asyncio
async def test_domains_have_independent_request_spacing(monkeypatch):
    clock = Mock(side_effect=[100.0, 100.0, 100.25, 100.25])
    sleep = AsyncMock()
    monkeypatch.setattr(
        dispatcher, "time", SimpleNamespace(time=clock, monotonic=clock)
    )
    monkeypatch.setattr(dispatcher.asyncio, "sleep", sleep)
    limiter = dispatcher.RateLimiter(base_delay=(2.0, 2.0))

    await limiter.wait_if_needed("https://one.example/first")
    await limiter.wait_if_needed("https://two.example/first")

    sleep.assert_not_awaited()
