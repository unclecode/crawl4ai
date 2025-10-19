# Multi-Container Architecture - Technical Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Components](#components)
4. [Data Flow](#data-flow)
5. [Redis Aggregation Strategy](#redis-aggregation-strategy)
6. [Container Discovery](#container-discovery)
7. [Load Balancing & Routing](#load-balancing--routing)
8. [Monitoring Dashboard](#monitoring-dashboard)
9. [CLI Commands](#cli-commands)
10. [Configuration](#configuration)
11. [Deployment Modes](#deployment-modes)
12. [Troubleshooting](#troubleshooting)

---

## Overview

Crawl4AI's multi-container deployment architecture enables horizontal scaling with intelligent load balancing, centralized monitoring, and real-time data aggregation using Redis as the coordination layer.

### Key Features

- **Horizontal Scaling**: Deploy 1 to N containers
- **Load Balancing**: Nginx with round-robin for API, sticky sessions for monitoring
- **Centralized Monitoring**: Redis-backed data aggregation across all containers
- **Real-time Dashboard**: WebSocket-powered monitoring with per-container filtering
- **Zero-downtime Scaling**: Add/remove containers without service interruption
- **Container Discovery**: Automatic heartbeat-based registration

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Requests                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │     Nginx     │ Port 11235
                  │ Load Balancer │
                  └───────┬───────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Crawl4AI-1  │  │  Crawl4AI-2  │  │  Crawl4AI-3  │
│  Container   │  │  Container   │  │  Container   │
│              │  │              │  │              │
│ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │
│ │ Monitor  │ │  │ │ Monitor  │ │  │ │ Monitor  │ │
│ │ Stats    │ │  │ │ Stats    │ │  │ │ Stats    │ │
│ └────┬─────┘ │  │ └────┬─────┘ │  │ └────┬─────┘ │
│      │       │  │      │       │  │      │       │
│      │ Write │  │      │ Write │  │      │ Write │
│      ▼       │  │      ▼       │  │      ▼       │
└──────┼───────┘  └──────┼───────┘  └──────┼───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                  ┌─────────────┐
                  │    Redis    │
                  │  Datastore  │
                  └─────────────┘
                         │
                         │ Aggregate Read
                         ▼
                  ┌─────────────┐
                  │  Dashboard  │
                  │  /monitor   │
                  └─────────────┘
```

---

## Components

### 1. Nginx Load Balancer

**Purpose**: Entry point for all requests, distributes load across containers

**Configuration**: `crawl4ai/templates/nginx.conf.template`

**Upstreams**:

```nginx
# Backend API (round-robin load balancing)
upstream crawl4ai_backend {
    server crawl4ai:11235;
}

# Monitor/Dashboard (sticky sessions using ip_hash)
upstream crawl4ai_monitor {
    ip_hash;  # Same client always goes to same container
    server crawl4ai:11235;
}
```

**Routing Rules**:

- `/crawl`, `/health`, `/batch` → `crawl4ai_backend` (round-robin)
- `/monitor/*`, `/dashboard` → `crawl4ai_monitor` (sticky sessions)
- `/monitor/ws` → WebSocket proxy with upgrade headers

**Port Mapping**:
- Host: `11235` → Nginx: `80` → Containers: `11235`

---

### 2. Crawl4AI Containers

**Base Image**: `unclecode/crawl4ai:latest`

**Scaling**: Configured via Docker Compose `deploy.replicas` or `--scale` flag

**Environment Variables**:
```bash
REDIS_HOST=redis
REDIS_PORT=6379
OPENAI_API_KEY=${OPENAI_API_KEY}
# ... other LLM provider keys
```

**Internal Services**:
- **API Server**: FastAPI/Gunicorn on port 11235
- **Monitor Stats**: Background worker tracking metrics
- **Heartbeat Worker**: Registers container in Redis every 30s
- **Browser Pool**: Permanent/Hot/Cold browser management

**Container ID**: Extracted from `/proc/self/cgroup` or hostname

---

### 3. Redis Datastore

**Purpose**: Centralized coordination and data aggregation

**Image**: `redis:alpine`

**Persistence**: `appendonly yes` with volume mount

**Data Structure**:

```
# Container Discovery
monitor:active_containers          # SET of container IDs
monitor:heartbeat:{container_id}   # JSON heartbeat data (60s TTL)

# Per-Container Data
monitor:{container_id}:active_requests     # JSON list (5min TTL)
monitor:{container_id}:completed           # JSON list (1h TTL)
monitor:{container_id}:janitor             # JSON list (1h TTL)
monitor:{container_id}:errors              # JSON list (1h TTL)

# Shared Aggregate Data
monitor:endpoint_stats                     # JSON aggregate stats (24h TTL)
```

**Volume**: `redis_data:/data` for persistence

---

## Data Flow

### Request Lifecycle

```
1. Client → Nginx (port 11235)
2. Nginx → Crawl4AI Container (round-robin)
3. Container:
   a. Track request start → monitor.track_request_start()
   b. Persist to Redis: monitor:{container_id}:active_requests
   c. Process crawl request
   d. Track request end → monitor.track_request_end()
   e. Persist to Redis: monitor:{container_id}:completed
4. Response → Client
```

### Monitoring Data Flow

```
1. All Containers:
   - Write stats to Redis with container_id prefix
   - Send heartbeat every 30s
   - Track: requests, browsers, errors, janitor events

2. Redis:
   - Stores per-container data
   - TTL-based expiration
   - Active container set maintained

3. Monitor API (/monitor/*):
   - Reads from Redis
   - Aggregates data from ALL containers
   - Sorts by timestamp
   - Returns unified view

4. Dashboard:
   - Fetches aggregated data
   - Maps container IDs to labels (C-1, C-2, C-3)
   - Client-side filtering
   - WebSocket for real-time updates
```

---

## Redis Aggregation Strategy

### Why Redis?

1. **No Direct Communication**: Containers don't need to discover/talk to each other
2. **Decoupled**: Adding/removing containers doesn't affect others
3. **Atomic Operations**: Redis handles concurrent writes
4. **TTL Support**: Automatic cleanup of stale data
5. **Fast Reads**: In-memory aggregation queries

### Write Strategy

**Container-Side** (`monitor.py`):

```python
# Each container writes its own data
await redis.set(
    f"monitor:{self.container_id}:completed",
    json.dumps(list(self.completed_requests)),
    ex=3600  # 1 hour TTL
)

# Add to active containers set
await redis.sadd("monitor:active_containers", self.container_id)

# Heartbeat with metadata
await redis.setex(
    f"monitor:heartbeat:{self.container_id}",
    60,  # 60s TTL
    json.dumps({"id": self.container_id, "hostname": hostname})
)
```

### Read Strategy

**API-Side** (`monitor_routes.py`):

```python
async def _aggregate_completed_requests(limit=100):
    # 1. Get all active containers
    container_ids = await redis.smembers("monitor:active_containers")

    # 2. Fetch from each container
    all_requests = []
    for container_id in container_ids:
        data = await redis.get(f"monitor:{container_id}:completed")
        if data:
            all_requests.extend(json.loads(data))

    # 3. Sort and limit
    all_requests.sort(key=lambda x: x.get("end_time", 0), reverse=True)
    return all_requests[:limit]
```

---

## Container Discovery

### Heartbeat Mechanism

**Frequency**: Every 30 seconds

**Worker**: `monitor.py` - `_heartbeat_worker()`

**Data Sent**:
```json
{
  "id": "b790d0b6c9d4",
  "hostname": "b790d0b6c9d4",
  "last_seen": 1760785944.18,
  "mode": "compose"
}
```

**TTL**: 60 seconds (2x heartbeat interval for fault tolerance)

**Discovery API**: `/monitor/containers`

```python
async def get_containers():
    # Read from Redis heartbeats
    container_ids = await redis.smembers("monitor:active_containers")

    containers = []
    for cid in container_ids:
        heartbeat = await redis.get(f"monitor:heartbeat:{cid}")
        if heartbeat:
            info = json.loads(heartbeat)
            containers.append({
                "id": info["id"],
                "hostname": info["hostname"],
                "healthy": True  # If heartbeat exists, container is alive
            })

    return {"containers": containers, "count": len(containers)}
```

### Container Failure Handling

1. Container stops → Heartbeat stops
2. After 60s → Redis TTL expires → Key deleted
3. Next `/monitor/containers` call → Container no longer in list
4. Dashboard auto-updates → Shows only healthy containers

---

## Load Balancing & Routing

### API Endpoints (Round-Robin)

**Nginx Config**:
```nginx
location / {
    proxy_pass http://crawl4ai_backend;  # No ip_hash
}
```

**Behavior**:
- Sequential distribution: Req1→C1, Req2→C2, Req3→C3, Req4→C1...
- Maximizes throughput
- Balanced load across containers

**Use Cases**:
- `/crawl` - Crawl requests
- `/batch` - Batch operations
- `/health` - Health checks

---

### Monitor/Dashboard (Sticky Sessions)

**Nginx Config**:
```nginx
upstream crawl4ai_monitor {
    ip_hash;  # Client IP-based routing
    server crawl4ai:11235;
}

location ~ ^/(monitor|dashboard) {
    proxy_pass http://crawl4ai_monitor;
}
```

**Behavior**:
- Client IP hashed → Always same container for same client
- Dashboard consistency
- WebSocket connection persistence

**Why Sticky Sessions?**:
- WebSocket requires persistent connection
- Dashboard state consistency
- Simpler debugging (same container per user)

---

### WebSocket Routing

**Nginx Config**:
```nginx
location = /monitor/ws {
    proxy_pass http://crawl4ai_monitor;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
}
```

**Key Features**:
- **Exact match** (`location =`) - Highest priority
- **Upgrade headers** - HTTP → WebSocket protocol switch
- **Long timeouts** - 7 days for persistent connections
- **Sticky upstream** - Uses `crawl4ai_monitor` with `ip_hash`

---

## Monitoring Dashboard

### Architecture

**Frontend**: Single-page HTML/CSS/JavaScript
- **Path**: `/app/static/monitor/index.html`
- **URL**: `http://localhost:11235/dashboard/`

**Backend**:
- REST API: `/monitor/*` endpoints
- WebSocket: `/monitor/ws` for real-time updates

### Data Sources

**API Endpoints**:

```
GET /monitor/containers         # Container discovery
GET /monitor/requests           # All requests (aggregated)
GET /monitor/browsers           # All browsers (aggregated)
GET /monitor/logs/janitor       # Janitor events (aggregated)
GET /monitor/logs/errors        # Errors (aggregated)
GET /monitor/health             # System health
GET /monitor/endpoints/stats    # Endpoint analytics
GET /monitor/timeline           # Metrics timeline
WS  /monitor/ws                 # Real-time updates
```

**Aggregation**:
- API reads from **all containers** via Redis
- Sorts by timestamp across containers
- Returns unified dataset with `container_id` on each item

### Container Filtering

**UI Components**:

1. **Infrastructure Card**:
   ```
   [All] [C-1] [C-2] [C-3]
   ```

2. **Container Mapping**:
   ```javascript
   containerMapping = {
       "b790d0b6c9d4": "C-1",  // container_id → label
       "f899b55bd5f5": "C-2",
       "076a35479dd9": "C-3"
   }
   ```

3. **Filter Logic**:
   ```javascript
   // Filter active requests
   const filteredActive = currentContainerFilter === 'all'
       ? requests.active
       : requests.active.filter(r => r.container_id === currentContainerFilter);
   ```

**All Data Shows Container Labels**:
- Requests: `C-1 req_abc123 /crawl ...`
- Browsers: `Type: permanent, Container: C-1`
- Janitor: `C-1 19:27:42 close_hot ...`
- Errors: `C-2 Error: ...`

### Real-Time Updates (WebSocket)

**Connection**:
```javascript
const wsUrl = `${protocol}//${window.location.host}/monitor/ws`;
ws = new WebSocket(wsUrl);
```

**Update Frequency**: Every 2 seconds

**Data Payload**:
```json
{
  "timestamp": 1760785944.18,
  "container_id": "b790d0b6c9d4",
  "health": { ... },
  "requests": {
    "active": [ ... ],
    "completed": [ ... ]
  },
  "browsers": [ ... ],
  "timeline": { ... },
  "janitor": [ ... ],
  "errors": [ ... ]
}
```

**Note**: WebSocket currently sends from **one container** (sticky session), but all API calls aggregate from Redis.

---

## CLI Commands

### Start Multi-Container Deployment

```bash
# Default: 3 replicas
docker compose up -d

# Custom scale
docker compose up -d --scale crawl4ai=5

# With build
docker compose up -d --build --scale crawl4ai=3
```

### Scale Running Deployment

```bash
# Scale up
docker compose up -d --scale crawl4ai=5 --no-recreate

# Scale down
docker compose up -d --scale crawl4ai=2 --no-recreate
```

### View Container Status

```bash
# List all containers
docker compose ps

# Check health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View specific container logs
docker logs fix-docker-crawl4ai-1 -f

# View nginx logs
docker logs fix-docker-nginx-1 -f
```

### Redis Inspection

```bash
# Enter Redis CLI
docker exec -it fix-docker-redis-1 redis-cli

# Inside Redis CLI:
KEYS monitor:*                          # List all monitor keys
SMEMBERS monitor:active_containers      # Show active containers
GET monitor:b790d0b6c9d4:completed      # Get completed requests
TTL monitor:heartbeat:b790d0b6c9d4      # Check heartbeat TTL
```

### Debugging

```bash
# Check container IDs
docker ps --filter "name=crawl4ai" --format "{{.ID}} {{.Names}}"

# Inspect Redis data
docker exec fix-docker-redis-1 redis-cli KEYS "monitor:*:completed"

# Test API directly
curl http://localhost:11235/monitor/containers | jq

# Test WebSocket (requires websocat or wscat)
websocat ws://localhost:11235/monitor/ws

# View nginx upstream routing
docker exec fix-docker-nginx-1 cat /etc/nginx/nginx.conf | grep -A 5 "upstream"
```

---

## Configuration

### Docker Compose (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  redis:
    image: redis:alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - crawl4ai_net
    restart: unless-stopped

  crawl4ai:
    image: unclecode/crawl4ai:latest
    build:
      context: .
      dockerfile: Dockerfile
    env_file:
      - .llm.env
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - /dev/shm:/dev/shm
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
    depends_on:
      - redis
    networks:
      - crawl4ai_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11235/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "11235:80"
    volumes:
      - ./crawl4ai/templates/nginx.conf.template:/etc/nginx/nginx.conf:ro
    depends_on:
      - crawl4ai
    networks:
      - crawl4ai_net
    restart: unless-stopped

networks:
  crawl4ai_net:
    driver: bridge

volumes:
  redis_data:
```

### Environment Variables (`.llm.env`)

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=...
GROQ_API_KEY=...
TOGETHER_API_KEY=...
MISTRAL_API_KEY=...
GEMINI_API_TOKEN=...
LLM_PROVIDER=openai/gpt-4  # Optional default provider
```

### Nginx Configuration

**Template**: `crawl4ai/templates/nginx.conf.template`

**Key Settings**:
```nginx
worker_processes auto;

upstream crawl4ai_backend {
    # Round-robin for API
    server crawl4ai:11235;
}

upstream crawl4ai_monitor {
    # Sticky sessions for monitoring
    ip_hash;
    server crawl4ai:11235;
}

server {
    listen 80;
    client_max_body_size 10M;

    # WebSocket (exact match, highest priority)
    location = /monitor/ws { ... }

    # Monitor/Dashboard (sticky)
    location ~ ^/(monitor|dashboard) {
        proxy_pass http://crawl4ai_monitor;
    }

    # API (round-robin)
    location / {
        proxy_pass http://crawl4ai_backend;
    }
}
```

---

## Deployment Modes

### Single Container

**Use Case**: Development, testing, low-traffic

**Command**:
```bash
docker compose up -d --scale crawl4ai=1
```

**Characteristics**:
- No load balancing overhead
- Direct port access possible
- Simpler debugging
- Dashboard shows `mode: "single"`

---

### Compose (Multi-Container)

**Use Case**: Production, high-availability, horizontal scaling

**Command**:
```bash
docker compose up -d --scale crawl4ai=3
```

**Characteristics**:
- Nginx load balancing
- Redis aggregation
- Horizontal scaling (1-N containers)
- Dashboard shows `mode: "compose"`
- Zero-downtime scaling

**Scaling Limits**:
- **Minimum**: 1 container
- **Maximum**: Limited by host resources
- **Recommended**: 3-10 containers per host

---

### Docker Swarm (Future)

**Use Case**: Multi-host orchestration, auto-scaling

**Command**:
```bash
docker stack deploy -c docker-compose.yml crawl4ai
```

**Characteristics**:
- Multi-host deployment
- Built-in service discovery
- Auto-healing
- Dashboard shows `mode: "swarm"`
- Requires shared Redis (external or global service)

---

## Troubleshooting

### Container Discovery Issues

**Symptom**: Dashboard shows fewer containers than expected

**Diagnosis**:
```bash
# Check active containers
docker exec fix-docker-redis-1 redis-cli SMEMBERS monitor:active_containers

# Check heartbeats
docker exec fix-docker-redis-1 redis-cli KEYS "monitor:heartbeat:*"

# Check container logs for heartbeat errors
docker logs fix-docker-crawl4ai-1 | grep -i heartbeat
```

**Solutions**:
- Wait 30s for heartbeat to register
- Check Redis connectivity from containers
- Verify containers are healthy: `docker ps`

---

### No Data in Dashboard

**Symptom**: Dashboard shows "No data" or empty sections

**Diagnosis**:
```bash
# Check if containers are writing to Redis
docker exec fix-docker-redis-1 redis-cli KEYS "monitor:*:completed"

# Test aggregation endpoint
curl http://localhost:11235/monitor/requests | jq

# Check for errors in container logs
docker logs fix-docker-crawl4ai-1 | grep -i "error\|redis"
```

**Solutions**:
- Make some API requests to generate data
- Check Redis connection (REDIS_HOST, REDIS_PORT)
- Verify containers can write to Redis

---

### WebSocket Connection Failed

**Symptom**: Dashboard shows "Disconnected" or WebSocket errors

**Diagnosis**:
```bash
# Test WebSocket upgrade
curl -i -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: test" \
     http://localhost:11235/monitor/ws

# Check nginx config
docker exec fix-docker-nginx-1 cat /etc/nginx/nginx.conf | grep -A 10 "/monitor/ws"

# Check nginx error logs
docker logs fix-docker-nginx-1 | grep -i "websocket\|upgrade"
```

**Solutions**:
- Verify nginx has WebSocket proxy config
- Check `location = /monitor/ws` is before regex locations
- Ensure upgrade headers are set correctly

---

### Filtering Not Working

**Symptom**: Clicking container filter buttons doesn't filter data

**Diagnosis**:
```bash
# Check if container_id is in data
curl http://localhost:11235/monitor/requests | jq '.completed[0].container_id'

# Verify container mapping in browser console
# Open browser console and check: containerMapping
```

**Solutions**:
- Ensure all data has `container_id` field
- Check JavaScript console for errors
- Rebuild image if backend changes weren't applied

---

### Load Balancing Issues

**Symptom**: All requests going to one container

**Diagnosis**:
```bash
# Check nginx upstream config
docker exec fix-docker-nginx-1 cat /etc/nginx/nginx.conf | grep -A 5 "upstream crawl4ai"

# Monitor which container handles requests
docker logs fix-docker-crawl4ai-1 | grep "GET /crawl"
docker logs fix-docker-crawl4ai-2 | grep "GET /crawl"
docker logs fix-docker-crawl4ai-3 | grep "GET /crawl"
```

**Solutions**:
- Verify nginx upstream has no `ip_hash` for API endpoints
- Check if all containers are healthy
- Restart nginx: `docker restart fix-docker-nginx-1`

---

## Performance Considerations

### Redis Memory Usage

**Per Container** (approximate):
- Active requests: ~1KB × 10 = 10KB
- Completed requests: ~500B × 100 = 50KB
- Janitor events: ~200B × 100 = 20KB
- Errors: ~300B × 100 = 30KB
- Heartbeat: ~100B

**Total per container**: ~110KB

**For 10 containers**: ~1.1MB

**Recommendation**: Redis with 256MB is more than sufficient

---

### Container Resource Limits

**Recommended per container**:
```yaml
resources:
  limits:
    memory: 4G
    cpus: '2'
  reservations:
    memory: 1G
    cpus: '1'
```

**Considerations**:
- Each container runs permanent browser (~270MB)
- Hot pool browsers (~180MB each)
- Peak memory during crawls
- Adjust based on workload

---

### Scaling Guidelines

| Containers | Use Case | Expected Throughput |
|-----------|----------|---------------------|
| 1 | Development | ~10 req/min |
| 3 | Small production | ~30 req/min |
| 5 | Medium production | ~50 req/min |
| 10 | Large production | ~100 req/min |

**Bottlenecks**:
1. Redis throughput (unlikely with <1000 req/min)
2. Nginx connection limits (adjust worker_connections)
3. Host CPU/memory
4. Browser pool limits (adjust pool sizes)

---

## Security Considerations

### Redis Security

**Current Setup**: No authentication (internal network only)

**Production Recommendations**:
```yaml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}
  environment:
    - REDIS_PASSWORD=strong_password_here
```

Update containers:
```yaml
environment:
  - REDIS_HOST=redis
  - REDIS_PASSWORD=${REDIS_PASSWORD}
```

---

### Nginx Security

**Recommendations**:
- Enable rate limiting
- Add authentication for sensitive endpoints
- Use HTTPS with TLS certificates
- Restrict `/monitor` to internal IPs

**Example Rate Limiting**:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /crawl {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://crawl4ai_backend;
}
```

---

## Maintenance

### Backup Redis Data

```bash
# Create backup
docker exec fix-docker-redis-1 redis-cli BGSAVE

# Copy dump file
docker cp fix-docker-redis-1:/data/dump.rdb ./backup-$(date +%Y%m%d).rdb
```

### Cleanup Old Data

```bash
# Redis TTLs handle automatic cleanup
# Manual cleanup if needed:
docker exec fix-docker-redis-1 redis-cli KEYS "monitor:*:completed" | xargs redis-cli DEL
```

### Rolling Updates

```bash
# Update one container at a time
docker compose up -d --no-deps --scale crawl4ai=3 crawl4ai

# Or rebuild and rolling restart
docker compose build crawl4ai
docker compose up -d --no-deps --scale crawl4ai=3 crawl4ai
```

---

## Appendix

### File Locations

```
deploy/docker/
├── server.py                          # Main FastAPI server
├── monitor.py                         # Monitoring stats with Redis
├── monitor_routes.py                  # Monitor API endpoints
├── utils.py                           # get_container_id(), detect_deployment_mode()
├── static/monitor/index.html          # Dashboard UI
├── supervisord.conf                   # Process manager config
└── requirements.txt                   # Python dependencies

crawl4ai/templates/
├── docker-compose.template.yml        # Docker Compose template
└── nginx.conf.template                # Nginx configuration

docker-compose.yml                     # Active compose file
Dockerfile                             # Container image definition
```

### API Response Examples

**GET /monitor/containers**:
```json
{
  "mode": "compose",
  "container_id": "b790d0b6c9d4",
  "containers": [
    {"id": "b790d0b6c9d4", "hostname": "b790d0b6c9d4", "healthy": true},
    {"id": "f899b55bd5f5", "hostname": "f899b55bd5f5", "healthy": true},
    {"id": "076a35479dd9", "hostname": "076a35479dd9", "healthy": true}
  ],
  "count": 3
}
```

**GET /monitor/requests**:
```json
{
  "active": [],
  "completed": [
    {
      "id": "req_26d1cbf8",
      "endpoint": "/crawl",
      "url": "https://httpbin.org/html",
      "container_id": "b790d0b6c9d4",
      "elapsed": 2.66,
      "success": true,
      "status_code": 200
    }
  ]
}
```

---

## Changelog

### Version 0.7.4

- Added Redis aggregation for multi-container support
- Implemented container heartbeat discovery
- Added per-container filtering in dashboard
- Updated nginx config for WebSocket proxy
- Added infrastructure monitoring card

---

**Document Version**: 1.0
**Last Updated**: 2025-01-18
**Author**: Crawl4AI Team
