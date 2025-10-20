#!/bin/bash
# Test: Operations when server is not running
# Expected: Appropriate error messages

set -e

echo "=== Test: Operations When Not Running ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Make sure nothing is running
crwl server stop 2>/dev/null || true
sleep 2

# Try status when not running
echo "Checking status when not running..."
OUTPUT=$(crwl server status 2>&1 || true)
echo "$OUTPUT"
echo ""

if ! echo "$OUTPUT" | grep -iq "no server"; then
    echo "❌ Status should indicate no server running"
    exit 1
fi

# Try stop when not running
echo "Trying to stop when not running..."
OUTPUT=$(crwl server stop 2>&1 || true)
echo "$OUTPUT"
echo ""

if ! echo "$OUTPUT" | grep -iq "no server\|not running"; then
    echo "❌ Stop should indicate no server running"
    exit 1
fi

# Try scale when not running
echo "Trying to scale when not running..."
OUTPUT=$(crwl server scale 3 2>&1 || true)
echo "$OUTPUT"
echo ""

if ! echo "$OUTPUT" | grep -iq "no server\|not running"; then
    echo "❌ Scale should indicate no server running"
    exit 1
fi

echo "✅ Test passed: Appropriate errors for operations when not running"
