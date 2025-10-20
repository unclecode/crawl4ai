#!/bin/bash
# Test: Long-running stability test (5 minutes)
# Expected: Server remains stable over extended period

set -e

echo "=== Test: Long-Running Stability (5 minutes) ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start server
echo "Starting server with 2 replicas..."
crwl server start --replicas 2 >/dev/null 2>&1
sleep 10

# Get start time
START_TIME=$(date +%s)
DURATION=300  # 5 minutes in seconds
REQUEST_COUNT=0
ERROR_COUNT=0

echo ""
echo "Running stability test for 5 minutes..."
echo "Making periodic requests every 10 seconds..."
echo ""

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    if [[ $ELAPSED -ge $DURATION ]]; then
        break
    fi

    REMAINING=$((DURATION - ELAPSED))
    echo "[$ELAPSED/$DURATION seconds] Remaining: ${REMAINING}s, Requests: $REQUEST_COUNT, Errors: $ERROR_COUNT"

    # Make a request
    if curl -s -X POST http://localhost:11235/crawl \
        -H "Content-Type: application/json" \
        -d '{"urls": ["https://httpbin.org/html"], "crawler_config": {}}' > /dev/null 2>&1; then
        REQUEST_COUNT=$((REQUEST_COUNT + 1))
    else
        ERROR_COUNT=$((ERROR_COUNT + 1))
        echo "  ⚠️  Request failed"
    fi

    # Check health every 30 seconds
    if [[ $((ELAPSED % 30)) -eq 0 ]]; then
        HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
        if [[ "$HEALTH" != "ok" ]]; then
            echo "  ❌ Health check failed!"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi

        # Get memory stats
        MEM=$(curl -s http://localhost:11235/monitor/health | jq -r '.container.memory_percent' 2>/dev/null || echo "N/A")
        echo "  Memory: ${MEM}%"
    fi

    sleep 10
done

echo ""
echo "Test duration completed!"
echo "Total requests: $REQUEST_COUNT"
echo "Total errors: $ERROR_COUNT"

# Get final stats
echo ""
echo "Final statistics:"
curl -s http://localhost:11235/monitor/endpoints/stats | jq '.' 2>/dev/null || echo "No stats available"

# Verify error rate is acceptable (<10%)
ERROR_RATE=$(echo "scale=2; $ERROR_COUNT * 100 / $REQUEST_COUNT" | bc -l 2>/dev/null || echo "0")
echo ""
echo "Error rate: ${ERROR_RATE}%"

# Cleanup
echo ""
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1

# Check error rate
ERROR_OK=$(echo "$ERROR_RATE < 10" | bc -l 2>/dev/null || echo "1")
if [[ "$ERROR_OK" != "1" ]]; then
    echo "❌ Error rate too high: ${ERROR_RATE}%"
    exit 1
fi

echo ""
echo "✅ Test passed: Server remained stable over 5 minutes"
echo "   Requests: $REQUEST_COUNT, Errors: $ERROR_COUNT, Error rate: ${ERROR_RATE}%"
