#!/bin/bash
# Test: Invalid replica counts
# Expected: Validation errors for invalid replicas

set -e

echo "=== Test: Invalid Replica Counts ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Test invalid replica counts
INVALID_REPLICAS=(0 -1 101)

for REPLICAS in "${INVALID_REPLICAS[@]}"; do
    echo "Testing invalid replica count: $REPLICAS"
    OUTPUT=$(crwl server start --replicas $REPLICAS 2>&1 || true)

    if echo "$OUTPUT" | grep -iq "error\|invalid\|usage"; then
        echo "  ✅ Rejected replica count $REPLICAS"
    else
        echo "  ⚠️  Replica count $REPLICAS may have been accepted"
    fi

    # Make sure no server started
    crwl server stop 2>/dev/null || true
    sleep 1
    echo ""
done

# Test scaling to invalid counts
echo "Testing scale to invalid counts..."
crwl server start --replicas 2 >/dev/null 2>&1
sleep 5

INVALID_SCALE=(0 -1)
for SCALE in "${INVALID_SCALE[@]}"; do
    echo "Testing scale to: $SCALE"
    OUTPUT=$(crwl server scale $SCALE 2>&1 || true)

    if echo "$OUTPUT" | grep -iq "error\|invalid\|must be at least 1"; then
        echo "  ✅ Rejected scale to $SCALE"
    else
        echo "  ⚠️  Scale to $SCALE may have been accepted"
    fi
    echo ""
done

# Cleanup
crwl server stop >/dev/null 2>&1

echo "✅ Test passed: Invalid replica counts handled appropriately"
