#!/bin/bash
# Test: Start server with environment file
# Expected: Server loads environment variables

set -e

echo "=== Test: Start with Environment File ==="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

# Create a test env file
TEST_ENV_FILE="/tmp/test_crawl4ai.env"
cat > "$TEST_ENV_FILE" <<EOF
TEST_VAR=test_value
OPENAI_API_KEY=sk-test-key
EOF

echo "Created test env file at $TEST_ENV_FILE"

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Start with env file
echo "Starting server with env file..."
crwl server start --env-file "$TEST_ENV_FILE"

sleep 5

# Verify server started
HEALTH=$(curl -s http://localhost:11235/health | jq -r '.status' 2>/dev/null || echo "error")
if [[ "$HEALTH" != "ok" ]]; then
    echo "❌ Health check failed"
    rm -f "$TEST_ENV_FILE"
    crwl server stop
    exit 1
fi

# Cleanup
echo "Cleaning up..."
crwl server stop >/dev/null 2>&1
rm -f "$TEST_ENV_FILE"

echo ""
echo "✅ Test passed: Server started with environment file"
