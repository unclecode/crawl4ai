# Webhook Feature Test Script

This directory contains a comprehensive test script for the webhook feature implementation.

## Overview

The `test_webhook_feature.sh` script automates the entire process of testing the webhook feature:

1. ✅ Fetches and switches to the webhook feature branch
2. ✅ Activates the virtual environment
3. ✅ Installs all required dependencies
4. ✅ Starts Redis server in background
5. ✅ Starts Crawl4AI server in background
6. ✅ Runs webhook integration test
7. ✅ Verifies job completion via webhook
8. ✅ Cleans up and returns to original branch

## Prerequisites

- Python 3.10+
- Virtual environment already created (`venv/` in project root)
- Git repository with the webhook feature branch
- `redis-server` (script will attempt to install if missing)
- `curl` and `lsof` commands available

## Usage

### Quick Start

From the project root:

```bash
./tests/test_webhook_feature.sh
```

Or from the tests directory:

```bash
cd tests
./test_webhook_feature.sh
```

### What the Script Does

#### Step 1: Branch Management
- Saves your current branch
- Fetches the webhook feature branch from remote
- Switches to the webhook feature branch

#### Step 2: Environment Setup
- Activates your existing virtual environment
- Installs dependencies from `deploy/docker/requirements.txt`
- Installs Flask for the webhook receiver

#### Step 3: Service Startup
- Starts Redis server on port 6379
- Starts Crawl4AI server on port 11235
- Waits for server health check to pass

#### Step 4: Webhook Test
- Creates a webhook receiver on port 8080
- Submits a crawl job for `https://example.com` with webhook config
- Waits for webhook notification (60s timeout)
- Verifies webhook payload contains expected data

#### Step 5: Cleanup
- Stops webhook receiver
- Stops Crawl4AI server
- Stops Redis server
- Returns to your original branch

## Expected Output

```
[INFO] Starting webhook feature test script
[INFO] Project root: /path/to/crawl4ai
[INFO] Step 1: Fetching PR branch...
[INFO] Current branch: develop
[SUCCESS] Branch fetched
[INFO] Step 2: Switching to branch: claude/implement-webhook-crawl-feature-011CULZY1Jy8N5MUkZqXkRVp
[SUCCESS] Switched to webhook feature branch
[INFO] Step 3: Activating virtual environment...
[SUCCESS] Virtual environment activated
[INFO] Step 4: Installing server dependencies...
[SUCCESS] Dependencies installed
[INFO] Step 5a: Starting Redis...
[SUCCESS] Redis started (PID: 12345)
[INFO] Step 5b: Starting server on port 11235...
[INFO] Server started (PID: 12346)
[INFO] Waiting for server to be ready...
[SUCCESS] Server is ready!
[INFO] Step 6: Creating webhook test script...
[INFO] Running webhook test...

🚀 Submitting crawl job with webhook...
✅ Job submitted successfully, task_id: crawl_abc123
⏳ Waiting for webhook notification...

✅ Webhook received: {
  "task_id": "crawl_abc123",
  "task_type": "crawl",
  "status": "completed",
  "timestamp": "2025-10-22T00:00:00.000000+00:00",
  "urls": ["https://example.com"],
  "data": { ... }
}

✅ Webhook received!
   Task ID: crawl_abc123
   Status: completed
   URLs: ['https://example.com']
   ✅ Data included in webhook payload
   📄 Crawled 1 URL(s)
      - https://example.com: 1234 chars

🎉 Webhook test PASSED!

[INFO] Step 7: Verifying test results...
[SUCCESS] ✅ Webhook test PASSED!
[SUCCESS] All tests completed successfully! 🎉
[INFO] Cleanup will happen automatically...
[INFO] Starting cleanup...
[INFO] Stopping webhook receiver...
[INFO] Stopping server...
[INFO] Stopping Redis...
[INFO] Switching back to branch: develop
[SUCCESS] Cleanup complete
```

## Troubleshooting

### Server Failed to Start

If the server fails to start, check the logs:

```bash
tail -100 /tmp/crawl4ai_server.log
```

Common issues:
- Port 11235 already in use: `lsof -ti:11235 | xargs kill -9`
- Missing dependencies: Check that all packages are installed

### Redis Connection Failed

Check if Redis is running:

```bash
redis-cli ping
# Should return: PONG
```

If not running:

```bash
redis-server --port 6379 --daemonize yes
```

### Webhook Not Received

The script has a 60-second timeout for webhook delivery. If the webhook isn't received:

1. Check server logs: `/tmp/crawl4ai_server.log`
2. Verify webhook receiver is running on port 8080
3. Check network connectivity between components

### Script Interruption

If the script is interrupted (Ctrl+C), cleanup happens automatically via trap. The script will:
- Kill all background processes
- Stop Redis
- Return to your original branch

To manually cleanup if needed:

```bash
# Kill processes by port
lsof -ti:11235 | xargs kill -9  # Server
lsof -ti:8080 | xargs kill -9   # Webhook receiver
lsof -ti:6379 | xargs kill -9   # Redis

# Return to your branch
git checkout develop  # or your branch name
```

## Testing Different URLs

To test with a different URL, modify the script or create a custom test:

```python
payload = {
    "urls": ["https://your-url-here.com"],
    "browser_config": {"headless": True},
    "crawler_config": {"cache_mode": "bypass"},
    "webhook_config": {
        "webhook_url": "http://localhost:8080/webhook",
        "webhook_data_in_payload": True
    }
}
```

## Files Generated

The script creates temporary files:

- `/tmp/crawl4ai_server.log` - Server output logs
- `/tmp/test_webhook.py` - Webhook test Python script

These are not cleaned up automatically so you can review them after the test.

## Exit Codes

- `0` - All tests passed successfully
- `1` - Test failed (check output for details)

## Safety Features

- ✅ Automatic cleanup on exit, interrupt, or error
- ✅ Returns to original branch on completion
- ✅ Kills all background processes
- ✅ Comprehensive error handling
- ✅ Colored output for easy reading
- ✅ Detailed logging at each step

## Notes

- The script uses `set -e` to exit on any command failure
- All background processes are tracked and cleaned up
- The virtual environment must exist before running
- Redis must be available (installed or installable via apt-get/brew)

## Integration with CI/CD

This script can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Test Webhook Feature
  run: |
    chmod +x tests/test_webhook_feature.sh
    ./tests/test_webhook_feature.sh
```

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review server logs at `/tmp/crawl4ai_server.log`
3. Ensure all prerequisites are met
4. Open an issue with the full output of the script
