"""
Docker Webhook Example for Crawl4AI

This example demonstrates how to use webhooks with the Crawl4AI job queue API.
Instead of polling for results, webhooks notify your application when jobs complete.

Supports both:
- /crawl/job - Raw crawling with markdown extraction
- /llm/job - LLM-powered content extraction

Prerequisites:
1. Crawl4AI Docker container running on localhost:11235
2. Flask installed: pip install flask requests
3. LLM API key configured in .llm.env (for LLM extraction examples)

Usage:
1. Run this script: python docker_webhook_example.py
2. The webhook server will start on http://localhost:8080
3. Jobs will be submitted and webhooks will be received automatically
"""

import requests
import json
import time
from flask import Flask, request, jsonify
from threading import Thread

# Configuration
CRAWL4AI_BASE_URL = "http://localhost:11235"
WEBHOOK_BASE_URL = "http://localhost:8080"  # Your webhook receiver URL

# Initialize Flask app for webhook receiver
app = Flask(__name__)

# Store received webhook data for demonstration
received_webhooks = []


@app.route('/webhooks/crawl-complete', methods=['POST'])
def handle_crawl_webhook():
    """
    Webhook handler that receives notifications when crawl jobs complete.

    Payload structure:
    {
        "task_id": "crawl_abc123",
        "task_type": "crawl",
        "status": "completed" or "failed",
        "timestamp": "2025-10-21T10:30:00.000000+00:00",
        "urls": ["https://example.com"],
        "error": "error message" (only if failed),
        "data": {...} (only if webhook_data_in_payload=True)
    }
    """
    payload = request.json
    print(f"\n{'='*60}")
    print(f"📬 Webhook received for task: {payload['task_id']}")
    print(f"   Status: {payload['status']}")
    print(f"   Timestamp: {payload['timestamp']}")
    print(f"   URLs: {payload['urls']}")

    if payload['status'] == 'completed':
        # If data is in payload, process it directly
        if 'data' in payload:
            print(f"   ✅ Data included in webhook")
            data = payload['data']
            # Process the crawl results here
            for result in data.get('results', []):
                print(f"      - Crawled: {result.get('url')}")
                print(f"      - Markdown length: {len(result.get('markdown', ''))}")
        else:
            # Fetch results from API if not included
            print(f"   📥 Fetching results from API...")
            task_id = payload['task_id']
            result_response = requests.get(f"{CRAWL4AI_BASE_URL}/crawl/job/{task_id}")
            if result_response.ok:
                data = result_response.json()
                print(f"   ✅ Results fetched successfully")
                # Process the crawl results here
                for result in data['result'].get('results', []):
                    print(f"      - Crawled: {result.get('url')}")
                    print(f"      - Markdown length: {len(result.get('markdown', ''))}")

    elif payload['status'] == 'failed':
        print(f"   ❌ Job failed: {payload.get('error', 'Unknown error')}")

    print(f"{'='*60}\n")

    # Store webhook for demonstration
    received_webhooks.append(payload)

    # Return 200 OK to acknowledge receipt
    return jsonify({"status": "received"}), 200


@app.route('/webhooks/llm-complete', methods=['POST'])
def handle_llm_webhook():
    """
    Webhook handler that receives notifications when LLM extraction jobs complete.

    Payload structure:
    {
        "task_id": "llm_1698765432_12345",
        "task_type": "llm_extraction",
        "status": "completed" or "failed",
        "timestamp": "2025-10-21T10:30:00.000000+00:00",
        "urls": ["https://example.com/article"],
        "error": "error message" (only if failed),
        "data": {"extracted_content": {...}} (only if webhook_data_in_payload=True)
    }
    """
    payload = request.json
    print(f"\n{'='*60}")
    print(f"🤖 LLM Webhook received for task: {payload['task_id']}")
    print(f"   Task Type: {payload['task_type']}")
    print(f"   Status: {payload['status']}")
    print(f"   Timestamp: {payload['timestamp']}")
    print(f"   URL: {payload['urls'][0]}")

    if payload['status'] == 'completed':
        # If data is in payload, process it directly
        if 'data' in payload:
            print(f"   ✅ Data included in webhook")
            data = payload['data']
            # Webhook wraps extracted content in 'extracted_content' field
            extracted = data.get('extracted_content', {})
            print(f"      - Extracted content:")
            print(f"        {json.dumps(extracted, indent=8)}")
        else:
            # Fetch results from API if not included
            print(f"   📥 Fetching results from API...")
            task_id = payload['task_id']
            result_response = requests.get(f"{CRAWL4AI_BASE_URL}/llm/job/{task_id}")
            if result_response.ok:
                data = result_response.json()
                print(f"   ✅ Results fetched successfully")
                # API returns unwrapped content in 'result' field
                extracted = data['result']
                print(f"      - Extracted content:")
                print(f"        {json.dumps(extracted, indent=8)}")

    elif payload['status'] == 'failed':
        print(f"   ❌ Job failed: {payload.get('error', 'Unknown error')}")

    print(f"{'='*60}\n")

    # Store webhook for demonstration
    received_webhooks.append(payload)

    # Return 200 OK to acknowledge receipt
    return jsonify({"status": "received"}), 200


def start_webhook_server():
    """Start the Flask webhook server in a separate thread"""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)


def submit_crawl_job_with_webhook(urls, webhook_url, include_data=False):
    """
    Submit a crawl job with webhook notification.

    Args:
        urls: List of URLs to crawl
        webhook_url: URL to receive webhook notifications
        include_data: Whether to include full results in webhook payload

    Returns:
        task_id: The job's task identifier
    """
    payload = {
        "urls": urls,
        "browser_config": {"headless": True},
        "crawler_config": {"cache_mode": "bypass"},
        "webhook_config": {
            "webhook_url": webhook_url,
            "webhook_data_in_payload": include_data,
            # Optional: Add custom headers for authentication
            # "webhook_headers": {
            #     "X-Webhook-Secret": "your-secret-token"
            # }
        }
    }

    print(f"\n🚀 Submitting crawl job...")
    print(f"   URLs: {urls}")
    print(f"   Webhook: {webhook_url}")
    print(f"   Include data: {include_data}")

    response = requests.post(
        f"{CRAWL4AI_BASE_URL}/crawl/job",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.ok:
        data = response.json()
        task_id = data['task_id']
        print(f"   ✅ Job submitted successfully")
        print(f"   Task ID: {task_id}")
        return task_id
    else:
        print(f"   ❌ Failed to submit job: {response.text}")
        return None


def submit_llm_job_with_webhook(url, query, webhook_url, include_data=False, schema=None, provider=None):
    """
    Submit an LLM extraction job with webhook notification.

    Args:
        url: URL to extract content from
        query: Instruction for the LLM (e.g., "Extract article title and author")
        webhook_url: URL to receive webhook notifications
        include_data: Whether to include full results in webhook payload
        schema: Optional JSON schema for structured extraction
        provider: Optional LLM provider (e.g., "openai/gpt-4o-mini")

    Returns:
        task_id: The job's task identifier
    """
    payload = {
        "url": url,
        "q": query,
        "cache": False,
        "webhook_config": {
            "webhook_url": webhook_url,
            "webhook_data_in_payload": include_data,
            # Optional: Add custom headers for authentication
            # "webhook_headers": {
            #     "X-Webhook-Secret": "your-secret-token"
            # }
        }
    }

    if schema:
        payload["schema"] = schema

    if provider:
        payload["provider"] = provider

    print(f"\n🤖 Submitting LLM extraction job...")
    print(f"   URL: {url}")
    print(f"   Query: {query}")
    print(f"   Webhook: {webhook_url}")
    print(f"   Include data: {include_data}")
    if provider:
        print(f"   Provider: {provider}")

    response = requests.post(
        f"{CRAWL4AI_BASE_URL}/llm/job",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.ok:
        data = response.json()
        task_id = data['task_id']
        print(f"   ✅ Job submitted successfully")
        print(f"   Task ID: {task_id}")
        return task_id
    else:
        print(f"   ❌ Failed to submit job: {response.text}")
        return None


def submit_job_without_webhook(urls):
    """
    Submit a job without webhook (traditional polling approach).

    Args:
        urls: List of URLs to crawl

    Returns:
        task_id: The job's task identifier
    """
    payload = {
        "urls": urls,
        "browser_config": {"headless": True},
        "crawler_config": {"cache_mode": "bypass"}
    }

    print(f"\n🚀 Submitting crawl job (without webhook)...")
    print(f"   URLs: {urls}")

    response = requests.post(
        f"{CRAWL4AI_BASE_URL}/crawl/job",
        json=payload
    )

    if response.ok:
        data = response.json()
        task_id = data['task_id']
        print(f"   ✅ Job submitted successfully")
        print(f"   Task ID: {task_id}")
        return task_id
    else:
        print(f"   ❌ Failed to submit job: {response.text}")
        return None


def poll_job_status(task_id, timeout=60):
    """
    Poll for job status (used when webhook is not configured).

    Args:
        task_id: The job's task identifier
        timeout: Maximum time to wait in seconds
    """
    print(f"\n⏳ Polling for job status...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(f"{CRAWL4AI_BASE_URL}/crawl/job/{task_id}")

        if response.ok:
            data = response.json()
            status = data.get('status', 'unknown')

            if status == 'completed':
                print(f"   ✅ Job completed!")
                return data
            elif status == 'failed':
                print(f"   ❌ Job failed: {data.get('error', 'Unknown error')}")
                return data
            else:
                print(f"   ⏳ Status: {status}, waiting...")
                time.sleep(2)
        else:
            print(f"   ❌ Failed to get status: {response.text}")
            return None

    print(f"   ⏰ Timeout reached")
    return None


def main():
    """Run the webhook demonstration"""

    # Check if Crawl4AI is running
    try:
        health = requests.get(f"{CRAWL4AI_BASE_URL}/health", timeout=5)
        print(f"✅ Crawl4AI is running: {health.json()}")
    except:
        print(f"❌ Cannot connect to Crawl4AI at {CRAWL4AI_BASE_URL}")
        print("   Please make sure Docker container is running:")
        print("   docker run -d -p 11235:11235 --name crawl4ai unclecode/crawl4ai:latest")
        return

    # Start webhook server in background thread
    print(f"\n🌐 Starting webhook server at {WEBHOOK_BASE_URL}...")
    webhook_thread = Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()
    time.sleep(2)  # Give server time to start

    # Example 1: Job with webhook (notification only, fetch data separately)
    print(f"\n{'='*60}")
    print("Example 1: Webhook Notification Only")
    print(f"{'='*60}")
    task_id_1 = submit_crawl_job_with_webhook(
        urls=["https://example.com"],
        webhook_url=f"{WEBHOOK_BASE_URL}/webhooks/crawl-complete",
        include_data=False
    )

    # Example 2: Job with webhook (data included in payload)
    time.sleep(5)  # Wait a bit between requests
    print(f"\n{'='*60}")
    print("Example 2: Webhook with Full Data")
    print(f"{'='*60}")
    task_id_2 = submit_crawl_job_with_webhook(
        urls=["https://www.python.org"],
        webhook_url=f"{WEBHOOK_BASE_URL}/webhooks/crawl-complete",
        include_data=True
    )

    # Example 3: LLM extraction with webhook (notification only)
    time.sleep(5)  # Wait a bit between requests
    print(f"\n{'='*60}")
    print("Example 3: LLM Extraction with Webhook (Notification Only)")
    print(f"{'='*60}")
    task_id_3 = submit_llm_job_with_webhook(
        url="https://www.example.com",
        query="Extract the main heading and description from this page.",
        webhook_url=f"{WEBHOOK_BASE_URL}/webhooks/llm-complete",
        include_data=False,
        provider="openai/gpt-4o-mini"
    )

    # Example 4: LLM extraction with webhook (data included + schema)
    time.sleep(5)  # Wait a bit between requests
    print(f"\n{'='*60}")
    print("Example 4: LLM Extraction with Schema and Full Data")
    print(f"{'='*60}")

    # Define a schema for structured extraction
    schema = json.dumps({
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Page title"},
            "description": {"type": "string", "description": "Page description"}
        },
        "required": ["title"]
    })

    task_id_4 = submit_llm_job_with_webhook(
        url="https://www.python.org",
        query="Extract the title and description of this website",
        webhook_url=f"{WEBHOOK_BASE_URL}/webhooks/llm-complete",
        include_data=True,
        schema=schema,
        provider="openai/gpt-4o-mini"
    )

    # Example 5: Traditional polling (no webhook)
    time.sleep(5)  # Wait a bit between requests
    print(f"\n{'='*60}")
    print("Example 5: Traditional Polling (No Webhook)")
    print(f"{'='*60}")
    task_id_5 = submit_job_without_webhook(
        urls=["https://github.com"]
    )
    if task_id_5:
        result = poll_job_status(task_id_5)
        if result and result.get('status') == 'completed':
            print(f"   ✅ Results retrieved via polling")

    # Wait for webhooks to arrive
    print(f"\n⏳ Waiting for webhooks to be received...")
    time.sleep(30)  # Give jobs time to complete and webhooks to arrive (longer for LLM)

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"Total webhooks received: {len(received_webhooks)}")

    crawl_webhooks = [w for w in received_webhooks if w['task_type'] == 'crawl']
    llm_webhooks = [w for w in received_webhooks if w['task_type'] == 'llm_extraction']

    print(f"\n📊 Breakdown:")
    print(f"   - Crawl webhooks: {len(crawl_webhooks)}")
    print(f"   - LLM extraction webhooks: {len(llm_webhooks)}")

    print(f"\n📋 Details:")
    for i, webhook in enumerate(received_webhooks, 1):
        task_type = webhook['task_type']
        icon = "🕷️" if task_type == "crawl" else "🤖"
        print(f"{i}. {icon} Task {webhook['task_id']}: {webhook['status']} ({task_type})")

    print(f"\n✅ Demo completed!")
    print(f"\n💡 Pro tips:")
    print(f"   - In production, your webhook URL should be publicly accessible")
    print(f"     (e.g., https://myapp.com/webhooks) or use ngrok for testing")
    print(f"   - Both /crawl/job and /llm/job support the same webhook configuration")
    print(f"   - Use webhook_data_in_payload=true to get results directly in the webhook")
    print(f"   - LLM jobs may take longer, adjust timeouts accordingly")


if __name__ == "__main__":
    main()
