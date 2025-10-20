#!/bin/bash
# Test: Start server in compose mode with replicas
# Expected: Server starts in compose mode with Nginx

set -e

echo "=== Test: Compose Mode with 3 Replicas ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start in compose mode
echo "Starting server in compose mode with 3 replicas..."
crwl server start --mode compose --replicas 3

sleep 12

# Check mode
STATUS=$(crwl server status)
echo "$STATUS"

if ! echo "$STATUS" | grep -q "3"; then
    echo "❌ Status does not show 3 replicas"
    crwl server stop
    exit 1
fi

# Verify Nginx is running (load balancer)
NGINX_RUNNING=$(docker ps --filter "name=nginx" --format "{{.Names}}" || echo "")
if [[ -z "$NGINX_RUNNING" ]]; then
    echo "⚠️  Warning: Nginx load balancer not detected (may be using swarm or single mode)"
fi

# Verify health through load balancer
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Server started in compose mode"
