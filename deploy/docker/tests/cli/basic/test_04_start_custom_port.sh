#!/bin/bash
# Test: Start server with custom port
# Expected: Server starts on port 8080 instead of default 11235

set -e

echo "=== Test: Start Server with Custom Port ==="
echo "Expected: Server on port 8080"
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start on custom port
echo "Starting server on port 8080..."
crwl server start --port 8080

sleep 5

# Check health on custom port
echo "Checking health on port 8080..."
HEALTH=$(curl -s http://localhost:8080/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed on port 8080: $HEALTH"
    crwl server stop
    exit 1
fi

# Verify default port is NOT responding
echo "Verifying port 11235 is not in use..."
if curl -s http://localhost:11235/health > /dev/null 2>&1; then
    echo "❌ Server is also running on default port 11235"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop

echo ""
echo "✅ Test passed: Server started on custom port 8080"
