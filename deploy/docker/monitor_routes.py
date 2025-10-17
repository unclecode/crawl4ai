# monitor_routes.py - Monitor API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from monitor import get_monitor
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/health")
async def get_health():
    """Get current system health snapshot."""
    try:
        monitor = get_monitor()
        return monitor.get_health_summary()
    except Exception as e:
        logger.error(f"Error getting health: {e}")
        raise HTTPException(500, str(e))


@router.get("/requests")
async def get_requests(status: str = "all", limit: int = 50):
    """Get active and completed requests.

    Args:
        status: Filter by 'active', 'completed', 'success', 'error', or 'all'
        limit: Max number of completed requests to return (default 50)
    """
    try:
        monitor = get_monitor()

        if status == "active":
            return {"active": monitor.get_active_requests(), "completed": []}
        elif status == "completed":
            return {"active": [], "completed": monitor.get_completed_requests(limit)}
        elif status in ["success", "error"]:
            return {"active": [], "completed": monitor.get_completed_requests(limit, status)}
        else:  # "all"
            return {
                "active": monitor.get_active_requests(),
                "completed": monitor.get_completed_requests(limit)
            }
    except Exception as e:
        logger.error(f"Error getting requests: {e}")
        raise HTTPException(500, str(e))


@router.get("/browsers")
async def get_browsers():
    """Get detailed browser pool information."""
    try:
        monitor = get_monitor()
        browsers = monitor.get_browser_list()

        # Calculate summary stats
        total_browsers = len(browsers)
        total_memory = sum(b["memory_mb"] for b in browsers)

        # Calculate reuse rate from recent requests
        recent = monitor.get_completed_requests(100)
        pool_hits = sum(1 for r in recent if r.get("pool_hit", False))
        reuse_rate = (pool_hits / len(recent) * 100) if recent else 0

        return {
            "browsers": browsers,
            "summary": {
                "total_count": total_browsers,
                "total_memory_mb": total_memory,
                "reuse_rate_percent": round(reuse_rate, 1)
            }
        }
    except Exception as e:
        logger.error(f"Error getting browsers: {e}")
        raise HTTPException(500, str(e))


@router.get("/endpoints/stats")
async def get_endpoint_stats():
    """Get aggregated endpoint statistics."""
    try:
        monitor = get_monitor()
        return monitor.get_endpoint_stats_summary()
    except Exception as e:
        logger.error(f"Error getting endpoint stats: {e}")
        raise HTTPException(500, str(e))


@router.get("/timeline")
async def get_timeline(metric: str = "memory", window: str = "5m"):
    """Get timeline data for charts.

    Args:
        metric: 'memory', 'requests', or 'browsers'
        window: Time window (only '5m' supported for now)
    """
    try:
        monitor = get_monitor()
        return monitor.get_timeline_data(metric, window)
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        raise HTTPException(500, str(e))


@router.get("/logs/janitor")
async def get_janitor_log(limit: int = 100):
    """Get recent janitor cleanup events."""
    try:
        monitor = get_monitor()
        return {"events": monitor.get_janitor_log(limit)}
    except Exception as e:
        logger.error(f"Error getting janitor log: {e}")
        raise HTTPException(500, str(e))


@router.get("/logs/errors")
async def get_errors_log(limit: int = 100):
    """Get recent errors."""
    try:
        monitor = get_monitor()
        return {"errors": monitor.get_errors_log(limit)}
    except Exception as e:
        logger.error(f"Error getting errors log: {e}")
        raise HTTPException(500, str(e))


# ========== Control Actions ==========

class KillBrowserRequest(BaseModel):
    sig: str


@router.post("/actions/cleanup")
async def force_cleanup():
    """Force immediate janitor cleanup (kills idle cold pool browsers)."""
    try:
        from crawler_pool import COLD_POOL, LAST_USED, USAGE_COUNT, LOCK
        import time
        from contextlib import suppress

        killed_count = 0
        now = time.time()

        async with LOCK:
            for sig in list(COLD_POOL.keys()):
                # Kill all cold pool browsers immediately
                logger.info(f"🧹 Force cleanup: closing cold browser (sig={sig[:8]})")
                with suppress(Exception):
                    await COLD_POOL[sig].close()
                COLD_POOL.pop(sig, None)
                LAST_USED.pop(sig, None)
                USAGE_COUNT.pop(sig, None)
                killed_count += 1

        monitor = get_monitor()
        monitor.track_janitor_event("force_cleanup", "manual", {"killed": killed_count})

        return {"success": True, "killed_browsers": killed_count}
    except Exception as e:
        logger.error(f"Error during force cleanup: {e}")
        raise HTTPException(500, str(e))


@router.post("/actions/kill_browser")
async def kill_browser(req: KillBrowserRequest):
    """Kill a specific browser by signature (hot or cold only).

    Args:
        sig: Browser config signature (first 8 chars)
    """
    try:
        from crawler_pool import HOT_POOL, COLD_POOL, LAST_USED, USAGE_COUNT, LOCK, DEFAULT_CONFIG_SIG
        from contextlib import suppress

        # Find full signature matching prefix
        target_sig = None
        pool_type = None

        async with LOCK:
            # Check hot pool
            for sig in HOT_POOL.keys():
                if sig.startswith(req.sig):
                    target_sig = sig
                    pool_type = "hot"
                    break

            # Check cold pool
            if not target_sig:
                for sig in COLD_POOL.keys():
                    if sig.startswith(req.sig):
                        target_sig = sig
                        pool_type = "cold"
                        break

            # Check if trying to kill permanent
            if DEFAULT_CONFIG_SIG and DEFAULT_CONFIG_SIG.startswith(req.sig):
                raise HTTPException(403, "Cannot kill permanent browser. Use restart instead.")

            if not target_sig:
                raise HTTPException(404, f"Browser with sig={req.sig} not found")

            # Kill the browser
            if pool_type == "hot":
                browser = HOT_POOL.pop(target_sig)
            else:
                browser = COLD_POOL.pop(target_sig)

            with suppress(Exception):
                await browser.close()

            LAST_USED.pop(target_sig, None)
            USAGE_COUNT.pop(target_sig, None)

        logger.info(f"🔪 Killed {pool_type} browser (sig={target_sig[:8]})")

        monitor = get_monitor()
        monitor.track_janitor_event("kill_browser", target_sig, {"pool": pool_type, "manual": True})

        return {"success": True, "killed_sig": target_sig[:8], "pool_type": pool_type}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error killing browser: {e}")
        raise HTTPException(500, str(e))


@router.post("/actions/restart_browser")
async def restart_browser(req: KillBrowserRequest):
    """Restart a browser (kill + recreate). Works for permanent too.

    Args:
        sig: Browser config signature (first 8 chars), or "permanent"
    """
    try:
        from crawler_pool import (PERMANENT, HOT_POOL, COLD_POOL, LAST_USED,
                                  USAGE_COUNT, LOCK, DEFAULT_CONFIG_SIG, init_permanent)
        from crawl4ai import AsyncWebCrawler, BrowserConfig
        from contextlib import suppress
        import time

        # Handle permanent browser restart
        if req.sig == "permanent" or (DEFAULT_CONFIG_SIG and DEFAULT_CONFIG_SIG.startswith(req.sig)):
            async with LOCK:
                if PERMANENT:
                    with suppress(Exception):
                        await PERMANENT.close()

                # Reinitialize permanent
                from utils import load_config
                config = load_config()
                await init_permanent(BrowserConfig(
                    extra_args=config["crawler"]["browser"].get("extra_args", []),
                    **config["crawler"]["browser"].get("kwargs", {}),
                ))

            logger.info("🔄 Restarted permanent browser")
            return {"success": True, "restarted": "permanent"}

        # Handle hot/cold browser restart
        target_sig = None
        pool_type = None
        browser_config = None

        async with LOCK:
            # Find browser
            for sig in HOT_POOL.keys():
                if sig.startswith(req.sig):
                    target_sig = sig
                    pool_type = "hot"
                    # Would need to reconstruct config (not stored currently)
                    break

            if not target_sig:
                for sig in COLD_POOL.keys():
                    if sig.startswith(req.sig):
                        target_sig = sig
                        pool_type = "cold"
                        break

            if not target_sig:
                raise HTTPException(404, f"Browser with sig={req.sig} not found")

            # Kill existing
            if pool_type == "hot":
                browser = HOT_POOL.pop(target_sig)
            else:
                browser = COLD_POOL.pop(target_sig)

            with suppress(Exception):
                await browser.close()

            # Note: We can't easily recreate with same config without storing it
            # For now, just kill and let new requests create fresh ones
            LAST_USED.pop(target_sig, None)
            USAGE_COUNT.pop(target_sig, None)

        logger.info(f"🔄 Restarted {pool_type} browser (sig={target_sig[:8]})")

        monitor = get_monitor()
        monitor.track_janitor_event("restart_browser", target_sig, {"pool": pool_type})

        return {"success": True, "restarted_sig": target_sig[:8], "note": "Browser will be recreated on next request"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting browser: {e}")
        raise HTTPException(500, str(e))


@router.post("/stats/reset")
async def reset_stats():
    """Reset today's endpoint counters."""
    try:
        monitor = get_monitor()
        monitor.endpoint_stats.clear()
        await monitor._persist_endpoint_stats()

        return {"success": True, "message": "Endpoint stats reset"}
    except Exception as e:
        logger.error(f"Error resetting stats: {e}")
        raise HTTPException(500, str(e))
