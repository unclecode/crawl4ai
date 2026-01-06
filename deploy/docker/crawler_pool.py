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
POOL_AUDIT_ENABLED = os.getenv("CRAWL4AI_POOL_AUDIT_ENABLED", "false").lower() == "true"
PERMANENT_BROWSER_DISABLED = os.getenv("CRAWL4AI_PERMANENT_BROWSER_DISABLED", "false").lower() == "true"

MAX_USAGE_COUNT = int(os.getenv("CRAWL4AI_BROWSER_MAX_USAGE", "100"))
MEMORY_RETIRE_THRESHOLD = int(os.getenv("CRAWL4AI_MEMORY_RETIRE_THRESHOLD", "75"))
MEMORY_RETIRE_MIN_USAGE = int(os.getenv("CRAWL4AI_MEMORY_RETIRE_MIN_USAGE", "10"))

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
        # Use permanent browser if not disabled and config matches
        if not PERMANENT_BROWSER_DISABLED and PERMANENT and _is_default_config(sig):
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            logger.info("🔥 Using permanent browser")
            return PERMANENT

        # Check hot pool
        if sig in HOT_POOL:
            crawler = HOT_POOL[sig]
            usage = USAGE_COUNT.get(sig, 0)
            
            if not hasattr(crawler, 'active_requests'):
                crawler.active_requests = 0

            should_retire = False
            if RETIREMENT_ENABLED:
                if usage >= MAX_USAGE_COUNT:
                    should_retire = True
                    logger.info(f"👴 Retirement time for browser {sig[:8]}: Max usage reached ({usage})")
                elif usage >= MEMORY_RETIRE_MIN_USAGE:
                    try:
                        mem_percent = psutil.virtual_memory().percent
                        if mem_percent > MEMORY_RETIRE_THRESHOLD:
                            should_retire = True
                            logger.info(f"👴 Retirement time for browser {sig[:8]}: Memory high ({mem_percent}%)")
                    except Exception as e:
                        logger.warning(f"Failed to check memory for retirement: {e}")

            if should_retire:
                RETIRED_POOL[sig] = HOT_POOL.pop(sig)
            else:
                LAST_USED[sig] = time.time()
                USAGE_COUNT[sig] = usage + 1
                crawler.active_requests += 1
                logger.info(f"♨️  Using hot pool browser (sig={sig[:8]}, usage={USAGE_COUNT[sig]}, active={crawler.active_requests})")
                return crawler

        # Check cold pool
        if sig in COLD_POOL:
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1

            if USAGE_COUNT[sig] >= 3:
                logger.info(f"⬆️  Promoting to hot pool (sig={sig[:8]}, count={USAGE_COUNT[sig]})")
                HOT_POOL[sig] = COLD_POOL.pop(sig)
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
        if hasattr(crawler, 'active_requests'):
            crawler.active_requests -= 1
            if crawler.active_requests < 0:
                crawler.active_requests = 0

async def init_permanent(cfg: BrowserConfig):
    """Initialize permanent default browser."""
    global PERMANENT, DEFAULT_CONFIG_SIG
    
    # Log retirement status once on startup
    if RETIREMENT_ENABLED:
        logger.info(f"✅ Browser retirement enabled (Max Usage: {MAX_USAGE_COUNT}, Mem Threshold: {MEMORY_RETIRE_THRESHOLD}%)")
    else:
        logger.info("ℹ️ Browser retirement disabled")

    async with LOCK:
        DEFAULT_CONFIG_SIG = _sig(cfg)
        if PERMANENT_BROWSER_DISABLED:
            logger.info("ℹ️ Permanent browser is DISABLED via config")
            return

        logger.info("🔥 Creating permanent default browser")
        PERMANENT = AsyncWebCrawler(config=cfg, thread_safe=False)
        await PERMANENT.start()
        LAST_USED[DEFAULT_CONFIG_SIG] = time.time()
        USAGE_COUNT[DEFAULT_CONFIG_SIG] = 0

async def close_all():
    """Close all browsers."""
    async with LOCK:
        tasks = []
        tasks.extend([c.close() for c in HOT_POOL.values()])
        tasks.extend([c.close() for c in COLD_POOL.values()])
        tasks.extend([c.close() for c in RETIRED_POOL.values()]) 
        await asyncio.gather(*tasks, return_exceptions=True)
        HOT_POOL.clear()
        COLD_POOL.clear()
        RETIRED_POOL.clear()
        LAST_USED.clear()
        USAGE_COUNT.clear()

async def janitor():
    """Adaptive cleanup based on memory pressure."""
    last_audit_time = 0
    while True:
        mem_pct = get_container_memory_percent()

        # Adaptive intervals and TTLs
        # Strictly follow BASE_IDLE_TTL without multipliers
        if mem_pct > 80:
            interval, cold_ttl, hot_ttl = 10, 30, 60
        elif mem_pct > 60:
            interval, cold_ttl, hot_ttl = 30, 60, 120
        else:
            interval, cold_ttl, hot_ttl = 60, BASE_IDLE_TTL, BASE_IDLE_TTL

        await asyncio.sleep(interval)

        now = time.time()
        async with LOCK:
            # [Audit Log] Every 5 minutes
            if POOL_AUDIT_ENABLED and now - last_audit_time >= 300:
                def _pool_info(pool):
                    res = []
                    for s, c in pool.items():
                        req = getattr(c, 'active_requests', 0)
                        u_count = USAGE_COUNT.get(s, 0)
                        res.append(f"{s[:8]}(req={req}, usage={u_count})")
                    return res
                
                logger.info(
                    f"🧐 [Pool Audit]\n"
                    f"  - PERMANENT: {'Active' if PERMANENT else 'None/Disabled'}\n"
                    f"  - HOT_POOL: {len(HOT_POOL)} {_pool_info(HOT_POOL)}\n"
                    f"  - COLD_POOL: {len(COLD_POOL)} {_pool_info(COLD_POOL)}\n"
                    f"  - RETIRED_POOL: {len(RETIRED_POOL)} {_pool_info(RETIRED_POOL)}\n"
                    f"  - System Memory: {mem_pct:.1f}%"
                )
                last_audit_time = now

            # Clean cold pool
            for sig in list(COLD_POOL.keys()):
                if now - LAST_USED.get(sig, now) > cold_ttl:
                    crawler = COLD_POOL[sig]
                    if not hasattr(crawler, 'active_requests') or crawler.active_requests == 0:
                        logger.info(f"🧹 Closing cold browser (idle, sig={sig[:8]})")
                        with suppress(Exception):
                            await crawler.close()
                        COLD_POOL.pop(sig, None)
                        LAST_USED.pop(sig, None)
                        USAGE_COUNT.pop(sig, None)

            # Clean hot pool
            for sig in list(HOT_POOL.keys()):
                if now - LAST_USED.get(sig, now) > hot_ttl:
                    crawler = HOT_POOL[sig]
                    if not hasattr(crawler, 'active_requests') or crawler.active_requests == 0:
                        logger.info(f"🧹 Closing hot browser (idle={now - LAST_USED[sig]:.0f}s, sig={sig[:8]})")
                        with suppress(Exception):
                            await crawler.close()
                        HOT_POOL.pop(sig, None)
                        LAST_USED.pop(sig, None)
                        USAGE_COUNT.pop(sig, None)
            
            # Clean retired pool
            for sig in list(RETIRED_POOL.keys()):
                crawler = RETIRED_POOL[sig]
                if hasattr(crawler, 'active_requests') and crawler.active_requests == 0:
                    logger.info(f"💀 Janitor closing retired browser (sig={sig[:8]})")
                    with suppress(Exception):
                        await crawler.close()
                    RETIRED_POOL.pop(sig, None)

            if mem_pct > 60 or len(RETIRED_POOL) > 0:
                logger.info(f"📊 Pool: hot={len(HOT_POOL)}, cold={len(COLD_POOL)}, retired={len(RETIRED_POOL)}, mem={mem_pct:.1f}%")
