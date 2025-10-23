# Crawl4AI Docker Architecture - AI Context Map

**Purpose:** Dense technical reference for AI agents to understand complete system architecture.
**Format:** Symbolic, compressed, high-information-density documentation.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│ CRAWL4AI DOCKER ORCHESTRATION SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│ Modes: Single (N=1) | Swarm (N>1) | Compose+Nginx (N>1)     │
│ Entry: cnode CLI → deploy/docker/cnode_cli.py               │
│ Core: deploy/docker/server_manager.py                       │
│ Server: deploy/docker/server.py (FastAPI)                   │
│ API: deploy/docker/api.py (crawl endpoints)                 │
│ Monitor: deploy/docker/monitor.py + monitor_routes.py       │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure & File Map

```
deploy/
├── docker/                          # Server runtime & orchestration
│   ├── server.py                    # FastAPI app entry [CRITICAL]
│   ├── api.py                       # /crawl, /screenshot, /pdf endpoints
│   ├── server_manager.py            # Docker orchestration logic [CORE]
│   ├── cnode_cli.py                 # CLI interface (Click-based)
│   ├── monitor.py                   # Real-time metrics collector
│   ├── monitor_routes.py            # /monitor dashboard routes
│   ├── crawler_pool.py              # Browser pool management
│   ├── hook_manager.py              # Pre/post crawl hooks
│   ├── job.py                       # Job queue schema
│   ├── utils.py                     # Helpers (port check, health)
│   ├── auth.py                      # API key authentication
│   ├── schemas.py                   # Pydantic models
│   ├── mcp_bridge.py                # MCP protocol bridge
│   ├── supervisord.conf             # Process manager config
│   ├── config.yml                   # Server config template
│   ├── requirements.txt             # Python deps
│   ├── static/                      # Web assets
│   │   ├── monitor/                 # Dashboard UI
│   │   └── playground/              # API playground
│   └── tests/                       # Test suite
│
└── installer/                       # User-facing installation
    ├── cnode_pkg/                   # Standalone package
    │   ├── cli.py                   # Copy of cnode_cli.py
    │   ├── server_manager.py        # Copy of server_manager.py
    │   └── requirements.txt         # click, rich, anyio, pyyaml
    ├── install-cnode.sh             # Remote installer (git sparse-checkout)
    ├── sync-cnode.sh                # Dev tool (source→pkg sync)
    ├── USER_GUIDE.md                # Human-readable guide
    ├── README.md                    # Developer documentation
    └── QUICKSTART.md                # Cheat sheet
```

---

## Core Components Deep Dive

### 1. `server_manager.py` - Orchestration Engine

**Role:** Manages Docker container lifecycle, auto-detects deployment mode.

**Key Classes:**
- `ServerManager` - Main orchestrator
  - `start(replicas, mode, port, env_file, image)` → Deploy server
  - `stop(remove_volumes)` → Teardown
  - `status()` → Health check
  - `scale(replicas)` → Live scaling
  - `logs(follow, tail)` → Stream logs
  - `cleanup(force)` → Emergency cleanup

**State Management:**
- File: `~/.crawl4ai/server_state.yml`
- Schema: `{mode, replicas, port, image, started_at, containers[]}`
- Atomic writes with lock file

**Deployment Modes:**
```python
if replicas == 1:
    mode = "single"  # docker run
elif swarm_available():
    mode = "swarm"   # docker stack deploy
else:
    mode = "compose" # docker-compose + nginx
```

**Container Naming:**
- Single: `crawl4ai-server`
- Swarm: `crawl4ai-stack_crawl4ai`
- Compose: `crawl4ai-server-{1..N}`, `crawl4ai-nginx`

**Networks:**
- `crawl4ai-network` (bridge mode for all)

**Volumes:**
- `crawl4ai-redis-data` - Persistent queue
- `crawl4ai-profiles` - Browser profiles

**Health Checks:**
- Endpoint: `http://localhost:{port}/health`
- Timeout: 30s startup
- Retry: 3 attempts

---

### 2. `server.py` - FastAPI Application

**Role:** HTTP server exposing crawl API + monitoring.

**Startup Flow:**
```python
app = FastAPI()
@app.on_event("startup")
async def startup():
    init_crawler_pool()      # Pre-warm browsers
    init_redis_connection()  # Job queue
    start_monitor_collector() # Metrics
```

**Key Endpoints:**
```
POST /crawl          → api.py:crawl_endpoint()
POST /crawl/stream   → api.py:crawl_stream_endpoint()
POST /screenshot     → api.py:screenshot_endpoint()
POST /pdf            → api.py:pdf_endpoint()
GET  /health         → server.py:health_check()
GET  /monitor        → monitor_routes.py:dashboard()
WS   /monitor/ws     → monitor_routes.py:websocket_endpoint()
GET  /playground     → static/playground/index.html
```

**Process Manager:**
- Uses `supervisord` to manage:
  - FastAPI server (port 11235)
  - Redis (port 6379)
  - Background workers

**Environment:**
```bash
CRAWL4AI_PORT=11235
REDIS_URL=redis://localhost:6379
MAX_CONCURRENT_CRAWLS=5
BROWSER_POOL_SIZE=3
```

---

### 3. `api.py` - Crawl Endpoints

**Main Endpoint:** `POST /crawl`

**Request Schema:**
```json
{
  "urls": ["https://example.com"],
  "priority": 10,
  "browser_config": {
    "type": "BrowserConfig",
    "params": {"headless": true, "viewport_width": 1920}
  },
  "crawler_config": {
    "type": "CrawlerRunConfig",
    "params": {"cache_mode": "bypass", "extraction_strategy": {...}}
  }
}
```

**Processing Flow:**
```
1. Validate request (Pydantic)
2. Queue job → Redis
3. Get browser from pool → crawler_pool.py
4. Execute crawl → AsyncWebCrawler
5. Apply hooks → hook_manager.py
6. Return result (JSON)
7. Release browser to pool
```

**Memory Management:**
- Browser pool: Max 3 instances
- LRU eviction when pool full
- Explicit cleanup: `browser.close()` in finally block
- Redis TTL: 1 hour for completed jobs

**Error Handling:**
```python
try:
    result = await crawler.arun(url, config)
except PlaywrightError as e:
    # Browser crash - release & recreate
    await pool.invalidate(browser_id)
except TimeoutError as e:
    # Timeout - kill & retry
    await crawler.kill()
except Exception as e:
    # Unknown - log & fail gracefully
    logger.error(f"Crawl failed: {e}")
```

---

### 4. `crawler_pool.py` - Browser Pool Manager

**Role:** Manage persistent browser instances to avoid startup overhead.

**Class:** `CrawlerPool`
- `get_crawler()` → Lease browser (async with context manager)
- `release_crawler(id)` → Return to pool
- `warm_up(count)` → Pre-launch browsers
- `cleanup()` → Close all browsers

**Pool Strategy:**
```python
pool = {
    "browser_1": {"crawler": AsyncWebCrawler(), "in_use": False},
    "browser_2": {"crawler": AsyncWebCrawler(), "in_use": False},
    "browser_3": {"crawler": AsyncWebCrawler(), "in_use": False},
}

async with pool.get_crawler() as crawler:
    result = await crawler.arun(url)
    # Auto-released on context exit
```

**Anti-Leak Mechanisms:**
1. Context managers enforce cleanup
2. Watchdog thread kills stale browsers (>10min idle)
3. Max lifetime: 1 hour per browser
4. Force GC after browser close

---

### 5. `monitor.py` + `monitor_routes.py` - Real-time Dashboard

**Architecture:**
```
[Browser] <--WebSocket--> [monitor_routes.py] <--Events--> [monitor.py]
                              ↓
                          [Redis Pub/Sub]
                              ↓
                       [Metrics Collector]
```

**Metrics Collected:**
- Requests/sec (sliding window)
- Active crawls (real-time count)
- Response times (p50, p95, p99)
- Error rate (5min rolling)
- Memory usage (RSS, heap)
- Browser pool utilization

**WebSocket Protocol:**
```json
// Server → Client
{
  "type": "metrics",
  "data": {
    "rps": 45.3,
    "active_crawls": 12,
    "p95_latency": 1234,
    "error_rate": 0.02
  }
}

// Client → Server
{
  "type": "subscribe",
  "channels": ["metrics", "logs"]
}
```

**Dashboard Route:** `/monitor`
- Real-time graphs (Chart.js)
- Request log stream
- Container health status
- Resource utilization

---

### 6. `cnode_cli.py` - CLI Interface

**Framework:** Click (Python CLI framework)

**Command Structure:**
```
cnode
├── start [--replicas N] [--port P] [--mode M] [--image I]
├── stop [--remove-volumes]
├── status
├── scale N
├── logs [--follow] [--tail N]
├── restart [--replicas N]
└── cleanup [--force]
```

**Execution Flow:**
```python
@cli.command("start")
def start_cmd(replicas, mode, port, env_file, image):
    manager = ServerManager()
    result = anyio.run(manager.start(...))  # Async bridge
    if result["success"]:
        console.print(success_panel)
```

**User Feedback:**
- Rich library for colors/tables
- Progress spinners during operations
- Error messages with hints
- Status tables with health indicators

**State Persistence:**
- Saves deployment config to `~/.crawl4ai/server_state.yml`
- Enables stateless commands (status, scale, restart)

---

### 7. Docker Orchestration Details

**Single Container Mode (N=1):**
```bash
docker run -d \
  --name crawl4ai-server \
  --network crawl4ai-network \
  -p 11235:11235 \
  -v crawl4ai-redis-data:/data \
  unclecode/crawl4ai:latest
```

**Docker Swarm Mode (N>1, Swarm available):**
```yaml
# docker-compose.swarm.yml
version: '3.8'
services:
  crawl4ai:
    image: unclecode/crawl4ai:latest
    deploy:
      replicas: 5
      update_config:
        parallelism: 2
        delay: 10s
      restart_policy:
        condition: on-failure
    ports:
      - "11235:11235"
    networks:
      - crawl4ai-network
```

Deploy: `docker stack deploy -c docker-compose.swarm.yml crawl4ai-stack`

**Docker Compose + Nginx Mode (N>1, fallback):**
```yaml
# docker-compose.yml
services:
  crawl4ai-1:
    image: unclecode/crawl4ai:latest
    networks: [crawl4ai-network]

  crawl4ai-2:
    image: unclecode/crawl4ai:latest
    networks: [crawl4ai-network]

  nginx:
    image: nginx:alpine
    ports: ["11235:80"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    networks: [crawl4ai-network]
```

Nginx config (round-robin load balancing):
```nginx
upstream crawl4ai_backend {
    server crawl4ai-1:11235;
    server crawl4ai-2:11235;
    server crawl4ai-3:11235;
}

server {
    listen 80;
    location / {
        proxy_pass http://crawl4ai_backend;
        proxy_set_header Host $host;
    }
}
```

---

## Memory Leak Prevention Strategy

### Problem Areas & Solutions

**1. Browser Instances**
```python
# ❌ BAD - Leak risk
crawler = AsyncWebCrawler()
result = await crawler.arun(url)
# Browser never closed!

# ✅ GOOD - Guaranteed cleanup
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url)
    # Auto-closed on exit
```

**2. WebSocket Connections**
```python
# monitor_routes.py
active_connections = set()

@app.websocket("/monitor/ws")
async def websocket_endpoint(websocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            await websocket.send_json(get_metrics())
    finally:
        active_connections.remove(websocket)  # Critical!
```

**3. Redis Connections**
```python
# Use connection pooling
redis_pool = aioredis.ConnectionPool(
    host="localhost",
    port=6379,
    max_connections=10,
    decode_responses=True
)

# Reuse connections
async def get_job(job_id):
    async with redis_pool.get_connection() as conn:
        data = await conn.get(f"job:{job_id}")
    # Connection auto-returned to pool
```

**4. Async Task Cleanup**
```python
# Track background tasks
background_tasks = set()

async def crawl_task(url):
    try:
        result = await crawl(url)
    finally:
        background_tasks.discard(asyncio.current_task())

# On shutdown
async def shutdown():
    tasks = list(background_tasks)
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
```

**5. File Descriptor Leaks**
```python
# Use context managers for files
async def save_screenshot(url):
    async with aiofiles.open(f"{job_id}.png", "wb") as f:
        await f.write(screenshot_bytes)
    # File auto-closed
```

---

## Installation & Distribution

### User Installation Flow

**Script:** `deploy/installer/install-cnode.sh`

**Steps:**
1. Check Python 3.8+ exists
2. Check pip available
3. Check Docker installed (warn if missing)
4. Create temp dir: `mktemp -d`
5. Git sparse-checkout:
   ```bash
   git init
   git remote add origin https://github.com/unclecode/crawl4ai.git
   git config core.sparseCheckout true
   echo "deploy/installer/cnode_pkg/*" > .git/info/sparse-checkout
   git pull --depth=1 origin main
   ```
6. Install deps: `pip install click rich anyio pyyaml`
7. Copy package: `cnode_pkg/ → /usr/local/lib/cnode/`
8. Create wrapper: `/usr/local/bin/cnode`
   ```bash
   #!/usr/bin/env bash
   export PYTHONPATH="/usr/local/lib/cnode:$PYTHONPATH"
   exec python3 -m cnode_pkg.cli "$@"
   ```
9. Cleanup temp dir

**Result:**
- Binary-like experience (fast startup: ~0.1s)
- No need for PyInstaller (49x faster)
- Platform-independent (any OS with Python)

---

## Development Workflow

### Source Code Sync (Auto)

**Git Hook:** `.githooks/pre-commit`

**Trigger:** When committing `deploy/docker/cnode_cli.py` or `server_manager.py`

**Action:**
```bash
1. Diff source vs package
2. If different:
   - Run sync-cnode.sh
   - Copy cnode_cli.py → cnode_pkg/cli.py
   - Fix imports: s/deploy.docker/cnode_pkg/g
   - Copy server_manager.py → cnode_pkg/
   - Stage synced files
3. Continue commit
```

**Setup:** `./setup-hooks.sh` (configures `git config core.hooksPath .githooks`)

**Smart Behavior:**
- Silent when no sync needed
- Only syncs if content differs
- Minimal output: `✓ cnode synced`

---

## API Request/Response Flow

### Example: POST /crawl

**Request:**
```bash
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "browser_config": {
      "type": "BrowserConfig",
      "params": {"headless": true}
    },
    "crawler_config": {
      "type": "CrawlerRunConfig",
      "params": {"cache_mode": "bypass"}
    }
  }'
```

**Processing:**
```
1. FastAPI receives request → api.py:crawl_endpoint()
2. Validate schema → Pydantic models in schemas.py
3. Create job → job.py:Job(id=uuid4(), urls=[...])
4. Queue to Redis → LPUSH crawl_queue {job_json}
5. Get browser from pool → crawler_pool.py:get_crawler()
6. Execute crawl:
   a. Launch page → browser.new_page()
   b. Navigate → page.goto(url)
   c. Extract → extraction_strategy.extract()
   d. Generate markdown → markdown_generator.generate()
7. Store result → Redis SETEX result:{job_id} 3600 {result_json}
8. Release browser → pool.release(browser_id)
9. Return response:
   {
     "success": true,
     "result": {
       "url": "https://example.com",
       "markdown": "# Example Domain...",
       "metadata": {"title": "Example Domain"},
       "extracted_content": {...}
     }
   }
```

**Error Cases:**
- 400: Invalid request schema
- 429: Rate limit exceeded
- 500: Internal error (browser crash, timeout)
- 503: Service unavailable (all browsers busy)

---

## Scaling Behavior

### Scale-Up (1 → 10 replicas)

**Command:** `cnode scale 10`

**Swarm Mode:**
```bash
docker service scale crawl4ai-stack_crawl4ai=10
# Docker handles:
# - Container creation
# - Network attachment
# - Load balancer update
# - Rolling deployment
```

**Compose Mode:**
```bash
# Update docker-compose.yml
# Change replica count in all service definitions
docker-compose up -d --scale crawl4ai=10
# Regenerate nginx.conf with 10 upstreams
docker exec nginx nginx -s reload
```

**Load Distribution:**
- Swarm: Built-in ingress network (VIP-based round-robin)
- Compose: Nginx upstream (round-robin, can configure least_conn)

**Zero-Downtime:**
- Swarm: Yes (rolling update, parallelism=2)
- Compose: Partial (nginx reload is graceful, but brief spike)

---

## Configuration Files

### `config.yml` - Server Configuration

```yaml
server:
  port: 11235
  host: "0.0.0.0"
  workers: 4

crawler:
  max_concurrent: 5
  timeout: 30
  retries: 3

browser:
  pool_size: 3
  headless: true
  args:
    - "--no-sandbox"
    - "--disable-dev-shm-usage"

redis:
  host: "localhost"
  port: 6379
  db: 0

monitoring:
  enabled: true
  metrics_interval: 5  # seconds
```

### `supervisord.conf` - Process Management

```ini
[supervisord]
nodaemon=true

[program:redis]
command=redis-server --port 6379
autorestart=true

[program:fastapi]
command=uvicorn server:app --host 0.0.0.0 --port 11235
autorestart=true
stdout_logfile=/var/log/crawl4ai/api.log

[program:monitor]
command=python monitor.py
autorestart=true
```

---

## Testing & Quality

### Test Structure

```
deploy/docker/tests/
├── cli/                    # CLI command tests
│   └── test_commands.py    # start, stop, scale, status
├── monitor/                # Dashboard tests
│   └── test_websocket.py   # WS connection, metrics
└── codebase_test/          # Integration tests
    └── test_api.py         # End-to-end crawl tests
```

### Key Test Cases

**CLI Tests:**
- `test_start_single()` - Starts 1 replica
- `test_start_cluster()` - Starts N replicas
- `test_scale_up()` - Scales 1→5
- `test_scale_down()` - Scales 5→2
- `test_status()` - Reports correct state
- `test_logs()` - Streams logs

**API Tests:**
- `test_crawl_success()` - Basic crawl works
- `test_crawl_timeout()` - Handles slow sites
- `test_concurrent_crawls()` - Parallel requests
- `test_browser_pool()` - Reuses browsers
- `test_memory_cleanup()` - No leaks after 100 crawls

**Monitor Tests:**
- `test_websocket_connect()` - WS handshake
- `test_metrics_stream()` - Receives updates
- `test_multiple_clients()` - Handles N connections

---

## Critical File Cross-Reference

| Component | Primary File | Dependencies |
|-----------|--------------|--------------|
| **CLI Entry** | `cnode_cli.py:482` | `server_manager.py`, `click`, `rich` |
| **Orchestrator** | `server_manager.py:45` | `docker`, `yaml`, `anyio` |
| **API Server** | `server.py:120` | `api.py`, `monitor_routes.py` |
| **Crawl Logic** | `api.py:78` | `crawler_pool.py`, `AsyncWebCrawler` |
| **Browser Pool** | `crawler_pool.py:23` | `AsyncWebCrawler`, `asyncio` |
| **Monitoring** | `monitor.py:156` | `redis`, `psutil` |
| **Dashboard** | `monitor_routes.py:89` | `monitor.py`, `websockets` |
| **Hooks** | `hook_manager.py:12` | `api.py`, custom user hooks |

**Startup Chain:**
```
cnode start
  └→ cnode_cli.py:start_cmd()
      └→ server_manager.py:start()
          └→ docker run/stack/compose
              └→ supervisord
                  ├→ redis-server
                  ├→ server.py
                  │   └→ api.py (routes)
                  │   └→ crawler_pool.py (init)
                  └→ monitor.py (collector)
```

---

## Symbolic Notation Summary

```
⊕ Addition/Creation      ⊖ Removal/Cleanup
⊗ Multiplication/Scale   ⊘ Division/Split
→ Flow/Dependency        ← Reverse flow
⇄ Bidirectional          ⇵ Up/Down scale
✓ Success/Complete       ✗ Failure/Error
⚠ Warning                ⚡ Performance critical
🔒 Lock/Exclusive        🔓 Unlock/Shared
📊 Metrics               📝 Logs
🌐 Network               💾 Storage
🧠 Memory                🐳 Docker
```

**State Machine:**
```
[STOPPED] →start→ [STARTING] →ready→ [RUNNING]
[RUNNING] →scale→ [SCALING] →done→ [RUNNING]
[RUNNING] →stop→ [STOPPING] →done→ [STOPPED]
[ANY] →error→ [ERROR] →cleanup→ [STOPPED]
```

---

## Quick Reference Commands

```bash
# Install
curl -sSL https://raw.githubusercontent.com/unclecode/crawl4ai/main/deploy/installer/install-cnode.sh | bash

# Deploy
cnode start --replicas 5 --port 11235

# Monitor
open http://localhost:11235/monitor

# Scale
cnode scale 10

# Test
curl -X POST http://localhost:11235/crawl -H "Content-Type: application/json" -d '{"urls":["https://example.com"]}'

# Logs
cnode logs -f

# Teardown
cnode stop --remove-volumes
```

---

## Future AI Agent Instructions

**When debugging:** Read this file first, then check specific source files mentioned.

**When extending:** Follow existing patterns (context managers, async/await, type hints).

**When optimizing:** Profile first (monitor.py metrics), then optimize hot paths (crawler_pool.py, api.py).

**When troubleshooting memory:** Check browser pool cleanup, WebSocket connection tracking, Redis connection pooling.

**When scaling issues:** Verify Docker mode (swarm vs compose), check nginx config if compose, review load balancer logs.

---

**END OF ARCHITECTURE MAP**
*Version: 1.0.0 | Last Updated: 2025-10-21 | Token-Optimized for AI Consumption*
