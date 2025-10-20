#!/bin/bash
# Test: Start server with multiple replicas
# Expected: Server starts with 3 replicas in compose mode

set -e

echo "=== Test: Start Server with 3 Replicas ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start with 3 replicas
echo "Starting server with 3 replicas..."
crwl server start --replicas 3

sleep 10

# Check status shows 3 replicas
echo "Checking status..."
STATUS_OUTPUT=$(crwl server status)
echo "$STATUS_OUTPUT"

if ! echo "$STATUS_OUTPUT" | grep -q "3"; then
    echo "❌ Status does not show 3 replicas"
    crwl server stop
    exit 1
fi

# Check health endpoint
echo "Checking health endpoint..."
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed"
    crwl server stop
    exit 1
fi

# Check container discovery (should show 3 containers eventually)
echo "Checking container discovery..."
sleep 5  # Wait for heartbeats
CONTAINERS=$(curl -s http://localhost:11235/monitor/containers | jq -r '.count' 2>/dev/null || echo "0")
echo "Container count: $CONTAINERS"

# Cleanup
echo "Cleaning up..."
crwl server stop

echo ""
echo "✅ Test passed: Server started with 3 replicas"
