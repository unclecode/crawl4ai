#!/bin/bash
# Test: View server logs
# Expected: Logs are displayed without errors

set -e

echo "=== Test: Server Logs Command ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Start server
echo "Starting server..."
crwl server start >/dev/null 2>&1
sleep 5

# Make a request to generate some logs
echo "Making request to generate logs..."
curl -s http://localhost:11235/health > /dev/null

# Check logs (tail)
echo "Fetching logs (last 50 lines)..."
LOGS=$(crwl server logs --tail 50 2>&1 || echo "ERROR")
if [[ "$LOGS" == "ERROR" ]]; then
    echo "❌ Failed to retrieve logs"
    crwl server stop
    exit 1
fi

echo "Log sample (first 10 lines):"
echo "$LOGS" | head -n 10
echo ""

# Verify logs contain something (not empty)
if [[ -z "$LOGS" ]]; then
    echo "❌ Logs are empty"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Logs retrieved successfully"
