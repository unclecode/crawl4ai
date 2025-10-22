# Crawl4AI API Platform - Production Deployment PRD

**Version:** 1.0
**Target:** Digital Ocean Split Architecture
**Pattern:** API Gateway + Redis Queue + Browser Worker Pool

---

## 1. Architecture Overview

### 1.1 Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Internet Traffic                      │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              DO Load Balancer (HTTP/HTTPS)              │
│                   Port 80/443 → 11235                    │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼────────┐
│  API Server  │ │ API Server  │ │ API Server   │
│  Container   │ │ Container   │ │  Container   │
│  (1GB RAM)   │ │ (1GB RAM)   │ │  (1GB RAM)   │
│              │ │             │ │              │
│  FastAPI     │ │  FastAPI    │ │  FastAPI     │
│  + Auth      │ │  + Auth     │ │  + Auth      │
│  + Rate Lim  │ │  + Rate Lim │ │  + Rate Lim  │
│  NO Chromium │ │ NO Chromium │ │ NO Chromium  │
└───────┬──────┘ └──────┬──────┘ └─────┬────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              Managed Redis (Persistent)                  │
│           Queues: jobs, results, webhooks                │
│              Keys: sessions, rate_limits                 │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────────┬─────────────┐
        │               │                   │             │
┌───────▼──────┐ ┌──────▼──────┐ ┌─────────▼───┐ ┌───────▼──────┐
│   Worker 1   │ │  Worker 2   │ │  Worker 3   │ │  Worker N    │
│  (4GB RAM)   │ │  (4GB RAM)  │ │  (4GB RAM)  │ │  (4GB RAM)   │
│              │ │             │ │             │ │              │
│  Crawl4AI    │ │  Crawl4AI   │ │  Crawl4AI   │ │  Crawl4AI    │
│  + Chromium  │ │  + Chromium │ │  + Chromium │ │  + Chromium  │
│  (Job Puller)│ │ (Job Puller)│ │(Job Puller) │ │ (Job Puller) │
└──────────────┘ └─────────────┘ └─────────────┘ └──────────────┘
```

### 1.2 Data Flow

**Job Submission:**
```
Client → LB → API Server → Validate → Push to Redis Queue → Return task_id
```

**Job Execution:**
```
Worker → Pull from Queue → Execute Crawl → Store Result in Redis → Send Webhook
```

**Result Retrieval:**
```
Client → LB → API Server → Fetch from Redis → Return Result
```

---

## 2. Component Specifications

### 2.1 API Server Container

**Image:** `crawl4ai-api-server:v1`
**Base:** `python:3.12-slim`
**RAM:** 1GB
**CPU:** 1 vCPU

**Includes:**
- FastAPI server
- Redis client
- Auth/API key validation
- Rate limiting
- Webhook trigger logic
- NO browser, NO crawl4ai core

**Endpoints Supported:**
- `POST /crawl/job` - Queue job
- `GET /crawl/job/{task_id}` - Get result
- `POST /llm/job` - Queue LLM job
- `GET /llm/job/{task_id}` - Get LLM result
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /token` - JWT auth

**Excluded Endpoints:**
- `/crawl` (sync) - removed
- `/crawl/stream` - removed (use job pattern only)

**Environment Variables:**
```bash
REDIS_URL=redis://managed-redis:6379/0
REDIS_POOL_SIZE=50
API_KEY_HEADER=X-API-Key
JWT_SECRET=<secret>
RATE_LIMIT_DEFAULT=1000/minute
WEBHOOK_TIMEOUT=30
WORKER_COUNT=4
```

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies (NO playwright, NO chromium)
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy API server code only
COPY deploy/docker/api_server.py .
COPY deploy/docker/auth.py .
COPY deploy/docker/schemas.py .
COPY deploy/docker/utils.py .

EXPOSE 11235

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "11235", "--workers", "4"]
```

### 2.2 Browser Worker Container

**Image:** `crawl4ai-worker:v1`
**Base:** `python:3.12-slim`
**RAM:** 4GB
**CPU:** 2 vCPU

**Includes:**
- Crawl4AI library
- Chromium browser
- Redis client
- Job processor
- Webhook sender
- NO FastAPI server

**Worker Logic:**
```python
while True:
    # 1. Pull job from Redis queue (BLPOP)
    job = redis.blpop('crawl_queue', timeout=5)

    if job:
        task_id, job_data = parse_job(job)

        # 2. Execute crawl
        result = await execute_crawl(job_data)

        # 3. Store result
        redis.setex(f"result:{task_id}", 3600, json.dumps(result))

        # 4. Send webhook if configured
        if job_data.get('webhook_url'):
            await send_webhook(job_data['webhook_url'], task_id, result)

        # 5. Update metrics
        redis.incr('metrics:jobs_completed')
```

**Environment Variables:**
```bash
REDIS_URL=redis://managed-redis:6379/0
WORKER_ID=worker-{uuid}
MAX_CONCURRENT_JOBS=5
BROWSER_POOL_SIZE=3
RESULT_TTL=3600
WEBHOOK_RETRY_COUNT=5
LOG_LEVEL=INFO
```

**Dockerfile:**
```dockerfile
FROM unclecode/crawl4ai:latest

WORKDIR /app

# Install worker dependencies
COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

# Copy worker code
COPY deploy/docker/worker.py .
COPY deploy/docker/webhook.py .

# No EXPOSE needed (worker doesn't listen)

CMD ["python", "worker.py"]
```

---

## 3. Code Structure

### 3.1 New Files to Create

```
deploy/docker/
├── api_server.py          # NEW: Stripped-down API (job queue only)
├── worker.py              # NEW: Job processor
├── requirements-api.txt   # NEW: API dependencies
├── requirements-worker.txt # NEW: Worker dependencies
├── docker-compose.yml     # MODIFIED: Multi-service
├── Dockerfile.api         # NEW: API server image
├── Dockerfile.worker      # NEW: Worker image
└── deploy.sh             # NEW: DO deployment script
```

### 3.2 api_server.py Pseudocode

```python
from fastapi import FastAPI, Depends
from redis import asyncio as aioredis
import uuid
from schemas import CrawlJobPayload, WebhookConfig

app = FastAPI()
redis = aioredis.from_url(REDIS_URL)

@app.post("/crawl/job")
async def submit_job(payload: CrawlJobPayload, api_key: str = Depends(validate_api_key)):
    # 1. Validate API key and rate limit
    await check_rate_limit(api_key)

    # 2. Create task
    task_id = f"crawl_{uuid.uuid4().hex[:8]}"

    # 3. Push to queue
    job = {
        "task_id": task_id,
        "urls": payload.urls,
        "browser_config": payload.browser_config,
        "crawler_config": payload.crawler_config,
        "webhook_config": payload.webhook_config.dict() if payload.webhook_config else None,
        "created_at": datetime.utcnow().isoformat(),
        "api_key": api_key
    }

    await redis.rpush("crawl_queue", json.dumps(job))
    await redis.hset(f"task:{task_id}", mapping={
        "status": "queued",
        "created_at": job["created_at"],
        "api_key": api_key
    })

    return {"task_id": task_id, "status": "queued"}

@app.get("/crawl/job/{task_id}")
async def get_result(task_id: str, api_key: str = Depends(validate_api_key)):
    # 1. Check task ownership
    task_info = await redis.hgetall(f"task:{task_id}")
    if task_info.get("api_key") != api_key:
        raise HTTPException(403, "Access denied")

    # 2. Get result
    result = await redis.get(f"result:{task_id}")

    if not result:
        status = task_info.get("status", "unknown")
        return {"task_id": task_id, "status": status, "result": None}

    return json.loads(result)
```

### 3.3 worker.py Pseudocode

```python
import asyncio
from redis import asyncio as aioredis
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from webhook import WebhookDeliveryService

redis = aioredis.from_url(REDIS_URL)
webhook_service = WebhookDeliveryService(config)

async def process_job(job_data):
    task_id = job_data['task_id']

    try:
        # Update status
        await redis.hset(f"task:{task_id}", "status", "processing")

        # Execute crawl
        browser_config = BrowserConfig(**job_data.get('browser_config', {}))
        crawler_config = CrawlerRunConfig(**job_data.get('crawler_config', {}))

        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun_many(
                urls=job_data['urls'],
                config=crawler_config
            )

        # Prepare result
        result = {
            "task_id": task_id,
            "status": "completed",
            "results": [r.model_dump() for r in results],
            "completed_at": datetime.utcnow().isoformat()
        }

        # Store result (1 hour TTL)
        await redis.setex(f"result:{task_id}", 3600, json.dumps(result))
        await redis.hset(f"task:{task_id}", "status", "completed")

        # Send webhook
        if job_data.get('webhook_config'):
            await webhook_service.notify_job_completion(
                task_id=task_id,
                task_type="crawl",
                status="completed",
                urls=job_data['urls'],
                webhook_config=job_data['webhook_config'],
                result=result
            )

        logger.info(f"Job {task_id} completed")

    except Exception as e:
        # Handle failure
        await redis.hset(f"task:{task_id}", mapping={
            "status": "failed",
            "error": str(e)
        })

        if job_data.get('webhook_config'):
            await webhook_service.notify_job_completion(
                task_id=task_id,
                task_type="crawl",
                status="failed",
                urls=job_data['urls'],
                webhook_config=job_data['webhook_config'],
                error=str(e)
            )

        logger.error(f"Job {task_id} failed: {e}")

async def worker_loop():
    logger.info(f"Worker {WORKER_ID} started")

    while True:
        try:
            # Blocking pop from queue (5s timeout)
            job = await redis.blpop("crawl_queue", timeout=5)

            if job:
                _, job_json = job
                job_data = json.loads(job_json)
                await process_job(job_data)

        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(worker_loop())
```

---

## 4. Digital Ocean Infrastructure

### 4.1 Resource Requirements

**Load Balancer:**
- Type: Application Load Balancer
- Algorithm: Round Robin
- Health Check: `/health` every 10s
- SSL: Let's Encrypt auto-cert
- Cost: $12/month

**API Servers:**
- Droplet Size: Basic (1GB RAM, 1 vCPU) = $6/month
- Count: 2 minimum, 5 maximum
- OS: Ubuntu 22.04 LTS
- Auto-scale based on: CPU > 70% or Request count

**Browser Workers:**
- Droplet Size: Basic (4GB RAM, 2 vCPU) = $24/month
- Count: 2 minimum, 20 maximum
- OS: Ubuntu 22.04 LTS
- Auto-scale based on: Redis queue depth > 50

**Managed Redis:**
- Plan: Basic (1GB RAM)
- Persistence: Yes
- Backups: Daily
- Cost: $15/month

**Total Base Cost:** $12 + (2×$6) + (2×$24) + $15 = **$87/month**

### 4.2 DO CLI Setup

**Install CLI:**
```bash
# Install doctl
cd ~
wget https://github.com/digitalocean/doctl/releases/download/v1.98.1/doctl-1.98.1-linux-amd64.tar.gz
tar xf doctl-*.tar.gz
sudo mv doctl /usr/local/bin
doctl auth init
```

**Create SSH Key:**
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/crawl4ai_deploy
doctl compute ssh-key import crawl4ai-key --public-key-file ~/.ssh/crawl4ai_deploy.pub
```

---

## 5. Deployment Scripts

### 5.1 Build and Push Images

**Script: `build_and_push.sh`**

```bash
#!/bin/bash
set -e

VERSION="v1.0.0"
REGISTRY="registry.digitalocean.com/crawl4ai"

echo "Building API Server image..."
docker build -f Dockerfile.api -t $REGISTRY/api-server:$VERSION .
docker push $REGISTRY/api-server:$VERSION

echo "Building Worker image..."
docker build -f Dockerfile.worker -t $REGISTRY/worker:$VERSION .
docker push $REGISTRY/worker:$VERSION

echo "Tagging latest..."
docker tag $REGISTRY/api-server:$VERSION $REGISTRY/api-server:latest
docker tag $REGISTRY/worker:$VERSION $REGISTRY/worker:latest

docker push $REGISTRY/api-server:latest
docker push $REGISTRY/worker:latest

echo "✅ Images built and pushed"
```

### 5.2 Infrastructure Provisioning

**Script: `deploy_infrastructure.sh`**

```bash
#!/bin/bash
set -e

PROJECT_NAME="crawl4ai-prod"
REGION="nyc3"

# 1. Create VPC
echo "Creating VPC..."
VPC_ID=$(doctl vpcs create \
  --name $PROJECT_NAME-vpc \
  --region $REGION \
  --ip-range "10.100.0.0/16" \
  --format ID --no-header)

echo "VPC ID: $VPC_ID"

# 2. Create Managed Redis
echo "Creating Managed Redis..."
REDIS_ID=$(doctl databases create $PROJECT_NAME-redis \
  --engine redis \
  --region $REGION \
  --size db-s-1vcpu-1gb \
  --version 7 \
  --format ID --no-header)

echo "Waiting for Redis to be ready..."
doctl databases wait $REDIS_ID

REDIS_HOST=$(doctl databases get $REDIS_ID --format PrivateHost --no-header)
REDIS_PORT=$(doctl databases get $REDIS_ID --format Port --no-header)
REDIS_PASSWORD=$(doctl databases get $REDIS_ID --format Password --no-header)

echo "Redis: $REDIS_HOST:$REDIS_PORT"

# 3. Create API Server Droplets
echo "Creating API Server droplets..."
for i in {1..2}; do
  doctl compute droplet create api-server-$i \
    --image docker-20-04 \
    --size s-1vcpu-1gb \
    --region $REGION \
    --vpc-uuid $VPC_ID \
    --tag-names api-server,production \
    --user-data-file cloud-init-api.yml \
    --wait
done

# 4. Create Worker Droplets
echo "Creating Worker droplets..."
for i in {1..2}; do
  doctl compute droplet create worker-$i \
    --image docker-20-04 \
    --size s-2vcpu-4gb \
    --region $REGION \
    --vpc-uuid $VPC_ID \
    --tag-names worker,production \
    --user-data-file cloud-init-worker.yml \
    --wait
done

# 5. Create Load Balancer
echo "Creating Load Balancer..."
API_IPS=$(doctl compute droplet list --tag-name api-server --format PublicIPv4 --no-header | tr '\n' ',')

doctl compute load-balancer create \
  --name $PROJECT_NAME-lb \
  --region $REGION \
  --forwarding-rules entry_protocol:https,entry_port:443,target_protocol:http,target_port:11235,certificate_id:auto \
  --health-check protocol:http,port:11235,path:/health,check_interval_seconds:10 \
  --tag-name api-server

echo "✅ Infrastructure deployed"
echo ""
echo "REDIS_URL=redis://:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT/0"
```

### 5.3 Cloud-Init Scripts

**File: `cloud-init-api.yml`**

```yaml
#cloud-config
packages:
  - docker.io
  - docker-compose

write_files:
  - path: /etc/systemd/system/crawl4ai-api.service
    content: |
      [Unit]
      Description=Crawl4AI API Server
      After=docker.service
      Requires=docker.service

      [Service]
      Environment="REDIS_URL=redis://:PASSWORD@HOST:PORT/0"
      ExecStartPre=/usr/bin/docker pull registry.digitalocean.com/crawl4ai/api-server:latest
      ExecStart=/usr/bin/docker run --rm --name api-server \
        -p 11235:11235 \
        -e REDIS_URL=${REDIS_URL} \
        registry.digitalocean.com/crawl4ai/api-server:latest
      ExecStop=/usr/bin/docker stop api-server
      Restart=always

      [Install]
      WantedBy=multi-user.target

runcmd:
  - systemctl daemon-reload
  - systemctl enable crawl4ai-api
  - systemctl start crawl4ai-api
```

**File: `cloud-init-worker.yml`**

```yaml
#cloud-config
packages:
  - docker.io

write_files:
  - path: /etc/systemd/system/crawl4ai-worker.service
    content: |
      [Unit]
      Description=Crawl4AI Worker
      After=docker.service
      Requires=docker.service

      [Service]
      Environment="REDIS_URL=redis://:PASSWORD@HOST:PORT/0"
      Environment="WORKER_ID=%H"
      ExecStartPre=/usr/bin/docker pull registry.digitalocean.com/crawl4ai/worker:latest
      ExecStart=/usr/bin/docker run --rm --name worker \
        --shm-size=2g \
        -e REDIS_URL=${REDIS_URL} \
        -e WORKER_ID=${WORKER_ID} \
        registry.digitalocean.com/crawl4ai/worker:latest
      ExecStop=/usr/bin/docker stop worker
      Restart=always

      [Install]
      WantedBy=multi-user.target

runcmd:
  - systemctl daemon-reload
  - systemctl enable crawl4ai-worker
  - systemctl start crawl4ai-worker
```

---

## 6. Auto-Scaling System

### 6.1 Scaling Logic

**Metrics to Monitor:**
```python
# Queue depth (Redis)
queue_depth = redis.llen("crawl_queue")

# Active workers
active_workers = len(doctl_list_droplets(tag="worker"))

# CPU usage (via DO API)
avg_cpu = get_avg_cpu(droplets)
```

**Scaling Rules:**

| Metric | Threshold | Action |
|--------|-----------|--------|
| Queue depth > 100 | Workers < 20 | Add 2 workers |
| Queue depth > 500 | Workers < 20 | Add 5 workers |
| Queue depth < 20 | Workers > 2 | Remove 1 worker |
| API CPU > 80% | API servers < 5 | Add 1 API server |
| API CPU < 30% | API servers > 2 | Remove 1 API server |

**Cooldown:** 5 minutes between scaling actions

### 6.2 Auto-Scaler Script

**File: `autoscaler.py`**

```python
#!/usr/bin/env python3
import redis
import digitalocean
import time
from datetime import datetime, timedelta

REDIS_URL = "redis://:pass@host:port/0"
DO_TOKEN = "your_token"
MIN_WORKERS = 2
MAX_WORKERS = 20
MIN_API = 2
MAX_API = 5
COOLDOWN_MINUTES = 5

redis_client = redis.from_url(REDIS_URL)
manager = digitalocean.Manager(token=DO_TOKEN)

last_scale_time = {}

def get_queue_depth():
    return redis_client.llen("crawl_queue")

def get_droplets_by_tag(tag):
    return [d for d in manager.get_all_droplets() if tag in d.tags]

def can_scale(component):
    last_time = last_scale_time.get(component)
    if not last_time:
        return True
    return datetime.now() - last_time > timedelta(minutes=COOLDOWN_MINUTES)

def scale_workers(count):
    if not can_scale("workers"):
        print("⏳ Cooldown active for workers")
        return

    if count > 0:
        print(f"➕ Adding {count} worker(s)")
        # Create droplets using snapshot or template
        for i in range(count):
            droplet = digitalocean.Droplet(
                token=DO_TOKEN,
                name=f"worker-{int(time.time())}-{i}",
                region='nyc3',
                image='docker-20-04',
                size_slug='s-2vcpu-4gb',
                tags=['worker', 'production', 'autoscaled'],
                user_data=open('cloud-init-worker.yml').read()
            )
            droplet.create()
    else:
        print(f"➖ Removing {abs(count)} worker(s)")
        workers = get_droplets_by_tag("autoscaled")
        for droplet in workers[:abs(count)]:
            droplet.destroy()

    last_scale_time["workers"] = datetime.now()

def autoscale_loop():
    print("🤖 Autoscaler started")

    while True:
        try:
            # Get metrics
            queue_depth = get_queue_depth()
            workers = get_droplets_by_tag("worker")
            worker_count = len(workers)

            print(f"📊 Queue: {queue_depth}, Workers: {worker_count}")

            # Scale workers based on queue
            if queue_depth > 500 and worker_count < MAX_WORKERS:
                scale_workers(5)
            elif queue_depth > 100 and worker_count < MAX_WORKERS:
                scale_workers(2)
            elif queue_depth < 20 and worker_count > MIN_WORKERS:
                scale_workers(-1)

            # Sleep 2 minutes
            time.sleep(120)

        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    autoscale_loop()
```

**Deploy as systemd service on control droplet:**

```bash
# /etc/systemd/system/autoscaler.service
[Unit]
Description=Crawl4AI Autoscaler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/crawl4ai
ExecStart=/usr/bin/python3 /opt/crawl4ai/autoscaler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 7. Monitoring & Observability

### 7.1 Metrics to Track

**Redis Metrics:**
```python
# Queue metrics
crawl_queue_depth = LLEN crawl_queue
jobs_completed_total = GET metrics:jobs_completed
jobs_failed_total = GET metrics:jobs_failed

# Performance metrics
avg_job_duration = GET metrics:avg_job_duration
webhook_success_rate = GET metrics:webhook_success_rate
```

**System Metrics (via DO API):**
- Droplet CPU usage
- Droplet memory usage
- Droplet network I/O
- Load balancer connections

**Application Metrics (Prometheus):**
```python
# In API server
from prometheus_client import Counter, Histogram

jobs_submitted = Counter('jobs_submitted_total', 'Total jobs submitted')
job_duration = Histogram('job_duration_seconds', 'Job execution time')
webhook_attempts = Counter('webhook_attempts_total', 'Webhook delivery attempts', ['status'])
```

### 7.2 Monitoring Stack

**Option 1: Managed (Recommended for Year 1)**
- DataDog: $15/host/month
- New Relic: $25/month
- Total: ~$100/month

**Option 2: Self-Hosted**
```yaml
# docker-compose-monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Dashboards to create:**
1. Queue depth over time
2. Worker utilization
3. Job success/failure rate
4. Response time p50/p95/p99
5. Webhook delivery rate
6. Cost per job

### 7.3 Alerting Rules

```yaml
# alerts.yml
groups:
  - name: crawl4ai
    interval: 1m
    rules:
      - alert: HighQueueDepth
        expr: crawl_queue_depth > 1000
        for: 5m
        annotations:
          summary: "Queue backing up"

      - alert: AllWorkersDown
        expr: count(up{job="worker"}) == 0
        for: 2m
        annotations:
          summary: "All workers are down"

      - alert: HighJobFailureRate
        expr: rate(jobs_failed_total[5m]) > 0.1
        for: 10m
        annotations:
          summary: "Job failure rate > 10%"
```

---

## 8. Testing Strategy

### 8.1 Local Testing

**Test Setup:**
```bash
# Start local stack
docker-compose up -d

# Submit test job
curl -X POST http://localhost:11235/crawl/job \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "webhook_config": {
      "webhook_url": "https://webhook.site/unique-id"
    }
  }'

# Check result
curl http://localhost:11235/crawl/job/{task_id}
```

**Test Cases:**
1. Single URL crawl
2. Multiple URLs (5, 10, 50)
3. Webhook delivery (success)
4. Webhook delivery (failure + retry)
5. Queue backlog handling
6. Worker failure recovery
7. Rate limiting
8. API key validation

### 8.2 Load Testing

**Script: `load_test.py`**

```python
import asyncio
import aiohttp
import time

async def submit_job(session, i):
    start = time.time()
    async with session.post(
        "https://api.crawl4ai.com/crawl/job",
        json={"urls": [f"https://example.com/?test={i}"]},
        headers={"X-API-Key": "test_key"}
    ) as resp:
        result = await resp.json()
        duration = time.time() - start
        return {"task_id": result["task_id"], "duration": duration}

async def load_test(concurrency=100, total=1000):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(total):
            tasks.append(submit_job(session, i))

            if len(tasks) >= concurrency:
                results = await asyncio.gather(*tasks)
                print(f"Submitted {len(results)} jobs")
                tasks = []

        if tasks:
            await asyncio.gather(*tasks)

# Run: python load_test.py
asyncio.run(load_test(concurrency=50, total=500))
```

**Metrics to collect:**
- Jobs/second throughput
- P50/P95/P99 latency
- Queue depth under load
- Worker utilization
- Error rate

**Target Performance:**
- Handle 1000 concurrent jobs
- P95 latency < 30s
- Error rate < 0.1%

---

## 9. Cost Optimization

### 9.1 Strategies

**Infrastructure:**
1. Use preemptible/spot droplets for workers (50% cheaper)
2. Aggressive auto-scaling down during low traffic
3. Shared Redis instead of dedicated per-env
4. Use CDN for static assets (CloudFlare free tier)

**Application:**
1. Cache common crawls (example.com, etc)
2. Batch similar jobs together
3. Smart browser pool reuse
4. Compress results before storing

**Pricing:**
```python
# Cost model
COST_PER_API_SERVER = 6  # per month
COST_PER_WORKER = 24     # per month
COST_REDIS = 15
COST_LB = 12

def calculate_cost(api_count, worker_count):
    return (
        api_count * COST_PER_API_SERVER +
        worker_count * COST_PER_WORKER +
        COST_REDIS +
        COST_LB
    )

# Base: 2 API + 2 Workers = $87/mo
# Peak: 5 API + 10 Workers = $297/mo
```

**Revenue Model:**
```python
# Charge customers based on usage
FREE_TIER = 100  # requests/month
STARTER_TIER = 5000  # $20/mo
PRO_TIER = 50000     # $100/mo

# Cost per 1000 requests at scale
avg_job_duration = 10  # seconds
worker_capacity = 6    # jobs/minute
cost_per_worker_hour = 24 / 30 / 24  # $0.033/hr

cost_per_1000_requests = (
    (1000 / worker_capacity / 60) * cost_per_worker_hour
)  # ~$0.92 per 1000 requests

# Charge $2 per 1000 = 54% margin
```

### 9.2 Cost Monitoring

**Track:**
- Cost per request
- Cost per customer
- Infrastructure utilization %
- Idle resource time

**Alert if:**
- Cost per request > $0.002
- Idle time > 30%
- Utilization < 50%

---

## 10. Security

### 10.1 API Key Management

**Storage:**
```python
# Redis schema
api_key:{key_hash} -> {
    "user_id": "uuid",
    "tier": "pro",
    "rate_limit": "1000/minute",
    "created_at": "timestamp",
    "active": true
}

# Rate limiting
rate_limit:{api_key}:{minute} -> request_count
```

**Validation:**
```python
async def validate_api_key(api_key: str):
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_data = await redis.hgetall(f"api_key:{key_hash}")

    if not key_data or not key_data.get("active"):
        raise HTTPException(401, "Invalid API key")

    return key_data
```

### 10.2 Network Security

**Firewall Rules:**
```bash
# API Servers
- Allow: 443 from LB
- Allow: 22 from bastion only
- Allow: 6379 to Redis (private network)
- Deny: all else

# Workers
- Allow: 6379 to Redis (private network)
- Allow: 22 from bastion only
- Deny: all else
```

**SSL/TLS:**
- LB: Auto SSL via Let's Encrypt
- Redis: TLS enabled
- Internal: VPC isolation (encryption in transit)

### 10.3 Secrets Management

**Use DO Secrets:**
```bash
doctl compute secret create redis-password --value "xxx"
doctl compute secret create jwt-secret --value "xxx"
```

**Inject into droplets:**
```yaml
#cloud-config
write_files:
  - path: /etc/crawl4ai/secrets.env
    content: |
      REDIS_PASSWORD={{.RedisPassword}}
      JWT_SECRET={{.JWTSecret}}
    permissions: '0600'
```

---

## 11. Deployment Checklist

### 11.1 Pre-Deployment

- [ ] Test Docker images locally
- [ ] Run integration tests
- [ ] Load test (1000 concurrent jobs)
- [ ] Verify webhook delivery
- [ ] Test auto-scaling logic
- [ ] Review security settings
- [ ] Set up monitoring
- [ ] Configure alerts
- [ ] Document API endpoints
- [ ] Create runbook

### 11.2 Deployment Steps

```bash
# 1. Build images
./build_and_push.sh

# 2. Deploy infrastructure
./deploy_infrastructure.sh

# 3. Verify health
doctl compute load-balancer list
curl https://api.crawl4ai.com/health

# 4. Submit test job
curl -X POST https://api.crawl4ai.com/crawl/job \
  -H "X-API-Key: test" \
  -d '{"urls": ["https://example.com"]}'

# 5. Monitor for 24 hours
watch -n 60 'doctl compute droplet list'
```

### 11.3 Post-Deployment

- [ ] Monitor queue depth for 24h
- [ ] Check error logs
- [ ] Verify webhook delivery rate
- [ ] Test auto-scaling (manual trigger)
- [ ] Validate cost metrics
- [ ] Run smoke tests every hour
- [ ] Customer beta testing

---

## 12. Rollback Plan

**If deployment fails:**

```bash
# 1. Switch LB to old droplets
doctl compute load-balancer update $LB_ID --droplet-ids $OLD_DROPLET_IDS

# 2. Scale down new droplets
doctl compute droplet delete $(doctl compute droplet list --tag-name new --format ID --no-header)

# 3. Restore Redis snapshot
doctl databases backups restore $REDIS_ID $BACKUP_ID

# 4. Investigate
tail -f /var/log/crawl4ai/*.log
```

---

## 13. Success Metrics (First 90 Days)

**Technical:**
- 99.5% uptime
- P95 latency < 30s
- <0.1% error rate
- Webhook delivery > 99%

**Business:**
- 100 API keys created
- 50K requests/month processed
- <$150/month infrastructure cost
- Cost per request < $0.002

**Scaling:**
- Auto-scaler working (0 manual interventions)
- Queue never exceeds 1000 depth
- Worker utilization > 60%
- API server utilization > 50%

---

## 14. Files Summary

**To Create:**
1. `deploy/docker/api_server.py` - Stripped API server
2. `deploy/docker/worker.py` - Job processor
3. `deploy/docker/Dockerfile.api` - API image
4. `deploy/docker/Dockerfile.worker` - Worker image
5. `deploy/docker/requirements-api.txt` - API deps
6. `deploy/docker/requirements-worker.txt` - Worker deps
7. `scripts/build_and_push.sh` - Build script
8. `scripts/deploy_infrastructure.sh` - Provision script
9. `scripts/autoscaler.py` - Auto-scaling daemon
10. `scripts/cloud-init-api.yml` - API droplet config
11. `scripts/cloud-init-worker.yml` - Worker droplet config
12. `tests/load_test.py` - Load testing
13. `docs/API.md` - API documentation
14. `docs/RUNBOOK.md` - Operations guide

**To Modify:**
1. Current `server.py` - Extract job queue logic
2. Current `job.py` - Simplify to queue only
3. Current `webhook.py` - Use as-is

---

## 15. Next Steps

**Week 1:**
- [ ] Create API server code
- [ ] Create worker code
- [ ] Build Docker images
- [ ] Test locally with docker-compose

**Week 2:**
- [ ] Deploy to DO staging
- [ ] Integration testing
- [ ] Load testing
- [ ] Fix bugs

**Week 3:**
- [ ] Deploy to production
- [ ] Monitor for 1 week
- [ ] Optimize based on metrics
- [ ] Beta customers

**Week 4:**
- [ ] Launch publicly
- [ ] Marketing
- [ ] Support setup
- [ ] Iterate

---

**END OF PRD**
