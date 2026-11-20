# crawler_pool.py - Smart browser pool with tiered management
import asyncio, json, hashlib, time
from contextlib import suppress
from typing import Dict, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig
from utils import load_config, get_container_memory_percent
import logging

logger = logging.getLogger(__name__)
CONFIG = load_config()

# Pool tiers
PERMANENT: Optional[AsyncWebCrawler] = None  # Always-ready default browser
HOT_POOL: Dict[str, AsyncWebCrawler] = {}    # Frequent configs
COLD_POOL: Dict[str, AsyncWebCrawler] = {}   # Rare configs
LAST_USED: Dict[str, float] = {}
USAGE_COUNT: Dict[str, int] = {}
LOCK = asyncio.Lock()

# Config
MEM_LIMIT = CONFIG.get("crawler", {}).get("memory_threshold_percent", 95.0)
BASE_IDLE_TTL = CONFIG.get("crawler", {}).get("pool", {}).get("idle_ttl_sec", 300)
RECYCLE_PAGES = CONFIG.get("crawler", {}).get("pool", {}).get("max_pages_before_recycle", 0)
DEFAULT_CONFIG_SIG = None  # Cached sig for default config
_PERMANENT_CFG: Optional[BrowserConfig] = None  # To relaunch a crashed permanent browser
_CLOSING = set()  # Strong refs to detached close tasks


def _apply_pool_defaults(cfg: BrowserConfig) -> BrowserConfig:
    """Apply pool-owned policy to a browser config before it is pooled.

    Browsers handed out by this pool are long-lived, and the endpoints build
    their BrowserConfig from the request body (see api.py handle_crawl_request),
    so config.yml's browser kwargs never reach them. Pooling is what makes a
    browser long-lived, so the pool is where its recycling policy belongs.

    Applied before _sig() so every request shares one signature and pooling is
    unaffected. An explicit per-request value wins. See #2231.
    """
    if RECYCLE_PAGES and not cfg.max_pages_before_recycle:
        cfg.max_pages_before_recycle = RECYCLE_PAGES
    return cfg


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


def _sig(cfg: BrowserConfig) -> str:
    """Generate config signature."""
    payload = json.dumps(cfg.to_dict(), sort_keys=True, separators=(",",":"))
    return hashlib.sha1(payload.encode()).hexdigest()

def _is_default_config(sig: str) -> bool:
    """Check if config matches default."""
    return sig == DEFAULT_CONFIG_SIG

def _is_alive(crawler: AsyncWebCrawler) -> bool:
    """False once the crawler's browser process has died (OOM, crash, kill).

    Without this a dead browser stays pooled forever: the janitor only closes
    idle crawlers, and a dead one keeps being handed out. See #842.
    """
    bm = getattr(crawler.crawler_strategy, "browser_manager", None)
    if bm is None:
        return True
    if bm.browser is not None:
        return bm.browser.is_connected()
    # Persistent context: there is no Browser object, only the context
    impl = getattr(bm.default_context, "_impl_obj", None)
    return not getattr(impl, "_closing_or_closed", False)

def _close_detached(crawler: AsyncWebCrawler):
    """Close a dead crawler in the background so it never blocks LOCK."""
    async def _close():
        with suppress(Exception):
            await asyncio.wait_for(crawler.close(), timeout=30)
    task = asyncio.create_task(_close())
    _CLOSING.add(task)
    task.add_done_callback(_CLOSING.discard)

def _evict(pool: Dict[str, AsyncWebCrawler], sig: str):
    """Drop a dead hot/cold crawler; the next request for its config gets a new one."""
    logger.warning(f"💀 Pooled browser died, dropping it (sig={sig[:8]})")
    _close_detached(pool.pop(sig))
    LAST_USED.pop(sig, None)
    USAGE_COUNT.pop(sig, None)

async def _restart_permanent():
    """Relaunch a crashed permanent browser. Caller holds LOCK.

    On failure PERMANENT keeps the dead crawler, so the next call retries.
    """
    global PERMANENT
    logger.warning("💀 Permanent browser died, relaunching")
    crawler = AsyncWebCrawler(config=_PERMANENT_CFG, thread_safe=False)
    await crawler.start()
    _close_detached(PERMANENT)
    PERMANENT = crawler

async def get_crawler(cfg: BrowserConfig) -> AsyncWebCrawler:
    """Get crawler from pool with tiered strategy."""
    sig = _sig(_apply_pool_defaults(cfg))
    async with LOCK:
        # Check permanent browser for default config
        if PERMANENT and _is_default_config(sig):
            if not _is_alive(PERMANENT):
                await _restart_permanent()
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            if not hasattr(PERMANENT, 'active_requests'):
                PERMANENT.active_requests = 0
            PERMANENT.active_requests += 1
            logger.info("🔥 Using permanent browser")
            return PERMANENT

        for pool in (HOT_POOL, COLD_POOL):
            if sig in pool and not _is_alive(pool[sig]):
                _evict(pool, sig)  # falls through to create a new one

        # Check hot pool
        if sig in HOT_POOL:
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            crawler = HOT_POOL[sig]
            if not hasattr(crawler, 'active_requests'):
                crawler.active_requests = 0
            crawler.active_requests += 1
            logger.info(f"♨️  Using hot pool browser (sig={sig[:8]}, active={crawler.active_requests})")
            return crawler

        # Check cold pool (promote to hot if used 3+ times)
        if sig in COLD_POOL:
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            crawler = COLD_POOL[sig]
            if not hasattr(crawler, 'active_requests'):
                crawler.active_requests = 0
            crawler.active_requests += 1

            if USAGE_COUNT[sig] >= 3:
                logger.info(f"⬆️  Promoting to hot pool (sig={sig[:8]}, count={USAGE_COUNT[sig]})")
                HOT_POOL[sig] = COLD_POOL.pop(sig)

                # Track promotion in monitor
                try:
                    from monitor import get_monitor
                    await get_monitor().track_janitor_event("promote", sig, {"count": USAGE_COUNT[sig]})
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
        logger.info(f"🆕 Creating new browser in cold pool (sig={sig[:8]}, mem={mem_pct:.1f}%)")
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
        if hasattr(crawler, 'active_requests'):
            crawler.active_requests = max(0, crawler.active_requests - 1)

async def init_permanent(cfg: BrowserConfig):
    """Initialize permanent default browser."""
    global PERMANENT, DEFAULT_CONFIG_SIG, _PERMANENT_CFG
    async with LOCK:
        if PERMANENT:
            return
        DEFAULT_CONFIG_SIG = _sig(_apply_pool_defaults(cfg))
        _PERMANENT_CFG = cfg
        logger.info("🔥 Creating permanent default browser")
        PERMANENT = AsyncWebCrawler(config=cfg, thread_safe=False)
        await PERMANENT.start()
        LAST_USED[DEFAULT_CONFIG_SIG] = time.time()
        USAGE_COUNT[DEFAULT_CONFIG_SIG] = 0

async def close_all():
    """Close all browsers."""
    async with LOCK:
        tasks = []
        if PERMANENT:
            tasks.append(PERMANENT.close())
        tasks.extend([c.close() for c in HOT_POOL.values()])
        tasks.extend([c.close() for c in COLD_POOL.values()])
        await asyncio.gather(*tasks, return_exceptions=True)
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
            # Replace dead browsers before any request reaches them
            if PERMANENT and not _is_alive(PERMANENT):
                try:
                    await _restart_permanent()
                except Exception as e:
                    logger.error(f"🧹 Could not relaunch permanent browser: {e}")
            for pool in (HOT_POOL, COLD_POOL):
                for sig in [s for s, c in pool.items() if not _is_alive(c)]:
                    _evict(pool, sig)

            # Clean cold pool
            for sig in list(COLD_POOL.keys()):
                if now - LAST_USED.get(sig, now) > cold_ttl:
                    crawler = COLD_POOL[sig]
                    if getattr(crawler, 'active_requests', 0) > 0:
                        continue  # still serving requests, skip
                    idle_time = now - LAST_USED[sig]
                    logger.info(f"🧹 Closing cold browser (sig={sig[:8]}, idle={idle_time:.0f}s)")
                    with suppress(Exception):
                        await crawler.close()
                    COLD_POOL.pop(sig, None)
                    LAST_USED.pop(sig, None)
                    USAGE_COUNT.pop(sig, None)

                    # Track in monitor
                    try:
                        from monitor import get_monitor
                        await get_monitor().track_janitor_event("close_cold", sig, {"idle_seconds": int(idle_time), "ttl": cold_ttl})
                    except:
                        pass

            # Clean hot pool (more conservative)
            for sig in list(HOT_POOL.keys()):
                if now - LAST_USED.get(sig, now) > hot_ttl:
                    crawler = HOT_POOL[sig]
                    if getattr(crawler, 'active_requests', 0) > 0:
                        continue  # still serving requests, skip
                    idle_time = now - LAST_USED[sig]
                    logger.info(f"🧹 Closing hot browser (sig={sig[:8]}, idle={idle_time:.0f}s)")
                    with suppress(Exception):
                        await crawler.close()
                    HOT_POOL.pop(sig, None)
                    LAST_USED.pop(sig, None)
                    USAGE_COUNT.pop(sig, None)

                    # Track in monitor
                    try:
                        from monitor import get_monitor
                        await get_monitor().track_janitor_event("close_hot", sig, {"idle_seconds": int(idle_time), "ttl": hot_ttl})
                    except:
                        pass

            # Log pool stats
            if mem_pct > 60:
                logger.info(f"📊 Pool: hot={len(HOT_POOL)}, cold={len(COLD_POOL)}, mem={mem_pct:.1f}%")
