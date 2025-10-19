# Crawl4AI DevOps Agent Context

## Service Overview
**Crawl4AI**: Browser-based web crawling service with AI extraction. Docker deployment with horizontal scaling (1-N containers), Redis coordination, Nginx load balancing.

## Architecture Quick Reference

```
Client → Nginx:11235 → [crawl4ai-1, crawl4ai-2, ...crawl4ai-N] ← Redis
                              ↓
                         Monitor Dashboard
```

**Components:**
- **Nginx**: Load balancer (round-robin API, sticky monitoring)
- **Crawl4AI containers**: FastAPI + Playwright browsers
- **Redis**: Container discovery (heartbeats 30s), monitoring data aggregation
- **Monitor**: Real-time dashboard at `/dashboard`

## CLI Commands

### Start/Stop
```bash
crwl server start [-r N] [--port P] [--mode auto|single|swarm|compose] [--env-file F] [--image I]
crwl server stop [--remove-volumes]
crwl server restart [-r N]
```

### Management
```bash
crwl server status        # Show mode, replicas, port, uptime
crwl server scale N       # Live scaling (Swarm/Compose only)
crwl server logs [-f] [--tail N]
```

**Defaults**: replicas=1, port=11235, mode=auto, image=unclecode/crawl4ai:latest

## Deployment Modes

| Replicas | Mode | Load Balancer | Use Case |
|----------|------|---------------|----------|
| N=1 | single | None | Dev/testing |
| N>1 | swarm | Built-in | Production (if `docker swarm init` done) |
| N>1 | compose | Nginx | Production (fallback) |

**Mode Detection** (when mode=auto):
1. If N=1 → single
2. If N>1 & Swarm active → swarm
3. If N>1 & Swarm inactive → compose

## File Locations

```
~/.crawl4ai/server/
├── state.json              # Current deployment state
├── docker-compose.yml      # Generated compose file
└── nginx.conf              # Generated nginx config

/app/                       # Inside container
├── deploy/docker/server.py
├── deploy/docker/monitor.py
├── deploy/docker/static/monitor/index.html
└── crawler_pool.py         # Browser pool (PERMANENT, HOT_POOL, COLD_POOL)
```

## Monitoring & Troubleshooting

### Health Checks
```bash
curl http://localhost:11235/health              # Service health
curl http://localhost:11235/monitor/containers  # Container discovery
curl http://localhost:11235/monitor/requests    # Aggregated requests
```

### Dashboard
- URL: `http://localhost:11235/dashboard/`
- Features: Container filtering (All/C-1/C-2/C-3), real-time WebSocket, timeline charts
- WebSocket: `/monitor/ws` (sticky sessions)

### Common Issues

**No containers showing in dashboard:**
```bash
docker exec <redis-container> redis-cli SMEMBERS monitor:active_containers
docker exec <redis-container> redis-cli KEYS "monitor:heartbeat:*"
```
Wait 30s for heartbeat registration.

**Load balancing not working:**
```bash
docker exec <nginx-container> cat /etc/nginx/nginx.conf | grep upstream
docker logs <nginx-container> | grep error
```
Check Nginx upstream has no `ip_hash` for API endpoints.

**Redis connection errors:**
```bash
docker logs <crawl4ai-container> | grep -i redis
docker exec <crawl4ai-container> ping redis
```
Verify REDIS_HOST=redis, REDIS_PORT=6379.

**Containers not scaling:**
```bash
# Swarm
docker service ls
docker service ps crawl4ai

# Compose
docker compose -f ~/.crawl4ai/server/docker-compose.yml ps
docker compose -f ~/.crawl4ai/server/docker-compose.yml up -d --scale crawl4ai=N
```

### Redis Data Structure
```
monitor:active_containers              # SET: {container_ids}
monitor:heartbeat:{cid}                # STRING: {id, hostname, last_seen} TTL=60s
monitor:{cid}:active_requests          # STRING: JSON list, TTL=5min
monitor:{cid}:completed                # STRING: JSON list, TTL=1h
monitor:{cid}:janitor                  # STRING: JSON list, TTL=1h
monitor:{cid}:errors                   # STRING: JSON list, TTL=1h
monitor:endpoint_stats                 # STRING: JSON aggregate, TTL=24h
```

## Environment Variables

### Required for Multi-LLM
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=...
GROQ_API_KEY=...
TOGETHER_API_KEY=...
MISTRAL_API_KEY=...
GEMINI_API_TOKEN=...
```

### Redis Configuration (Optional)
```bash
REDIS_HOST=redis                       # Default: redis
REDIS_PORT=6379                        # Default: 6379
REDIS_TTL_ACTIVE_REQUESTS=300          # Default: 5min
REDIS_TTL_COMPLETED_REQUESTS=3600      # Default: 1h
REDIS_TTL_JANITOR_EVENTS=3600          # Default: 1h
REDIS_TTL_ERRORS=3600                  # Default: 1h
REDIS_TTL_ENDPOINT_STATS=86400         # Default: 24h
REDIS_TTL_HEARTBEAT=60                 # Default: 1min
```

## API Endpoints

### Core API
- `POST /crawl` - Crawl URL (load-balanced)
- `POST /batch` - Batch crawl (load-balanced)
- `GET /health` - Health check (load-balanced)

### Monitor API (Aggregated from all containers)
- `GET /monitor/health` - Local container health
- `GET /monitor/containers` - All active containers
- `GET /monitor/requests` - All requests (active + completed)
- `GET /monitor/browsers` - Browser pool status (local only)
- `GET /monitor/logs/janitor` - Janitor cleanup events
- `GET /monitor/logs/errors` - Error logs
- `GET /monitor/endpoints/stats` - Endpoint analytics
- `WS /monitor/ws` - Real-time updates (aggregated)

### Control Actions
- `POST /monitor/actions/cleanup` - Force browser cleanup
- `POST /monitor/actions/kill_browser` - Kill specific browser
- `POST /monitor/actions/restart_browser` - Restart browser
- `POST /monitor/stats/reset` - Reset endpoint counters

## Docker Commands Reference

### Inspection
```bash
# List containers
docker ps --filter "name=crawl4ai"

# Container logs
docker logs <container-id> -f --tail 100

# Redis CLI
docker exec -it <redis-container> redis-cli
KEYS monitor:*
SMEMBERS monitor:active_containers
GET monitor:<cid>:completed
TTL monitor:heartbeat:<cid>

# Nginx config
docker exec <nginx-container> cat /etc/nginx/nginx.conf

# Container stats
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Compose Operations
```bash
# Scale
docker compose -f ~/.crawl4ai/server/docker-compose.yml up -d --scale crawl4ai=5

# Restart service
docker compose -f ~/.crawl4ai/server/docker-compose.yml restart crawl4ai

# View services
docker compose -f ~/.crawl4ai/server/docker-compose.yml ps
```

### Swarm Operations
```bash
# Initialize Swarm
docker swarm init

# Scale service
docker service scale crawl4ai=5

# Service info
docker service ls
docker service ps crawl4ai --no-trunc

# Service logs
docker service logs crawl4ai --tail 100 -f
```

## Performance & Scaling

### Resource Recommendations
| Containers | Memory/Container | Total Memory | Use Case |
|------------|-----------------|--------------|----------|
| 1 | 4GB | 4GB | Development |
| 3 | 4GB | 12GB | Small prod |
| 5 | 4GB | 20GB | Medium prod |
| 10 | 4GB | 40GB | Large prod |

**Expected Throughput**: ~10 req/min per container (depends on crawl complexity)

### Scaling Guidelines
- **Horizontal**: Add replicas (`crwl server scale N`)
- **Vertical**: Adjust `--memory 8G --cpus 4` in kwargs
- **Browser Pool**: Permanent (1) + Hot pool (adaptive) + Cold pool (cleanup by janitor)

### Redis Memory Usage
- **Per container**: ~110KB (requests + events + errors + heartbeat)
- **10 containers**: ~1.1MB
- **Recommendation**: 256MB Redis is sufficient for <100 containers

## Security Notes

### Input Validation
All CLI inputs validated:
- Image name: alphanumeric + `.-/:_@` only, max 256 chars
- Port: 1-65535
- Replicas: 1-100
- Env file: must exist and be readable
- Container IDs: alphanumeric + `-_` only (prevents Redis injection)

### Network Security
- Nginx forwards to internal `crawl4ai` service (Docker network)
- Monitor endpoints have NO authentication (add MONITOR_TOKEN env for security)
- Redis is internal-only (no external port)

### Recommended Production Setup
```bash
# Add authentication
export MONITOR_TOKEN="your-secret-token"

# Use Redis password
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}

# Enable rate limiting in Nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

## Common User Scenarios

### Scenario 1: Fresh Deployment
```bash
crwl server start --replicas 3 --env-file .env
# Wait for health check, then access http://localhost:11235/health
```

### Scenario 2: Scaling Under Load
```bash
crwl server scale 10
# Live scaling, no downtime
```

### Scenario 3: Debugging Slow Requests
```bash
# Check dashboard
open http://localhost:11235/dashboard/

# Check container logs
docker logs <slowest-container-id> --tail 100

# Check browser pool
curl http://localhost:11235/monitor/browsers | jq
```

### Scenario 4: Redis Connection Issues
```bash
# Check Redis connectivity
docker exec <crawl4ai-container> nc -zv redis 6379

# Check Redis logs
docker logs <redis-container>

# Restart containers (triggers reconnect with retry logic)
crwl server restart
```

### Scenario 5: Container Not Appearing in Dashboard
```bash
# Wait 30s for heartbeat
sleep 30

# Check Redis
docker exec <redis-container> redis-cli SMEMBERS monitor:active_containers

# Check container logs for heartbeat errors
docker logs <missing-container> | grep -i heartbeat
```

## Code Context for Advanced Debugging

### Key Classes
- `MonitorStats` (monitor.py): Tracks stats, Redis persistence, heartbeat worker
- `ServerManager` (server_manager.py): CLI orchestration, mode detection
- Browser pool globals: `PERMANENT`, `HOT_POOL`, `COLD_POOL`, `LOCK` (crawler_pool.py)

### Critical Timeouts
- Browser pool lock: 2s timeout (prevents deadlock)
- WebSocket connection: 5s timeout
- Health check: 30-60s timeout
- Heartbeat interval: 30s, TTL: 60s
- Redis retry: 3 attempts, backoff: 0.5s/1s/2s
- Circuit breaker: 5 failures → 5min backoff

### State Transitions
```
NOT_RUNNING → STARTING → HEALTHY → RUNNING
                ↓           ↓
            FAILED      UNHEALTHY → STOPPED
```

State file: `~/.crawl4ai/server/state.json` (atomic writes, fcntl locking)

## Quick Diagnostic Commands

```bash
# Full system check
crwl server status
docker ps
curl http://localhost:11235/health
curl http://localhost:11235/monitor/containers | jq

# Redis check
docker exec <redis-container> redis-cli PING
docker exec <redis-container> redis-cli INFO stats

# Network check
docker network ls
docker network inspect <network-name>

# Logs check
docker logs <nginx-container> --tail 50
docker logs <redis-container> --tail 50
docker compose -f ~/.crawl4ai/server/docker-compose.yml logs --tail 100
```

## Agent Decision Tree

**User reports slow crawling:**
1. Check dashboard for active requests stuck → kill browser if >5min
2. Check browser pool status → cleanup if hot/cold pool >10
3. Check container CPU/memory → scale up if >80%
4. Check Redis latency → restart Redis if >100ms

**User reports missing containers:**
1. Wait 30s for heartbeat
2. Check `docker ps` vs dashboard count
3. Check Redis SMEMBERS monitor:active_containers
4. Check container logs for Redis connection errors
5. Verify REDIS_HOST/PORT env vars

**User reports 502/503 errors:**
1. Check Nginx logs for upstream errors
2. Check container health: `curl http://localhost:11235/health`
3. Check if all containers are healthy: `docker ps`
4. Restart Nginx: `docker restart <nginx-container>`

**User wants to update image:**
1. `crwl server stop`
2. `docker pull unclecode/crawl4ai:latest`
3. `crwl server start --replicas <previous-count>`

---

**Version**: Crawl4AI v0.7.4+
**Last Updated**: 2025-01-20
**AI Agent Note**: All commands, file paths, and Redis keys verified against codebase. Use exact syntax shown. For user-facing responses, translate technical details to plain language.
