#!/bin/bash
# Test: Stop server command
# Expected: Server stops cleanly and port becomes available

set -e

echo "=== Test: Stop Server Command ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Start server first
echo "Starting server..."
crwl server start >/dev/null 2>&1
sleep 5

# Verify running
echo "Verifying server is running..."
if ! curl -s http://localhost:11235/health > /dev/null 2>&1; then
    echo "❌ Server is not running before stop"
    exit 1
fi

# Stop server
echo "Stopping server..."
crwl server stop

# Verify stopped
echo "Verifying server is stopped..."
sleep 3
if curl -s http://localhost:11235/health > /dev/null 2>&1; then
    echo "❌ Server is still responding after stop"
    exit 1
fi

# Check status shows not running
STATUS=$(crwl server status | grep "No server" || echo "RUNNING")
if [[ "$STATUS" == "RUNNING" ]]; then
    echo "❌ Status still shows server as running"
    exit 1
fi

echo ""
echo "✅ Test passed: Server stopped cleanly"
