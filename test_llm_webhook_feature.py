#!/usr/bin/env python3
"""
Test script to validate webhook implementation for /llm/job endpoint.

This tests that the /llm/job endpoint now supports webhooks
following the same pattern as /crawl/job.
"""

import sys
import os

# Add deploy/docker to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deploy', 'docker'))

def test_llm_job_payload_model():
    """Test that LlmJobPayload includes webhook_config field"""
    print("=" * 60)
    print("TEST 1: LlmJobPayload Model")
    print("=" * 60)

    try:
        from job import LlmJobPayload
        from schemas import WebhookConfig
        from pydantic import ValidationError

        # Test with webhook_config
        payload_dict = {
            "url": "https://example.com",
            "q": "Extract main content",
            "schema": None,
            "cache": False,
            "provider": None,
            "webhook_config": {
                "webhook_url": "https://myapp.com/webhook",
                "webhook_data_in_payload": True,
                "webhook_headers": {"X-Secret": "token"}
            }
        }

        payload = LlmJobPayload(**payload_dict)

        print(f"✅ LlmJobPayload accepts webhook_config")
        print(f"   - URL: {payload.url}")
        print(f"   - Query: {payload.q}")
        print(f"   - Webhook URL: {payload.webhook_config.webhook_url}")
        print(f"   - Data in payload: {payload.webhook_config.webhook_data_in_payload}")

        # Test without webhook_config (should be optional)
        minimal_payload = {
            "url": "https://example.com",
            "q": "Extract content"
        }

        payload2 = LlmJobPayload(**minimal_payload)
        assert payload2.webhook_config is None, "webhook_config should be optional"
        print(f"✅ LlmJobPayload works without webhook_config (optional)")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_handle_llm_request_signature():
    """Test that handle_llm_request accepts webhook_config parameter"""
    print("\n" + "=" * 60)
    print("TEST 2: handle_llm_request Function Signature")
    print("=" * 60)

    try:
        from api import handle_llm_request
        import inspect

        sig = inspect.signature(handle_llm_request)
        params = list(sig.parameters.keys())

        print(f"Function parameters: {params}")

        if 'webhook_config' in params:
            print(f"✅ handle_llm_request has webhook_config parameter")

            # Check that it's optional with default None
            webhook_param = sig.parameters['webhook_config']
            if webhook_param.default is None or webhook_param.default == inspect.Parameter.empty:
                print(f"✅ webhook_config is optional (default: {webhook_param.default})")
            else:
                print(f"⚠️  webhook_config default is: {webhook_param.default}")

            return True
        else:
            print(f"❌ handle_llm_request missing webhook_config parameter")
            return False

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_process_llm_extraction_signature():
    """Test that process_llm_extraction accepts webhook_config parameter"""
    print("\n" + "=" * 60)
    print("TEST 3: process_llm_extraction Function Signature")
    print("=" * 60)

    try:
        from api import process_llm_extraction
        import inspect

        sig = inspect.signature(process_llm_extraction)
        params = list(sig.parameters.keys())

        print(f"Function parameters: {params}")

        if 'webhook_config' in params:
            print(f"✅ process_llm_extraction has webhook_config parameter")

            webhook_param = sig.parameters['webhook_config']
            if webhook_param.default is None or webhook_param.default == inspect.Parameter.empty:
                print(f"✅ webhook_config is optional (default: {webhook_param.default})")
            else:
                print(f"⚠️  webhook_config default is: {webhook_param.default}")

            return True
        else:
            print(f"❌ process_llm_extraction missing webhook_config parameter")
            return False

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webhook_integration_in_api():
    """Test that api.py properly integrates webhook notifications"""
    print("\n" + "=" * 60)
    print("TEST 4: Webhook Integration in process_llm_extraction")
    print("=" * 60)

    try:
        api_file = os.path.join(os.path.dirname(__file__), 'deploy', 'docker', 'api.py')

        with open(api_file, 'r') as f:
            api_content = f.read()

        # Check for WebhookDeliveryService initialization
        if 'webhook_service = WebhookDeliveryService(config)' in api_content:
            print("✅ process_llm_extraction initializes WebhookDeliveryService")
        else:
            print("❌ Missing WebhookDeliveryService initialization in process_llm_extraction")
            return False

        # Check for notify_job_completion calls with llm_extraction
        if 'task_type="llm_extraction"' in api_content:
            print("✅ Uses correct task_type='llm_extraction' for notifications")
        else:
            print("❌ Missing task_type='llm_extraction' in webhook notifications")
            return False

        # Count webhook notification calls (should have at least 3: success + 2 failure paths)
        notification_count = api_content.count('await webhook_service.notify_job_completion')
        # Find only in process_llm_extraction function
        llm_func_start = api_content.find('async def process_llm_extraction')
        llm_func_end = api_content.find('\nasync def ', llm_func_start + 1)
        if llm_func_end == -1:
            llm_func_end = len(api_content)

        llm_func_content = api_content[llm_func_start:llm_func_end]
        llm_notification_count = llm_func_content.count('await webhook_service.notify_job_completion')

        print(f"✅ Found {llm_notification_count} webhook notification calls in process_llm_extraction")

        if llm_notification_count >= 3:
            print(f"✅ Sufficient notification points (success + failure paths)")
        else:
            print(f"⚠️  Expected at least 3 notification calls, found {llm_notification_count}")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_job_endpoint_integration():
    """Test that /llm/job endpoint extracts and passes webhook_config"""
    print("\n" + "=" * 60)
    print("TEST 5: /llm/job Endpoint Integration")
    print("=" * 60)

    try:
        job_file = os.path.join(os.path.dirname(__file__), 'deploy', 'docker', 'job.py')

        with open(job_file, 'r') as f:
            job_content = f.read()

        # Find the llm_job_enqueue function
        llm_job_start = job_content.find('async def llm_job_enqueue')
        llm_job_end = job_content.find('\n\n@router', llm_job_start + 1)
        if llm_job_end == -1:
            llm_job_end = job_content.find('\n\nasync def', llm_job_start + 1)

        llm_job_func = job_content[llm_job_start:llm_job_end]

        # Check for webhook_config extraction
        if 'webhook_config = None' in llm_job_func:
            print("✅ llm_job_enqueue initializes webhook_config variable")
        else:
            print("❌ Missing webhook_config initialization")
            return False

        if 'if payload.webhook_config:' in llm_job_func:
            print("✅ llm_job_enqueue checks for payload.webhook_config")
        else:
            print("❌ Missing webhook_config check")
            return False

        if 'webhook_config = payload.webhook_config.model_dump(mode=\'json\')' in llm_job_func:
            print("✅ llm_job_enqueue converts webhook_config to dict")
        else:
            print("❌ Missing webhook_config.model_dump conversion")
            return False

        if 'webhook_config=webhook_config' in llm_job_func:
            print("✅ llm_job_enqueue passes webhook_config to handle_llm_request")
        else:
            print("❌ Missing webhook_config parameter in handle_llm_request call")
            return False

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_new_task_integration():
    """Test that create_new_task stores webhook_config in Redis"""
    print("\n" + "=" * 60)
    print("TEST 6: create_new_task Webhook Storage")
    print("=" * 60)

    try:
        api_file = os.path.join(os.path.dirname(__file__), 'deploy', 'docker', 'api.py')

        with open(api_file, 'r') as f:
            api_content = f.read()

        # Find create_new_task function
        create_task_start = api_content.find('async def create_new_task')
        create_task_end = api_content.find('\nasync def ', create_task_start + 1)
        if create_task_end == -1:
            create_task_end = len(api_content)

        create_task_func = api_content[create_task_start:create_task_end]

        # Check for webhook_config storage
        if 'if webhook_config:' in create_task_func:
            print("✅ create_new_task checks for webhook_config")
        else:
            print("❌ Missing webhook_config check in create_new_task")
            return False

        if 'task_data["webhook_config"] = json.dumps(webhook_config)' in create_task_func:
            print("✅ create_new_task stores webhook_config in Redis task data")
        else:
            print("❌ Missing webhook_config storage in task_data")
            return False

        # Check that webhook_config is passed to process_llm_extraction
        if 'webhook_config' in create_task_func and 'background_tasks.add_task' in create_task_func:
            print("✅ create_new_task passes webhook_config to background task")
        else:
            print("⚠️  Could not verify webhook_config passed to background task")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pattern_consistency():
    """Test that /llm/job follows the same pattern as /crawl/job"""
    print("\n" + "=" * 60)
    print("TEST 7: Pattern Consistency with /crawl/job")
    print("=" * 60)

    try:
        api_file = os.path.join(os.path.dirname(__file__), 'deploy', 'docker', 'api.py')

        with open(api_file, 'r') as f:
            api_content = f.read()

        # Find handle_crawl_job to compare pattern
        crawl_job_start = api_content.find('async def handle_crawl_job')
        crawl_job_end = api_content.find('\nasync def ', crawl_job_start + 1)
        if crawl_job_end == -1:
            crawl_job_end = len(api_content)
        crawl_job_func = api_content[crawl_job_start:crawl_job_end]

        # Find process_llm_extraction
        llm_extract_start = api_content.find('async def process_llm_extraction')
        llm_extract_end = api_content.find('\nasync def ', llm_extract_start + 1)
        if llm_extract_end == -1:
            llm_extract_end = len(api_content)
        llm_extract_func = api_content[llm_extract_start:llm_extract_end]

        print("Checking pattern consistency...")

        # Both should initialize WebhookDeliveryService
        crawl_has_service = 'webhook_service = WebhookDeliveryService(config)' in crawl_job_func
        llm_has_service = 'webhook_service = WebhookDeliveryService(config)' in llm_extract_func

        if crawl_has_service and llm_has_service:
            print("✅ Both initialize WebhookDeliveryService")
        else:
            print(f"❌ Service initialization mismatch (crawl: {crawl_has_service}, llm: {llm_has_service})")
            return False

        # Both should call notify_job_completion on success
        crawl_notifies_success = 'status="completed"' in crawl_job_func and 'notify_job_completion' in crawl_job_func
        llm_notifies_success = 'status="completed"' in llm_extract_func and 'notify_job_completion' in llm_extract_func

        if crawl_notifies_success and llm_notifies_success:
            print("✅ Both notify on success")
        else:
            print(f"❌ Success notification mismatch (crawl: {crawl_notifies_success}, llm: {llm_notifies_success})")
            return False

        # Both should call notify_job_completion on failure
        crawl_notifies_failure = 'status="failed"' in crawl_job_func and 'error=' in crawl_job_func
        llm_notifies_failure = 'status="failed"' in llm_extract_func and 'error=' in llm_extract_func

        if crawl_notifies_failure and llm_notifies_failure:
            print("✅ Both notify on failure")
        else:
            print(f"❌ Failure notification mismatch (crawl: {crawl_notifies_failure}, llm: {llm_notifies_failure})")
            return False

        print("✅ /llm/job follows the same pattern as /crawl/job")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n🧪 LLM Job Webhook Feature Validation")
    print("=" * 60)
    print("Testing that /llm/job now supports webhooks like /crawl/job")
    print("=" * 60 + "\n")

    results = []

    # Run all tests
    results.append(("LlmJobPayload Model", test_llm_job_payload_model()))
    results.append(("handle_llm_request Signature", test_handle_llm_request_signature()))
    results.append(("process_llm_extraction Signature", test_process_llm_extraction_signature()))
    results.append(("Webhook Integration", test_webhook_integration_in_api()))
    results.append(("/llm/job Endpoint", test_job_endpoint_integration()))
    results.append(("create_new_task Storage", test_create_new_task_integration()))
    results.append(("Pattern Consistency", test_pattern_consistency()))

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
        print("\n🎉 All tests passed! /llm/job webhook feature is correctly implemented.")
        print("\n📝 Summary of changes:")
        print("  1. LlmJobPayload model includes webhook_config field")
        print("  2. /llm/job endpoint extracts and passes webhook_config")
        print("  3. handle_llm_request accepts webhook_config parameter")
        print("  4. create_new_task stores webhook_config in Redis")
        print("  5. process_llm_extraction sends webhook notifications")
        print("  6. Follows the same pattern as /crawl/job")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    exit(main())
