"""Tests for crawler_pool.restart_permanent().

These exercise the real `deploy/docker/crawler_pool.py` module. `crawl4ai` and
`utils` are stubbed before the import so the pool's lifecycle can be tested
without Playwright, a browser, or a config file — no Docker and no running
server needed.

Regression coverage for the permanent-browser restart, which used to call
init_permanent() while holding the pool LOCK. asyncio.Lock is not reentrant,
so that deadlocked the pool for the life of the process: every later
get_crawler() blocked forever while /health kept answering OK.
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


class FakeCrawler:
    """Records start/close so a test can assert what happened to a browser."""

    instances = []

    def __init__(self, config=None, thread_safe=False):
        self.config = config
        self.started = False
        self.closed = False
        self.close_gate = None  # set to an asyncio.Event to hang close()
        FakeCrawler.instances.append(self)

    async def start(self):
        self.started = True

    async def close(self):
        if self.close_gate is not None:
            await self.close_gate.wait()
        self.closed = True


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

    saved = {name: sys.modules.get(name) for name in ("crawl4ai", "utils", "crawler_pool")}
    sys.modules["crawl4ai"] = fake_crawl4ai
    sys.modules["utils"] = fake_utils
    sys.modules.pop("crawler_pool", None)
    sys.path.insert(0, str(DOCKER_DIR))

    FakeCrawler.instances = []
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

    The restart itself waits on the close, but it holds no lock while it does,
    so unrelated requests keep being served.
    """
    cfg = FakeBrowserConfig(headless=True)
    await pool.init_permanent(cfg)
    pool.PERMANENT.close_gate = asyncio.Event()  # close() will never return

    restart = asyncio.create_task(pool.restart_permanent(cfg))
    await asyncio.sleep(0)  # let it reach the close

    other = FakeBrowserConfig(headless=True, text_mode=True)
    crawler = await asyncio.wait_for(pool.get_crawler(other), timeout=5)
    assert crawler.started

    restart.cancel()
    await asyncio.gather(restart, return_exceptions=True)


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
