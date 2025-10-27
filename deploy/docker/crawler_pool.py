# crawler_pool.py  (new file)
import asyncio
import hashlib
import json
import time
from contextlib import suppress
from typing import Dict, Optional

import psutil

from crawl4ai import AsyncWebCrawler, BrowserConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

# Import browser adapters with fallback
try:
    from crawl4ai.browser_adapter import BrowserAdapter, PlaywrightAdapter
except ImportError:
    # Fallback for development environment
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from crawl4ai.browser_adapter import BrowserAdapter, PlaywrightAdapter
from utils import load_config

CONFIG = load_config()

POOL: Dict[str, AsyncWebCrawler] = {}
LAST_USED: Dict[str, float] = {}
LOCK = asyncio.Lock()

MEM_LIMIT = CONFIG.get("crawler", {}).get(
    "memory_threshold_percent", 95.0
)  # % RAM – refuse new browsers above this
IDLE_TTL = (
    CONFIG.get("crawler", {}).get("pool", {}).get("idle_ttl_sec", 1800)
)  # close if unused for 30 min


def _sig(cfg: BrowserConfig, adapter: Optional[BrowserAdapter] = None) -> str:
    try:
        config_payload = json.dumps(cfg.to_dict(), sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        # Fallback to string representation if JSON serialization fails
        config_payload = str(cfg.to_dict())
    adapter_name = adapter.__class__.__name__ if adapter else "PlaywrightAdapter"
    payload = f"{config_payload}:{adapter_name}"
    return hashlib.sha1(payload.encode()).hexdigest()


async def get_crawler(
    cfg: BrowserConfig, adapter: Optional[BrowserAdapter] = None
) -> AsyncWebCrawler:
    sig = None
    try:
        sig = _sig(cfg, adapter)
        async with LOCK:
            if sig in POOL:
                LAST_USED[sig] = time.time()
                return POOL[sig]
            if psutil.virtual_memory().percent >= MEM_LIMIT:
                raise MemoryError("RAM pressure – new browser denied")

            # Create crawler - let it initialize the strategy with proper logger
            # Pass browser_adapter as a kwarg so AsyncWebCrawler can use it when creating the strategy
            crawler = AsyncWebCrawler(
                config=cfg, 
                thread_safe=False
            )
            
            # Set the browser adapter on the strategy after crawler initialization
            if adapter:
                # Create a new strategy with the adapter and the crawler's logger
                from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
                crawler.crawler_strategy = AsyncPlaywrightCrawlerStrategy(
                    browser_config=cfg, 
                    logger=crawler.logger,
                    browser_adapter=adapter
                )
            
            await crawler.start()
            POOL[sig] = crawler
            LAST_USED[sig] = time.time()
            return crawler
    except MemoryError as e:
        raise MemoryError(f"RAM pressure – new browser denied: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to start browser: {e}")
    finally:
        if sig:
            if sig in POOL:
                LAST_USED[sig] = time.time()
            else:
                # If we failed to start the browser, we should remove it from the pool
                POOL.pop(sig, None)
                LAST_USED.pop(sig, None)
        # If we failed to start the browser, we should remove it from the pool


async def close_all():
    async with LOCK:
        await asyncio.gather(
            *(c.close() for c in POOL.values()), return_exceptions=True
        )
        POOL.clear()
        LAST_USED.clear()


async def janitor():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        async with LOCK:
            for sig, crawler in list(POOL.items()):
                if now - LAST_USED[sig] > IDLE_TTL:
                    with suppress(Exception):
                        await crawler.close()
                    POOL.pop(sig, None)
                    LAST_USED.pop(sig, None)
