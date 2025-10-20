#!/bin/bash
# Test: Try starting server when already running
# Expected: Error message indicating server is already running

set -e

echo "=== Test: Start When Already Running ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start server
echo "Starting server..."
crwl server start >/dev/null 2>&1
sleep 5

# Try to start again
echo ""
echo "Attempting to start server again (should fail)..."
OUTPUT=$(crwl server start 2>&1 || true)
echo "$OUTPUT"

# Verify error message
if echo "$OUTPUT" | grep -iq "already running"; then
    echo ""
    echo "✅ Test passed: Proper error for already running server"
else
    echo ""
    echo "❌ Test failed: Expected 'already running' error message"
    crwl server stop
    exit 1
fi

# Verify original server still running
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Original server is not running"
    crwl server stop
    exit 1
fi

# Cleanup
crwl server stop >/dev/null 2>&1
