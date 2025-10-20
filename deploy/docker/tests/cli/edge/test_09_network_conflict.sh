#!/bin/bash
# Test: Docker network name collision
# Expected: Handles existing network gracefully

set -e

echo "=== Test: Network Name Conflict ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Create a network with similar name
NETWORK_NAME="crawl4ai_test_net"
echo "Creating test network: $NETWORK_NAME..."
docker network create "$NETWORK_NAME" 2>/dev/null || echo "Network may already exist"

# Start server (should either use existing network or create its own)
echo ""
echo "Starting server..."
crwl server start >/dev/null 2>&1
sleep 5

# Verify server started successfully
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Server failed to start"
    docker network rm "$NETWORK_NAME" 2>/dev/null || true
    crwl server stop
    exit 1
fi

echo "✅ Server started successfully despite network conflict"

# Cleanup
crwl server stop >/dev/null 2>&1
sleep 2

# Remove test network
docker network rm "$NETWORK_NAME" 2>/dev/null || echo "Network already removed"

echo ""
echo "✅ Test passed: Handled network conflict gracefully"
