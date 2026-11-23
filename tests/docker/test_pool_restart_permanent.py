"""Tests for crawler_pool.restart_permanent().

These exercise the real `deploy/docker/crawler_pool.py` module. `crawl4ai` and
`utils` are stubbed before the import so the pool's lifecycle can be tested
without Playwright, a browser, or a config file — no Docker and no running
server needed.

Regression coverage for the permanent-browser restart, which used to call
init_permanent() while holding the pool LOCK. asyncio.Lock is not reentrant,
so that deadlocked the pool for the life of the process: every later
get_crawler() blocked forever while /health kept answering OK.

The restart starts the replacement first, swaps it in under LOCK, then drains
and closes the old browser, so PERMANENT is never None and a failed start
leaves the old browser serving.
"""

import asyncio
import importlib
import sys
import types
from pathlib import Path

import pytest

DOCKER_DIR = Path(__file__).resolve().parents[2] / "deploy" / "docker"


# ---------------------------------------------------------------------------
# Stubs for the two modules crawler_pool imports at module scope
# ---------------------------------------------------------------------------


class FakeBrowserConfig:
    """Minimal stand-in: crawler_pool only needs to_dict() for the signature."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def to_dict(self):
        return dict(self.kwargs)


class FakeDriver:
    """Stands in for the Playwright driver that owns a browser's processes."""

    def __init__(self):
        self.stopped = False

    async def stop(self):
        self.stopped = True


class FakeCrawler:
    """Records start/close so a test can assert what happened to a browser.

    ``next_start_*`` are consumed by the next crawler the pool creates. The
    ``close_*`` knobs are set on an existing instance, e.g. ``pool.PERMANENT``.
    """

    instances = []
    next_start_error = None  # raised by the next start()
    next_start_gate = None  # asyncio.Event the next start() waits on

    def __init__(self, config=None, thread_safe=False):
        self.config = config
        self.started = False
        self.closed = False
        self.close_gate = None  # set to an asyncio.Event to hang close()
        self.close_error = None  # set to an exception close() raises
        self.start_error = FakeCrawler.next_start_error
        self.start_gate = FakeCrawler.next_start_gate
        FakeCrawler.next_start_error = FakeCrawler.next_start_gate = None
        self.driver = FakeDriver()
        self.crawler_strategy = types.SimpleNamespace(
            browser_manager=types.SimpleNamespace(playwright=self.driver)
        )
        FakeCrawler.instances.append(self)

    async def start(self):
        if self.start_gate is not None:
            await self.start_gate.wait()
        if self.start_error is not None:
            raise self.start_error
        self.started = True

    async def close(self):
        if self.close_gate is not None:
            await self.close_gate.wait()
        if self.close_error is not None:
            # Like BrowserManager.close(): the driver is only stopped after
            # browser.close() succeeds, so a failing close leaves it running.
            raise self.close_error
        self.closed = True
        self.driver.stopped = True


@pytest.fixture
def pool():
    """Import crawler_pool against the stubs, fresh for every test."""
    fake_crawl4ai = types.ModuleType("crawl4ai")
    fake_crawl4ai.AsyncWebCrawler = FakeCrawler
    fake_crawl4ai.BrowserConfig = FakeBrowserConfig

    fake_utils = types.ModuleType("utils")
    fake_utils.load_config = lambda: {
        "crawler": {"memory_threshold_percent": 95.0, "pool": {"idle_ttl_sec": 300}}
    }
    fake_utils.get_container_memory_percent = lambda: 10.0

    saved = {
        name: sys.modules.get(name) for name in ("crawl4ai", "utils", "crawler_pool")
    }
    sys.modules["crawl4ai"] = fake_crawl4ai
    sys.modules["utils"] = fake_utils
    sys.modules.pop("crawler_pool", None)
    sys.path.insert(0, str(DOCKER_DIR))

    FakeCrawler.instances = []
    FakeCrawler.next_start_error = FakeCrawler.next_start_gate = None
    try:
        yield importlib.import_module("crawler_pool")
    finally:
        sys.path.remove(str(DOCKER_DIR))
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_restart_permanent_replaces_the_browser(pool):
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    first = pool.PERMANENT
    sig_before = pool.DEFAULT_CONFIG_SIG

    await asyncio.wait_for(pool.restart_permanent(cfg), timeout=5)

    assert first.closed, "the old permanent browser should be closed"
    assert pool.PERMANENT is not first, "a new browser should have replaced it"
    assert pool.PERMANENT.started, "the replacement should be started"
    assert pool.DEFAULT_CONFIG_SIG == sig_before, "same config, same signature"


@pytest.mark.asyncio
async def test_restart_permanent_leaves_the_pool_usable(pool):
    """The regression: after a restart the pool LOCK must still be free."""
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)

    await asyncio.wait_for(pool.restart_permanent(cfg), timeout=5)

    crawler = await asyncio.wait_for(pool.get_crawler(cfg), timeout=5)
    assert crawler is pool.PERMANENT


@pytest.mark.asyncio
async def test_a_hanging_close_does_not_block_the_pool(pool):
    """A browser that will not close must not take the whole server with it.

    The old browser is retired outside LOCK, after the swap, so requests are
    served by the replacement while the old one is still closing.
    """
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    old = pool.PERMANENT
    old.close_gate = asyncio.Event()  # close() will never return

    restart = asyncio.create_task(pool.restart_permanent(cfg))
    await asyncio.sleep(0.1)  # swapped in, now stuck retiring the old browser

    crawler = await asyncio.wait_for(pool.get_crawler(cfg), timeout=5)
    assert crawler is pool.PERMANENT and crawler is not old
    other = FakeBrowserConfig(headless=True, text_mode=True)
    assert (await asyncio.wait_for(pool.get_crawler(other), timeout=5)).started

    restart.cancel()
    await asyncio.gather(restart, return_exceptions=True)


@pytest.mark.asyncio
async def test_default_request_during_a_slow_restart_creates_no_duplicate(pool):
    """PERMANENT stays set while the replacement starts, so a default-config
    request is served by the old browser and nothing lands in the cold pool."""
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    old = pool.PERMANENT

    FakeCrawler.next_start_gate = asyncio.Event()
    gate = FakeCrawler.next_start_gate
    restart = asyncio.create_task(pool.restart_permanent(cfg))
    await asyncio.sleep(0.1)  # the new browser is starting, not yet swapped in

    served = await asyncio.wait_for(pool.get_crawler(cfg), timeout=5)
    assert served is old
    assert not pool.COLD_POOL and not pool.HOT_POOL

    gate.set()
    await pool.release_crawler(served)
    await asyncio.wait_for(restart, timeout=5)
    assert pool.PERMANENT is not old
    assert not pool.COLD_POOL and not pool.HOT_POOL


@pytest.mark.asyncio
async def test_failed_start_leaves_the_old_browser_serving(pool):
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    old = pool.PERMANENT

    FakeCrawler.next_start_error = RuntimeError("chromium is not executable")
    with pytest.raises(RuntimeError):
        await asyncio.wait_for(pool.restart_permanent(cfg), timeout=5)

    failed = FakeCrawler.instances[-1]
    assert pool.PERMANENT is old and old.started and not old.closed
    assert failed is not old and not failed.started
    assert failed.closed, "the browser that failed to start must be torn down"
    assert await pool.get_crawler(cfg) is old


@pytest.mark.asyncio
async def test_restart_cancelled_while_starting_tears_the_new_browser_down(pool):
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    old = pool.PERMANENT

    FakeCrawler.next_start_gate = asyncio.Event()  # start() never finishes
    restart = asyncio.create_task(pool.restart_permanent(cfg))
    await asyncio.sleep(0.1)
    restart.cancel()
    await asyncio.gather(restart, return_exceptions=True)

    assert pool.PERMANENT is old and not old.closed
    assert FakeCrawler.instances[-1].closed


@pytest.mark.asyncio
async def test_failed_start_at_startup_leaves_no_half_built_permanent(pool):
    """init_permanent() used to assign PERMANENT before start(), and arun()
    starts a crawler that is not ready, so a failed start left a global every
    concurrent request could start again."""
    cfg = FakeBrowserConfig(headless=True)

    FakeCrawler.next_start_error = RuntimeError("chromium is not executable")
    with pytest.raises(RuntimeError):
        await pool.init_permanent(cfg)

    assert pool.PERMANENT is None
    assert FakeCrawler.instances[-1].closed


@pytest.mark.asyncio
async def test_restart_waits_for_requests_on_the_old_browser(pool):
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    old = await pool.get_crawler(cfg)  # a request now holds the old browser
    assert old.active_requests == 1

    restart = asyncio.create_task(pool.restart_permanent(cfg))
    await asyncio.sleep(0.5)
    assert pool.PERMANENT is not old, "new requests already go to the new browser"
    assert not old.closed, "the old browser must not be closed under a request"

    await pool.release_crawler(old)
    await asyncio.wait_for(restart, timeout=5)
    assert old.closed


@pytest.mark.asyncio
async def test_failing_close_still_stops_the_old_browsers_driver(pool, caplog):
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    old = pool.PERMANENT
    old.close_error = RuntimeError("browser.close() failed")

    with caplog.at_level("WARNING"):
        await asyncio.wait_for(pool.restart_permanent(cfg), timeout=5)

    assert old.driver.stopped, "Chromium would otherwise outlive the restart"
    assert not pool.PERMANENT.driver.stopped, "the new browser is untouched"
    assert "browser.close() failed" in caplog.text, "the failure is logged"


@pytest.mark.asyncio
async def test_hanging_close_is_bounded_and_still_stops_the_driver(pool):
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    old = pool.PERMANENT
    old.close_gate = asyncio.Event()

    with pytest.raises(asyncio.TimeoutError):
        await pool._retire_browser(old, drain_timeout=0, close_timeout=0.2)

    assert old.driver.stopped


@pytest.mark.asyncio
async def test_concurrent_restarts_retire_every_replaced_browser(pool):
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)

    await asyncio.wait_for(
        asyncio.gather(*(pool.restart_permanent(cfg) for _ in range(3))), timeout=5
    )

    live = [c for c in FakeCrawler.instances if c.started and not c.closed]
    assert live == [pool.PERMANENT], "exactly one browser is left running"


@pytest.mark.asyncio
async def test_init_permanent_under_the_lock_deadlocks(pool):
    """Documents the original bug: the route did exactly this.

    Kept as a guard on the assumption the fix rests on — that LOCK is a plain,
    non-reentrant asyncio.Lock. If this ever stops timing out, restart_permanent
    can be simplified; until then, nothing may call init_permanent() while
    holding it.
    """
    cfg = FakeBrowserConfig(headless=True)

    async def restart_the_old_way():
        async with pool.LOCK:
            await pool.init_permanent(cfg)

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(restart_the_old_way(), timeout=1)
