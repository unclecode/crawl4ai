#!/bin/bash
# Test: Start server with default settings
# Expected: Server starts with 1 replica on port 11235

set -e

echo "=== Test: Start Server with Defaults ==="
echo "Expected: 1 replica, port 11235, auto mode"
echo ""

# Activate virtual environment
# Navigate to project root and activate venv
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup any existing server
echo "Cleaning up any existing server..."
crwl server stop 2>/dev/null || true
sleep 2

# Start server with defaults
echo "Starting server with default settings..."
crwl server start

# Wait for server to be ready
echo "Waiting for server to be healthy..."
sleep 5

# Verify server is running
echo "Checking server status..."
STATUS=$(crwl server status | grep "Running" || echo "NOT_RUNNING")
if [[ "$STATUS" == "NOT_RUNNING" ]]; then
    echo "❌ Server failed to start"
    crwl server stop
    exit 1
fi

# Check health endpoint
echo "Checking health endpoint..."
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed: $HEALTH"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop

echo ""
echo "✅ Test passed: Server started with defaults and responded to health check"
