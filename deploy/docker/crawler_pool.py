# crawler_pool.py - Smart browser pool with tiered management
import asyncio, json, hashlib, signal, time
from contextlib import suppress
from typing import Dict, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig
from utils import load_config, get_container_memory_percent
import logging

logger = logging.getLogger(__name__)
CONFIG = load_config()

# Pool tiers
PERMANENT: Optional[AsyncWebCrawler] = None  # Always-ready default browser
HOT_POOL: Dict[str, AsyncWebCrawler] = {}  # Frequent configs
COLD_POOL: Dict[str, AsyncWebCrawler] = {}  # Rare configs
LAST_USED: Dict[str, float] = {}
USAGE_COUNT: Dict[str, int] = {}
LOCK = asyncio.Lock()

# Config
MEM_LIMIT = CONFIG.get("crawler", {}).get("memory_threshold_percent", 95.0)
MEM_RECYCLE_THRESHOLD = CONFIG.get("crawler", {}).get("memory_recycle_percent", 88.0)
BASE_IDLE_TTL = CONFIG.get("crawler", {}).get("pool", {}).get("idle_ttl_sec", 300)
PERMANENT_MAX_AGE_S = (
    CONFIG.get("crawler", {}).get("pool", {}).get("permanent_max_age_sec", 4 * 3600)
)  # 4 h
PERMANENT_MAX_REQUESTS = (
    CONFIG.get("crawler", {}).get("pool", {}).get("permanent_max_requests", 2000)
)
DEFAULT_CONFIG_SIG = None  # Cached sig for default config
_PERMANENT_CFG: Optional[BrowserConfig] = None  # Saved for crash recovery
_PERMANENT_STARTED_AT: float = (
    0.0  # Wall-clock time when PERMANENT was last (re)started
)


def get_pool_snapshot() -> dict:
    """Return a point-in-time snapshot of pool state for monitoring.

    This is intentionally lock-free. Under CPython's GIL, reading
    ``len(dict)``, ``dict.copy()``, and ``x is not None`` are atomic
    operations, so the monitor can safely call this without contending
    on the pool LOCK that is held during slow browser start/close ops.
    The worst case is a slightly stale count, which is acceptable for
    dashboard display purposes.
    """
    return {
        "permanent": PERMANENT,
        "permanent_sig": DEFAULT_CONFIG_SIG,
        "hot_pool": HOT_POOL.copy(),
        "cold_pool": COLD_POOL.copy(),
        "last_used": LAST_USED.copy(),
        "usage_count": USAGE_COUNT.copy(),
    }


def _get_browser_proc(crawler: AsyncWebCrawler):
    """Return the Playwright subprocess (Popen) object for *crawler*, or None.

    Playwright stores the underlying Chromium process as
    ``transport._proc`` on the pipe/websocket transport object.  We walk
    the standard (Browser) and persistent-context paths, returning None
    if the reference is unavailable for any reason.
    """
    try:
        strategy = getattr(crawler, "crawler_strategy", None)
        bm = getattr(strategy, "browser_manager", None)
        if bm is None:
            return None
        if getattr(bm, "_launched_persistent", False):
            ctx = getattr(bm, "default_context", None)
            impl = getattr(ctx, "_impl_obj", None)
            conn = getattr(impl, "_connection", None)
            transport = getattr(conn, "_transport", None)
        else:
            browser = getattr(bm, "browser", None)
            channel = getattr(browser, "_channel", None)
            conn = getattr(channel, "_connection", None)
            transport = getattr(conn, "_transport", None)
        proc = getattr(transport, "_proc", None)
        # Return only if the process hasn't exited yet
        if proc is not None and proc.returncode is None:
            return proc
        return None
    except Exception:
        return None


def _kill_proc_tree(pid: int) -> None:
    """SIGKILL *pid* and all its descendant processes using psutil.

    Called after ``crawler.close()`` to ensure Chromium renderer / utility
    sub-processes that survived the close are reaped immediately rather than
    continuing to hold memory until the next GC or container restart.
    """
    try:
        import psutil

        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            with suppress(Exception):
                child.send_signal(signal.SIGKILL)
        with suppress(Exception):
            parent.send_signal(signal.SIGKILL)
        logger.debug(
            f"Killed Chromium process tree (pid={pid}, children={len(children)})"
        )
    except Exception:
        pass


async def _close_and_kill(crawler: AsyncWebCrawler) -> None:
    """Close *crawler* then force-kill any surviving Chromium OS processes.

    ``crawler.close()`` sends a polite shutdown to Chromium, but when the
    browser has already crashed the command is never delivered and the OS
    process tree stays alive.  Capturing the subprocess reference *before*
    calling close (while the transport object still exists) and then issuing
    SIGKILL afterwards guarantees that no renderer or utility processes linger
    regardless of whether the close succeeded.
    """
    chrome_proc = _get_browser_proc(crawler)
    with suppress(Exception):
        await asyncio.wait_for(crawler.close(), timeout=5.0)
    if chrome_proc is not None:
        _kill_proc_tree(chrome_proc.pid)


def _sig(cfg: BrowserConfig) -> str:
    """Generate config signature."""
    payload = json.dumps(cfg.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(payload.encode()).hexdigest()


def _is_default_config(sig: str) -> bool:
    """Check if config matches default."""
    return sig == DEFAULT_CONFIG_SIG


def _is_crawler_alive(crawler: AsyncWebCrawler) -> bool:
    """Check whether a pooled crawler's Playwright browser is still responsive.

    The Chromium process can die from OOM or /dev/shm exhaustion.  When that
    happens the Playwright driver connection closes, and every subsequent
    ``BrowserContext.new_page()`` call raises
    ``Connection closed while reading from the driver``.

    We inspect the internal Playwright state rather than attempting a live
    page-open probe because the probe itself could hang or raise, and we
    already hold the pool LOCK.

    Important: ``browser.is_connected()`` is updated via an async callback
    chain (``Connection.close()`` → ``Browser._on_close()``).  It can return
    True for several event-loop cycles after the OS pipe has already closed.
    We therefore also check ``_channel._connection._transport`` directly: the
    transport reference is cleared to ``None`` synchronously inside
    ``Connection.close()`` the instant asyncio fires ``connection_lost()``,
    giving an immediate and reliable dead-browser signal independent of the
    async callback backlog.

    See: https://github.com/unclecode/crawl4ai/issues/842
    """
    try:
        strategy = getattr(crawler, "crawler_strategy", None)
        if strategy is None:
            return False

        # AsyncPlaywrightCrawlerStrategy stores a BrowserManager
        bm = getattr(strategy, "browser_manager", None)
        if bm is None:
            return False

        # Persistent context path — no separate browser object
        if getattr(bm, "_launched_persistent", False):
            ctx = getattr(bm, "default_context", None)
            if ctx is None:
                return False
            # Persistent contexts expose no is_connected(); check impl internals
            impl = getattr(ctx, "_impl_obj", None)
            if impl is None:
                return False
            conn = getattr(impl, "_connection", None)
            if conn is None:
                return False
            # _connection._transport is None once the pipe/websocket dies
            transport = getattr(conn, "_transport", None)
            return transport is not None

        browser = getattr(bm, "browser", None)
        if browser is None:
            return False

        # is_connected() lags — check the transport first for an immediate signal.
        # Playwright's Browser extends ChannelOwner, so _channel._connection
        # is the live Connection object whose _transport goes None on pipe close.
        channel = getattr(browser, "_channel", None)
        if channel is not None:
            conn = getattr(channel, "_connection", None)
            if conn is not None:
                transport = getattr(conn, "_transport", None)
                if transport is None:
                    return False  # pipe gone — browser is dead

        return browser.is_connected()
    except Exception:
        return False


async def _replace_permanent(reason: str = "dead") -> AsyncWebCrawler:
    """Close the permanent browser and start a fresh one.

    *reason* is logged to distinguish crash recovery ("dead") from proactive
    recycling ("memory pressure", "max age", "max requests").
    Must be called while LOCK is held.
    """
    global PERMANENT, _PERMANENT_STARTED_AT
    logger.warning(f"🔧 Permanent browser recycling ({reason}) — recreating…")

    if PERMANENT:
        await _close_and_kill(PERMANENT)
        PERMANENT = None

    # Also reset the class-level Playwright singleton so a fresh one is started
    try:
        from crawl4ai.browser_manager import BrowserManager

        BrowserManager._playwright_instance = None
    except Exception:
        pass

    new_crawler = AsyncWebCrawler(config=_PERMANENT_CFG, thread_safe=False)
    await new_crawler.start()
    PERMANENT = new_crawler
    _PERMANENT_STARTED_AT = time.time()
    LAST_USED[DEFAULT_CONFIG_SIG] = _PERMANENT_STARTED_AT
    logger.info("✅ Permanent browser recreated successfully")
    return PERMANENT


async def _replace_pooled(
    pool: Dict[str, AsyncWebCrawler], sig: str, cfg: BrowserConfig
) -> AsyncWebCrawler:
    """Close a dead pooled browser and start a fresh replacement."""
    logger.warning(f"🔧 Pooled browser dead (sig={sig[:8]}) — recreating…")
    old = pool.pop(sig, None)
    if old:
        await _close_and_kill(old)
    new_crawler = AsyncWebCrawler(config=cfg, thread_safe=False)
    await new_crawler.start()
    new_crawler.active_requests = 1
    pool[sig] = new_crawler
    LAST_USED[sig] = time.time()
    logger.info(f"✅ Pooled browser recreated (sig={sig[:8]})")
    return new_crawler


async def get_crawler(cfg: BrowserConfig) -> AsyncWebCrawler:
    """Get crawler from pool with tiered strategy."""
    sig = _sig(cfg)
    async with LOCK:
        # Check permanent browser for default config
        if PERMANENT and _is_default_config(sig):
            # Crash recovery: verify the browser is still alive
            if not _is_crawler_alive(PERMANENT):
                crawler = await _replace_permanent()
            else:
                crawler = PERMANENT
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            if not hasattr(crawler, "active_requests"):
                crawler.active_requests = 0
            crawler.active_requests += 1
            logger.info("🔥 Using permanent browser")
            return crawler

        # Check hot pool
        if sig in HOT_POOL:
            crawler = HOT_POOL[sig]
            # Crash recovery: verify the browser is still alive
            if not _is_crawler_alive(crawler):
                crawler = await _replace_pooled(HOT_POOL, sig, cfg)
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            if not hasattr(crawler, "active_requests"):
                crawler.active_requests = 0
            crawler.active_requests += 1
            logger.info(
                f"♨️  Using hot pool browser (sig={sig[:8]}, active={crawler.active_requests})"
            )
            return crawler

        # Check cold pool (promote to hot if used 3+ times)
        if sig in COLD_POOL:
            crawler = COLD_POOL[sig]
            # Crash recovery: verify the browser is still alive
            if not _is_crawler_alive(crawler):
                crawler = await _replace_pooled(COLD_POOL, sig, cfg)
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            if not hasattr(crawler, "active_requests"):
                crawler.active_requests = 0
            crawler.active_requests += 1

            if USAGE_COUNT[sig] >= 3:
                logger.info(
                    f"⬆️  Promoting to hot pool (sig={sig[:8]}, count={USAGE_COUNT[sig]})"
                )
                HOT_POOL[sig] = COLD_POOL.pop(sig)

                # Track promotion in monitor
                try:
                    from monitor import get_monitor

                    await get_monitor().track_janitor_event(
                        "promote", sig, {"count": USAGE_COUNT[sig]}
                    )
                except:
                    pass

                return HOT_POOL[sig]

            logger.info(f"❄️  Using cold pool browser (sig={sig[:8]})")
            return crawler

        # Memory check before creating new
        mem_pct = get_container_memory_percent()
        if mem_pct >= MEM_LIMIT:
            logger.error(f"💥 Memory pressure: {mem_pct:.1f}% >= {MEM_LIMIT}%")
            raise MemoryError(f"Memory at {mem_pct:.1f}%, refusing new browser")

        # Create new in cold pool
        logger.info(
            f"🆕 Creating new browser in cold pool (sig={sig[:8]}, mem={mem_pct:.1f}%)"
        )
        crawler = AsyncWebCrawler(config=cfg, thread_safe=False)
        await crawler.start()
        crawler.active_requests = 1
        COLD_POOL[sig] = crawler
        LAST_USED[sig] = time.time()
        USAGE_COUNT[sig] = 1
        return crawler


async def release_crawler(crawler: AsyncWebCrawler):
    """Decrement active request count for a pooled crawler.

    Call this in a finally block after finishing work with a crawler
    obtained via get_crawler() so the janitor knows when it's safe
    to close idle browsers.
    """
    async with LOCK:
        if hasattr(crawler, "active_requests"):
            crawler.active_requests = max(0, crawler.active_requests - 1)


async def init_permanent(cfg: BrowserConfig):
    """Initialize permanent default browser."""
    global PERMANENT, DEFAULT_CONFIG_SIG, _PERMANENT_CFG, _PERMANENT_STARTED_AT
    async with LOCK:
        if PERMANENT:
            return
        DEFAULT_CONFIG_SIG = _sig(cfg)
        _PERMANENT_CFG = cfg  # Save config for crash recovery
        logger.info("🔥 Creating permanent default browser")
        PERMANENT = AsyncWebCrawler(config=cfg, thread_safe=False)
        await PERMANENT.start()
        _PERMANENT_STARTED_AT = time.time()
        LAST_USED[DEFAULT_CONFIG_SIG] = _PERMANENT_STARTED_AT
        USAGE_COUNT[DEFAULT_CONFIG_SIG] = 0


async def close_all():
    """Close all browsers."""
    async with LOCK:
        all_crawlers = []
        if PERMANENT:
            all_crawlers.append(PERMANENT)
        all_crawlers.extend(HOT_POOL.values())
        all_crawlers.extend(COLD_POOL.values())
        await asyncio.gather(
            *[_close_and_kill(c) for c in all_crawlers], return_exceptions=True
        )
        HOT_POOL.clear()
        COLD_POOL.clear()
        LAST_USED.clear()
        USAGE_COUNT.clear()


async def janitor():
    """Adaptive cleanup based on memory pressure."""
    while True:
        mem_pct = get_container_memory_percent()

        # Adaptive intervals and TTLs
        if mem_pct > 80:
            interval, cold_ttl, hot_ttl = 10, 30, 120
        elif mem_pct > 60:
            interval, cold_ttl, hot_ttl = 30, 60, 300
        else:
            interval, cold_ttl, hot_ttl = 60, BASE_IDLE_TTL, BASE_IDLE_TTL * 2

        await asyncio.sleep(interval)

        now = time.time()
        async with LOCK:
            # Proactive health check: permanent browser
            if PERMANENT and not _is_crawler_alive(PERMANENT):
                logger.warning("🧹 Janitor detected dead permanent browser")
                try:
                    await _replace_permanent(reason="dead")
                except Exception as e:
                    logger.error(f"🧹 Failed to replace permanent browser: {e}")

            # Proactive recycling: permanent browser (memory pressure / age / request count)
            elif PERMANENT and getattr(PERMANENT, "active_requests", 0) == 0:
                age_s = now - _PERMANENT_STARTED_AT
                req_count = USAGE_COUNT.get(DEFAULT_CONFIG_SIG, 0)
                recycle_reason = None
                if mem_pct >= MEM_RECYCLE_THRESHOLD and not HOT_POOL and not COLD_POOL:
                    recycle_reason = f"memory pressure ({mem_pct:.1f}%)"
                elif age_s >= PERMANENT_MAX_AGE_S:
                    recycle_reason = f"max age ({age_s / 3600:.1f}h)"
                elif req_count >= PERMANENT_MAX_REQUESTS:
                    recycle_reason = f"max requests ({req_count})"
                if recycle_reason:
                    try:
                        await _replace_permanent(reason=recycle_reason)
                        USAGE_COUNT[DEFAULT_CONFIG_SIG] = 0
                    except Exception as e:
                        logger.error(f"🧹 Failed to recycle permanent browser: {e}")

            # Proactive health check: hot pool
            for sig in list(HOT_POOL.keys()):
                if not _is_crawler_alive(HOT_POOL[sig]):
                    logger.warning(
                        f"🧹 Janitor detected dead hot browser (sig={sig[:8]})"
                    )
                    old = HOT_POOL.pop(sig, None)
                    if old:
                        await _close_and_kill(old)
                    LAST_USED.pop(sig, None)
                    USAGE_COUNT.pop(sig, None)

            # Proactive health check: cold pool
            for sig in list(COLD_POOL.keys()):
                if not _is_crawler_alive(COLD_POOL[sig]):
                    logger.warning(
                        f"🧹 Janitor detected dead cold browser (sig={sig[:8]})"
                    )
                    old = COLD_POOL.pop(sig, None)
                    if old:
                        await _close_and_kill(old)
                    LAST_USED.pop(sig, None)
                    USAGE_COUNT.pop(sig, None)

            # Clean cold pool (idle timeout)
            for sig in list(COLD_POOL.keys()):
                if now - LAST_USED.get(sig, now) > cold_ttl:
                    crawler = COLD_POOL[sig]
                    if getattr(crawler, "active_requests", 0) > 0:
                        continue  # still serving requests, skip
                    idle_time = now - LAST_USED[sig]
                    logger.info(
                        f"🧹 Closing cold browser (sig={sig[:8]}, idle={idle_time:.0f}s)"
                    )
                    COLD_POOL.pop(sig, None)
                    LAST_USED.pop(sig, None)
                    USAGE_COUNT.pop(sig, None)
                    await _close_and_kill(crawler)

                    # Track in monitor
                    try:
                        from monitor import get_monitor

                        await get_monitor().track_janitor_event(
                            "close_cold",
                            sig,
                            {"idle_seconds": int(idle_time), "ttl": cold_ttl},
                        )
                    except:
                        pass

            # Clean hot pool (more conservative)
            for sig in list(HOT_POOL.keys()):
                if now - LAST_USED.get(sig, now) > hot_ttl:
                    crawler = HOT_POOL[sig]
                    if getattr(crawler, "active_requests", 0) > 0:
                        continue  # still serving requests, skip
                    idle_time = now - LAST_USED[sig]
                    logger.info(
                        f"🧹 Closing hot browser (sig={sig[:8]}, idle={idle_time:.0f}s)"
                    )
                    HOT_POOL.pop(sig, None)
                    LAST_USED.pop(sig, None)
                    USAGE_COUNT.pop(sig, None)
                    await _close_and_kill(crawler)

                    # Track in monitor
                    try:
                        from monitor import get_monitor

                        await get_monitor().track_janitor_event(
                            "close_hot",
                            sig,
                            {"idle_seconds": int(idle_time), "ttl": hot_ttl},
                        )
                    except:
                        pass

            # Log pool stats
            if mem_pct > 60:
                perm_age = (
                    f", perm_age={int((now - _PERMANENT_STARTED_AT) / 60)}m"
                    if PERMANENT
                    else ""
                )
                logger.info(
                    f"📊 Pool: perm={'yes' if PERMANENT else 'no'}, hot={len(HOT_POOL)}, cold={len(COLD_POOL)}, mem={mem_pct:.1f}%{perm_age}"
                )
