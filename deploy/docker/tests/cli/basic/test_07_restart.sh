#!/bin/bash
# Test: Restart server command
# Expected: Server restarts with same configuration

set -e

echo "=== Test: Restart Server Command ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Start server with specific config
echo "Starting server with 2 replicas..."
crwl server start --replicas 2 >/dev/null 2>&1
sleep 8

# Get initial container ID
echo "Getting initial state..."
INITIAL_STATUS=$(crwl server status)
echo "$INITIAL_STATUS"

# Restart
echo ""
echo "Restarting server..."
crwl server restart

sleep 8

# Check status after restart
echo "Checking status after restart..."
RESTART_STATUS=$(crwl server status)
echo "$RESTART_STATUS"

# Verify still has 2 replicas
if ! echo "$RESTART_STATUS" | grep -q "2"; then
    echo "❌ Replica count not preserved after restart"
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
echo "✅ Test passed: Server restarted with preserved configuration"
