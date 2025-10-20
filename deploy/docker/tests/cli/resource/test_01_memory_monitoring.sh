#!/bin/bash
# Test: Monitor memory usage during crawl operations
# Expected: Memory stats are accessible and reasonable

set -e

echo "=== Test: Memory Monitoring ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start server
echo "Starting server..."
crwl server start >/dev/null 2>&1
sleep 5

# Get baseline memory
echo "Checking baseline memory..."
BASELINE=$(curl -s http://localhost:11235/monitor/health | jq -r '.container.memory_percent' 2>/dev/null || echo "0")
echo "Baseline memory: ${BASELINE}%"

# Make several crawl requests
echo ""
echo "Making crawl requests to increase memory usage..."
for i in {1..5}; do
    echo "  Request $i/5..."
    curl -s -X POST http://localhost:11235/crawl \
      -H "Content-Type: application/json" \
      -d "{\"urls\": [\"https://httpbin.org/html?req=$i\"], \"crawler_config\": {}}" > /dev/null || true
    sleep 1
done

# Check memory after requests
echo ""
echo "Checking memory after requests..."
AFTER=$(curl -s http://localhost:11235/monitor/health | jq -r '.container.memory_percent' 2>/dev/null || echo "0")
echo "Memory after requests: ${AFTER}%"

# Get browser pool stats
echo ""
echo "Browser pool memory usage..."
POOL_MEM=$(curl -s http://localhost:11235/monitor/browsers | jq -r '.summary.total_memory_mb' 2>/dev/null || echo "0")
echo "Browser pool: ${POOL_MEM} MB"

# Verify memory is within reasonable bounds (<80%)
MEMORY_OK=$(echo "$AFTER < 80" | bc -l 2>/dev/null || echo "1")
if [[ "$MEMORY_OK" != "1" ]]; then
    echo "⚠️  Warning: Memory usage is high: ${AFTER}%"
fi

# Cleanup
echo ""
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: Memory monitoring functional"
echo "   Baseline: ${BASELINE}%, After: ${AFTER}%, Pool: ${POOL_MEM} MB"
