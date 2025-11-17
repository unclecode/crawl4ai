# Crawl4AI Docker Server - Technical Architecture

**Version**: 0.7.4
**Last Updated**: October 2025
**Status**: Production-ready with real-time monitoring

This document provides a comprehensive technical overview of the Crawl4AI Docker server architecture, including the smart browser pool, real-time monitoring system, and all production optimizations.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Smart Browser Pool](#smart-browser-pool)
4. [Real-time Monitoring System](#real-time-monitoring-system)
5. [API Layer](#api-layer)
6. [Memory Management](#memory-management)
7. [Production Optimizations](#production-optimizations)
8. [Deployment & Operations](#deployment--operations)
9. [Troubleshooting & Debugging](#troubleshooting--debugging)

---

## System Overview

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Requests                          │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Server (server.py)                                  │
│  ├─ REST API Endpoints (/crawl, /html, /md, /llm, etc.)    │
│  ├─ WebSocket Endpoint (/monitor/ws)                        │
│  └─ Background Tasks (janitor, timeline_updater)            │
└────┬────────────────────┬────────────────────┬──────────────┘
     │                    │                    │
     ▼                    ▼                    ▼
┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ Browser     │  │ Monitor System   │  │ Redis           │
│ Pool        │  │ (monitor.py)     │  │ (Persistence)   │
│             │  │                  │  │                 │
│ PERMANENT ●─┤  │ ├─ Stats         │  │ ├─ Endpoint     │
│ HOT_POOL  ♨─┤  │ ├─ Requests      │  │ │   Stats       │
│ COLD_POOL ❄─┤  │ ├─ Browsers      │  │ ├─ Task         │
│             │  │ ├─ Timeline      │  │ │   Results     │
│ Janitor  🧹─┤  │ └─ Events/Errors │  │ └─ Cache        │
└─────────────┘  └──────────────────┘  └─────────────────┘
```

### Key Features

- **10x Memory Efficiency**: Smart 3-tier browser pooling reduces memory from 500-700MB to 50-70MB per concurrent user
- **Real-time Monitoring**: WebSocket-based live dashboard with 2-second update intervals
- **Production-Ready**: Comprehensive error handling, timeouts, cleanup, and graceful shutdown
- **Container-Aware**: Accurate memory detection using cgroup v2/v1
- **Auto-Recovery**: Graceful WebSocket fallback, lock protection, background workers

---

## Core Components

### 1. Server Core (`server.py`)

**Responsibilities:**
- FastAPI application lifecycle management
- Route registration and middleware
- Background task orchestration
- Graceful shutdown handling

**Key Functions:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    - Initialize Redis connection
    - Create monitor stats instance
    - Start persistence worker
    - Initialize permanent browser
    - Start janitor (browser cleanup)
    - Start timeline updater (5s interval)

    yield

    # Shutdown
    - Cancel background tasks
    - Persist final monitor stats
    - Stop persistence worker
    - Close all browsers
```

**Configuration:**
- Loaded from `config.yml`
- Browser settings, memory thresholds, rate limiting
- LLM provider credentials
- Server host/port

### 2. API Layer (`api.py`)

**Endpoints:**

| Endpoint | Method | Purpose | Pool Usage |
|----------|--------|---------|------------|
| `/health` | GET | Health check | None |
| `/crawl` | POST | Full crawl with all features | ✓ Pool |
| `/crawl_stream` | POST | Streaming crawl results | ✓ Pool |
| `/html` | POST | HTML extraction | ✓ Pool |
| `/md` | POST | Markdown generation | ✓ Pool |
| `/screenshot` | POST | Page screenshots | ✓ Pool |
| `/pdf` | POST | PDF generation | ✓ Pool |
| `/llm/{path}` | GET/POST | LLM extraction | ✓ Pool |
| `/crawl/job` | POST | Background job creation | ✓ Pool |

**Request Flow:**

```python
@app.post("/crawl")
async def crawl(body: CrawlRequest):
    # 1. Track request start
    request_id = f"req_{uuid4().hex[:8]}"
    await get_monitor().track_request_start(request_id, "/crawl", url, config)

    # 2. Get browser from pool
    from crawler_pool import get_crawler
    crawler = await get_crawler(browser_config)

    # 3. Execute crawl
    result = await crawler.arun(url, config=crawler_config)

    # 4. Track request completion
    await get_monitor().track_request_end(request_id, success=True)

    # 5. Return result (browser stays in pool)
    return result
```

### 3. Utility Layer (`utils.py`)

**Container Memory Detection:**

```python
def get_container_memory_percent() -> float:
    """Accurate container memory detection"""
    try:
        # Try cgroup v2 first
        current = int(Path("/sys/fs/cgroup/memory.current").read_text().strip())
        max_mem = int(Path("/sys/fs/cgroup/memory.max").read_text().strip())
        return (current / max_mem) * 100
    except:
        # Fallback to cgroup v1
        usage = int(Path("/sys/fs/cgroup/memory/memory.usage_in_bytes").read_text())
        limit = int(Path("/sys/fs/cgroup/memory/memory.limit_in_bytes").read_text())
        return (usage / limit) * 100
    except:
        # Final fallback to psutil (may be inaccurate in containers)
        return psutil.virtual_memory().percent
```

**Helper Functions:**
- `get_base_url()`: Request base URL extraction
- `is_task_id()`: Task ID validation
- `should_cleanup_task()`: TTL-based cleanup logic
- `validate_llm_provider()`: LLM configuration validation

---

## Smart Browser Pool

### Architecture

The browser pool implements a 3-tier strategy optimized for real-world usage patterns:

```
┌──────────────────────────────────────────────────────────┐
│  PERMANENT Browser (Default Config)                      │
│  ● Always alive, never cleaned                           │
│  ● Serves 90% of requests                                │
│  ● ~270MB memory                                         │
└──────────────────────────────────────────────────────────┘
                        ▲
                        │ 90% of requests
                        │
┌──────────────────────────────────────────────────────────┐
│  HOT_POOL (Frequently Used Configs)                      │
│  ♨ Configs used 3+ times                                 │
│  ♨ Longer TTL (2-5 min depending on memory)             │
│  ♨ ~180MB per browser                                   │
└──────────────────────────────────────────────────────────┘
                        ▲
                        │ Promotion at 3 uses
                        │
┌──────────────────────────────────────────────────────────┐
│  COLD_POOL (Rarely Used Configs)                         │
│  ❄ New/rare browser configs                             │
│  ❄ Short TTL (30s-5min depending on memory)             │
│  ❄ ~180MB per browser                                   │
└──────────────────────────────────────────────────────────┘
```

### Implementation (`crawler_pool.py`)

**Core Data Structures:**

```python
PERMANENT: Optional[AsyncWebCrawler] = None  # Default browser
HOT_POOL: Dict[str, AsyncWebCrawler] = {}    # Frequent configs
COLD_POOL: Dict[str, AsyncWebCrawler] = {}   # Rare configs
LAST_USED: Dict[str, float] = {}             # Timestamp tracking
USAGE_COUNT: Dict[str, int] = {}             # Usage counter
LOCK = asyncio.Lock()                        # Thread-safe access
```

**Browser Acquisition Flow:**

```python
async def get_crawler(cfg: BrowserConfig) -> AsyncWebCrawler:
    sig = _sig(cfg)  # SHA1 hash of config

    async with LOCK:  # Prevent race conditions
        # 1. Check permanent browser
        if _is_default_config(sig):
            return PERMANENT

        # 2. Check hot pool
        if sig in HOT_POOL:
            USAGE_COUNT[sig] += 1
            return HOT_POOL[sig]

        # 3. Check cold pool (with promotion logic)
        if sig in COLD_POOL:
            USAGE_COUNT[sig] += 1
            if USAGE_COUNT[sig] >= 3:
                # Promote to hot pool
                HOT_POOL[sig] = COLD_POOL.pop(sig)
                await get_monitor().track_janitor_event("promote", sig, {...})
                return HOT_POOL[sig]
            return COLD_POOL[sig]

        # 4. Memory check before creating new
        if get_container_memory_percent() >= MEM_LIMIT:
            raise MemoryError(f"Memory at {mem}%, refusing new browser")

        # 5. Create new browser in cold pool
        crawler = AsyncWebCrawler(config=cfg)
        await crawler.start()
        COLD_POOL[sig] = crawler
        return crawler
```

**Janitor (Adaptive Cleanup):**

```python
async def janitor():
    """Memory-adaptive browser cleanup"""
    while True:
        mem_pct = get_container_memory_percent()

        # Adaptive intervals based on memory pressure
        if mem_pct > 80:
            interval, cold_ttl, hot_ttl = 10, 30, 120      # Aggressive
        elif mem_pct > 60:
            interval, cold_ttl, hot_ttl = 30, 60, 300      # Moderate
        else:
            interval, cold_ttl, hot_ttl = 60, 300, 600     # Relaxed

        await asyncio.sleep(interval)

        async with LOCK:
            # Clean cold pool first (less valuable)
            for sig in list(COLD_POOL.keys()):
                if now - LAST_USED[sig] > cold_ttl:
                    await COLD_POOL[sig].close()
                    del COLD_POOL[sig], LAST_USED[sig], USAGE_COUNT[sig]
                    await track_janitor_event("close_cold", sig, {...})

            # Clean hot pool (more conservative)
            for sig in list(HOT_POOL.keys()):
                if now - LAST_USED[sig] > hot_ttl:
                    await HOT_POOL[sig].close()
                    del HOT_POOL[sig], LAST_USED[sig], USAGE_COUNT[sig]
                    await track_janitor_event("close_hot", sig, {...})
```

**Config Signature Generation:**

```python
def _sig(cfg: BrowserConfig) -> str:
    """Generate unique signature for browser config"""
    payload = json.dumps(cfg.to_dict(), sort_keys=True, separators=(",",":"))
    return hashlib.sha1(payload.encode()).hexdigest()
```

---

## Real-time Monitoring System

### Architecture

The monitoring system provides real-time insights via WebSocket with automatic fallback to HTTP polling.

**Components:**

```
┌─────────────────────────────────────────────────────────┐
│  MonitorStats Class (monitor.py)                        │
│  ├─ In-memory queues (deques with maxlen)              │
│  ├─ Background persistence worker                       │
│  ├─ Timeline tracking (5-min window, 5s resolution)    │
│  └─ Time-based expiry (5min for old entries)           │
└───────────┬─────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│  WebSocket Endpoint (/monitor/ws)                       │
│  ├─ 2-second update intervals                          │
│  ├─ Auto-reconnect with exponential backoff            │
│  ├─ Comprehensive data payload                         │
│  └─ Graceful fallback to polling                       │
└───────────┬─────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│  Dashboard UI (static/monitor/index.html)               │
│  ├─ Connection status indicator                        │
│  ├─ Live updates (health, requests, browsers)          │
│  ├─ Timeline charts (memory, requests, browsers)       │
│  └─ Janitor events & error logs                        │
└─────────────────────────────────────────────────────────┘
```

### Monitor Stats (`monitor.py`)

**Data Structures:**

```python
class MonitorStats:
    # In-memory queues
    active_requests: Dict[str, Dict]           # Currently processing
    completed_requests: deque(maxlen=100)      # Last 100 completed
    janitor_events: deque(maxlen=100)          # Cleanup events
    errors: deque(maxlen=100)                  # Error log

    # Endpoint stats (persisted to Redis)
    endpoint_stats: Dict[str, Dict]            # Aggregated stats

    # Timeline data (5min window, 5s resolution = 60 points)
    memory_timeline: deque(maxlen=60)
    requests_timeline: deque(maxlen=60)
    browser_timeline: deque(maxlen=60)

    # Background persistence
    _persist_queue: asyncio.Queue(maxsize=10)
    _persist_worker_task: Optional[asyncio.Task]
```

**Request Tracking:**

```python
async def track_request_start(request_id, endpoint, url, config):
    """Track new request"""
    self.active_requests[request_id] = {
        "id": request_id,
        "endpoint": endpoint,
        "url": url,
        "start_time": time.time(),
        "mem_start": psutil.Process().memory_info().rss / (1024 * 1024)
    }

    # Update endpoint stats
    if endpoint not in self.endpoint_stats:
        self.endpoint_stats[endpoint] = {
            "count": 0, "total_time": 0, "errors": 0,
            "pool_hits": 0, "success": 0
        }
    self.endpoint_stats[endpoint]["count"] += 1

    # Queue background persistence
    self._persist_queue.put_nowait(True)

async def track_request_end(request_id, success, error=None, ...):
    """Track request completion"""
    req_info = self.active_requests.pop(request_id)
    elapsed = time.time() - req_info["start_time"]
    mem_delta = current_mem - req_info["mem_start"]

    # Add to completed queue
    self.completed_requests.append({
        "id": request_id,
        "endpoint": req_info["endpoint"],
        "url": req_info["url"],
        "success": success,
        "elapsed": elapsed,
        "mem_delta": mem_delta,
        "end_time": time.time()
    })

    # Update stats
    self.endpoint_stats[endpoint]["success" if success else "errors"] += 1
    await self._persist_endpoint_stats()
```

**Background Persistence Worker:**

```python
async def _persistence_worker(self):
    """Background worker for Redis persistence"""
    while True:
        try:
            await self._persist_queue.get()
            await self._persist_endpoint_stats()
            self._persist_queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Persistence worker error: {e}")

async def _persist_endpoint_stats(self):
    """Persist stats to Redis with error handling"""
    try:
        await self.redis.set(
            "monitor:endpoint_stats",
            json.dumps(self.endpoint_stats),
            ex=86400  # 24h TTL
        )
    except Exception as e:
        logger.warning(f"Failed to persist endpoint stats: {e}")
```

**Time-based Cleanup:**

```python
def _cleanup_old_entries(self, max_age_seconds=300):
    """Remove entries older than 5 minutes"""
    now = time.time()
    cutoff = now - max_age_seconds

    # Clean completed requests
    while self.completed_requests and \
          self.completed_requests[0].get("end_time", 0) < cutoff:
        self.completed_requests.popleft()

    # Clean janitor events
    while self.janitor_events and \
          self.janitor_events[0].get("timestamp", 0) < cutoff:
        self.janitor_events.popleft()

    # Clean errors
    while self.errors and \
          self.errors[0].get("timestamp", 0) < cutoff:
        self.errors.popleft()
```

### WebSocket Implementation (`monitor_routes.py`)

**Endpoint:**

```python
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time monitoring updates"""
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        while True:
            try:
                monitor = get_monitor()

                # Gather comprehensive monitoring data
                data = {
                    "timestamp": time.time(),
                    "health": await monitor.get_health_summary(),
                    "requests": {
                        "active": monitor.get_active_requests(),
                        "completed": monitor.get_completed_requests(limit=10)
                    },
                    "browsers": await monitor.get_browser_list(),
                    "timeline": {
                        "memory": monitor.get_timeline_data("memory", "5m"),
                        "requests": monitor.get_timeline_data("requests", "5m"),
                        "browsers": monitor.get_timeline_data("browsers", "5m")
                    },
                    "janitor": monitor.get_janitor_log(limit=10),
                    "errors": monitor.get_errors_log(limit=10)
                }

                await websocket.send_json(data)
                await asyncio.sleep(2)  # 2-second update interval

            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}", exc_info=True)
                await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
    finally:
        logger.info("WebSocket connection closed")
```

**Input Validation:**

```python
@router.get("/requests")
async def get_requests(status: str = "all", limit: int = 50):
    # Input validation
    if status not in ["all", "active", "completed", "success", "error"]:
        raise HTTPException(400, f"Invalid status: {status}")
    if limit < 1 or limit > 1000:
        raise HTTPException(400, f"Invalid limit: {limit}")

    monitor = get_monitor()
    # ... return data
```

### Frontend Dashboard

**Connection Management:**

```javascript
// WebSocket with auto-reconnect
function connectWebSocket() {
    if (wsReconnectAttempts >= MAX_WS_RECONNECT) {
        // Fallback to polling after 5 failed attempts
        useWebSocket = false;
        updateConnectionStatus('polling');
        startAutoRefresh();
        return;
    }

    updateConnectionStatus('connecting');
    const wsUrl = `${protocol}//${window.location.host}/monitor/ws`;
    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        wsReconnectAttempts = 0;
        updateConnectionStatus('connected');
        stopAutoRefresh();  // Stop polling
    };

    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateDashboard(data);  // Update all sections
    };

    websocket.onclose = () => {
        updateConnectionStatus('disconnected', 'Reconnecting...');
        if (useWebSocket) {
            setTimeout(connectWebSocket, 2000 * wsReconnectAttempts);
        } else {
            startAutoRefresh();  // Fallback to polling
        }
    };
}
```

**Connection Status Indicator:**

| Status | Color | Animation | Meaning |
|--------|-------|-----------|---------|
| Live | Green | Pulsing fast | WebSocket connected |
| Connecting... | Yellow | Pulsing slow | Attempting connection |
| Polling | Blue | Pulsing slow | HTTP polling fallback |
| Disconnected | Red | None | Connection failed |

---

## API Layer

### Request/Response Flow

```
Client Request
    │
    ▼
FastAPI Route Handler
    │
    ├─→ Monitor: track_request_start()
    │
    ├─→ Browser Pool: get_crawler(config)
    │       │
    │       ├─→ Check PERMANENT
    │       ├─→ Check HOT_POOL
    │       ├─→ Check COLD_POOL
    │       └─→ Create New (if needed)
    │
    ├─→ Execute Crawl
    │       │
    │       ├─→ Fetch page
    │       ├─→ Extract content
    │       ├─→ Apply filters/strategies
    │       └─→ Return result
    │
    ├─→ Monitor: track_request_end()
    │
    └─→ Return Response (browser stays in pool)
```

### Error Handling Strategy

**Levels:**

1. **Route Level**: HTTP exceptions with proper status codes
2. **Monitor Level**: Try-except with logging, non-critical failures
3. **Pool Level**: Memory checks, lock protection, graceful degradation
4. **WebSocket Level**: Auto-reconnect, fallback to polling

**Example:**

```python
@app.post("/crawl")
async def crawl(body: CrawlRequest):
    request_id = f"req_{uuid4().hex[:8]}"

    try:
        # Monitor tracking (non-blocking on failure)
        try:
            await get_monitor().track_request_start(...)
        except:
            pass  # Monitor not critical

        # Browser acquisition (with memory protection)
        crawler = await get_crawler(browser_config)

        # Crawl execution
        result = await crawler.arun(url, config=cfg)

        # Success tracking
        try:
            await get_monitor().track_request_end(request_id, success=True)
        except:
            pass

        return result

    except MemoryError as e:
        # Memory pressure - return 503
        await get_monitor().track_request_end(request_id, success=False, error=str(e))
        raise HTTPException(503, "Server at capacity")
    except Exception as e:
        # General errors - return 500
        await get_monitor().track_request_end(request_id, success=False, error=str(e))
        raise HTTPException(500, str(e))
```

---

## Memory Management

### Container Memory Detection

**Priority Order:**
1. cgroup v2 (`/sys/fs/cgroup/memory.{current,max}`)
2. cgroup v1 (`/sys/fs/cgroup/memory/memory.{usage,limit}_in_bytes`)
3. psutil fallback (may be inaccurate in containers)

**Usage:**

```python
mem_pct = get_container_memory_percent()

if mem_pct >= 95:  # Critical
    raise MemoryError("Refusing new browser")
elif mem_pct > 80:  # High pressure
    # Janitor: aggressive cleanup (10s interval, 30s TTL)
elif mem_pct > 60:  # Moderate pressure
    # Janitor: moderate cleanup (30s interval, 60s TTL)
else:  # Normal
    # Janitor: relaxed cleanup (60s interval, 300s TTL)
```

### Memory Budgets

| Component | Memory | Notes |
|-----------|--------|-------|
| Base Container | 270 MB | Python + FastAPI + libraries |
| Permanent Browser | 270 MB | Always-on default browser |
| Hot Pool Browser | 180 MB | Per frequently-used config |
| Cold Pool Browser | 180 MB | Per rarely-used config |
| Active Crawl Overhead | 50-200 MB | Temporary, released after request |

**Example Calculation:**

```
Container: 270 MB
Permanent: 270 MB
2x Hot:    360 MB
1x Cold:   180 MB
Total:     1080 MB baseline

Under load (10 concurrent):
+ Active crawls: ~500-1000 MB
= Peak: 1.5-2 GB
```

---

## Production Optimizations

### Code Review Fixes Applied

**Critical (3):**
1. ✅ Lock protection for browser pool access
2. ✅ Async track_janitor_event implementation
3. ✅ Error handling in request tracking

**Important (8):**
4. ✅ Background persistence worker (replaces fire-and-forget)
5. ✅ Time-based expiry (5min cleanup for old entries)
6. ✅ Input validation (status, limit, metric, window)
7. ✅ Timeline updater timeout (4s max)
8. ✅ Warn when killing browsers with active requests
9. ✅ Monitor cleanup on shutdown
10. ✅ Document memory estimates
11. ✅ Structured error responses (HTTPException)

### Performance Characteristics

**Latency:**

| Scenario | Time | Notes |
|----------|------|-------|
| Pool Hit (Permanent) | <100ms | Browser ready |
| Pool Hit (Hot/Cold) | <100ms | Browser ready |
| New Browser Creation | 3-5s | Chromium startup |
| Simple Page Fetch | 1-3s | Network + render |
| Complex Extraction | 5-10s | LLM processing |

**Throughput:**

| Load | Concurrent | Response Time | Success Rate |
|------|-----------|---------------|--------------|
| Light | 1-10 | <3s | 100% |
| Medium | 10-50 | 3-8s | 100% |
| Heavy | 50-100 | 8-15s | 95-100% |
| Extreme | 100+ | 15-30s | 80-95% |

### Reliability Features

**Race Condition Protection:**
- `asyncio.Lock` on all pool operations
- Lock on browser pool stats access
- Async janitor event tracking

**Graceful Degradation:**
- WebSocket → HTTP polling fallback
- Redis persistence failures (logged, non-blocking)
- Monitor tracking failures (logged, non-blocking)

**Resource Cleanup:**
- Janitor cleanup (adaptive intervals)
- Time-based expiry (5min for old data)
- Shutdown cleanup (persist final stats, close browsers)
- Background worker cancellation

---

## Deployment & Operations

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp .llm.env.example .llm.env
# Edit .llm.env with your API keys

# Run server
python -m uvicorn server:app --host 0.0.0.0 --port 11235 --reload
```

### Docker Deployment

```bash
# Build image
docker build -t crawl4ai:latest -f Dockerfile .

# Run container
docker run -d \
  --name crawl4ai \
  -p 11235:11235 \
  --shm-size=1g \
  --env-file .llm.env \
  crawl4ai:latest
```

### Production Configuration

**`config.yml` Key Settings:**

```yaml
crawler:
  browser:
    extra_args:
      - "--disable-gpu"
      - "--disable-dev-shm-usage"
      - "--no-sandbox"
    kwargs:
      headless: true
      text_mode: true  # Reduces memory by 30-40%

  memory_threshold_percent: 95  # Refuse new browsers above this

  pool:
    idle_ttl_sec: 300  # Base TTL for cold pool (5 min)

  rate_limiter:
    enabled: true
    base_delay: [1.0, 3.0]  # Random delay between requests
```

### Monitoring

**Access Dashboard:**
```
http://localhost:11235/static/monitor/
```

**Check Logs:**
```bash
# All activity
docker logs crawl4ai -f

# Pool activity only
docker logs crawl4ai | grep -E "(🔥|♨️|❄️|🆕|⬆️)"

# Errors only
docker logs crawl4ai | grep ERROR
```

**Metrics:**
```bash
# Container stats
docker stats crawl4ai

# Memory percentage
curl http://localhost:11235/monitor/health | jq '.container.memory_percent'

# Pool status
curl http://localhost:11235/monitor/browsers | jq '.summary'
```

---

## Troubleshooting & Debugging

### Common Issues

**1. WebSocket Not Connecting**

Symptoms: Yellow "Connecting..." indicator, falls back to blue "Polling"

Debug:
```bash
# Check server logs
docker logs crawl4ai | grep WebSocket

# Test WebSocket manually
python test-websocket.py
```

Fix: Check firewall/proxy settings, ensure port 11235 accessible

**2. High Memory Usage**

Symptoms: Container OOM kills, 503 errors, slow responses

Debug:
```bash
# Check current memory
curl http://localhost:11235/monitor/health | jq '.container.memory_percent'

# Check browser pool
curl http://localhost:11235/monitor/browsers

# Check janitor activity
docker logs crawl4ai | grep "🧹"
```

Fix:
- Lower `memory_threshold_percent` in config.yml
- Increase container memory limit
- Enable `text_mode: true` in browser config
- Reduce idle_ttl_sec for more aggressive cleanup

**3. Browser Pool Not Reusing**

Symptoms: High "New Created" count, poor reuse rate

Debug:
```python
# Check config signature matching
from crawl4ai import BrowserConfig
import json, hashlib

cfg = BrowserConfig(...)  # Your config
sig = hashlib.sha1(json.dumps(cfg.to_dict(), sort_keys=True).encode()).hexdigest()
print(f"Config signature: {sig[:8]}")
```

Check logs for permanent browser signature:
```bash
docker logs crawl4ai | grep "permanent"
```

Fix: Ensure endpoint configs match permanent browser config exactly

**4. Janitor Not Cleaning Up**

Symptoms: Memory stays high after idle period

Debug:
```bash
# Check janitor events
curl http://localhost:11235/monitor/logs/janitor

# Check pool stats over time
watch -n 5 'curl -s http://localhost:11235/monitor/browsers | jq ".summary"'
```

Fix:
- Janitor runs every 10-60s depending on memory
- Hot pool browsers have longer TTL (by design)
- Permanent browser never cleaned (by design)

### Debug Tools

**Config Signature Checker:**

```python
from crawl4ai import BrowserConfig
import json, hashlib

def check_sig(cfg: BrowserConfig) -> str:
    payload = json.dumps(cfg.to_dict(), sort_keys=True, separators=(",",":"))
    sig = hashlib.sha1(payload.encode()).hexdigest()
    return sig[:8]

# Example
cfg1 = BrowserConfig()
cfg2 = BrowserConfig(headless=True)
print(f"Default: {check_sig(cfg1)}")
print(f"Custom:  {check_sig(cfg2)}")
```

**Monitor Stats Dumper:**

```bash
#!/bin/bash
# Dump all monitor stats to JSON

curl -s http://localhost:11235/monitor/health > health.json
curl -s http://localhost:11235/monitor/requests?limit=100 > requests.json
curl -s http://localhost:11235/monitor/browsers > browsers.json
curl -s http://localhost:11235/monitor/logs/janitor > janitor.json
curl -s http://localhost:11235/monitor/logs/errors > errors.json

echo "Monitor stats dumped to *.json files"
```

**WebSocket Test Script:**

```python
# test-websocket.py (included in repo)
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:11235/monitor/ws"
    async with websockets.connect(uri) as websocket:
        for i in range(5):
            message = await websocket.recv()
            data = json.loads(message)
            print(f"\nUpdate #{i+1}:")
            print(f"  Health: CPU {data['health']['container']['cpu_percent']}%")
            print(f"  Active Requests: {len(data['requests']['active'])}")
            print(f"  Browsers: {len(data['browsers'])}")

asyncio.run(test_websocket())
```

### Performance Tuning

**For High Throughput:**

```yaml
# config.yml
crawler:
  memory_threshold_percent: 90  # Allow more browsers
  pool:
    idle_ttl_sec: 600  # Keep browsers longer
  rate_limiter:
    enabled: false  # Disable for max speed
```

**For Low Memory:**

```yaml
# config.yml
crawler:
  browser:
    kwargs:
      text_mode: true  # 30-40% memory reduction
  memory_threshold_percent: 80  # More conservative
  pool:
    idle_ttl_sec: 60  # Aggressive cleanup
```

**For Stability:**

```yaml
# config.yml
crawler:
  memory_threshold_percent: 85  # Balanced
  pool:
    idle_ttl_sec: 300  # Moderate cleanup
  rate_limiter:
    enabled: true
    base_delay: [2.0, 5.0]  # Prevent rate limiting
```

---

## Test Suite

**Location:** `deploy/docker/tests/`

**Tests:**

1. `test_1_basic.py` - Health check, container lifecycle
2. `test_2_memory.py` - Memory tracking, leak detection
3. `test_3_pool.py` - Pool reuse validation
4. `test_4_concurrent.py` - Concurrent load testing
5. `test_5_pool_stress.py` - Multi-config pool behavior
6. `test_6_multi_endpoint.py` - All endpoint validation
7. `test_7_cleanup.py` - Janitor cleanup verification

**Run All Tests:**

```bash
cd deploy/docker/tests
pip install -r requirements.txt

# Build image first
cd /path/to/repo
docker build -t crawl4ai-local:latest .

# Run tests
cd deploy/docker/tests
for test in test_*.py; do
    echo "Running $test..."
    python $test || break
done
```

---

## Architecture Decision Log

### Why 3-Tier Pool?

**Decision:** PERMANENT + HOT_POOL + COLD_POOL

**Rationale:**
- 90% of requests use default config → permanent browser serves most traffic
- Frequent variants (hot) deserve longer TTL for better reuse
- Rare configs (cold) should be cleaned aggressively to save memory

**Alternatives Considered:**
- Single pool: Too simple, no optimization for common case
- LRU cache: Doesn't capture "hot" vs "rare" distinction
- Per-endpoint pools: Too complex, over-engineering

### Why WebSocket + Polling Fallback?

**Decision:** WebSocket primary, HTTP polling backup

**Rationale:**
- WebSocket provides real-time updates (2s interval)
- Polling fallback ensures reliability in restricted networks
- Auto-reconnect handles temporary disconnections

**Alternatives Considered:**
- Polling only: Works but higher latency, more server load
- WebSocket only: Fails in restricted networks
- Server-Sent Events: One-way, no client messages

### Why Background Persistence Worker?

**Decision:** Queue-based worker for Redis operations

**Rationale:**
- Fire-and-forget loses data on failures
- Queue provides buffering and retry capability
- Non-blocking keeps request path fast

**Alternatives Considered:**
- Synchronous writes: Blocks request handling
- Fire-and-forget: Silent failures
- Batch writes: Complex state management

---

## Contributing

When modifying the architecture:

1. **Maintain backward compatibility** in API contracts
2. **Add tests** for new functionality
3. **Update this document** with architectural changes
4. **Profile memory impact** before production
5. **Test under load** using the test suite

**Code Review Checklist:**
- [ ] Race conditions protected with locks
- [ ] Error handling with proper logging
- [ ] Graceful degradation on failures
- [ ] Memory impact measured
- [ ] Tests added/updated
- [ ] Documentation updated

---

## License & Credits

**Crawl4AI** - Created by Unclecode
**GitHub**: https://github.com/unclecode/crawl4ai
**License**: See LICENSE file in repository

**Architecture & Optimizations**: October 2025
**WebSocket Monitoring**: October 2025
**Production Hardening**: October 2025

---

**End of Technical Architecture Document**

For questions or issues, please open a GitHub issue at:
https://github.com/unclecode/crawl4ai/issues
