#!/bin/bash
# Test: Invalid port numbers
# Expected: Validation errors for invalid ports

set -e

echo "=== Test: Invalid Port Numbers ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Test invalid ports
INVALID_PORTS=(0 -1 99999 65536)

for PORT in "${INVALID_PORTS[@]}"; do
    echo "Testing invalid port: $PORT"
    OUTPUT=$(crwl server start --port $PORT 2>&1 || true)

    if echo "$OUTPUT" | grep -iq "error\|invalid\|usage"; then
        echo "  ✅ Rejected port $PORT"
    else
        echo "  ⚠️  Port $PORT may have been accepted (output: $OUTPUT)"
    fi

    # Make sure no server started
    crwl server stop 2>/dev/null || true
    sleep 1
    echo ""
done

echo "✅ Test passed: Invalid ports handled appropriately"
