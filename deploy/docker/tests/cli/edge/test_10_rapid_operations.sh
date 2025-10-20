#!/bin/bash
# Test: Rapid start/stop/restart operations
# Expected: System handles rapid operations without corruption

set -e

echo "=== Test: Rapid Operations ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Test 1: Rapid start/stop
echo "Test 1: Rapid start/stop cycles..."
for i in {1..3}; do
    echo "  Cycle $i/3..."
    crwl server start >/dev/null 2>&1
    sleep 3
    crwl server stop >/dev/null 2>&1
    sleep 2
done
echo "  ✅ Completed rapid start/stop cycles"

# Test 2: Restart immediately after start
echo ""
echo "Test 2: Restart immediately after start..."
crwl server start >/dev/null 2>&1
sleep 3
crwl server restart >/dev/null 2>&1
sleep 5

HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "  ❌ Health check failed after rapid restart"
    crwl server stop
    exit 1
fi
echo "  ✅ Rapid restart successful"

# Test 3: Multiple status checks
echo ""
echo "Test 3: Multiple rapid status checks..."
for i in {1..5}; do
    crwl server status >/dev/null 2>&1 || echo "  ⚠️  Status check $i failed"
done
echo "  ✅ Multiple status checks completed"

# Test 4: Stop and immediate start
echo ""
echo "Test 4: Stop and immediate start..."
crwl server stop >/dev/null 2>&1
sleep 2
crwl server start >/dev/null 2>&1
sleep 5

HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "  ❌ Health check failed after stop/start"
    crwl server stop
    exit 1
fi
echo "  ✅ Stop/immediate start successful"

# Cleanup
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: System handles rapid operations correctly"
