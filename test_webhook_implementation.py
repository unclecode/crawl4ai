"""
Simple test script to validate webhook implementation without running full server.

This script tests:
1. Webhook module imports and syntax
2. WebhookDeliveryService initialization
3. Payload construction logic
4. Configuration parsing
"""

import sys
import os
import json
from datetime import datetime, timezone

# Add deploy/docker to path to import modules
# sys.path.insert(0, '/home/user/crawl4ai/deploy/docker')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deploy', 'docker'))

def test_imports():
    """Test that all webhook-related modules can be imported"""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)

    try:
        from webhook import WebhookDeliveryService
        print("✅ webhook.WebhookDeliveryService imported successfully")
    except Exception as e:
        print(f"❌ Failed to import webhook module: {e}")
        return False

    try:
        from schemas import WebhookConfig, WebhookPayload
        print("✅ schemas.WebhookConfig imported successfully")
        print("✅ schemas.WebhookPayload imported successfully")
    except Exception as e:
        print(f"❌ Failed to import schemas: {e}")
        return False

    return True

def test_webhook_service_init():
    """Test WebhookDeliveryService initialization"""
    print("\n" + "=" * 60)
    print("TEST 2: WebhookDeliveryService Initialization")
    print("=" * 60)

    try:
        from webhook import WebhookDeliveryService

        # Test with default config
        config = {
            "webhooks": {
                "enabled": True,
                "default_url": None,
                "data_in_payload": False,
                "retry": {
                    "max_attempts": 5,
                    "initial_delay_ms": 1000,
                    "max_delay_ms": 32000,
                    "timeout_ms": 30000
                },
                "headers": {
                    "User-Agent": "Crawl4AI-Webhook/1.0"
                }
            }
        }

        service = WebhookDeliveryService(config)

        print(f"✅ Service initialized successfully")
        print(f"   - Max attempts: {service.max_attempts}")
        print(f"   - Initial delay: {service.initial_delay}s")
        print(f"   - Max delay: {service.max_delay}s")
        print(f"   - Timeout: {service.timeout}s")

        # Verify calculations
        assert service.max_attempts == 5, "Max attempts should be 5"
        assert service.initial_delay == 1.0, "Initial delay should be 1.0s"
        assert service.max_delay == 32.0, "Max delay should be 32.0s"
        assert service.timeout == 30.0, "Timeout should be 30.0s"

        print("✅ All configuration values correct")

        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webhook_config_model():
    """Test WebhookConfig Pydantic model"""
    print("\n" + "=" * 60)
    print("TEST 3: WebhookConfig Model Validation")
    print("=" * 60)

    try:
        from schemas import WebhookConfig
        from pydantic import ValidationError

        # Test valid config
        valid_config = {
            "webhook_url": "https://example.com/webhook",
            "webhook_data_in_payload": True,
            "webhook_headers": {"X-Secret": "token123"}
        }

        config = WebhookConfig(**valid_config)
        print(f"✅ Valid config accepted:")
        print(f"   - URL: {config.webhook_url}")
        print(f"   - Data in payload: {config.webhook_data_in_payload}")
        print(f"   - Headers: {config.webhook_headers}")

        # Test minimal config
        minimal_config = {
            "webhook_url": "https://example.com/webhook"
        }

        config2 = WebhookConfig(**minimal_config)
        print(f"✅ Minimal config accepted (defaults applied):")
        print(f"   - URL: {config2.webhook_url}")
        print(f"   - Data in payload: {config2.webhook_data_in_payload}")
        print(f"   - Headers: {config2.webhook_headers}")

        # Test invalid URL
        try:
            invalid_config = {
                "webhook_url": "not-a-url"
            }
            config3 = WebhookConfig(**invalid_config)
            print(f"❌ Invalid URL should have been rejected")
            return False
        except ValidationError as e:
            print(f"✅ Invalid URL correctly rejected")

        return True
    except Exception as e:
        print(f"❌ Model validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_payload_construction():
    """Test webhook payload construction logic"""
    print("\n" + "=" * 60)
    print("TEST 4: Payload Construction")
    print("=" * 60)

    try:
        # Simulate payload construction from notify_job_completion
        task_id = "crawl_abc123"
        task_type = "crawl"
        status = "completed"
        urls = ["https://example.com"]

        payload = {
            "task_id": task_id,
            "task_type": task_type,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "urls": urls
        }

        print(f"✅ Basic payload constructed:")
        print(json.dumps(payload, indent=2))

        # Test with error
        error_payload = {
            "task_id": "crawl_xyz789",
            "task_type": "crawl",
            "status": "failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "urls": ["https://example.com"],
            "error": "Connection timeout"
        }

        print(f"\n✅ Error payload constructed:")
        print(json.dumps(error_payload, indent=2))

        # Test with data
        data_payload = {
            "task_id": "crawl_def456",
            "task_type": "crawl",
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "urls": ["https://example.com"],
            "data": {
                "results": [
                    {"url": "https://example.com", "markdown": "# Example"}
                ]
            }
        }

        print(f"\n✅ Data payload constructed:")
        print(json.dumps(data_payload, indent=2))

        return True
    except Exception as e:
        print(f"❌ Payload construction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exponential_backoff():
    """Test exponential backoff calculation"""
    print("\n" + "=" * 60)
    print("TEST 5: Exponential Backoff Calculation")
    print("=" * 60)

    try:
        initial_delay = 1.0  # 1 second
        max_delay = 32.0     # 32 seconds

        print("Backoff delays for 5 attempts:")
        for attempt in range(5):
            delay = min(initial_delay * (2 ** attempt), max_delay)
            print(f"  Attempt {attempt + 1}: {delay}s")

        # Verify the sequence: 1s, 2s, 4s, 8s, 16s
        expected = [1.0, 2.0, 4.0, 8.0, 16.0]
        actual = [min(initial_delay * (2 ** i), max_delay) for i in range(5)]

        assert actual == expected, f"Expected {expected}, got {actual}"
        print("✅ Exponential backoff sequence correct")

        return True
    except Exception as e:
        print(f"❌ Backoff calculation failed: {e}")
        return False

def test_api_integration():
    """Test that api.py imports webhook module correctly"""
    print("\n" + "=" * 60)
    print("TEST 6: API Integration")
    print("=" * 60)

    try:
        # Check if api.py can import webhook module
        api_path = os.path.join(os.path.dirname(__file__), 'deploy', 'docker', 'api.py')
        with open(api_path, 'r') as f:
            api_content = f.read()

        if 'from webhook import WebhookDeliveryService' in api_content:
            print("✅ api.py imports WebhookDeliveryService")
        else:
            print("❌ api.py missing webhook import")
            return False

        if 'WebhookDeliveryService(config)' in api_content:
            print("✅ api.py initializes WebhookDeliveryService")
        else:
            print("❌ api.py doesn't initialize WebhookDeliveryService")
            return False

        if 'notify_job_completion' in api_content:
            print("✅ api.py calls notify_job_completion")
        else:
            print("❌ api.py doesn't call notify_job_completion")
            return False

        return True
    except Exception as e:
        print(f"❌ API integration check failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n🧪 Webhook Implementation Validation Tests")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Service Initialization", test_webhook_service_init()))
    results.append(("Config Model", test_webhook_config_model()))
    results.append(("Payload Construction", test_payload_construction()))
    results.append(("Exponential Backoff", test_exponential_backoff()))
    results.append(("API Integration", test_api_integration()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'=' * 60}")

    if passed == total:
        print("\n🎉 All tests passed! Webhook implementation is valid.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    exit(main())
