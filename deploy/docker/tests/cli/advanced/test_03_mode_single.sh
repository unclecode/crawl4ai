#!/bin/bash
# Test: Start server explicitly in single mode
# Expected: Server starts in single mode

set -e

echo "=== Test: Explicit Single Mode ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start in single mode explicitly
echo "Starting server in single mode..."
crwl server start --mode single

sleep 5

# Check mode
STATUS=$(crwl server status)
echo "$STATUS"

if ! echo "$STATUS" | grep -q "single"; then
    echo "❌ Mode is not 'single'"
    crwl server stop
    exit 1
fi

if ! echo "$STATUS" | grep -q "1"; then
    echo "❌ Should have 1 replica in single mode"
    crwl server stop
    exit 1
fi

# Verify health
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
echo "✅ Test passed: Server started in single mode"
