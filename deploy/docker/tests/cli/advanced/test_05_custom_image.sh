#!/bin/bash
# Test: Start server with custom image tag
# Expected: Server uses specified image

set -e

echo "=== Test: Custom Image Specification ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Use latest tag explicitly (or specify a different tag if available)
IMAGE="unclecode/crawl4ai:latest"
echo "Starting server with image: $IMAGE..."
crwl server start --image "$IMAGE"

sleep 5

# Check status shows correct image
STATUS=$(crwl server status)
echo "$STATUS"

if ! echo "$STATUS" | grep -q "crawl4ai"; then
    echo "❌ Status does not show correct image"
    crwl server stop
    exit 1
fi

# Verify health
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Server started with custom image"
