#!/bin/bash
# Test: Start with maximum replicas and stress test
# Expected: Server handles max replicas (10) and distributes load

set -e

echo "=== Test: Maximum Replicas Stress Test ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start with 10 replicas (max recommended)
echo "Starting server with 10 replicas..."
echo "This may take some time..."
crwl server start --replicas 10 >/dev/null 2>&1
sleep 20

# Verify status
echo "Checking status..."
STATUS=$(crwl server status)
if ! echo "$STATUS" | grep -q "10"; then
    echo "❌ Failed to start 10 replicas"
    crwl server stop
    exit 1
fi

# Wait for container discovery
echo ""
echo "Waiting for container discovery..."
sleep 10

# Check containers
CONTAINER_COUNT=$(curl -s http://localhost:11235/monitor/containers | jq -r '.count' 2>/dev/null || echo "0")
echo "Discovered containers: $CONTAINER_COUNT"

# Send burst of requests
echo ""
echo "Sending burst of 20 requests..."
for i in {1..20}; do
    curl -s -X POST http://localhost:11235/crawl \
      -H "Content-Type: application/json" \
      -d "{\"urls\": [\"https://httpbin.org/html?req=$i\"], \"crawler_config\": {}}" > /dev/null &
done

wait

# Check health after stress
echo ""
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed after max replica stress"
    crwl server stop
    exit 1
fi

# Check endpoint stats
echo ""
echo "Endpoint statistics:"
curl -s http://localhost:11235/monitor/endpoints/stats | jq '.' 2>/dev/null || echo "No stats available"

# Cleanup
echo ""
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Successfully stress tested with 10 replicas"
