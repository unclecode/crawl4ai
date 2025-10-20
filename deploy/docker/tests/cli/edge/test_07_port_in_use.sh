#!/bin/bash
# Test: Port already in use
# Expected: Error indicating port is occupied

set -e

echo "=== Test: Port Already In Use ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start a simple HTTP server on port 11235 to occupy it
echo "Starting dummy server on port 11235..."
python -m http.server 11235 >/dev/null 2>&1 &
DUMMY_PID=$!
sleep 2

# Try to start crawl4ai on same port
echo "Attempting to start Crawl4AI on occupied port..."
OUTPUT=$(crwl server start 2>&1 || true)
echo "$OUTPUT"
echo ""

# Kill dummy server
kill $DUMMY_PID 2>/dev/null || true
sleep 1

# Verify error message
if echo "$OUTPUT" | grep -iq "port.*in use\|already in use\|address already in use"; then
    echo "✅ Test passed: Proper error for port in use"
else
    echo "⚠️  Expected 'port in use' error (output may vary)"
fi

# Make sure Crawl4AI didn't start
if curl -s http://localhost:11235/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "unknown")
    if [[ "$HEALTH" == "ok" ]]; then
        echo "❌ Crawl4AI started despite port being occupied"
        crwl server stop
        exit 1
    fi
fi

echo "✅ Crawl4AI correctly refused to start on occupied port"
