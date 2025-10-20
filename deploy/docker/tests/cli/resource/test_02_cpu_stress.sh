#!/bin/bash
# Test: CPU usage under concurrent load
# Expected: Server handles concurrent requests without errors

set -e

echo "=== Test: CPU Stress Test ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start server with 3 replicas for better load distribution
echo "Starting server with 3 replicas..."
crwl server start --replicas 3 >/dev/null 2>&1
sleep 12

# Get baseline CPU
echo "Checking baseline container stats..."
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
  --filter "name=crawl4ai" 2>/dev/null || echo "Unable to get container stats"

# Send concurrent requests
echo ""
echo "Sending 10 concurrent requests..."
for i in {1..10}; do
    curl -s -X POST http://localhost:11235/crawl \
      -H "Content-Type: application/json" \
      -d "{\"urls\": [\"https://httpbin.org/html?req=$i\"], \"crawler_config\": {}}" > /dev/null &
done

# Wait for all requests to complete
echo "Waiting for requests to complete..."
wait

# Check stats after load
echo ""
echo "Container stats after load:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
  --filter "name=crawl4ai" 2>/dev/null || echo "Unable to get container stats"

# Verify health
echo ""
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed after CPU stress"
    crwl server stop
    exit 1
fi

# Cleanup
echo ""
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Server handled concurrent load successfully"
