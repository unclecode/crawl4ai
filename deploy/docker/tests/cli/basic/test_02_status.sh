#!/bin/bash
# Test: Check server status command
# Expected: Shows running status with correct details

set -e

echo "=== Test: Server Status Command ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Start server first
echo "Starting server..."
crwl server start >/dev/null 2>&1
sleep 5

# Check status
echo "Checking server status..."
STATUS_OUTPUT=$(crwl server status)
echo "$STATUS_OUTPUT"
echo ""

# Verify output contains expected fields
if ! echo "$STATUS_OUTPUT" | grep -q "Running"; then
    echo "❌ Status does not show 'Running'"
    crwl server stop
    exit 1
fi

if ! echo "$STATUS_OUTPUT" | grep -q "11235"; then
    echo "❌ Status does not show correct port"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Status command shows correct information"
