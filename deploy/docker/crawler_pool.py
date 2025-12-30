# crawler_pool.py - Smart browser pool with tiered management
import asyncio, json, hashlib, time, os
import psutil
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
RETIRED_POOL: Dict[str, AsyncWebCrawler] = {} # Browsers marked for retirement
LAST_USED: Dict[str, float] = {}
USAGE_COUNT: Dict[str, int] = {}
LOCK = asyncio.Lock()

# Config
MEM_LIMIT = CONFIG.get("crawler", {}).get("memory_threshold_percent", 95.0)
BASE_IDLE_TTL = CONFIG.get("crawler", {}).get("pool", {}).get("idle_ttl_sec", 300)
DEFAULT_CONFIG_SIG = None  # Cached sig for default config

# Retirement Config (from env)
RETIREMENT_ENABLED = os.getenv("CRAWL4AI_BROWSER_RETIREMENT_ENABLED", "false").lower() == "true"
MAX_USAGE_COUNT = int(os.getenv("CRAWL4AI_BROWSER_MAX_USAGE", "100"))
MEMORY_RETIRE_THRESHOLD = int(os.getenv("CRAWL4AI_MEMORY_RETIRE_THRESHOLD", "75"))
MEMORY_RETIRE_MIN_USAGE = int(os.getenv("CRAWL4AI_MEMORY_RETIRE_MIN_USAGE", "10"))

# if RETIREMENT_ENABLED:
#     logger.info(f"✅ Browser retirement enabled (Max Usage: {MAX_USAGE_COUNT}, Mem Threshold: {MEMORY_RETIRE_THRESHOLD}%)")
# else:
#     logger.info("ℹ️ Browser retirement disabled")

def _sig(cfg: BrowserConfig) -> str:
    """Generate config signature."""
    payload = json.dumps(cfg.to_dict(), sort_keys=True, separators=(",",":"))
    return hashlib.sha1(payload.encode()).hexdigest()

def _is_default_config(sig: str) -> bool:
    """Check if config matches default."""
    return sig == DEFAULT_CONFIG_SIG

async def get_crawler(cfg: BrowserConfig) -> AsyncWebCrawler:
    """Get crawler from pool with tiered strategy."""
    sig = _sig(cfg)
    async with LOCK:
        # Check permanent browser for default config
        if PERMANENT and _is_default_config(sig):
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            logger.info("🔥 Using permanent browser")
            return PERMANENT

        # Check hot pool
        if sig in HOT_POOL:
            crawler = HOT_POOL[sig]
            usage = USAGE_COUNT.get(sig, 0)
            
            # Ensure active_requests is initialized
            if not hasattr(crawler, 'active_requests'):
                crawler.active_requests = 0

            should_retire = False
            
            if RETIREMENT_ENABLED:
                # 1. Max Usage Check
                if usage >= MAX_USAGE_COUNT:
                    should_retire = True
                    logger.info(f"👴 Retirement time for browser {sig[:8]}: Max usage reached ({usage})")
                
                # 2. Memory Check (if used enough times to stabilize)
                elif usage >= MEMORY_RETIRE_MIN_USAGE:
                    try:
                        mem_percent = psutil.virtual_memory().percent
                        if mem_percent > MEMORY_RETIRE_THRESHOLD:
                            should_retire = True
                            logger.info(f"👴 Retirement time for browser {sig[:8]}: Memory high ({mem_percent}%)")
                    except Exception as e:
                        logger.warning(f"Failed to check memory for retirement: {e}")

            if should_retire:
                # Move to retired pool
                RETIRED_POOL[sig] = HOT_POOL.pop(sig)
                # Do NOT close here, let janitor handle it when active_requests is 0
                # Fall through to create a new one
            else:
                # Healthy -> Reuse
                LAST_USED[sig] = time.time()
                USAGE_COUNT[sig] = usage + 1
                crawler.active_requests += 1
                logger.info(f"♨️  Using hot pool browser (sig={sig[:8]}, usage={USAGE_COUNT[sig]}, active={crawler.active_requests})")
                return crawler

        # Check cold pool (promote to hot if used 3+ times)
        if sig in COLD_POOL:
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1

            if USAGE_COUNT[sig] >= 3:
                logger.info(f"⬆️  Promoting to hot pool (sig={sig[:8]}, count={USAGE_COUNT[sig]})")
                HOT_POOL[sig] = COLD_POOL.pop(sig)

                # Track promotion in monitor
                try:
                    from monitor import get_monitor
                    await get_monitor().track_janitor_event("promote", sig, {"count": USAGE_COUNT[sig]})
                except:
                    pass
                
                crawler = HOT_POOL[sig]
                if not hasattr(crawler, 'active_requests'):
                    crawler.active_requests = 0
                crawler.active_requests += 1
                return crawler

            logger.info(f"❄️  Using cold pool browser (sig={sig[:8]})")
            crawler = COLD_POOL[sig]
            if not hasattr(crawler, 'active_requests'):
                crawler.active_requests = 0
            crawler.active_requests += 1
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
    """Decrement active request count for a crawler."""
    async with LOCK:
        # Permanent browser doesn't need ref counting in this scheme 
        # (unless we want to track it too, but we are not touching its lifecycle)
        if crawler is PERMANENT:
            return

        if hasattr(crawler, 'active_requests'):
            crawler.active_requests -= 1
            if crawler.active_requests < 0:
                crawler.active_requests = 0
            
            # Identify which pool it belongs to for logging
            # (Optimization: Just log active count)
            # logger.debug(f"Released crawler, active={crawler.active_requests}")

async def init_permanent(cfg: BrowserConfig):
    """Initialize permanent default browser."""
    global PERMANENT, DEFAULT_CONFIG_SIG
    
    # Log retirement status once on startup (hooked here as it's called during app startup)
    if RETIREMENT_ENABLED:
        logger.info(f"✅ Browser retirement enabled (Max Usage: {MAX_USAGE_COUNT}, Mem Threshold: {MEMORY_RETIRE_THRESHOLD}%)")
    else:
        logger.info("ℹ️ Browser retirement disabled")

    async with LOCK:
        if PERMANENT:
            return
        DEFAULT_CONFIG_SIG = _sig(cfg)
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
        tasks.extend([c.close() for c in RETIRED_POOL.values()]) # Close retired too
        await asyncio.gather(*tasks, return_exceptions=True)
        HOT_POOL.clear()
        COLD_POOL.clear()
        RETIRED_POOL.clear()
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
            # Clean cold pool
            for sig in list(COLD_POOL.keys()):
                if now - LAST_USED.get(sig, now) > cold_ttl:
                    crawler = COLD_POOL[sig]
                    # Only close if no active requests
                    if not hasattr(crawler, 'active_requests') or crawler.active_requests == 0:
                        idle_time = now - LAST_USED[sig]
                        logger.info(f"🧹 Closing cold browser (sig={sig[:8]}, idle={idle_time:.0f}s)")
                        with suppress(Exception):
                            await crawler.close()
                        COLD_POOL.pop(sig, None)
                        LAST_USED.pop(sig, None)
                        USAGE_COUNT.pop(sig, None)
                        try:
                            from monitor import get_monitor
                            await get_monitor().track_janitor_event("close_cold", sig, {"idle_seconds": int(idle_time), "ttl": cold_ttl})
                        except:
                            pass

            # Clean hot pool (more conservative)
            for sig in list(HOT_POOL.keys()):
                if now - LAST_USED.get(sig, now) > hot_ttl:
                    crawler = HOT_POOL[sig]
                    # Only close if no active requests
                    if not hasattr(crawler, 'active_requests') or crawler.active_requests == 0:
                        idle_time = now - LAST_USED[sig]
                        logger.info(f"🧹 Closing hot browser (sig={sig[:8]}, idle={idle_time:.0f}s)")
                        with suppress(Exception):
                            await crawler.close()
                        HOT_POOL.pop(sig, None)
                        LAST_USED.pop(sig, None)
                        USAGE_COUNT.pop(sig, None)
                        try:
                            from monitor import get_monitor
                            await get_monitor().track_janitor_event("close_hot", sig, {"idle_seconds": int(idle_time), "ttl": hot_ttl})
                        except:
                            pass
            
            # Clean retired pool (Aggressive cleanup)
            for sig in list(RETIRED_POOL.keys()):
                crawler = RETIRED_POOL[sig]
                # Only close if no active requests
                if hasattr(crawler, 'active_requests') and crawler.active_requests == 0:
                    logger.info(f"💀 Janitor closing retired browser (sig={sig[:8]})")
                    with suppress(Exception):
                        await crawler.close()
                    RETIRED_POOL.pop(sig, None)
                    # Keys might have been popped from LAST_USED/USAGE_COUNT already
                    LAST_USED.pop(sig, None)
                    USAGE_COUNT.pop(sig, None)
                    try:
                        from monitor import get_monitor
                        await get_monitor().track_janitor_event("close_retired", sig, {})
                    except:
                        pass

            # Log pool stats
            if mem_pct > 60 or len(RETIRED_POOL) > 0:
                logger.info(f"📊 Pool: hot={len(HOT_POOL)}, cold={len(COLD_POOL)}, retired={len(RETIRED_POOL)}, mem={mem_pct:.1f}%")
