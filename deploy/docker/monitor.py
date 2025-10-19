# monitor.py - Real-time monitoring stats with Redis persistence
import time
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass
from redis import asyncio as aioredis
from utils import get_container_memory_percent
import psutil
import logging

logger = logging.getLogger(__name__)


# ========== Configuration ==========

@dataclass
class RedisTTLConfig:
    """Redis TTL configuration (in seconds).

    Configures how long different types of monitoring data are retained in Redis.
    Adjust based on your monitoring needs and Redis memory constraints.
    """
    active_requests: int = 300  # 5 minutes - short-lived active request data
    completed_requests: int = 3600  # 1 hour - recent completed requests
    janitor_events: int = 3600  # 1 hour - browser cleanup events
    errors: int = 3600  # 1 hour - error logs
    endpoint_stats: int = 86400  # 24 hours - aggregated endpoint statistics
    heartbeat: int = 60  # 1 minute - container heartbeat (2x the 30s interval)

    @classmethod
    def from_env(cls) -> 'RedisTTLConfig':
        """Load TTL configuration from environment variables."""
        import os
        return cls(
            active_requests=int(os.getenv('REDIS_TTL_ACTIVE_REQUESTS', 300)),
            completed_requests=int(os.getenv('REDIS_TTL_COMPLETED_REQUESTS', 3600)),
            janitor_events=int(os.getenv('REDIS_TTL_JANITOR_EVENTS', 3600)),
            errors=int(os.getenv('REDIS_TTL_ERRORS', 3600)),
            endpoint_stats=int(os.getenv('REDIS_TTL_ENDPOINT_STATS', 86400)),
            heartbeat=int(os.getenv('REDIS_TTL_HEARTBEAT', 60)),
        )


class MonitorStats:
    """Tracks real-time server stats with Redis persistence."""

    def __init__(self, redis: aioredis.Redis, ttl_config: Optional[RedisTTLConfig] = None):
        self.redis = redis
        self.ttl = ttl_config or RedisTTLConfig.from_env()
        self.start_time = time.time()

        # Get container ID for Redis keys
        from utils import get_container_id
        self.container_id = get_container_id()

        # In-memory queues (fast reads, Redis backup)
        self.active_requests: Dict[str, Dict] = {}  # id -> request info
        self.completed_requests: deque = deque(maxlen=100)  # Last 100
        self.janitor_events: deque = deque(maxlen=100)
        self.errors: deque = deque(maxlen=100)

        # Endpoint stats (persisted in Redis)
        self.endpoint_stats: Dict[str, Dict] = {}  # endpoint -> {count, total_time, errors, ...}

        # Background persistence queue (max 10 pending persist requests)
        self._persist_queue: asyncio.Queue = asyncio.Queue(maxsize=10)
        self._persist_worker_task: Optional[asyncio.Task] = None

        # Heartbeat task for container discovery
        self._heartbeat_task: Optional[asyncio.Task] = None

        # Timeline data (5min window, 5s resolution = 60 points)
        self.memory_timeline: deque = deque(maxlen=60)
        self.requests_timeline: deque = deque(maxlen=60)
        self.browser_timeline: deque = deque(maxlen=60)

    async def track_request_start(self, request_id: str, endpoint: str, url: str, config: Dict = None):
        """Track new request start."""
        req_info = {
            "id": request_id,
            "endpoint": endpoint,
            "url": url[:100],  # Truncate long URLs
            "start_time": time.time(),
            "config_sig": config.get("sig", "default") if config else "default",
            "mem_start": psutil.Process().memory_info().rss / (1024 * 1024),
            "container_id": self.container_id
        }
        self.active_requests[request_id] = req_info

        # Persist to Redis
        await self._persist_active_requests()

        # Increment endpoint counter
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {
                "count": 0, "total_time": 0, "errors": 0,
                "pool_hits": 0, "success": 0
            }
        self.endpoint_stats[endpoint]["count"] += 1

        # Queue persistence (handled by background worker)
        try:
            self._persist_queue.put_nowait(True)
        except asyncio.QueueFull:
            logger.warning("Persistence queue full, skipping")

    async def track_request_end(self, request_id: str, success: bool, error: str = None,
                               pool_hit: bool = True, status_code: int = 200):
        """Track request completion."""
        if request_id not in self.active_requests:
            return

        req_info = self.active_requests.pop(request_id)
        end_time = time.time()
        elapsed = end_time - req_info["start_time"]
        mem_end = psutil.Process().memory_info().rss / (1024 * 1024)
        mem_delta = mem_end - req_info["mem_start"]

        # Update stats
        endpoint = req_info["endpoint"]
        if endpoint in self.endpoint_stats:
            self.endpoint_stats[endpoint]["total_time"] += elapsed
            if success:
                self.endpoint_stats[endpoint]["success"] += 1
            else:
                self.endpoint_stats[endpoint]["errors"] += 1
            if pool_hit:
                self.endpoint_stats[endpoint]["pool_hits"] += 1

        # Add to completed queue
        completed = {
            **req_info,
            "end_time": end_time,
            "elapsed": round(elapsed, 2),
            "mem_delta": round(mem_delta, 1),
            "success": success,
            "error": error,
            "status_code": status_code,
            "pool_hit": pool_hit,
            "container_id": self.container_id
        }
        self.completed_requests.append(completed)

        # Persist to Redis
        await self._persist_completed_requests()
        await self._persist_active_requests()  # Update active (removed this request)

        # Track errors
        if not success and error:
            error_entry = {
                "timestamp": end_time,
                "endpoint": endpoint,
                "url": req_info["url"],
                "error": error,
                "request_id": request_id,
                "message": error,
                "level": "ERROR",
                "container_id": self.container_id
            }
            self.errors.append(error_entry)
            await self._persist_errors()

        await self._persist_endpoint_stats()

    async def track_janitor_event(self, event_type: str, sig: str, details: Dict):
        """Track janitor cleanup events."""
        self.janitor_events.append({
            "timestamp": time.time(),
            "type": event_type,  # "close_cold", "close_hot", "promote"
            "sig": sig[:8],
            "details": details,
            "container_id": self.container_id
        })
        await self._persist_janitor_events()

    def _cleanup_old_entries(self, max_age_seconds: int = 300):
        """Remove entries older than max_age_seconds (default 5min)."""
        now = time.time()
        cutoff = now - max_age_seconds

        # Clean completed requests
        while self.completed_requests and self.completed_requests[0].get("end_time", 0) < cutoff:
            self.completed_requests.popleft()

        # Clean janitor events
        while self.janitor_events and self.janitor_events[0].get("timestamp", 0) < cutoff:
            self.janitor_events.popleft()

        # Clean errors
        while self.errors and self.errors[0].get("timestamp", 0) < cutoff:
            self.errors.popleft()

    async def update_timeline(self):
        """Update timeline data points (called every 5s)."""
        now = time.time()
        mem_pct = get_container_memory_percent()

        # Clean old entries (keep last 5 minutes)
        self._cleanup_old_entries(max_age_seconds=300)

        # Count requests in last 5s
        recent_reqs = sum(1 for req in self.completed_requests
                         if now - req.get("end_time", 0) < 5)

        # Browser counts (acquire lock with timeout to prevent deadlock)
        from crawler_pool import PERMANENT, HOT_POOL, COLD_POOL, LOCK
        try:
            async with asyncio.timeout(2.0):
                async with LOCK:
                    browser_count = {
                        "permanent": 1 if PERMANENT else 0,
                        "hot": len(HOT_POOL),
                        "cold": len(COLD_POOL)
                    }
        except asyncio.TimeoutError:
            logger.warning("Lock acquisition timeout in update_timeline, using cached browser counts")
            # Use last known values or defaults
            browser_count = {
                "permanent": 1,
                "hot": 0,
                "cold": 0
            }

        self.memory_timeline.append({"time": now, "value": mem_pct})
        self.requests_timeline.append({"time": now, "value": recent_reqs})
        self.browser_timeline.append({"time": now, "browsers": browser_count})

    async def _persist_endpoint_stats(self):
        """Persist endpoint stats to Redis with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.redis.set(
                    "monitor:endpoint_stats",
                    json.dumps(self.endpoint_stats),
                    ex=self.ttl.endpoint_stats
                )
                return  # Success
            except aioredis.ConnectionError as e:
                if attempt < max_retries - 1:
                    backoff = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                    logger.warning(f"Redis connection error persisting endpoint stats (attempt {attempt + 1}/{max_retries}), retrying in {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Failed to persist endpoint stats after {max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"Non-retryable error persisting endpoint stats: {e}")
                break

    async def _persist_active_requests(self):
        """Persist active requests to Redis with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.active_requests:
                    await self.redis.set(
                        f"monitor:{self.container_id}:active_requests",
                        json.dumps(list(self.active_requests.values())),
                        ex=self.ttl.active_requests
                    )
                else:
                    await self.redis.delete(f"monitor:{self.container_id}:active_requests")
                return  # Success
            except aioredis.ConnectionError as e:
                if attempt < max_retries - 1:
                    backoff = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                    logger.warning(f"Redis connection error persisting active requests (attempt {attempt + 1}/{max_retries}), retrying in {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Failed to persist active requests after {max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"Non-retryable error persisting active requests: {e}")
                break

    async def _persist_completed_requests(self):
        """Persist completed requests to Redis with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.redis.set(
                    f"monitor:{self.container_id}:completed",
                    json.dumps(list(self.completed_requests)),
                    ex=self.ttl.completed_requests
                )
                return  # Success
            except aioredis.ConnectionError as e:
                if attempt < max_retries - 1:
                    backoff = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                    logger.warning(f"Redis connection error persisting completed requests (attempt {attempt + 1}/{max_retries}), retrying in {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Failed to persist completed requests after {max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"Non-retryable error persisting completed requests: {e}")
                break

    async def _persist_janitor_events(self):
        """Persist janitor events to Redis with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.redis.set(
                    f"monitor:{self.container_id}:janitor",
                    json.dumps(list(self.janitor_events)),
                    ex=self.ttl.janitor_events
                )
                return  # Success
            except aioredis.ConnectionError as e:
                if attempt < max_retries - 1:
                    backoff = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                    logger.warning(f"Redis connection error persisting janitor events (attempt {attempt + 1}/{max_retries}), retrying in {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Failed to persist janitor events after {max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"Non-retryable error persisting janitor events: {e}")
                break

    async def _persist_errors(self):
        """Persist errors to Redis with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.redis.set(
                    f"monitor:{self.container_id}:errors",
                    json.dumps(list(self.errors)),
                    ex=self.ttl.errors
                )
                return  # Success
            except aioredis.ConnectionError as e:
                if attempt < max_retries - 1:
                    backoff = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                    logger.warning(f"Redis connection error persisting errors (attempt {attempt + 1}/{max_retries}), retrying in {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Failed to persist errors after {max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"Non-retryable error persisting errors: {e}")
                break

    async def _persistence_worker(self):
        """Background worker to persist stats to Redis."""
        while True:
            try:
                await self._persist_queue.get()
                await self._persist_endpoint_stats()
                self._persist_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Persistence worker error: {e}")

    def start_persistence_worker(self):
        """Start the background persistence worker."""
        if not self._persist_worker_task:
            self._persist_worker_task = asyncio.create_task(self._persistence_worker())
            logger.info("Started persistence worker")

    async def stop_persistence_worker(self):
        """Stop the background persistence worker."""
        if self._persist_worker_task:
            self._persist_worker_task.cancel()
            try:
                await self._persist_worker_task
            except asyncio.CancelledError:
                pass
            self._persist_worker_task = None
            logger.info("Stopped persistence worker")

    async def _heartbeat_worker(self):
        """Send heartbeat to Redis every 30s with circuit breaker for failures."""
        from utils import detect_deployment_mode
        import os

        heartbeat_failures = 0
        max_failures = 5  # Circuit breaker threshold

        while True:
            try:
                # Get hostname/container name for friendly display
                # Try HOSTNAME env var first (set by Docker Compose), then socket.gethostname()
                import socket
                hostname = os.getenv("HOSTNAME", socket.gethostname())

                # Register this container
                mode, containers = detect_deployment_mode()
                container_info = {
                    "id": self.container_id,
                    "hostname": hostname,
                    "last_seen": time.time(),
                    "mode": mode,
                    "failure_count": heartbeat_failures
                }

                # Set heartbeat with configured TTL
                await self.redis.setex(
                    f"monitor:heartbeat:{self.container_id}",
                    self.ttl.heartbeat,
                    json.dumps(container_info)
                )

                # Add to active containers set
                await self.redis.sadd("monitor:active_containers", self.container_id)

                # Reset failure counter on success
                heartbeat_failures = 0

                # Wait 30s before next heartbeat
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except aioredis.ConnectionError as e:
                heartbeat_failures += 1
                logger.error(
                    f"Heartbeat Redis connection error (attempt {heartbeat_failures}/{max_failures}): {e}"
                )

                if heartbeat_failures >= max_failures:
                    # Circuit breaker - back off for longer
                    logger.critical(
                        f"Heartbeat circuit breaker triggered after {heartbeat_failures} failures. "
                        f"Container will appear offline for 5 minutes."
                    )
                    await asyncio.sleep(300)  # 5 min backoff
                    heartbeat_failures = 0
                else:
                    # Exponential backoff
                    backoff = min(30 * (2 ** heartbeat_failures), 300)
                    await asyncio.sleep(backoff)
            except Exception as e:
                logger.error(f"Unexpected heartbeat error: {e}", exc_info=True)
                await asyncio.sleep(30)

    def start_heartbeat(self):
        """Start the heartbeat worker."""
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_worker())
            logger.info("Started heartbeat worker")

    async def stop_heartbeat(self):
        """Stop the heartbeat worker and immediately deregister container."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

            # Immediate deregistration (no 60s wait)
            try:
                await self.redis.srem("monitor:active_containers", self.container_id)
                await self.redis.delete(f"monitor:heartbeat:{self.container_id}")
                logger.info(f"Container {self.container_id} immediately deregistered from monitoring")
            except Exception as e:
                logger.warning(f"Failed to deregister container on shutdown: {e}")

            self._heartbeat_task = None
            logger.info("Stopped heartbeat worker")

    async def cleanup(self):
        """Cleanup on shutdown - persist final stats and stop workers."""
        logger.info("Monitor cleanup starting...")
        try:
            # Persist final stats before shutdown
            await self._persist_endpoint_stats()
            # Stop background workers
            await self.stop_persistence_worker()
            await self.stop_heartbeat()
            logger.info("Monitor cleanup completed")
        except Exception as e:
            logger.error(f"Monitor cleanup error: {e}")

    async def load_from_redis(self):
        """Load persisted stats from Redis and start workers."""
        try:
            data = await self.redis.get("monitor:endpoint_stats")
            if data:
                self.endpoint_stats = json.loads(data)
                logger.info("Loaded endpoint stats from Redis")

            # Start background workers
            self.start_heartbeat()

        except Exception as e:
            logger.warning(f"Failed to load from Redis: {e}")

    async def get_health_summary(self) -> Dict:
        """Get current system health snapshot."""
        mem_pct = get_container_memory_percent()
        cpu_pct = psutil.cpu_percent(interval=0.1)

        # Network I/O (delta since last call)
        net = psutil.net_io_counters()

        # Pool status (acquire lock with timeout to prevent race conditions)
        from crawler_pool import PERMANENT, HOT_POOL, COLD_POOL, LOCK
        try:
            async with asyncio.timeout(2.0):
                async with LOCK:
                    # TODO: Track actual browser process memory instead of estimates
                    # These are conservative estimates based on typical Chromium usage
                    permanent_mem = 270 if PERMANENT else 0  # Estimate: ~270MB for permanent browser
                    hot_mem = len(HOT_POOL) * 180  # Estimate: ~180MB per hot pool browser
                    cold_mem = len(COLD_POOL) * 180  # Estimate: ~180MB per cold pool browser
                    permanent_active = PERMANENT is not None
                    hot_count = len(HOT_POOL)
                    cold_count = len(COLD_POOL)
        except asyncio.TimeoutError:
            logger.warning("Lock acquisition timeout in get_health_summary, using defaults")
            # Use safe defaults when lock times out
            permanent_mem = 0
            hot_mem = 0
            cold_mem = 0
            permanent_active = False
            hot_count = 0
            cold_count = 0

        return {
            "container": {
                "memory_percent": round(mem_pct, 1),
                "cpu_percent": round(cpu_pct, 1),
                "network_sent_mb": round(net.bytes_sent / (1024**2), 2),
                "network_recv_mb": round(net.bytes_recv / (1024**2), 2),
                "uptime_seconds": int(time.time() - self.start_time)
            },
            "pool": {
                "permanent": {"active": permanent_active, "memory_mb": permanent_mem},
                "hot": {"count": hot_count, "memory_mb": hot_mem},
                "cold": {"count": cold_count, "memory_mb": cold_mem},
                "total_memory_mb": permanent_mem + hot_mem + cold_mem
            },
            "janitor": {
                "next_cleanup_estimate": "adaptive",  # Would need janitor state
                "memory_pressure": "LOW" if mem_pct < 60 else "MEDIUM" if mem_pct < 80 else "HIGH"
            }
        }

    def get_active_requests(self) -> List[Dict]:
        """Get list of currently active requests."""
        now = time.time()
        return [
            {
                **req,
                "elapsed": round(now - req["start_time"], 1),
                "status": "running"
            }
            for req in self.active_requests.values()
        ]

    def get_completed_requests(self, limit: int = 50, filter_status: str = "all") -> List[Dict]:
        """Get recent completed requests."""
        requests = list(self.completed_requests)[-limit:]
        if filter_status == "success":
            requests = [r for r in requests if r.get("success")]
        elif filter_status == "error":
            requests = [r for r in requests if not r.get("success")]
        return requests

    async def get_browser_list(self) -> List[Dict]:
        """Get detailed browser pool information with timeout protection."""
        from crawler_pool import PERMANENT, HOT_POOL, COLD_POOL, LAST_USED, USAGE_COUNT, DEFAULT_CONFIG_SIG, LOCK

        browsers = []
        now = time.time()

        # Acquire lock with timeout to prevent deadlock
        try:
            async with asyncio.timeout(2.0):
                async with LOCK:
                    if PERMANENT:
                        browsers.append({
                            "type": "permanent",
                            "sig": DEFAULT_CONFIG_SIG[:8] if DEFAULT_CONFIG_SIG else "unknown",
                            "age_seconds": int(now - self.start_time),
                            "last_used_seconds": int(now - LAST_USED.get(DEFAULT_CONFIG_SIG, now)),
                            "memory_mb": 270,
                            "hits": USAGE_COUNT.get(DEFAULT_CONFIG_SIG, 0),
                            "killable": False
                        })

                    for sig, crawler in HOT_POOL.items():
                        browsers.append({
                            "type": "hot",
                            "sig": sig[:8],
                            "age_seconds": int(now - self.start_time),  # Approximation
                            "last_used_seconds": int(now - LAST_USED.get(sig, now)),
                            "memory_mb": 180,  # Estimate
                            "hits": USAGE_COUNT.get(sig, 0),
                            "killable": True
                        })

                    for sig, crawler in COLD_POOL.items():
                        browsers.append({
                            "type": "cold",
                            "sig": sig[:8],
                            "age_seconds": int(now - self.start_time),
                            "last_used_seconds": int(now - LAST_USED.get(sig, now)),
                            "memory_mb": 180,
                            "hits": USAGE_COUNT.get(sig, 0),
                            "killable": True
                        })
        except asyncio.TimeoutError:
            logger.error("Browser list lock timeout - pool may be locked by janitor")
            # Return empty list when lock times out to prevent blocking
            return []

        return browsers

    def get_endpoint_stats_summary(self) -> Dict[str, Dict]:
        """Get aggregated endpoint statistics."""
        summary = {}
        for endpoint, stats in self.endpoint_stats.items():
            count = stats["count"]
            avg_time = (stats["total_time"] / count) if count > 0 else 0
            success_rate = (stats["success"] / count * 100) if count > 0 else 0
            pool_hit_rate = (stats["pool_hits"] / count * 100) if count > 0 else 0

            summary[endpoint] = {
                "count": count,
                "avg_latency_ms": round(avg_time * 1000, 1),
                "success_rate_percent": round(success_rate, 1),
                "pool_hit_rate_percent": round(pool_hit_rate, 1),
                "errors": stats["errors"]
            }
        return summary

    def get_timeline_data(self, metric: str, window: str = "5m") -> Dict:
        """Get timeline data for charts."""
        # For now, only 5m window supported
        if metric == "memory":
            data = list(self.memory_timeline)
        elif metric == "requests":
            data = list(self.requests_timeline)
        elif metric == "browsers":
            data = list(self.browser_timeline)
        else:
            return {"timestamps": [], "values": []}

        return {
            "timestamps": [int(d["time"]) for d in data],
            "values": [d.get("value", d.get("browsers")) for d in data]
        }

    def get_janitor_log(self, limit: int = 100) -> List[Dict]:
        """Get recent janitor events."""
        return list(self.janitor_events)[-limit:]

    def get_errors_log(self, limit: int = 100) -> List[Dict]:
        """Get recent errors."""
        return list(self.errors)[-limit:]

# Global instance (initialized in server.py)
monitor_stats: Optional[MonitorStats] = None

def get_monitor() -> MonitorStats:
    """Get global monitor instance."""
    if monitor_stats is None:
        raise RuntimeError("Monitor not initialized")
    return monitor_stats
