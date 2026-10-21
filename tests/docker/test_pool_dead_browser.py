"""The pool must replace a browser whose process died (#842).

Before the fix a crashed Chromium stayed pooled forever: the janitor only
closes idle crawlers, and a dead one kept being handed out, so every request
routed to it failed with "Target page, context or browser has been closed".

The real-browser tests kill Chromium with SIGKILL, the way the OOM killer does.
"""
import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import psutil
import pytest
import pytest_asyncio

from crawl4ai import BrowserConfig, CrawlerRunConfig

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "deploy" / "docker"))

pool = pytest.importorskip("crawler_pool", reason="docker server deps not installed")

HTML = "raw://<html><body><h1>alive</h1></body></html>"


@pytest_asyncio.fixture(autouse=True)
async def clean_pool():
    pool.PERMANENT = None
    pool.HOT_POOL.clear()
    pool.COLD_POOL.clear()
    pool.LAST_USED.clear()
    pool.USAGE_COUNT.clear()
    # The pool refuses new browsers under host memory pressure; not under test.
    with patch.object(pool, "get_container_memory_percent", return_value=10.0):
        yield
    await pool.close_all()
    if pool.PERMANENT:
        await pool.PERMANENT.close()
    pool.PERMANENT = None
    await asyncio.gather(*pool._CLOSING, return_exceptions=True)


def _kill_chromium(crawler):
    """SIGKILL every Chromium process the crawler's Playwright driver launched."""
    bm = crawler.crawler_strategy.browser_manager
    driver_pid = bm.playwright._impl_obj._connection._transport._proc.pid
    procs = psutil.Process(driver_pid).children(recursive=True)
    assert procs, "no browser process found under the driver"
    for p in procs:
        os.kill(p.pid, signal.SIGKILL)
    psutil.wait_procs(procs, timeout=5)


async def _wait_dead(crawler, timeout=5.0):
    """Playwright notices the dead pipe on its next event-loop turns."""
    end = time.monotonic() + timeout
    while pool._is_alive(crawler):
        assert time.monotonic() < end, "pool never saw the browser die"
        await asyncio.sleep(0.05)


async def _crawl_ok(crawler):
    result = await crawler.arun(HTML, config=CrawlerRunConfig())
    assert result.success, result.error_message
    assert "alive" in result.html


# --- real browser ----------------------------------------------------------

@pytest.mark.asyncio
async def test_killed_permanent_browser_is_relaunched():
    cfg = BrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    old = await pool.get_crawler(BrowserConfig(headless=True))
    await pool.release_crawler(old)

    _kill_chromium(old)
    await _wait_dead(old)

    new = await pool.get_crawler(BrowserConfig(headless=True))
    assert new is not old and new is pool.PERMANENT
    await _crawl_ok(new)
    await pool.release_crawler(new)
    assert new.active_requests == 0


@pytest.mark.asyncio
async def test_killed_hot_browser_is_replaced_and_others_untouched():
    cfg_a = BrowserConfig(headless=True, user_agent="a")
    cfg_b = BrowserConfig(headless=True, user_agent="b")
    a = await pool.get_crawler(cfg_a)
    b = await pool.get_crawler(cfg_b)
    for _ in range(2):  # third use promotes "a" to hot
        await pool.release_crawler(await pool.get_crawler(cfg_a))
    await pool.release_crawler(a)
    await pool.release_crawler(b)
    sig_a = pool._sig(cfg_a)
    assert pool.HOT_POOL[sig_a] is a

    _kill_chromium(a)
    await _wait_dead(a)

    new_a = await pool.get_crawler(cfg_a)
    assert new_a is not a
    await _crawl_ok(new_a)
    assert await pool.get_crawler(cfg_b) is b, "a healthy crawler was replaced"
    await _crawl_ok(b)
    await pool.release_crawler(new_a)
    await pool.release_crawler(b)
    # The PR #1946 bug: a replacement must not start with a leaked count,
    # or the janitor never closes it as idle.
    assert new_a.active_requests == 0


@pytest.mark.asyncio
async def test_killed_persistent_context_is_replaced(tmp_path):
    cfg = BrowserConfig(headless=True, use_persistent_context=True,
                        user_data_dir=str(tmp_path / "profile"))
    old = await pool.get_crawler(cfg)
    await pool.release_crawler(old)
    assert pool._is_alive(old)

    _kill_chromium(old)
    await _wait_dead(old)

    new = await pool.get_crawler(cfg)
    assert new is not old
    await _crawl_ok(new)
    await pool.release_crawler(new)


@pytest.mark.asyncio
async def test_concurrent_requests_after_crash_relaunch_once():
    await pool.init_permanent(BrowserConfig(headless=True))
    old = pool.PERMANENT
    _kill_chromium(old)
    await _wait_dead(old)

    got = await asyncio.gather(*[pool.get_crawler(BrowserConfig(headless=True))
                                 for _ in range(10)])
    assert len({id(c) for c in got}) == 1, "relaunched more than once"
    assert got[0] is not old and got[0].active_requests == 10
    await _crawl_ok(got[0])
    for c in got:
        await pool.release_crawler(c)
    assert got[0].active_requests == 0


@pytest.mark.asyncio
async def test_healthy_browser_is_reused_not_replaced():
    cfg = BrowserConfig(headless=True)
    first = await pool.get_crawler(cfg)
    for _ in range(5):
        c = await pool.get_crawler(cfg)
        assert c is first
        await pool.release_crawler(c)
    await pool.release_crawler(first)


# --- failure paths (fakes) -------------------------------------------------

def _fake(alive=True):
    c = MagicMock()
    c.crawler_strategy.browser_manager.browser.is_connected.return_value = alive
    c.close = AsyncMock()
    c.active_requests = 0
    return c


@pytest.mark.asyncio
async def test_failed_relaunch_keeps_retrying():
    dead = _fake(alive=False)
    pool.PERMANENT = dead
    pool.DEFAULT_CONFIG_SIG = pool._sig(pool._apply_pool_defaults(BrowserConfig()))
    fresh = _fake()
    with patch.object(pool, "AsyncWebCrawler") as cls:
        cls.return_value.start = AsyncMock(side_effect=RuntimeError("no shm"))
        with pytest.raises(RuntimeError):
            await pool.get_crawler(BrowserConfig())
        assert pool.PERMANENT is dead  # still dead, so the next call retries

        cls.return_value = fresh
        fresh.start = AsyncMock()
        assert await pool.get_crawler(BrowserConfig()) is fresh
    pool.PERMANENT = None


@pytest.mark.asyncio
async def test_hanging_close_does_not_block_the_pool():
    dead = _fake(alive=False)
    dead.close = AsyncMock(side_effect=lambda: asyncio.sleep(3600))
    pool.PERMANENT = dead
    pool.DEFAULT_CONFIG_SIG = pool._sig(pool._apply_pool_defaults(BrowserConfig()))
    fresh = _fake()
    fresh.start = AsyncMock()
    with patch.object(pool, "AsyncWebCrawler", return_value=fresh):
        got = await asyncio.wait_for(pool.get_crawler(BrowserConfig()), timeout=2)
    assert got is fresh
    for t in pool._CLOSING:
        t.cancel()
    pool.PERMANENT = None


@pytest.mark.asyncio
async def test_janitor_replaces_dead_browsers_without_a_request():
    dead_perm, dead_hot, live_cold = _fake(False), _fake(False), _fake(True)
    dead_hot.active_requests = 2  # in-flight requests on a dead browser
    pool.PERMANENT = dead_perm
    pool.HOT_POOL["h"] = dead_hot
    pool.COLD_POOL["c"] = live_cold
    pool.LAST_USED.update(h=time.time(), c=time.time())
    fresh = _fake()
    fresh.start = AsyncMock()

    class Stop(Exception):
        pass

    real_sleep = asyncio.sleep
    calls = []

    async def one_tick(_):
        calls.append(1)
        if len(calls) > 1:
            raise Stop
        await real_sleep(0)

    with (patch.object(pool, "AsyncWebCrawler", return_value=fresh),
          patch.object(pool.asyncio, "sleep", one_tick)):
        with pytest.raises(Stop):
            await pool.janitor()

    assert pool.PERMANENT is fresh
    assert "h" not in pool.HOT_POOL and "h" not in pool.LAST_USED
    assert pool.COLD_POOL["c"] is live_cold
    await asyncio.gather(*pool._CLOSING)
    dead_perm.close.assert_awaited()
    dead_hot.close.assert_awaited()
    pool.PERMANENT = None
