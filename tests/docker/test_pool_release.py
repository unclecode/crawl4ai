"""Tests for crawler pool release_crawler() and the janitor's stale-lease backstop.

These exercise the real deploy/docker/crawler_pool module (no Docker, no server)
using lightweight stand-in crawler objects.
"""

import asyncio
import copy
import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "deploy", "docker")))

import crawler_pool  # noqa: E402
import utils  # noqa: E402


class FakeCrawler:
    """Stand-in for AsyncWebCrawler; the pool only touches .active_requests."""

    def __init__(self, active_requests=0):
        self.active_requests = active_requests
        self.closed = False

    async def close(self):
        self.closed = True


def _reset_pool():
    crawler_pool.HOT_POOL.clear()
    crawler_pool.COLD_POOL.clear()
    crawler_pool.LAST_USED.clear()
    crawler_pool.USAGE_COUNT.clear()
    crawler_pool.PERMANENT = None
    crawler_pool.DEFAULT_CONFIG_SIG = None


@pytest.fixture(autouse=True)
def clean_pool():
    """Reset module globals so tests can't leak state into each other."""
    _reset_pool()
    yield
    _reset_pool()
    for t in list(crawler_pool._CLOSE_TASKS):
        t.cancel()


async def _drain_close_tasks():
    """Wait for the janitor's fire-and-forget close tasks to finish."""
    tasks = list(crawler_pool._CLOSE_TASKS)
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


# ---------------------------------------------------------------------------
# release_crawler
# ---------------------------------------------------------------------------

class TestReleaseCrawler:

    @pytest.mark.asyncio
    async def test_decrements(self):
        c = FakeCrawler(3)
        await crawler_pool.release_crawler(c)
        assert c.active_requests == 2

    @pytest.mark.asyncio
    async def test_floors_at_zero(self):
        c = FakeCrawler(0)
        await crawler_pool.release_crawler(c)
        assert c.active_requests == 0

    @pytest.mark.asyncio
    async def test_missing_attribute_is_noop(self):
        class Bare:
            pass

        await crawler_pool.release_crawler(Bare())  # must not raise

    @pytest.mark.asyncio
    async def test_does_not_take_the_pool_lock(self):
        """Regression: a release must not block behind a slow janitor/start holding LOCK."""
        c = FakeCrawler(1)
        async with crawler_pool.LOCK:
            await asyncio.wait_for(crawler_pool.release_crawler(c), timeout=0.5)
        assert c.active_requests == 0


    @pytest.mark.asyncio
    async def test_wall_clock_timeout_still_releases(self):
        """AC1's mechanism: asyncio.wait_for expiring must still run the finally that releases."""
        c = FakeCrawler(1)

        async def handler():
            try:
                await asyncio.wait_for(asyncio.sleep(60), timeout=0.01)  # the hung crawl
            finally:
                await crawler_pool.release_crawler(c)

        with pytest.raises(asyncio.TimeoutError):
            await handler()
        assert c.active_requests == 0


# ---------------------------------------------------------------------------
# janitor sweep: idle TTL + stale-lease backstop, driven through the real loop
# ---------------------------------------------------------------------------

def _one_pass_only(real_sleep):
    """Stand-in for asyncio.sleep that lets the janitor run exactly one pass."""
    passes = {"n": 0}

    async def fake(_delay):
        passes["n"] += 1
        if passes["n"] > 1:
            raise asyncio.CancelledError
        await real_sleep(0)

    return fake


class TestJanitorSweep:
    """Drives the real janitor loop with sleeps made instant."""

    def _patch(self, monkeypatch):
        real_sleep = asyncio.sleep
        monkeypatch.setattr(crawler_pool, "get_container_memory_percent", lambda: 10.0)
        monkeypatch.setattr(crawler_pool.asyncio, "sleep", _one_pass_only(real_sleep))

    @pytest.mark.asyncio
    async def test_force_closes_a_cold_browser_busy_past_the_ceiling(self, monkeypatch, caplog):
        c = FakeCrawler(1)  # counter stuck at 1, nobody using it
        crawler_pool.COLD_POOL["deadbeefcafe"] = c
        crawler_pool.LAST_USED["deadbeefcafe"] = (
            crawler_pool.time.time() - crawler_pool.STALE_CEILING - 1
        )
        self._patch(monkeypatch)

        with caplog.at_level("ERROR", logger="crawler_pool"):
            with pytest.raises(asyncio.CancelledError):
                await crawler_pool.janitor()
        await _drain_close_tasks()

        assert c.closed is True, "janitor never reclaimed the pinned browser"
        assert "deadbeefcafe" not in crawler_pool.COLD_POOL
        assert "deadbeef" in caplog.text, "force-close must log an ERROR naming the signature"

    @pytest.mark.asyncio
    async def test_force_closes_a_hot_browser_busy_past_the_ceiling(self, monkeypatch):
        """Both pools must apply the backstop, not just the cold one."""
        c = FakeCrawler(2)
        crawler_pool.HOT_POOL["sig-hot"] = c
        crawler_pool.LAST_USED["sig-hot"] = (
            crawler_pool.time.time() - crawler_pool.STALE_CEILING - 1
        )
        self._patch(monkeypatch)

        with pytest.raises(asyncio.CancelledError):
            await crawler_pool.janitor()
        await _drain_close_tasks()

        assert c.closed is True
        assert "sig-hot" not in crawler_pool.HOT_POOL

    @pytest.mark.asyncio
    async def test_skips_a_browser_idle_past_ttl_but_still_busy(self, monkeypatch):
        """A slow-but-legitimate crawl: past the idle TTL, under the leak ceiling, must not be closed."""
        c = FakeCrawler(1)
        crawler_pool.HOT_POOL["sig-slow"] = c
        # 700s: over hot_ttl (600) so the TTL sweep looks at it, under STALE_CEILING (>= 21600)
        crawler_pool.LAST_USED["sig-slow"] = crawler_pool.time.time() - 700
        self._patch(monkeypatch)

        with pytest.raises(asyncio.CancelledError):
            await crawler_pool.janitor()
        await _drain_close_tasks()

        assert c.closed is False, "closed a browser that was still serving a request"
        assert c.active_requests == 1
        assert crawler_pool.HOT_POOL.get("sig-slow") is c

    @pytest.mark.asyncio
    async def test_closes_an_idle_clean_browser_past_ttl(self, monkeypatch):
        """The ordinary reap path must still work through the background-close helper."""
        c = FakeCrawler(0)
        crawler_pool.COLD_POOL["sig-idle"] = c
        crawler_pool.LAST_USED["sig-idle"] = crawler_pool.time.time() - 400  # > cold_ttl (300)
        self._patch(monkeypatch)

        with pytest.raises(asyncio.CancelledError):
            await crawler_pool.janitor()
        await _drain_close_tasks()

        assert c.closed is True
        assert "sig-idle" not in crawler_pool.COLD_POOL

    @pytest.mark.asyncio
    async def test_a_hung_close_does_not_block_the_sweep(self, monkeypatch):
        """Regression: close() on a wedged browser must never freeze the janitor (it used
        to be awaited while holding the pool LOCK)."""
        class WedgedCrawler(FakeCrawler):
            def __init__(self):
                super().__init__(0)
                self.blocker = asyncio.Event()

            async def close(self):
                await self.blocker.wait()
                self.closed = True

        c = WedgedCrawler()
        crawler_pool.COLD_POOL["sig-wedge"] = c
        crawler_pool.LAST_USED["sig-wedge"] = crawler_pool.time.time() - 400
        self._patch(monkeypatch)

        # If close() were awaited inline this would hang forever instead of raising.
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(crawler_pool.janitor(), timeout=5)

        assert "sig-wedge" not in crawler_pool.COLD_POOL, "pool entry must go even if close hangs"
        assert not crawler_pool.LOCK.locked(), "LOCK must not be held while a close is pending"
        c.blocker.set()
        await _drain_close_tasks()
        assert c.closed is True


class TestStaleCeiling:

    def test_ceiling_derives_from_the_wall_clock(self):
        assert crawler_pool.STALE_CEILING == max(2 * crawler_pool._WALL_CLOCK, 21600)
        # 6h floor: streaming has no deadline; a lower floor kills legitimate long streams
        assert crawler_pool.STALE_CEILING >= 21600

    @pytest.mark.parametrize("configured,expected", [
        (0, 21600), (None, 21600), (False, 21600),   # unset -> auto: max(2 x 1800, 21600)
        (True, 21600),                               # YAML `true` must not become a 1-second ceiling
        (-1, 21600), ("30m", 21600),                 # nonsense -> auto, never break the janitor
        (45, 45), (86400, 86400),                    # a real value is used as written
    ])
    def test_stale_lease_override_resolves_through_the_real_module(self, configured, expected):
        cfg = copy.deepcopy(utils.load_config())
        cfg["limits"]["wall_clock_s"] = 1800
        cfg["crawler"]["pool"]["stale_lease_s"] = configured
        orig = utils.load_config
        utils.load_config = lambda: cfg
        try:
            assert importlib.reload(crawler_pool).STALE_CEILING == expected
        finally:
            utils.load_config = orig
            importlib.reload(crawler_pool)

    def test_bad_wall_clock_value_never_breaks_import(self):
        cfg = copy.deepcopy(utils.load_config())
        cfg["limits"]["wall_clock_s"] = "10m"  # nonsense -> fall back, never break the janitor
        cfg["crawler"]["pool"]["stale_lease_s"] = 0
        orig = utils.load_config
        utils.load_config = lambda: cfg
        try:
            assert importlib.reload(crawler_pool).STALE_CEILING == 21600
        finally:
            utils.load_config = orig
            importlib.reload(crawler_pool)

    def test_shipped_config_enables_the_crawl_deadline(self):
        """Without a deadline a hung crawl never reaches its finally, so nothing releases the browser."""
        assert crawler_pool._WALL_CLOCK > 0


class TestCloseAllDrainsBackgroundCloses:

    @pytest.mark.asyncio
    async def test_close_all_waits_for_pending_close_tasks(self):
        """Shutdown must not destroy live close tasks (no 'Task was destroyed' noise)."""
        started = asyncio.Event()
        finished = asyncio.Event()

        class SlowClose(FakeCrawler):
            async def close(self):
                started.set()
                await asyncio.sleep(0.05)
                self.closed = True
                finished.set()

        c = SlowClose()
        crawler_pool._close_in_background(c)
        await started.wait()

        await crawler_pool.close_all()

        assert finished.is_set(), "close_all returned while a background close was still running"
        assert c.closed is True
        assert not crawler_pool._CLOSE_TASKS

    @pytest.mark.asyncio
    async def test_close_all_never_holds_the_lock_while_a_close_hangs(self):
        """Regression: a wedged browser in the pool at shutdown must not freeze close_all
        while it holds LOCK (closes are routed through the background helper)."""
        blocker = asyncio.Event()

        class Wedged(FakeCrawler):
            async def close(self):
                await blocker.wait()
                self.closed = True

        c = Wedged()
        crawler_pool.HOT_POOL["sig-wedge"] = c

        shutdown = asyncio.create_task(crawler_pool.close_all())
        await asyncio.sleep(0.05)  # close_all is now waiting on the drain
        assert not shutdown.done()
        assert not crawler_pool.LOCK.locked(), "LOCK held while waiting on a wedged close"
        assert not crawler_pool.HOT_POOL, "pool must be cleared even while the close hangs"

        blocker.set()
        await asyncio.wait_for(shutdown, timeout=5)
        assert c.closed is True


# ---------------------------------------------------------------------------
# get_crawler: the acquire side of the counter
# ---------------------------------------------------------------------------

class TestActiveRequestsTracking:
    """Exercises the real get_crawler on pool hits, which never start a browser."""

    @staticmethod
    def _cfg():
        from crawl4ai import BrowserConfig
        return BrowserConfig(headless=True)

    @pytest.mark.asyncio
    async def test_hot_pool_hit_increments(self):
        cfg = self._cfg()
        c = FakeCrawler(0)
        crawler_pool.HOT_POOL[crawler_pool._sig(cfg)] = c

        assert await crawler_pool.get_crawler(cfg) is c
        assert c.active_requests == 1

    @pytest.mark.asyncio
    async def test_cold_pool_hit_increments(self):
        cfg = self._cfg()
        c = FakeCrawler(0)
        crawler_pool.COLD_POOL[crawler_pool._sig(cfg)] = c

        assert await crawler_pool.get_crawler(cfg) is c
        assert c.active_requests == 1

    @pytest.mark.asyncio
    async def test_permanent_hit_increments(self):
        cfg = self._cfg()
        c = FakeCrawler(0)
        crawler_pool.PERMANENT = c
        crawler_pool.DEFAULT_CONFIG_SIG = crawler_pool._sig(cfg)

        assert await crawler_pool.get_crawler(cfg) is c
        assert c.active_requests == 1


    @pytest.mark.asyncio
    async def test_third_use_promotes_cold_to_hot_and_keeps_counter(self):
        cfg = self._cfg()
        sig = crawler_pool._sig(cfg)
        c = FakeCrawler(0)
        crawler_pool.COLD_POOL[sig] = c
        crawler_pool.USAGE_COUNT[sig] = 2  # this call is the third

        assert await crawler_pool.get_crawler(cfg) is c
        assert crawler_pool.HOT_POOL.get(sig) is c
        assert sig not in crawler_pool.COLD_POOL
        assert c.active_requests == 1


    @pytest.mark.asyncio
    async def test_acquire_refreshes_last_used_so_a_busy_browser_is_not_reaped(self):
        """The backstop keys off LAST_USED, so every acquire must bump it."""
        cfg = self._cfg()
        sig = crawler_pool._sig(cfg)
        c = FakeCrawler(0)
        crawler_pool.HOT_POOL[sig] = c
        crawler_pool.LAST_USED[sig] = 0.0  # ancient

        await crawler_pool.get_crawler(cfg)
        assert crawler_pool.time.time() - crawler_pool.LAST_USED[sig] < 5
