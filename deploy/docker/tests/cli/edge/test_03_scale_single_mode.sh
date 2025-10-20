#!/bin/bash
# Test: Try to scale single container mode
# Expected: Error indicating single mode cannot be scaled

set -e

echo "=== Test: Scale Single Container Mode ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start in single mode
echo "Starting in single mode..."
crwl server start --mode single >/dev/null 2>&1
sleep 5

# Try to scale
echo ""
echo "Attempting to scale single mode (should fail)..."
OUTPUT=$(crwl server scale 3 2>&1 || true)
echo "$OUTPUT"
echo ""

# Verify error message
if echo "$OUTPUT" | grep -iq "single"; then
    echo "✅ Test passed: Proper error for scaling single mode"
else
    echo "❌ Test failed: Expected error about single mode"
    crwl server stop
    exit 1
fi

# Verify server still running
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Server is not running after failed scale"
    crwl server stop
    exit 1
fi

# Cleanup
crwl server stop >/dev/null 2>&1
