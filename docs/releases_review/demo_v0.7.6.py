#!/usr/bin/env python3
"""
Crawl4AI v0.7.6 Release Demo
============================

This demo showcases the major feature in v0.7.6:
**Webhook Support for Docker Job Queue API**

Features Demonstrated:
1. Asynchronous job processing with webhook notifications
2. Webhook support for /crawl/job endpoint
3. Webhook support for /llm/job endpoint
4. Notification-only vs data-in-payload modes
5. Custom webhook headers for authentication
6. Structured extraction with JSON schemas
7. Exponential backoff retry for reliable delivery

Prerequisites:
- Crawl4AI Docker container running on localhost:11235
- Flask installed: pip install flask requests
- LLM API key configured (for LLM examples)

Usage:
python docs/releases_review/demo_v0.7.6.py
"""

import requests
import json
import time
from flask import Flask, request, jsonify
from threading import Thread

# Configuration
CRAWL4AI_BASE_URL = "http://localhost:11235"
WEBHOOK_BASE_URL = "http://localhost:8080"

# Flask app for webhook receiver
app = Flask(__name__)
received_webhooks = []


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Universal webhook handler for both crawl and LLM extraction jobs."""
    payload = request.json
    task_id = payload['task_id']
    task_type = payload['task_type']
    status = payload['status']

    print(f"\n{'='*70}")
    print(f"📬 Webhook Received!")
    print(f"   Task ID: {task_id}")
    print(f"   Task Type: {task_type}")
    print(f"   Status: {status}")
    print(f"   Timestamp: {payload['timestamp']}")

    if status == 'completed':
        if 'data' in payload:
            print(f"   ✅ Data included in webhook")
            if task_type == 'crawl':
                results = payload['data'].get('results', [])
                print(f"   📊 Crawled {len(results)} URL(s)")
            elif task_type == 'llm_extraction':
                extracted = payload['data'].get('extracted_content', {})
                print(f"   🤖 Extracted: {json.dumps(extracted, indent=6)}")
        else:
            print(f"   📥 Notification only (fetch data separately)")
    elif status == 'failed':
        print(f"   ❌ Error: {payload.get('error', 'Unknown')}")

    print(f"{'='*70}\n")
    received_webhooks.append(payload)

    return jsonify({"status": "received"}), 200


def start_webhook_server():
    """Start Flask webhook server in background."""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)


def demo_1_crawl_webhook_notification_only():
    """Demo 1: Crawl job with webhook notification (data fetched separately)."""
    print("\n" + "="*70)
    print("DEMO 1: Crawl Job - Webhook Notification Only")
    print("="*70)
    print("Submitting crawl job with webhook notification...")

    payload = {
        "urls": ["https://example.com"],
        "browser_config": {"headless": True},
        "crawler_config": {"cache_mode": "bypass"},
        "webhook_config": {
            "webhook_url": f"{WEBHOOK_BASE_URL}/webhook",
            "webhook_data_in_payload": False,
            "webhook_headers": {
                "X-Demo": "v0.7.6",
                "X-Type": "crawl"
            }
        }
    }

    response = requests.post(f"{CRAWL4AI_BASE_URL}/crawl/job", json=payload)
    if response.ok:
        task_id = response.json()['task_id']
        print(f"✅ Job submitted: {task_id}")
        print("⏳ Webhook will notify when complete...")
        return task_id
    else:
        print(f"❌ Failed: {response.text}")
        return None


def demo_2_crawl_webhook_with_data():
    """Demo 2: Crawl job with full data in webhook payload."""
    print("\n" + "="*70)
    print("DEMO 2: Crawl Job - Webhook with Full Data")
    print("="*70)
    print("Submitting crawl job with data included in webhook...")

    payload = {
        "urls": ["https://www.python.org"],
        "browser_config": {"headless": True},
        "crawler_config": {"cache_mode": "bypass"},
        "webhook_config": {
            "webhook_url": f"{WEBHOOK_BASE_URL}/webhook",
            "webhook_data_in_payload": True,
            "webhook_headers": {
                "X-Demo": "v0.7.6",
                "X-Type": "crawl-with-data"
            }
        }
    }

    response = requests.post(f"{CRAWL4AI_BASE_URL}/crawl/job", json=payload)
    if response.ok:
        task_id = response.json()['task_id']
        print(f"✅ Job submitted: {task_id}")
        print("⏳ Webhook will include full results...")
        return task_id
    else:
        print(f"❌ Failed: {response.text}")
        return None


def demo_3_llm_webhook_notification_only():
    """Demo 3: LLM extraction with webhook notification (NEW in v0.7.6!)."""
    print("\n" + "="*70)
    print("DEMO 3: LLM Extraction - Webhook Notification Only (NEW!)")
    print("="*70)
    print("Submitting LLM extraction job with webhook notification...")

    payload = {
        "url": "https://www.example.com",
        "q": "Extract the main heading and description from this page",
        "provider": "openai/gpt-4o-mini",
        "cache": False,
        "webhook_config": {
            "webhook_url": f"{WEBHOOK_BASE_URL}/webhook",
            "webhook_data_in_payload": False,
            "webhook_headers": {
                "X-Demo": "v0.7.6",
                "X-Type": "llm"
            }
        }
    }

    response = requests.post(f"{CRAWL4AI_BASE_URL}/llm/job", json=payload)
    if response.ok:
        task_id = response.json()['task_id']
        print(f"✅ Job submitted: {task_id}")
        print("⏳ Webhook will notify when LLM extraction completes...")
        return task_id
    else:
        print(f"❌ Failed: {response.text}")
        return None


def demo_4_llm_webhook_with_schema():
    """Demo 4: LLM extraction with JSON schema and data in webhook (NEW in v0.7.6!)."""
    print("\n" + "="*70)
    print("DEMO 4: LLM Extraction - Schema + Full Data in Webhook (NEW!)")
    print("="*70)
    print("Submitting LLM extraction with JSON schema...")

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Page title"},
            "description": {"type": "string", "description": "Page description"},
            "main_topics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Main topics covered"
            }
        },
        "required": ["title"]
    }

    payload = {
        "url": "https://www.python.org",
        "q": "Extract the title, description, and main topics from this website",
        "schema": json.dumps(schema),
        "provider": "openai/gpt-4o-mini",
        "cache": False,
        "webhook_config": {
            "webhook_url": f"{WEBHOOK_BASE_URL}/webhook",
            "webhook_data_in_payload": True,
            "webhook_headers": {
                "X-Demo": "v0.7.6",
                "X-Type": "llm-with-schema"
            }
        }
    }

    response = requests.post(f"{CRAWL4AI_BASE_URL}/llm/job", json=payload)
    if response.ok:
        task_id = response.json()['task_id']
        print(f"✅ Job submitted: {task_id}")
        print("⏳ Webhook will include structured extraction results...")
        return task_id
    else:
        print(f"❌ Failed: {response.text}")
        return None


def demo_5_global_webhook_config():
    """Demo 5: Using global webhook configuration from config.yml."""
    print("\n" + "="*70)
    print("DEMO 5: Global Webhook Configuration")
    print("="*70)
    print("💡 You can configure a default webhook URL in config.yml:")
    print("""
    webhooks:
      enabled: true
      default_url: "https://myapp.com/webhooks/default"
      data_in_payload: false
      retry:
        max_attempts: 5
        initial_delay_ms: 1000
        max_delay_ms: 32000
        timeout_ms: 30000
    """)
    print("Then submit jobs WITHOUT webhook_config - they'll use the default!")
    print("This is useful for consistent webhook handling across all jobs.")


def demo_6_webhook_retry_logic():
    """Demo 6: Webhook retry mechanism with exponential backoff."""
    print("\n" + "="*70)
    print("DEMO 6: Webhook Retry Logic")
    print("="*70)
    print("🔄 Webhook delivery uses exponential backoff retry:")
    print("   • Max attempts: 5")
    print("   • Delays: 1s → 2s → 4s → 8s → 16s")
    print("   • Timeout: 30s per attempt")
    print("   • Retries on: 5xx errors, network errors, timeouts")
    print("   • No retry on: 4xx client errors")
    print("\nThis ensures reliable webhook delivery even with temporary failures!")


def print_summary():
    """Print demo summary and results."""
    print("\n" + "="*70)
    print("📊 DEMO SUMMARY")
    print("="*70)
    print(f"Total webhooks received: {len(received_webhooks)}")

    crawl_webhooks = [w for w in received_webhooks if w['task_type'] == 'crawl']
    llm_webhooks = [w for w in received_webhooks if w['task_type'] == 'llm_extraction']

    print(f"\nBreakdown:")
    print(f"  🕷️  Crawl jobs: {len(crawl_webhooks)}")
    print(f"  🤖 LLM extraction jobs: {len(llm_webhooks)}")

    print(f"\nDetails:")
    for i, webhook in enumerate(received_webhooks, 1):
        icon = "🕷️" if webhook['task_type'] == 'crawl' else "🤖"
        print(f"  {i}. {icon} {webhook['task_id']}: {webhook['status']}")

    print("\n" + "="*70)
    print("✨ v0.7.6 KEY FEATURES DEMONSTRATED:")
    print("="*70)
    print("✅ Webhook support for /crawl/job")
    print("✅ Webhook support for /llm/job (NEW!)")
    print("✅ Notification-only mode (fetch data separately)")
    print("✅ Data-in-payload mode (get full results in webhook)")
    print("✅ Custom headers for authentication")
    print("✅ JSON schema for structured LLM extraction")
    print("✅ Exponential backoff retry for reliable delivery")
    print("✅ Global webhook configuration support")
    print("✅ Universal webhook handler for both job types")
    print("\n💡 Benefits:")
    print("   • No more polling - get instant notifications")
    print("   • Better resource utilization")
    print("   • Reliable delivery with automatic retries")
    print("   • Consistent API across crawl and LLM jobs")
    print("   • Production-ready webhook infrastructure")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("🚀 Crawl4AI v0.7.6 Release Demo")
    print("="*70)
    print("Feature: Webhook Support for Docker Job Queue API")
    print("="*70)

    # Check if server is running
    try:
        health = requests.get(f"{CRAWL4AI_BASE_URL}/health", timeout=5)
        print(f"✅ Crawl4AI server is running")
    except:
        print(f"❌ Cannot connect to Crawl4AI at {CRAWL4AI_BASE_URL}")
        print("Please start Docker container:")
        print("  docker run -d -p 11235:11235 --env-file .llm.env unclecode/crawl4ai:0.7.6")
        return

    # Start webhook server
    print(f"\n🌐 Starting webhook server at {WEBHOOK_BASE_URL}...")
    webhook_thread = Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()
    time.sleep(2)

    # Run demos
    demo_1_crawl_webhook_notification_only()
    time.sleep(5)

    demo_2_crawl_webhook_with_data()
    time.sleep(5)

    demo_3_llm_webhook_notification_only()
    time.sleep(5)

    demo_4_llm_webhook_with_schema()
    time.sleep(5)

    demo_5_global_webhook_config()
    demo_6_webhook_retry_logic()

    # Wait for webhooks
    print("\n⏳ Waiting for all webhooks to arrive...")
    time.sleep(30)

    # Print summary
    print_summary()

    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70)
    print("\n📚 Documentation:")
    print("   • deploy/docker/WEBHOOK_EXAMPLES.md")
    print("   • docs/examples/docker_webhook_example.py")
    print("\n🔗 Upgrade:")
    print("   docker pull unclecode/crawl4ai:0.7.6")


if __name__ == "__main__":
    main()
