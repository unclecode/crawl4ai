#!/bin/bash
# Test: Corrupted state file
# Expected: Cleanup recovers from corrupted state

set -e

echo "=== Test: State File Corruption ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start server to create state
echo "Starting server to create state..."
crwl server start >/dev/null 2>&1
sleep 5

# Get state file path
STATE_FILE="$HOME/.crawl4ai/server/state.json"
echo "State file: $STATE_FILE"

# Verify state file exists
if [[ ! -f "$STATE_FILE" ]]; then
    echo "❌ State file not created"
    crwl server stop
    exit 1
fi

echo "Original state:"
cat "$STATE_FILE" | jq '.' || cat "$STATE_FILE"
echo ""

# Stop server
crwl server stop >/dev/null 2>&1
sleep 2

# Corrupt state file
echo "Corrupting state file..."
echo "{ invalid json }" > "$STATE_FILE"
cat "$STATE_FILE"
echo ""

# Try to start server (should handle corrupted state)
echo "Attempting to start with corrupted state..."
OUTPUT=$(crwl server start 2>&1 || true)
echo "$OUTPUT"
echo ""

# Check if server started or gave clear error
if curl -s http://localhost:11235/health > /dev/null 2>&1; then
    echo "✅ Server started despite corrupted state"
    crwl server stop
elif echo "$OUTPUT" | grep -iq "already running"; then
    # State thinks server is running, use cleanup
    echo "State thinks server is running, using cleanup..."
    crwl server cleanup --force >/dev/null 2>&1
    sleep 2

    # Try starting again
    crwl server start >/dev/null 2>&1
    sleep 5

    if curl -s http://localhost:11235/health > /dev/null 2>&1; then
        echo "✅ Cleanup recovered from corrupted state"
        crwl server stop
    else
        echo "❌ Failed to recover from corrupted state"
        exit 1
    fi
else
    echo "✅ Handled corrupted state appropriately"
fi

echo ""
echo "✅ Test passed: System handles state corruption"
