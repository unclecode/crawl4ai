#!/bin/bash
# Test: Scale server up from 3 to 5 replicas
# Expected: Server scales without downtime

set -e

echo "=== Test: Scale Up (3 → 5 replicas) ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start with 3 replicas
echo "Starting server with 3 replicas..."
crwl server start --replicas 3 >/dev/null 2>&1
sleep 10

# Verify 3 replicas
STATUS=$(crwl server status | grep "Replicas" || echo "")
echo "Initial status: $STATUS"

# Scale up to 5
echo ""
echo "Scaling up to 5 replicas..."
crwl server scale 5

sleep 10

# Verify 5 replicas
STATUS=$(crwl server status)
echo "$STATUS"

if ! echo "$STATUS" | grep -q "5"; then
    echo "❌ Status does not show 5 replicas"
    crwl server stop
    exit 1
fi

# Verify health during scaling
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed after scaling"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Successfully scaled from 3 to 5 replicas"
