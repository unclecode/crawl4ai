"""Tests for crash recovery additions to crawler_pool.py.

Covers the three-layer crash recovery mechanism added in the pool-crash-recovery PR:

  1. _is_crawler_alive()    — liveness detection via Playwright internals
  2. _replace_permanent()   — dead permanent browser replacement
  3. _replace_pooled()      — dead hot/cold browser replacement
  4. get_crawler() recovery — on-demand crash recovery paths
  5. janitor() health sweep — proactive dead-browser detection

All tests use mocks — no live browser or Docker required.

Import note: crawler_pool.py lives in deploy/docker/ and has a local `utils`
dependency.  We inject a shim module into sys.modules before importing so the
tests run identically whether or not the container helpers are present.
"""

import asyncio
import sys
import time
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# One-time module shim — must happen before `import crawler_pool`
# ---------------------------------------------------------------------------

_DOCKER_DIR = Path(__file__).resolve().parent.parent.parent / "deploy" / "docker"

_fake_utils = types.ModuleType("utils")
_fake_utils.load_config = lambda: {}
_fake_utils.get_container_memory_percent = lambda: 50.0
sys.modules.setdefault("utils", _fake_utils)

if str(_DOCKER_DIR) not in sys.path:
    sys.path.insert(0, str(_DOCKER_DIR))

import crawler_pool  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_standard_crawler(*, alive: bool = True) -> MagicMock:
    """Return a fake AsyncWebCrawler backed by a standard (non-persistent) browser.

    If *alive* is True the Playwright transport reference is a real MagicMock
    object (truthy).  If False the transport is None, which is the synchronous
    signal we use as the dead-browser indicator.
    """
    transport = MagicMock() if alive else None

    conn = MagicMock()
    conn._transport = transport

    channel = MagicMock()
    channel._connection = conn

    browser = MagicMock()
    browser._channel = channel
    browser.is_connected.return_value = alive

    bm = MagicMock()
    bm._launched_persistent = False
    bm.browser = browser

    strategy = MagicMock()
    strategy.browser_manager = bm

    crawler = MagicMock()
    crawler.crawler_strategy = strategy
    crawler.active_requests = 0
    return crawler


def _make_persistent_crawler(*, alive: bool = True) -> MagicMock:
    """Return a fake AsyncWebCrawler backed by a persistent browser context."""
    transport = MagicMock() if alive else None

    conn = MagicMock()
    conn._transport = transport

    impl = MagicMock()
    impl._connection = conn

    ctx = MagicMock()
    ctx._impl_obj = impl

    bm = MagicMock()
    bm._launched_persistent = True
    bm.default_context = ctx

    strategy = MagicMock()
    strategy.browser_manager = bm

    crawler = MagicMock()
    crawler.crawler_strategy = strategy
    crawler.active_requests = 0
    return crawler


@pytest.fixture(autouse=True)
def reset_pool():
    """Reset all module-level pool globals before (and after) each test."""
    def _clear():
        crawler_pool.PERMANENT = None
        crawler_pool.HOT_POOL.clear()
        crawler_pool.COLD_POOL.clear()
        crawler_pool.LAST_USED.clear()
        crawler_pool.USAGE_COUNT.clear()
        crawler_pool.DEFAULT_CONFIG_SIG = None
        crawler_pool._PERMANENT_CFG = None
        crawler_pool._PERMANENT_STARTED_AT = 0.0

    _clear()
    yield
    _clear()


# ===========================================================================
# 1.  _is_crawler_alive()
# ===========================================================================


class TestIsCrawlerAlive:
    """Unit tests for the _is_crawler_alive() liveness probe."""

    # --- standard browser ---------------------------------------------------

    def test_alive_standard_browser(self):
        """Live transport + is_connected()=True → alive."""
        crawler = _make_standard_crawler(alive=True)
        assert crawler_pool._is_crawler_alive(crawler) is True

    def test_dead_standard_browser_transport_none(self):
        """Transport is None (pipe closed) → dead."""
        crawler = _make_standard_crawler(alive=False)
        assert crawler_pool._is_crawler_alive(crawler) is False

    def test_transport_none_overrides_is_connected(self):
        """Transport=None → False even when is_connected() still says True.

        This is the key regression the PR fixes: browser.is_connected() lags
        by several event-loop cycles after the OS pipe closes, so we check the
        transport reference directly.
        """
        crawler = _make_standard_crawler(alive=True)  # live transport
        # Simulate the lag: clear the transport but leave is_connected() True
        bm = crawler.crawler_strategy.browser_manager
        bm.browser._channel._connection._transport = None
        bm.browser.is_connected.return_value = True  # still lagging

        assert crawler_pool._is_crawler_alive(crawler) is False

    def test_is_connected_false_marks_dead(self):
        """When transport exists but is_connected() is False → dead."""
        crawler = _make_standard_crawler(alive=True)
        crawler.crawler_strategy.browser_manager.browser.is_connected.return_value = (
            False
        )
        assert crawler_pool._is_crawler_alive(crawler) is False

    # --- persistent context -------------------------------------------------

    def test_alive_persistent_context(self):
        """Live persistent context transport → alive."""
        crawler = _make_persistent_crawler(alive=True)
        assert crawler_pool._is_crawler_alive(crawler) is True

    def test_dead_persistent_context(self):
        """Dead persistent context (transport=None) → dead."""
        crawler = _make_persistent_crawler(alive=False)
        assert crawler_pool._is_crawler_alive(crawler) is False

    def test_persistent_context_none(self):
        """default_context is None → dead."""
        crawler = _make_persistent_crawler(alive=True)
        crawler.crawler_strategy.browser_manager.default_context = None
        assert crawler_pool._is_crawler_alive(crawler) is False

    def test_persistent_impl_none(self):
        """_impl_obj is None → dead."""
        crawler = _make_persistent_crawler(alive=True)
        crawler.crawler_strategy.browser_manager.default_context._impl_obj = None
        assert crawler_pool._is_crawler_alive(crawler) is False

    # --- edge cases ---------------------------------------------------------

    def test_crawler_strategy_none(self):
        """Missing crawler_strategy → False (not a crash)."""
        crawler = MagicMock()
        crawler.crawler_strategy = None
        assert crawler_pool._is_crawler_alive(crawler) is False

    def test_browser_manager_none(self):
        """Missing browser_manager → False."""
        crawler = MagicMock()
        crawler.crawler_strategy.browser_manager = None
        assert crawler_pool._is_crawler_alive(crawler) is False

    def test_browser_none(self):
        """bm.browser is None (non-persistent) → False."""
        crawler = _make_standard_crawler(alive=True)
        crawler.crawler_strategy.browser_manager.browser = None
        assert crawler_pool._is_crawler_alive(crawler) is False

    def test_exception_returns_false(self):
        """Any unexpected exception during introspection → False, never raises."""
        crawler = MagicMock()
        # Accessing crawler_strategy raises to simulate a completely broken object
        type(crawler).crawler_strategy = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("corrupted"))
        )
        # Must not raise
        assert crawler_pool._is_crawler_alive(crawler) is False


# ===========================================================================
# 2.  _replace_permanent()
# ===========================================================================


class TestReplacePermanent:
    """Tests for the permanent-browser crash-recovery helper."""

    @pytest.mark.asyncio
    async def test_closes_old_browser(self):
        """The dead permanent browser is closed+killed before replacement."""
        old = AsyncMock()
        new = AsyncMock()
        new.start = AsyncMock()

        crawler_pool.PERMANENT = old
        crawler_pool.DEFAULT_CONFIG_SIG = "sig1"
        crawler_pool.LAST_USED["sig1"] = 0.0
        crawler_pool._PERMANENT_CFG = MagicMock()

        with (
            patch("crawler_pool._close_and_kill", new=AsyncMock()) as mock_kill,
            patch("crawler_pool.AsyncWebCrawler", return_value=new),
        ):
            await crawler_pool._replace_permanent(reason="dead")

        mock_kill.assert_awaited_once_with(old)

    @pytest.mark.asyncio
    async def test_uses_saved_config_for_new_browser(self):
        """New browser is started using the config saved at init_permanent() time."""
        new = AsyncMock()
        new.start = AsyncMock()
        cfg = MagicMock()

        crawler_pool.PERMANENT = None
        crawler_pool._PERMANENT_CFG = cfg
        crawler_pool.DEFAULT_CONFIG_SIG = "sig1"
        crawler_pool.LAST_USED["sig1"] = 0.0

        with (
            patch("crawler_pool._close_and_kill", new=AsyncMock()),
            patch("crawler_pool.AsyncWebCrawler", return_value=new) as mock_cls,
        ):
            await crawler_pool._replace_permanent()

        mock_cls.assert_called_once_with(config=cfg, thread_safe=False)
        new.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sets_permanent_and_returns_new_crawler(self):
        """PERMANENT module global is updated and the new crawler is returned."""
        new = AsyncMock()
        new.start = AsyncMock()

        crawler_pool._PERMANENT_CFG = MagicMock()
        crawler_pool.DEFAULT_CONFIG_SIG = "sig1"
        crawler_pool.LAST_USED["sig1"] = 0.0

        with (
            patch("crawler_pool._close_and_kill", new=AsyncMock()),
            patch("crawler_pool.AsyncWebCrawler", return_value=new),
        ):
            result = await crawler_pool._replace_permanent()

        assert result is new
        assert crawler_pool.PERMANENT is new

    @pytest.mark.asyncio
    async def test_updates_started_at_timestamp(self):
        """_PERMANENT_STARTED_AT is refreshed to approximately now."""
        new = AsyncMock()
        new.start = AsyncMock()

        crawler_pool._PERMANENT_CFG = MagicMock()
        crawler_pool.DEFAULT_CONFIG_SIG = "sig1"
        crawler_pool.LAST_USED["sig1"] = 0.0
        before = time.time()

        with (
            patch("crawler_pool._close_and_kill", new=AsyncMock()),
            patch("crawler_pool.AsyncWebCrawler", return_value=new),
        ):
            await crawler_pool._replace_permanent()

        assert crawler_pool._PERMANENT_STARTED_AT >= before
        assert crawler_pool._PERMANENT_STARTED_AT <= time.time() + 1


# ===========================================================================
# 3.  _replace_pooled()
# ===========================================================================


class TestReplacePooled:
    """Tests for the hot/cold-pool crash-recovery helper."""

    @pytest.mark.asyncio
    async def test_removes_old_and_inserts_new(self):
        """Dead crawler is closed+killed; fresh one takes its slot."""
        old = AsyncMock()
        new = AsyncMock()
        new.start = AsyncMock()
        cfg = MagicMock()
        sig = "deadpool"
        pool = {sig: old}
        crawler_pool.LAST_USED[sig] = 0.0

        with (
            patch("crawler_pool._close_and_kill", new=AsyncMock()) as mock_kill,
            patch("crawler_pool.AsyncWebCrawler", return_value=new),
        ):
            result = await crawler_pool._replace_pooled(pool, sig, cfg)

        assert result is new
        assert pool[sig] is new
        mock_kill.assert_awaited_once_with(old)

    @pytest.mark.asyncio
    async def test_new_browser_starts_with_active_requests_one(self):
        """Replacement enters the pool already holding one request slot."""
        new = AsyncMock()
        new.start = AsyncMock()
        cfg = MagicMock()
        sig = "freshsig"

        with (
            patch("crawler_pool._close_and_kill", new=AsyncMock()),
            patch("crawler_pool.AsyncWebCrawler", return_value=new),
        ):
            result = await crawler_pool._replace_pooled({}, sig, cfg)

        assert result.active_requests == 1


# ===========================================================================
# 4.  get_crawler() — on-demand crash recovery
# ===========================================================================


class TestGetCrawlerRecovery:
    """Integration-level tests: get_crawler() triggers recovery when browser is dead."""

    @pytest.mark.asyncio
    async def test_dead_permanent_triggers_replace_permanent(self):
        """get_crawler() calls _replace_permanent when the permanent browser is dead."""
        cfg = MagicMock()
        sig = "perm"
        fresh = AsyncMock()
        fresh.active_requests = 0

        crawler_pool.PERMANENT = _make_standard_crawler(alive=False)
        crawler_pool.DEFAULT_CONFIG_SIG = sig
        crawler_pool.LAST_USED[sig] = time.time()
        crawler_pool.USAGE_COUNT[sig] = 0
        crawler_pool._PERMANENT_CFG = cfg

        with (
            patch("crawler_pool._sig", return_value=sig),
            patch("crawler_pool._is_default_config", return_value=True),
            patch("crawler_pool._is_crawler_alive", return_value=False),
            patch(
                "crawler_pool._replace_permanent", new=AsyncMock(return_value=fresh)
            ) as mock_replace,
        ):
            result = await crawler_pool.get_crawler(cfg)

        mock_replace.assert_awaited_once()
        assert result is fresh

    @pytest.mark.asyncio
    async def test_alive_permanent_skips_replacement(self):
        """get_crawler() does NOT call _replace_permanent for a healthy permanent."""
        cfg = MagicMock()
        sig = "perm"
        live = _make_standard_crawler(alive=True)
        live.active_requests = 0

        crawler_pool.PERMANENT = live
        crawler_pool.DEFAULT_CONFIG_SIG = sig
        crawler_pool.LAST_USED[sig] = time.time()
        crawler_pool.USAGE_COUNT[sig] = 0

        with (
            patch("crawler_pool._sig", return_value=sig),
            patch("crawler_pool._is_default_config", return_value=True),
            patch("crawler_pool._is_crawler_alive", return_value=True),
            patch(
                "crawler_pool._replace_permanent", new=AsyncMock()
            ) as mock_replace,
        ):
            result = await crawler_pool.get_crawler(cfg)

        mock_replace.assert_not_awaited()
        assert result is live

    @pytest.mark.asyncio
    async def test_dead_hot_browser_triggers_replace_pooled(self):
        """get_crawler() replaces a dead hot-pool browser inline."""
        cfg = MagicMock()
        sig = "hot"
        dead = _make_standard_crawler(alive=False)
        fresh = AsyncMock()
        fresh.active_requests = 1

        crawler_pool.HOT_POOL[sig] = dead
        crawler_pool.LAST_USED[sig] = time.time()
        crawler_pool.USAGE_COUNT[sig] = 5

        with (
            patch("crawler_pool._sig", return_value=sig),
            patch("crawler_pool._is_default_config", return_value=False),
            patch("crawler_pool._is_crawler_alive", return_value=False),
            patch(
                "crawler_pool._replace_pooled", new=AsyncMock(return_value=fresh)
            ) as mock_replace,
        ):
            result = await crawler_pool.get_crawler(cfg)

        mock_replace.assert_awaited_once_with(crawler_pool.HOT_POOL, sig, cfg)
        assert result is fresh

    @pytest.mark.asyncio
    async def test_dead_cold_browser_triggers_replace_pooled(self):
        """get_crawler() replaces a dead cold-pool browser inline."""
        cfg = MagicMock()
        sig = "cold"
        dead = _make_standard_crawler(alive=False)
        fresh = AsyncMock()
        fresh.active_requests = 1

        crawler_pool.COLD_POOL[sig] = dead
        crawler_pool.LAST_USED[sig] = time.time()
        crawler_pool.USAGE_COUNT[sig] = 1

        with (
            patch("crawler_pool._sig", return_value=sig),
            patch("crawler_pool._is_default_config", return_value=False),
            patch("crawler_pool._is_crawler_alive", return_value=False),
            patch(
                "crawler_pool._replace_pooled", new=AsyncMock(return_value=fresh)
            ) as mock_replace,
        ):
            result = await crawler_pool.get_crawler(cfg)

        mock_replace.assert_awaited_once_with(crawler_pool.COLD_POOL, sig, cfg)
        assert result is fresh


# ===========================================================================
# 5.  janitor() — proactive health sweep
# ===========================================================================


def _janitor_sleep_side_effect():
    """Return a side_effect list for asyncio.sleep that lets one tick run then stops.

    The janitor loop is structured as:
        while True:
            mem_pct = ...
            await asyncio.sleep(interval)   ← 1st call: return normally
            async with LOCK:
                # health checks happen here
            # back to top of loop
            await asyncio.sleep(interval)   ← 2nd call: raise CancelledError
    """
    return [None, asyncio.CancelledError()]


class TestJanitorHealthSweep:
    """Tests for the proactive dead-browser detection inside the janitor loop."""

    @pytest.mark.asyncio
    async def test_dead_permanent_triggers_replace_permanent(self):
        """Janitor calls _replace_permanent when the permanent browser is dead."""
        dead = _make_standard_crawler(alive=False)
        crawler_pool.PERMANENT = dead
        crawler_pool.DEFAULT_CONFIG_SIG = "perm"
        crawler_pool.LAST_USED["perm"] = time.time()
        crawler_pool._PERMANENT_CFG = MagicMock()
        crawler_pool._PERMANENT_STARTED_AT = time.time()

        with (
            patch(
                "asyncio.sleep",
                new=AsyncMock(side_effect=_janitor_sleep_side_effect()),
            ),
            patch(
                "crawler_pool.get_container_memory_percent", return_value=50.0
            ),
            patch("crawler_pool._is_crawler_alive", return_value=False),
            patch(
                "crawler_pool._replace_permanent", new=AsyncMock()
            ) as mock_replace,
        ):
            with pytest.raises(asyncio.CancelledError):
                await crawler_pool.janitor()

        mock_replace.assert_awaited_once_with(reason="dead")

    @pytest.mark.asyncio
    async def test_dead_hot_browser_evicted_and_killed(self):
        """Janitor removes a dead hot-pool browser and force-kills its process."""
        sig = "hot_dead"
        dead = _make_standard_crawler(alive=False)
        crawler_pool.HOT_POOL[sig] = dead
        crawler_pool.LAST_USED[sig] = time.time()
        crawler_pool.USAGE_COUNT[sig] = 3

        with (
            patch(
                "asyncio.sleep",
                new=AsyncMock(side_effect=_janitor_sleep_side_effect()),
            ),
            patch(
                "crawler_pool.get_container_memory_percent", return_value=50.0
            ),
            patch("crawler_pool._is_crawler_alive", return_value=False),
            patch(
                "crawler_pool._close_and_kill", new=AsyncMock()
            ) as mock_kill,
        ):
            with pytest.raises(asyncio.CancelledError):
                await crawler_pool.janitor()

        assert sig not in crawler_pool.HOT_POOL
        assert sig not in crawler_pool.LAST_USED
        mock_kill.assert_awaited_once_with(dead)

    @pytest.mark.asyncio
    async def test_dead_cold_browser_evicted_and_killed(self):
        """Janitor removes a dead cold-pool browser."""
        sig = "cold_dead"
        dead = _make_standard_crawler(alive=False)
        crawler_pool.COLD_POOL[sig] = dead
        crawler_pool.LAST_USED[sig] = time.time()
        crawler_pool.USAGE_COUNT[sig] = 1

        with (
            patch(
                "asyncio.sleep",
                new=AsyncMock(side_effect=_janitor_sleep_side_effect()),
            ),
            patch(
                "crawler_pool.get_container_memory_percent", return_value=50.0
            ),
            patch("crawler_pool._is_crawler_alive", return_value=False),
            patch(
                "crawler_pool._close_and_kill", new=AsyncMock()
            ) as mock_kill,
        ):
            with pytest.raises(asyncio.CancelledError):
                await crawler_pool.janitor()

        assert sig not in crawler_pool.COLD_POOL
        mock_kill.assert_awaited_once_with(dead)

    @pytest.mark.asyncio
    async def test_alive_hot_browser_left_in_pool(self):
        """Janitor does not touch a live hot-pool browser."""
        sig = "hot_alive"
        live = _make_standard_crawler(alive=True)
        live.active_requests = 0
        # Set last-used to now so the idle-TTL cleanup doesn't fire either
        crawler_pool.HOT_POOL[sig] = live
        crawler_pool.LAST_USED[sig] = time.time()
        crawler_pool.USAGE_COUNT[sig] = 2

        with (
            patch(
                "asyncio.sleep",
                new=AsyncMock(side_effect=_janitor_sleep_side_effect()),
            ),
            patch(
                "crawler_pool.get_container_memory_percent", return_value=50.0
            ),
            patch("crawler_pool._is_crawler_alive", return_value=True),
            patch(
                "crawler_pool._close_and_kill", new=AsyncMock()
            ) as mock_kill,
        ):
            with pytest.raises(asyncio.CancelledError):
                await crawler_pool.janitor()

        assert sig in crawler_pool.HOT_POOL
        mock_kill.assert_not_awaited()
