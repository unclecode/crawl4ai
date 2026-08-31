# Crawl4AI v0.7.6 Release Notes

*Release Date: October 22, 2025*

I'm excited to announce Crawl4AI v0.7.6, featuring a complete webhook infrastructure for the Docker job queue API! This release eliminates polling and brings real-time notifications to both crawling and LLM extraction workflows.

## 🎯 What's New

### Webhook Support for Docker Job Queue API

The headline feature of v0.7.6 is comprehensive webhook support for asynchronous job processing. No more constant polling to check if your jobs are done - get instant notifications when they complete!

**Key Capabilities:**

- ✅ **Universal Webhook Support**: Both `/crawl/job` and `/llm/job` endpoints now support webhooks
- ✅ **Flexible Delivery Modes**: Choose notification-only or include full data in the webhook payload
- ✅ **Reliable Delivery**: Exponential backoff retry mechanism (5 attempts: 1s → 2s → 4s → 8s → 16s)
- ✅ **Custom Authentication**: Add custom headers for webhook authentication
- ✅ **Global Configuration**: Set default webhook URL in `config.yml` for all jobs
- ✅ **Task Type Identification**: Distinguish between `crawl` and `llm_extraction` tasks

### How It Works

Instead of constantly checking job status:

**OLD WAY (Polling):**
```python
# Submit job
response = requests.post("http://localhost:11235/crawl/job", json=payload)
task_id = response.json()['task_id']

# Poll until complete
while True:
    status = requests.get(f"http://localhost:11235/crawl/job/{task_id}")
    if status.json()['status'] == 'completed':
        break
    time.sleep(5)  # Wait and try again
```

**NEW WAY (Webhooks):**
```python
# Submit job with webhook
payload = {
    "urls": ["https://example.com"],
    "webhook_config": {
        "webhook_url": "https://myapp.com/webhook",
        "webhook_data_in_payload": True
    }
}
response = requests.post("http://localhost:11235/crawl/job", json=payload)

# Done! Webhook will notify you when complete
# Your webhook handler receives the results automatically
```

### Crawl Job Webhooks

```bash
curl -X POST http://localhost:11235/crawl/job \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "browser_config": {"headless": true},
    "crawler_config": {"cache_mode": "bypass"},
    "webhook_config": {
      "webhook_url": "https://myapp.com/webhooks/crawl-complete",
      "webhook_data_in_payload": false,
      "webhook_headers": {
        "X-Webhook-Secret": "your-secret-token"
      }
    }
  }'
```

### LLM Extraction Job Webhooks (NEW!)

```bash
curl -X POST http://localhost:11235/llm/job \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "q": "Extract the article title, author, and publication date",
    "schema": "{\"type\":\"object\",\"properties\":{\"title\":{\"type\":\"string\"}}}",
    "provider": "openai/gpt-4o-mini",
    "webhook_config": {
      "webhook_url": "https://myapp.com/webhooks/llm-complete",
      "webhook_data_in_payload": true
    }
  }'
```

### Webhook Payload Structure

**Success (with data):**
```json
{
  "task_id": "llm_1698765432",
  "task_type": "llm_extraction",
  "status": "completed",
  "timestamp": "2025-10-22T10:30:00.000000+00:00",
  "urls": ["https://example.com/article"],
  "data": {
    "extracted_content": {
      "title": "Understanding Web Scraping",
      "author": "John Doe",
      "date": "2025-10-22"
    }
  }
}
```

**Failure:**
```json
{
  "task_id": "crawl_abc123",
  "task_type": "crawl",
  "status": "failed",
  "timestamp": "2025-10-22T10:30:00.000000+00:00",
  "urls": ["https://example.com"],
  "error": "Connection timeout after 30s"
}
```

### Simple Webhook Handler Example

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.json

    task_id = payload['task_id']
    task_type = payload['task_type']
    status = payload['status']

    if status == 'completed':
        if 'data' in payload:
            # Process data directly
            data = payload['data']
        else:
            # Fetch from API
            endpoint = 'crawl' if task_type == 'crawl' else 'llm'
            response = requests.get(f'http://localhost:11235/{endpoint}/job/{task_id}')
            data = response.json()

        # Your business logic here
        print(f"Job {task_id} completed!")

    elif status == 'failed':
        error = payload.get('error', 'Unknown error')
        print(f"Job {task_id} failed: {error}")

    return jsonify({"status": "received"}), 200

app.run(port=8080)
```

## 📊 Performance Improvements

- **Reduced Server Load**: Eliminates constant polling requests
- **Lower Latency**: Instant notification vs. polling interval delay
- **Better Resource Usage**: Frees up client connections while jobs run in background
- **Scalable Architecture**: Handles high-volume crawling workflows efficiently

## 🐛 Bug Fixes

- Fixed webhook configuration serialization for Pydantic HttpUrl fields
- Improved error handling in webhook delivery service
- Enhanced Redis task storage for webhook config persistence

## 🌍 Expected Real-World Impact

### For Web Scraping Workflows
- **Reduced Costs**: Less API calls = lower bandwidth and server costs
- **Better UX**: Instant notifications improve user experience
- **Scalability**: Handle 100s of concurrent jobs without polling overhead

### For LLM Extraction Pipelines
- **Async Processing**: Submit LLM extraction jobs and move on
- **Batch Processing**: Queue multiple extractions, get notified as they complete
- **Integration**: Easy integration with workflow automation tools (Zapier, n8n, etc.)

### For Microservices
- **Event-Driven**: Perfect for event-driven microservice architectures
- **Decoupling**: Decouple job submission from result processing
- **Reliability**: Automatic retries ensure webhooks are delivered

## 🔄 Breaking Changes

**None!** This release is fully backward compatible.

- Webhook configuration is optional
- Existing code continues to work without modification
- Polling is still supported for jobs without webhook config

## 📚 Documentation

### New Documentation
- **[WEBHOOK_EXAMPLES.md](../deploy/docker/WEBHOOK_EXAMPLES.md)** - Comprehensive webhook usage guide
- **[docker_webhook_example.py](../docs/examples/docker_webhook_example.py)** - Working code examples

### Updated Documentation
- **[Docker README](../deploy/docker/README.md)** - Added webhook sections
- API documentation with webhook examples

## 🛠️ Migration Guide

No migration needed! Webhooks are opt-in:

1. **To use webhooks**: Add `webhook_config` to your job payload
2. **To keep polling**: Continue using your existing code

### Quick Start

```python
# Just add webhook_config to your existing payload
payload = {
    # Your existing configuration
    "urls": ["https://example.com"],
    "browser_config": {...},
    "crawler_config": {...},

    # NEW: Add webhook configuration
    "webhook_config": {
        "webhook_url": "https://myapp.com/webhook",
        "webhook_data_in_payload": True
    }
}
```

## 🔧 Configuration

### Global Webhook Configuration (config.yml)

```yaml
webhooks:
  enabled: true
  default_url: "https://myapp.com/webhooks/default"  # Optional
  data_in_payload: false
  retry:
    max_attempts: 5
    initial_delay_ms: 1000
    max_delay_ms: 32000
    timeout_ms: 30000
  headers:
    User-Agent: "Crawl4AI-Webhook/1.0"
```

## 🚀 Upgrade Instructions

### Docker

```bash
# Pull the latest image
docker pull unclecode/crawl4ai:0.7.6

# Or use latest tag
docker pull unclecode/crawl4ai:latest

# Run with webhook support
docker run -d \
  -p 11235:11235 \
  --env-file .llm.env \
  --name crawl4ai \
  unclecode/crawl4ai:0.7.6
```

### Python Package

```bash
pip install --upgrade crawl4ai
```

## 💡 Pro Tips

1. **Use notification-only mode** for large results - fetch data separately to avoid large webhook payloads
2. **Set custom headers** for webhook authentication and request tracking
3. **Configure global default webhook** for consistent handling across all jobs
4. **Implement idempotent webhook handlers** - same webhook may be delivered multiple times on retry
5. **Use structured schemas** with LLM extraction for predictable webhook data

## 🎬 Demo

Try the release demo:

```bash
python docs/releases_review/demo_v0.7.6.py
```

This comprehensive demo showcases:
- Crawl job webhooks (notification-only and with data)
- LLM extraction webhooks (with JSON schema support)
- Custom headers for authentication
- Webhook retry mechanism
- Real-time webhook receiver

## 🙏 Acknowledgments

Thank you to the community for the feedback that shaped this feature! Special thanks to everyone who requested webhook support for asynchronous job processing.

## 📞 Support

- **Documentation**: https://docs.crawl4ai.com
- **GitHub Issues**: https://github.com/unclecode/crawl4ai/issues
- **Discord**: https://discord.gg/crawl4ai

---

**Happy crawling with webhooks!** 🕷️🪝

*- unclecode*
