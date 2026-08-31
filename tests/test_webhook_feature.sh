#!/bin/bash

#############################################################################
# Webhook Feature Test Script
#
# This script tests the webhook feature implementation by:
# 1. Switching to the webhook feature branch
# 2. Installing dependencies
# 3. Starting the server
# 4. Running webhook tests
# 5. Cleaning up and returning to original branch
#
# Usage: ./test_webhook_feature.sh
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BRANCH_NAME="claude/implement-webhook-crawl-feature-011CULZY1Jy8N5MUkZqXkRVp"
VENV_PATH="venv"
SERVER_PORT=11235
WEBHOOK_PORT=8080
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# PID files for cleanup
REDIS_PID=""
SERVER_PID=""
WEBHOOK_PID=""

#############################################################################
# Utility Functions
#############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

cleanup() {
    log_info "Starting cleanup..."

    # Kill webhook receiver if running
    if [ ! -z "$WEBHOOK_PID" ] && kill -0 $WEBHOOK_PID 2>/dev/null; then
        log_info "Stopping webhook receiver (PID: $WEBHOOK_PID)..."
        kill $WEBHOOK_PID 2>/dev/null || true
    fi

    # Kill server if running
    if [ ! -z "$SERVER_PID" ] && kill -0 $SERVER_PID 2>/dev/null; then
        log_info "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
    fi

    # Kill Redis if running
    if [ ! -z "$REDIS_PID" ] && kill -0 $REDIS_PID 2>/dev/null; then
        log_info "Stopping Redis (PID: $REDIS_PID)..."
        kill $REDIS_PID 2>/dev/null || true
    fi

    # Also kill by port if PIDs didn't work
    lsof -ti:$SERVER_PORT | xargs kill -9 2>/dev/null || true
    lsof -ti:$WEBHOOK_PORT | xargs kill -9 2>/dev/null || true
    lsof -ti:6379 | xargs kill -9 2>/dev/null || true

    # Return to original branch
    if [ ! -z "$ORIGINAL_BRANCH" ]; then
        log_info "Switching back to branch: $ORIGINAL_BRANCH"
        git checkout $ORIGINAL_BRANCH 2>/dev/null || true
    fi

    log_success "Cleanup complete"
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

#############################################################################
# Main Script
#############################################################################

log_info "Starting webhook feature test script"
log_info "Project root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Step 1: Save current branch and fetch PR
log_info "Step 1: Fetching PR branch..."
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $ORIGINAL_BRANCH"

git fetch origin $BRANCH_NAME
log_success "Branch fetched"

# Step 2: Switch to new branch
log_info "Step 2: Switching to branch: $BRANCH_NAME"
git checkout $BRANCH_NAME
log_success "Switched to webhook feature branch"

# Step 3: Activate virtual environment
log_info "Step 3: Activating virtual environment..."
if [ ! -d "$VENV_PATH" ]; then
    log_error "Virtual environment not found at $VENV_PATH"
    log_info "Creating virtual environment..."
    python3 -m venv $VENV_PATH
fi

source $VENV_PATH/bin/activate
log_success "Virtual environment activated: $(which python)"

# Step 4: Install server dependencies
log_info "Step 4: Installing server dependencies..."
pip install -q -r deploy/docker/requirements.txt
log_success "Dependencies installed"

# Check if Redis is available
log_info "Checking Redis availability..."
if ! command -v redis-server &> /dev/null; then
    log_warning "Redis not found, attempting to install..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y redis-server
    elif command -v brew &> /dev/null; then
        brew install redis
    else
        log_error "Cannot install Redis automatically. Please install Redis manually."
        exit 1
    fi
fi

# Step 5: Start Redis in background
log_info "Step 5a: Starting Redis..."
redis-server --port 6379 --daemonize yes
sleep 2
REDIS_PID=$(pgrep redis-server)
log_success "Redis started (PID: $REDIS_PID)"

# Step 5b: Start server in background
log_info "Step 5b: Starting server on port $SERVER_PORT..."
cd deploy/docker

# Start server in background
python3 -m uvicorn server:app --host 0.0.0.0 --port $SERVER_PORT > /tmp/crawl4ai_server.log 2>&1 &
SERVER_PID=$!
cd "$PROJECT_ROOT"

log_info "Server started (PID: $SERVER_PID)"

# Wait for server to be ready
log_info "Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:$SERVER_PORT/health > /dev/null 2>&1; then
        log_success "Server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Server failed to start within 30 seconds"
        log_info "Server logs:"
        tail -50 /tmp/crawl4ai_server.log
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo ""

# Step 6: Create and run webhook test
log_info "Step 6: Creating webhook test script..."

cat > /tmp/test_webhook.py << 'PYTHON_SCRIPT'
import requests
import json
import time
from flask import Flask, request, jsonify
from threading import Thread, Event

# Configuration
CRAWL4AI_BASE_URL = "http://localhost:11235"
WEBHOOK_BASE_URL = "http://localhost:8080"

# Flask app for webhook receiver
app = Flask(__name__)
webhook_received = Event()
webhook_data = {}

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    global webhook_data
    webhook_data = request.json
    webhook_received.set()
    print(f"\n✅ Webhook received: {json.dumps(webhook_data, indent=2)}")
    return jsonify({"status": "received"}), 200

def start_webhook_server():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

# Start webhook server in background
webhook_thread = Thread(target=start_webhook_server, daemon=True)
webhook_thread.start()
time.sleep(2)

print("🚀 Submitting crawl job with webhook...")

# Submit job with webhook
payload = {
    "urls": ["https://example.com"],
    "browser_config": {"headless": True},
    "crawler_config": {"cache_mode": "bypass"},
    "webhook_config": {
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook",
        "webhook_data_in_payload": True
    }
}

response = requests.post(
    f"{CRAWL4AI_BASE_URL}/crawl/job",
    json=payload,
    headers={"Content-Type": "application/json"}
)

if not response.ok:
    print(f"❌ Failed to submit job: {response.text}")
    exit(1)

task_id = response.json()['task_id']
print(f"✅ Job submitted successfully, task_id: {task_id}")

# Wait for webhook (with timeout)
print("⏳ Waiting for webhook notification...")
if webhook_received.wait(timeout=60):
    print(f"✅ Webhook received!")
    print(f"   Task ID: {webhook_data.get('task_id')}")
    print(f"   Status: {webhook_data.get('status')}")
    print(f"   URLs: {webhook_data.get('urls')}")

    if webhook_data.get('status') == 'completed':
        if 'data' in webhook_data:
            print(f"   ✅ Data included in webhook payload")
            results = webhook_data['data'].get('results', [])
            if results:
                print(f"   📄 Crawled {len(results)} URL(s)")
                for result in results:
                    print(f"      - {result.get('url')}: {len(result.get('markdown', ''))} chars")
        print("\n🎉 Webhook test PASSED!")
        exit(0)
    else:
        print(f"   ❌ Job failed: {webhook_data.get('error')}")
        exit(1)
else:
    print("❌ Webhook not received within 60 seconds")
    # Try polling as fallback
    print("⏳ Trying to poll job status...")
    for i in range(10):
        status_response = requests.get(f"{CRAWL4AI_BASE_URL}/crawl/job/{task_id}")
        if status_response.ok:
            status = status_response.json()
            print(f"   Status: {status.get('status')}")
            if status.get('status') in ['completed', 'failed']:
                break
        time.sleep(2)
    exit(1)
PYTHON_SCRIPT

# Install Flask for webhook receiver
pip install -q flask

# Run the webhook test
log_info "Running webhook test..."
python3 /tmp/test_webhook.py &
WEBHOOK_PID=$!

# Wait for test to complete
wait $WEBHOOK_PID
TEST_EXIT_CODE=$?

# Step 7: Verify results
log_info "Step 7: Verifying test results..."
if [ $TEST_EXIT_CODE -eq 0 ]; then
    log_success "✅ Webhook test PASSED!"
else
    log_error "❌ Webhook test FAILED (exit code: $TEST_EXIT_CODE)"
    log_info "Server logs:"
    tail -100 /tmp/crawl4ai_server.log
    exit 1
fi

# Step 8: Cleanup happens automatically via trap
log_success "All tests completed successfully! 🎉"
log_info "Cleanup will happen automatically..."
