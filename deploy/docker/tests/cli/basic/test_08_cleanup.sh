#!/bin/bash
# Test: Force cleanup command
# Expected: All resources removed even if state is corrupted

set -e

echo "=== Test: Force Cleanup Command ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Start server
echo "Starting server..."
crwl server start >/dev/null 2>&1
sleep 5

# Run cleanup (will prompt, so use force flag)
echo "Running force cleanup..."
crwl server cleanup --force

sleep 3

# Verify no containers running
echo "Verifying cleanup..."
CONTAINERS=$(docker ps --filter "name=crawl4ai" --format "{{.Names}}" || echo "")
if [[ -n "$CONTAINERS" ]]; then
    echo "❌ Crawl4AI containers still running: $CONTAINERS"
    exit 1
fi

# Verify port is free
if curl -s http://localhost:11235/health > /dev/null 2>&1; then
    echo "❌ Server still responding after cleanup"
    exit 1
fi

# Verify status shows not running
STATUS=$(crwl server status | grep "No server" || echo "RUNNING")
if [[ "$STATUS" == "RUNNING" ]]; then
    echo "❌ Status still shows server running after cleanup"
    exit 1
fi

echo ""
echo "✅ Test passed: Force cleanup removed all resources"
