#!/bin/bash
# Test: Scale server down from 5 to 2 replicas
# Expected: Server scales down gracefully

set -e

echo "=== Test: Scale Down (5 → 2 replicas) ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start with 5 replicas
echo "Starting server with 5 replicas..."
crwl server start --replicas 5 >/dev/null 2>&1
sleep 12

# Verify 5 replicas
STATUS=$(crwl server status | grep "Replicas" || echo "")
echo "Initial status: $STATUS"

# Scale down to 2
echo ""
echo "Scaling down to 2 replicas..."
crwl server scale 2

sleep 8

# Verify 2 replicas
STATUS=$(crwl server status)
echo "$STATUS"

if ! echo "$STATUS" | grep -q "2"; then
    echo "❌ Status does not show 2 replicas"
    crwl server stop
    exit 1
fi

# Verify health after scaling down
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed after scaling down"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Successfully scaled down from 5 to 2 replicas"
