#!/bin/bash
# Test: Restart server with different replica count
# Expected: Server restarts with new replica count

set -e

echo "=== Test: Restart with Scale Change ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start with 2 replicas
echo "Starting server with 2 replicas..."
crwl server start --replicas 2 >/dev/null 2>&1
sleep 8

# Verify 2 replicas
STATUS=$(crwl server status | grep "Replicas" || echo "")
echo "Initial: $STATUS"

# Restart with 4 replicas
echo ""
echo "Restarting with 4 replicas..."
crwl server restart --replicas 4

sleep 10

# Verify 4 replicas
STATUS=$(crwl server status)
echo "$STATUS"

if ! echo "$STATUS" | grep -q "4"; then
    echo "❌ Status does not show 4 replicas after restart"
    crwl server stop
    exit 1
fi

# Verify health
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed after restart"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Server restarted with new replica count"
