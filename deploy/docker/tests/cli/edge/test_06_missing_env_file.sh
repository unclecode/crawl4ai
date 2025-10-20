#!/bin/bash
# Test: Non-existent environment file
# Expected: Error indicating file not found

set -e

echo "=== Test: Missing Environment File ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Try with non-existent file
FAKE_FILE="/tmp/nonexistent_$(date +%s).env"
echo "Attempting to start with non-existent env file: $FAKE_FILE"
OUTPUT=$(crwl server start --env-file "$FAKE_FILE" 2>&1 || true)
echo "$OUTPUT"
echo ""

# Verify error
if echo "$OUTPUT" | grep -iq "error\|does not exist\|not found\|no such file"; then
    echo "✅ Test passed: Proper error for missing env file"
else
    echo "❌ Test failed: Expected error about missing file"
    crwl server stop
    exit 1
fi

# Make sure no server started
if curl -s http://localhost:11235/health > /dev/null 2>&1; then
    echo "❌ Server should not have started"
    crwl server stop
    exit 1
fi

echo "✅ Server correctly refused to start with missing env file"
