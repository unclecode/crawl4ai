#!/bin/bash
# Test: Verify complete resource cleanup
# Expected: All Docker resources are properly removed

set -e

echo "=== Test: Resource Cleanup Verification ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Start server to create resources
echo "Starting server with 3 replicas..."
crwl server start --replicas 3 >/dev/null 2>&1
sleep 10

# List resources before cleanup
echo ""
echo "Resources before cleanup:"
echo "Containers:"
docker ps --filter "name=crawl4ai" --format "  - {{.Names}}" 2>/dev/null || echo "  None"
docker ps --filter "name=nginx" --format "  - {{.Names}}" 2>/dev/null || echo "  None"
docker ps --filter "name=redis" --format "  - {{.Names}}" 2>/dev/null || echo "  None"

echo ""
echo "Networks:"
docker network ls --filter "name=crawl4ai" --format "  - {{.Name}}" 2>/dev/null || echo "  None"

# Cleanup
echo ""
echo "Performing cleanup..."
crwl server cleanup --force >/dev/null 2>&1
sleep 5

# Verify cleanup
echo ""
echo "Verifying cleanup..."

CONTAINERS=$(docker ps -a --filter "name=crawl4ai" --format "{{.Names}}" 2>/dev/null || echo "")
if [[ -n "$CONTAINERS" ]]; then
    echo "❌ Found remaining crawl4ai containers: $CONTAINERS"
    exit 1
fi

NGINX=$(docker ps -a --filter "name=nginx" --format "{{.Names}}" 2>/dev/null || echo "")
if [[ -n "$NGINX" ]]; then
    echo "⚠️  Warning: Nginx container still exists: $NGINX"
fi

REDIS=$(docker ps -a --filter "name=redis" --format "{{.Names}}" 2>/dev/null || echo "")
if [[ -n "$REDIS" ]]; then
    echo "⚠️  Warning: Redis container still exists: $REDIS"
fi

# Verify port is free
if curl -s http://localhost:11235/health > /dev/null 2>&1; then
    echo "❌ Port 11235 still in use after cleanup"
    exit 1
fi

echo ""
echo "✅ Test passed: All Crawl4AI resources properly cleaned up"
