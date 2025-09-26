# crawler_pool.py  (new file)
import asyncio, json, hashlib, time, psutil
from contextlib import suppress
from typing import Dict, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig
from .utils import load_config

CONFIG = load_config()

POOL: Dict[str, AsyncWebCrawler] = {}
LAST_USED: Dict[str, float] = {}
LOCK = asyncio.Lock()

MEM_LIMIT  = CONFIG.get("crawler", {}).get("memory_threshold_percent", 95.0)   # % RAM – refuse new browsers above this
IDLE_TTL  = CONFIG.get("crawler", {}).get("pool", {}).get("idle_ttl_sec", 1800)   # close if unused for 30 min

def _sig(cfg: BrowserConfig, crawler_strategy: Optional[object]  = None) -> str:
    """
    Generate a unique signature for a crawler based on browser config
    and optional crawler strategy. This ensures that crawlers with
    different strategies (e.g., PDF) are stored separately in the pool.
    """
    payload = cfg.to_dict()

    if crawler_strategy is not None:
        payload["strategy"] = crawler_strategy.__class__.__name__

    json_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_payload.encode()).hexdigest()


# Track in-flight creations to dedupe concurrent get_crawler() calls
CREATING: Dict[str, asyncio.Future] = {}

async def get_crawler(
    cfg: BrowserConfig, crawler_strategy: Optional[object] = None
) -> AsyncWebCrawler:
    """
    Return a shared AsyncWebCrawler instance for the given config.
    Only the 'creator' coroutine actually starts the crawler and sets
    the future result to avoid InvalidStateError and double creation.
    """
    sig: Optional[str] = None
    try:
        sig = _sig(cfg, crawler_strategy=crawler_strategy)

        creator = False  # Track whether *this* caller will create the crawler
        async with LOCK:
            # Reuse an existing crawler if available
            if sig in POOL:
                LAST_USED[sig] = time.time()
                return POOL[sig]

            # Join in-flight creation if it exists
            fut = CREATING.get(sig)
            if fut is None:
                # First caller becomes the creator
                if psutil.virtual_memory().percent >= MEM_LIMIT:
                    raise MemoryError("RAM pressure – new browser denied")
                fut = asyncio.get_running_loop().create_future()
                CREATING[sig] = fut
                creator = True

        if creator:
            # Only the creator actually creates/starts the crawler
            try:
                crawler = AsyncWebCrawler(
                    config=cfg, thread_safe=False, crawler_strategy=crawler_strategy
                )
                await crawler.start()
                async with LOCK:
                    POOL[sig] = crawler
                    LAST_USED[sig] = time.time()
                fut.set_result(crawler)
            except Exception as e:
                fut.set_exception(e)
                raise RuntimeError("Failed to start browser") from e
            finally:
                async with LOCK:
                    CREATING.pop(sig, None)

        # Await the shared result (crawler or the same exception)
        return await fut

    except MemoryError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to start browser: {e}")
    finally:
        # Update last-used if a crawler now exists
        async with LOCK:
            if sig and sig in POOL:
                LAST_USED[sig] = time.time()
            else:
                if sig:
                    POOL.pop(sig, None)
                    LAST_USED.pop(sig, None)
        
async def close_all():
    async with LOCK:
        await asyncio.gather(*(c.close() for c in POOL.values()), return_exceptions=True)
        POOL.clear(); LAST_USED.clear()

async def janitor():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        async with LOCK:
            for sig, crawler in list(POOL.items()):
                if now - LAST_USED[sig] > IDLE_TTL:
                    with suppress(Exception): await crawler.close()
                    POOL.pop(sig, None); LAST_USED.pop(sig, None)
