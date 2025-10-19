# monitor_routes.py - Monitor API endpoints
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
from monitor import get_monitor
from utils import detect_deployment_mode, get_container_id
import logging
import asyncio
import json
import re

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitor", tags=["monitor"])


# ========== Security & Validation ==========

def validate_container_id(cid: str) -> bool:
    """Validate container ID format to prevent Redis key injection.

    Docker container IDs are 12-64 character hexadecimal strings.
    Hostnames are alphanumeric with dashes and underscores.

    Args:
        cid: Container ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not cid or not isinstance(cid, str):
        return False

    # Allow alphanumeric, dashes, and underscores only (1-64 chars)
    # This prevents path traversal (../../), wildcards (**), and other injection attempts
    return bool(re.match(r'^[a-zA-Z0-9_-]{1,64}$', cid))


# ========== Redis Aggregation Helpers ==========

async def _get_active_containers():
    """Get list of active container IDs from Redis with validation."""
    try:
        monitor = get_monitor()
        container_ids = await monitor.redis.smembers("monitor:active_containers")

        # Decode and validate each container ID
        validated = []
        for cid in container_ids:
            cid_str = cid.decode() if isinstance(cid, bytes) else cid

            if validate_container_id(cid_str):
                validated.append(cid_str)
            else:
                logger.warning(f"Invalid container ID format rejected: {cid_str}")

        return validated
    except Exception as e:
        logger.error(f"Failed to get active containers: {e}")
        return []


async def _aggregate_active_requests():
    """Aggregate active requests from all containers."""
    container_ids = await _get_active_containers()
    all_requests = []

    monitor = get_monitor()
    for container_id in container_ids:
        try:
            data = await monitor.redis.get(f"monitor:{container_id}:active_requests")
            if data:
                requests = json.loads(data)
                all_requests.extend(requests)
        except Exception as e:
            logger.warning(f"Failed to get active requests from {container_id}: {e}")

    return all_requests


async def _aggregate_completed_requests(limit=100):
    """Aggregate completed requests from all containers."""
    container_ids = await _get_active_containers()
    all_requests = []

    monitor = get_monitor()
    for container_id in container_ids:
        try:
            data = await monitor.redis.get(f"monitor:{container_id}:completed")
            if data:
                requests = json.loads(data)
                all_requests.extend(requests)
        except Exception as e:
            logger.warning(f"Failed to get completed requests from {container_id}: {e}")

    # Sort by end_time (most recent first) and limit
    all_requests.sort(key=lambda x: x.get("end_time", 0), reverse=True)
    return all_requests[:limit]


async def _aggregate_janitor_events(limit=100):
    """Aggregate janitor events from all containers."""
    container_ids = await _get_active_containers()
    all_events = []

    monitor = get_monitor()
    for container_id in container_ids:
        try:
            data = await monitor.redis.get(f"monitor:{container_id}:janitor")
            if data:
                events = json.loads(data)
                all_events.extend(events)
        except Exception as e:
            logger.warning(f"Failed to get janitor events from {container_id}: {e}")

    # Sort by timestamp (most recent first) and limit
    all_events.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return all_events[:limit]


async def _aggregate_errors(limit=100):
    """Aggregate errors from all containers."""
    container_ids = await _get_active_containers()
    all_errors = []

    monitor = get_monitor()
    for container_id in container_ids:
        try:
            data = await monitor.redis.get(f"monitor:{container_id}:errors")
            if data:
                errors = json.loads(data)
                all_errors.extend(errors)
        except Exception as e:
            logger.warning(f"Failed to get errors from {container_id}: {e}")

    # Sort by timestamp (most recent first) and limit
    all_errors.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return all_errors[:limit]


@router.get("/health")
async def get_health():
    """Get current system health snapshot."""
    try:
        monitor = get_monitor()
        return await monitor.get_health_summary()
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
    # Input validation
    if status not in ["all", "active", "completed", "success", "error"]:
        raise HTTPException(400, f"Invalid status: {status}. Must be one of: all, active, completed, success, error")
    if limit < 1 or limit > 1000:
        raise HTTPException(400, f"Invalid limit: {limit}. Must be between 1 and 1000")

    try:
        # Aggregate from all containers via Redis
        active_requests = await _aggregate_active_requests()
        completed_requests = await _aggregate_completed_requests(limit)

        # Filter by status if needed
        if status in ["success", "error"]:
            is_success = (status == "success")
            completed_requests = [r for r in completed_requests if r.get("success") == is_success]

        if status == "active":
            return {"active": active_requests, "completed": []}
        elif status == "completed":
            return {"active": [], "completed": completed_requests}
        else:  # "all" or success/error
            return {
                "active": active_requests,
                "completed": completed_requests
            }
    except Exception as e:
        logger.error(f"Error getting requests: {e}")
        raise HTTPException(500, str(e))


@router.get("/browsers")
async def get_browsers():
    """Get detailed browser pool information."""
    try:
        monitor = get_monitor()
        container_id = get_container_id()
        browsers = await monitor.get_browser_list()

        # Add container_id to each browser
        for browser in browsers:
            browser["container_id"] = container_id

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
            },
            "container_id": container_id
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
    # Input validation
    if metric not in ["memory", "requests", "browsers"]:
        raise HTTPException(400, f"Invalid metric: {metric}. Must be one of: memory, requests, browsers")
    if window != "5m":
        raise HTTPException(400, f"Invalid window: {window}. Only '5m' is currently supported")

    try:
        monitor = get_monitor()
        return monitor.get_timeline_data(metric, window)
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        raise HTTPException(500, str(e))


@router.get("/logs/janitor")
async def get_janitor_log(limit: int = 100):
    """Get recent janitor cleanup events."""
    # Input validation
    if limit < 1 or limit > 1000:
        raise HTTPException(400, f"Invalid limit: {limit}. Must be between 1 and 1000")

    try:
        # Aggregate from all containers via Redis
        events = await _aggregate_janitor_events(limit)
        return {"events": events}
    except Exception as e:
        logger.error(f"Error getting janitor log: {e}")
        raise HTTPException(500, str(e))


@router.get("/logs/errors")
async def get_errors_log(limit: int = 100):
    """Get recent errors."""
    # Input validation
    if limit < 1 or limit > 1000:
        raise HTTPException(400, f"Invalid limit: {limit}. Must be between 1 and 1000")

    try:
        # Aggregate from all containers via Redis
        errors = await _aggregate_errors(limit)
        return {"errors": errors}
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
        await monitor.track_janitor_event("force_cleanup", "manual", {"killed": killed_count})

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

            # Warn if there are active requests (browser might be in use)
            monitor = get_monitor()
            active_count = len(monitor.get_active_requests())
            if active_count > 0:
                logger.warning(f"Killing browser {target_sig[:8]} while {active_count} requests are active - may cause failures")

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
        await monitor.track_janitor_event("kill_browser", target_sig, {"pool": pool_type, "manual": True})

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
        await monitor.track_janitor_event("restart_browser", target_sig, {"pool": pool_type})

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


@router.get("/containers")
async def get_containers():
    """Get container deployment info from Redis heartbeats."""
    try:
        monitor = get_monitor()
        container_ids = await _get_active_containers()

        containers = []
        for cid in container_ids:
            try:
                # Get heartbeat data
                data = await monitor.redis.get(f"monitor:heartbeat:{cid}")
                if data:
                    info = json.loads(data)
                    containers.append({
                        "id": info.get("id", cid),
                        "hostname": info.get("hostname", cid),
                        "healthy": True  # If heartbeat exists, it's healthy
                    })
            except Exception as e:
                logger.warning(f"Failed to get heartbeat for {cid}: {e}")

        # Determine mode
        mode = "single" if len(containers) == 1 else "compose"
        if len(containers) > 1:
            # Check if any hostname has swarm pattern (service.slot.task_id)
            if any("." in c["hostname"] and len(c["hostname"].split(".")) > 2 for c in containers):
                mode = "swarm"

        return {
            "mode": mode,
            "container_id": get_container_id(),
            "containers": containers,
            "count": len(containers)
        }
    except Exception as e:
        logger.error(f"Error getting containers: {e}")
        raise HTTPException(500, str(e))


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates.

    Sends aggregated updates every 2 seconds from all containers with:
    - Health stats (local container)
    - Active/completed requests (aggregated from all containers)
    - Browser pool status (local container only - not in Redis)
    - Timeline data (local container - TODO: aggregate from Redis)
    - Janitor events (aggregated from all containers)
    - Errors (aggregated from all containers)
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        while True:
            try:
                # Gather aggregated monitoring data from Redis
                monitor = get_monitor()
                container_id = get_container_id()

                # Get container info
                containers_info = await get_containers()

                # AGGREGATE data from all containers via Redis
                active_reqs = await _aggregate_active_requests()
                completed_reqs = await _aggregate_completed_requests(limit=10)
                janitor_events = await _aggregate_janitor_events(limit=10)
                errors_log = await _aggregate_errors(limit=10)

                # Local container data (not aggregated)
                local_health = await monitor.get_health_summary()
                browsers = await monitor.get_browser_list()  # Browser list is local only

                # Add container_id to browsers (they're local)
                for browser in browsers:
                    browser["container_id"] = container_id

                data = {
                    "timestamp": asyncio.get_event_loop().time(),
                    "container_id": container_id,  # This container handling the WebSocket
                    "is_aggregated": True,  # Flag to indicate aggregated data
                    "local_health": local_health,  # This container's health
                    "containers": containers_info.get("containers", []),  # All containers
                    "requests": {
                        "active": active_reqs,  # Aggregated from all containers
                        "completed": completed_reqs  # Aggregated from all containers
                    },
                    "browsers": browsers,  # Local only (not in Redis)
                    "timeline": {
                        # TODO: Aggregate timeline from Redis (currently local only)
                        "memory": monitor.get_timeline_data("memory", "5m"),
                        "requests": monitor.get_timeline_data("requests", "5m"),
                        "browsers": monitor.get_timeline_data("browsers", "5m")
                    },
                    "janitor": janitor_events,  # Aggregated from all containers
                    "errors": errors_log  # Aggregated from all containers
                }

                # Send update to client
                await websocket.send_json(data)

                # Wait 2 seconds before next update
                await asyncio.sleep(2)

            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}", exc_info=True)
                await asyncio.sleep(2)  # Continue trying

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
    finally:
        logger.info("WebSocket connection closed")
