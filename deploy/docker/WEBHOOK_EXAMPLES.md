# Webhook Feature Examples

This document provides examples of how to use the webhook feature for crawl jobs in Crawl4AI.

## Overview

The webhook feature allows you to receive notifications when crawl jobs complete, eliminating the need for polling. Webhooks are sent with exponential backoff retry logic to ensure reliable delivery.

## Configuration

### Global Configuration (config.yml)

You can configure default webhook settings in `config.yml`:

```yaml
webhooks:
  enabled: true
  default_url: null  # Optional: default webhook URL for all jobs
  data_in_payload: false  # Optional: default behavior for including data
  retry:
    max_attempts: 5
    initial_delay_ms: 1000  # 1s, 2s, 4s, 8s, 16s exponential backoff
    max_delay_ms: 32000
    timeout_ms: 30000  # 30s timeout per webhook call
  headers:  # Optional: default headers to include
    User-Agent: "Crawl4AI-Webhook/1.0"
```

## API Usage Examples

### Example 1: Basic Webhook (Notification Only)

Send a webhook notification without including the crawl data in the payload.

**Request:**
```bash
curl -X POST http://localhost:11235/crawl/job \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "webhook_config": {
      "webhook_url": "https://myapp.com/webhooks/crawl-complete",
      "webhook_data_in_payload": false
    }
  }'
```

**Response:**
```json
{
  "task_id": "crawl_a1b2c3d4"
}
```

**Webhook Payload Received:**
```json
{
  "task_id": "crawl_a1b2c3d4",
  "task_type": "crawl",
  "status": "completed",
  "timestamp": "2025-10-21T10:30:00.000000+00:00",
  "urls": ["https://example.com"]
}
```

Your webhook handler should then fetch the results:
```bash
curl http://localhost:11235/crawl/job/crawl_a1b2c3d4
```

### Example 2: Webhook with Data Included

Include the full crawl results in the webhook payload.

**Request:**
```bash
curl -X POST http://localhost:11235/crawl/job \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "webhook_config": {
      "webhook_url": "https://myapp.com/webhooks/crawl-complete",
      "webhook_data_in_payload": true
    }
  }'
```

**Webhook Payload Received:**
```json
{
  "task_id": "crawl_a1b2c3d4",
  "task_type": "crawl",
  "status": "completed",
  "timestamp": "2025-10-21T10:30:00.000000+00:00",
  "urls": ["https://example.com"],
  "data": {
    "markdown": "...",
    "html": "...",
    "links": {...},
    "metadata": {...}
  }
}
```

### Example 3: Webhook with Custom Headers

Include custom headers for authentication or identification.

**Request:**
```bash
curl -X POST http://localhost:11235/crawl/job \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "webhook_config": {
      "webhook_url": "https://myapp.com/webhooks/crawl-complete",
      "webhook_data_in_payload": false,
      "webhook_headers": {
        "X-Webhook-Secret": "my-secret-token",
        "X-Service-ID": "crawl4ai-production"
      }
    }
  }'
```

The webhook will be sent with these additional headers plus the default headers from config.

### Example 4: Failure Notification

When a crawl job fails, a webhook is sent with error details.

**Webhook Payload on Failure:**
```json
{
  "task_id": "crawl_a1b2c3d4",
  "task_type": "crawl",
  "status": "failed",
  "timestamp": "2025-10-21T10:30:00.000000+00:00",
  "urls": ["https://example.com"],
  "error": "Connection timeout after 30s"
}
```

### Example 5: Using Global Default Webhook

If you set a `default_url` in config.yml, jobs without webhook_config will use it:

**config.yml:**
```yaml
webhooks:
  enabled: true
  default_url: "https://myapp.com/webhooks/default"
  data_in_payload: false
```

**Request (no webhook_config needed):**
```bash
curl -X POST http://localhost:11235/crawl/job \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"]
  }'
```

The webhook will be sent to the default URL configured in config.yml.

## Webhook Handler Example

Here's a simple Python Flask webhook handler:

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/webhooks/crawl-complete', methods=['POST'])
def handle_crawl_webhook():
    payload = request.json

    task_id = payload['task_id']
    status = payload['status']

    if status == 'completed':
        # If data not in payload, fetch it
        if 'data' not in payload:
            response = requests.get(f'http://localhost:11235/crawl/job/{task_id}')
            data = response.json()
        else:
            data = payload['data']

        # Process the crawl data
        print(f"Processing crawl results for {task_id}")
        # Your business logic here...

    elif status == 'failed':
        error = payload.get('error', 'Unknown error')
        print(f"Crawl job {task_id} failed: {error}")
        # Handle failure...

    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    app.run(port=8080)
```

## Retry Logic

The webhook delivery service uses exponential backoff retry logic:

- **Attempts:** Up to 5 attempts by default
- **Delays:** 1s → 2s → 4s → 8s → 16s
- **Timeout:** 30 seconds per attempt
- **Retry Conditions:**
  - Server errors (5xx status codes)
  - Network errors
  - Timeouts
- **No Retry:**
  - Client errors (4xx status codes)
  - Successful delivery (2xx status codes)

## Benefits

1. **No Polling Required** - Eliminates constant API calls to check job status
2. **Real-time Notifications** - Immediate notification when jobs complete
3. **Reliable Delivery** - Exponential backoff ensures webhooks are delivered
4. **Flexible** - Choose between notification-only or full data delivery
5. **Secure** - Support for custom headers for authentication
6. **Configurable** - Global defaults or per-job configuration

## TypeScript Client Example

```typescript
interface WebhookConfig {
  webhook_url: string;
  webhook_data_in_payload?: boolean;
  webhook_headers?: Record<string, string>;
}

interface CrawlJobRequest {
  urls: string[];
  browser_config?: Record<string, any>;
  crawler_config?: Record<string, any>;
  webhook_config?: WebhookConfig;
}

async function createCrawlJob(request: CrawlJobRequest) {
  const response = await fetch('http://localhost:11235/crawl/job', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });

  const { task_id } = await response.json();
  return task_id;
}

// Usage
const taskId = await createCrawlJob({
  urls: ['https://example.com'],
  webhook_config: {
    webhook_url: 'https://myapp.com/webhooks/crawl-complete',
    webhook_data_in_payload: false,
    webhook_headers: {
      'X-Webhook-Secret': 'my-secret'
    }
  }
});
```

## Monitoring and Debugging

Webhook delivery attempts are logged at INFO level:
- Successful deliveries
- Retry attempts with delays
- Final failures after max attempts

Check the application logs for webhook delivery status:
```bash
docker logs crawl4ai-container | grep -i webhook
```
