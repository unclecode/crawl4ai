#!/usr/bin/env python3
"""
Test client for demonstrating user-provided hooks in Crawl4AI Docker API
"""

import requests
import json
from typing import Dict, Any


API_BASE_URL = "http://localhost:11234"  # Adjust if needed


def test_hooks_info():
    """Get information about available hooks"""
    print("=" * 70)
    print("Testing: GET /hooks/info")
    print("=" * 70)
    
    response = requests.get(f"{API_BASE_URL}/hooks/info")
    if response.status_code == 200:
        data = response.json()
        print("Available Hook Points:")
        for hook, info in data['available_hooks'].items():
            print(f"\n{hook}:")
            print(f"  Parameters: {', '.join(info['parameters'])}")
            print(f"  Description: {info['description']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def test_basic_crawl_with_hooks():
    """Test basic crawling with user-provided hooks"""
    print("\n" + "=" * 70)
    print("Testing: POST /crawl with hooks")
    print("=" * 70)
    
    # Define hooks as Python code strings
    hooks_code = {
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    print("Hook: Setting up page context")
    # Block images to speed up crawling
    await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
    print("Hook: Images blocked")
    return page
""",
        
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    print("Hook: Before retrieving HTML")
    # Scroll to bottom to load lazy content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    print("Hook: Scrolled to bottom")
    return page
""",
        
        "before_goto": """
async def hook(page, context, url, **kwargs):
    print(f"Hook: About to navigate to {url}")
    # Add custom headers
    await page.set_extra_http_headers({
        'X-Test-Header': 'crawl4ai-hooks-test'
    })
    return page
"""
    }
    
    # Create request payload
    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_code,
            "timeout": 30
        }
    }
    
    print("Sending request with hooks...")
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Crawl successful!")
        
        # Check hooks status
        if 'hooks' in data:
            hooks_info = data['hooks']
            print("\nHooks Execution Summary:")
            print(f"  Status: {hooks_info['status']['status']}")
            print(f"  Attached hooks: {', '.join(hooks_info['status']['attached_hooks'])}")
            
            if hooks_info['status']['validation_errors']:
                print("\n⚠️ Validation Errors:")
                for error in hooks_info['status']['validation_errors']:
                    print(f"  - {error['hook_point']}: {error['error']}")
            
            if 'summary' in hooks_info:
                summary = hooks_info['summary']
                print(f"\nExecution Statistics:")
                print(f"  Total executions: {summary['total_executions']}")
                print(f"  Successful: {summary['successful']}")
                print(f"  Failed: {summary['failed']}")
                print(f"  Timed out: {summary['timed_out']}")
                print(f"  Success rate: {summary['success_rate']:.1f}%")
            
            if hooks_info['execution_log']:
                print("\nExecution Log:")
                for log_entry in hooks_info['execution_log']:
                    status_icon = "✅" if log_entry['status'] == 'success' else "❌"
                    print(f"  {status_icon} {log_entry['hook_point']}: {log_entry['status']} ({log_entry.get('execution_time', 0):.2f}s)")
            
            if hooks_info['errors']:
                print("\n❌ Hook Errors:")
                for error in hooks_info['errors']:
                    print(f"  - {error['hook_point']}: {error['error']}")
        
        # Show crawl results
        if 'results' in data:
            print(f"\nCrawled {len(data['results'])} URL(s)")
            for result in data['results']:
                print(f"  - {result['url']}: {'✅' if result['success'] else '❌'}")
    
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def test_invalid_hook():
    """Test with an invalid hook to see error handling"""
    print("\n" + "=" * 70)
    print("Testing: Invalid hook handling")
    print("=" * 70)
    
    # Intentionally broken hook
    hooks_code = {
        "on_page_context_created": """
def hook(page, context):  # Missing async!
    return page
""",
        
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    # This will cause an error
    await page.non_existent_method()
    return page
"""
    }
    
    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_code,
            "timeout": 5
        }
    }
    
    print("Sending request with invalid hooks...")
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        
        if 'hooks' in data:
            hooks_info = data['hooks']
            print(f"\nHooks Status: {hooks_info['status']['status']}")
            
            if hooks_info['status']['validation_errors']:
                print("\n✅ Validation caught errors (as expected):")
                for error in hooks_info['status']['validation_errors']:
                    print(f"  - {error['hook_point']}: {error['error']}")
            
            if hooks_info['errors']:
                print("\n✅ Runtime errors handled gracefully:")
                for error in hooks_info['errors']:
                    print(f"  - {error['hook_point']}: {error['error']}")
            
            # The crawl should still succeed despite hook errors
            if data.get('success'):
                print("\n✅ Crawl succeeded despite hook errors (error isolation working!)")
    
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def test_authentication_hook():
    """Test authentication using hooks"""
    print("\n" + "=" * 70)
    print("Testing: Authentication with hooks")
    print("=" * 70)
    
    hooks_code = {
        "before_goto": """
async def hook(page, context, url, **kwargs):
    # For httpbin.org basic auth test, set Authorization header
    import base64
    
    # httpbin.org/basic-auth/user/passwd expects username="user" and password="passwd"
    credentials = base64.b64encode(b"user:passwd").decode('ascii')
    
    await page.set_extra_http_headers({
        'Authorization': f'Basic {credentials}'
    })
    
    print(f"Hook: Set Authorization header for {url}")
    return page
""",
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    # Example: Add cookies for session tracking
    await context.add_cookies([
        {
            'name': 'session_id',
            'value': 'test_session_123',
            'domain': '.httpbin.org',
            'path': '/',
            'httpOnly': True,
            'secure': True
        }
    ])
    
    print("Hook: Added session cookie")
    return page
"""
    }
    
    payload = {
        "urls": ["https://httpbin.org/basic-auth/user/passwd"],
        "hooks": {
            "code": hooks_code,
            "timeout": 30
        }
    }
    
    print("Sending request with authentication hook...")
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Crawl with authentication hook successful")
            
            # Check if hooks executed
            if 'hooks' in data:
                hooks_info = data['hooks']
                if hooks_info.get('summary', {}).get('successful', 0) > 0:
                    print(f"✅ Authentication hooks executed: {hooks_info['summary']['successful']} successful")
                
                # Check for any hook errors
                if hooks_info.get('errors'):
                    print("⚠️ Hook errors:")
                    for error in hooks_info['errors']:
                        print(f"  - {error}")
            
            # Check if authentication worked by looking at the result
            if 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                if result.get('success'):
                    print("✅ Page crawled successfully (authentication worked!)")
                    # httpbin.org/basic-auth returns JSON with authenticated=true when successful
                    if 'authenticated' in str(result.get('html', '')):
                        print("✅ Authentication confirmed in response content")
                else:
                    print(f"❌ Crawl failed: {result.get('error_message', 'Unknown error')}")
        else:
            print("❌ Request failed")
            print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Error: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Error text: {response.text[:500]}")


def test_streaming_with_hooks():
    """Test streaming endpoint with hooks"""
    print("\n" + "=" * 70)
    print("Testing: POST /crawl/stream with hooks")
    print("=" * 70)
    
    hooks_code = {
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    await page.evaluate("document.querySelectorAll('img').forEach(img => img.remove())")
    return page
"""
    }
    
    payload = {
        "urls": ["https://httpbin.org/html", "https://httpbin.org/json"],
        "hooks": {
            "code": hooks_code,
            "timeout": 10
        }
    }
    
    print("Sending streaming request with hooks...")
    
    with requests.post(f"{API_BASE_URL}/crawl/stream", json=payload, stream=True) as response:
        if response.status_code == 200:
            # Check headers for hooks status
            hooks_status = response.headers.get('X-Hooks-Status')
            if hooks_status:
                print(f"Hooks Status (from header): {hooks_status}")
            
            print("\nStreaming results:")
            for line in response.iter_lines():
                if line:
                    try:
                        result = json.loads(line)
                        if 'url' in result:
                            print(f"  Received: {result['url']}")
                        elif 'status' in result:
                            print(f"  Stream status: {result['status']}")
                    except json.JSONDecodeError:
                        print(f"  Raw: {line.decode()}")
        else:
            print(f"Error: {response.status_code}")


def test_basic_without_hooks():
    """Test basic crawl without hooks"""
    print("\n" + "=" * 70)
    print("Testing: POST /crawl with no hooks")
    print("=" * 70)

    payload = {
        "urls": ["https://httpbin.org/html", "https://httpbin.org/json"]
    }

    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.status_code}")


def main():
    """Run all tests"""
    print("🔧 Crawl4AI Docker API - Hooks Testing")
    print("=" * 70)
    
    # Test 1: Get hooks information
    # test_hooks_info()
    
    # Test 2: Basic crawl with hooks
    # test_basic_crawl_with_hooks()
    
    # Test 3: Invalid hooks (error handling)
    test_invalid_hook()
    
    # # Test 4: Authentication hook
    # test_authentication_hook()
    
    # # Test 5: Streaming with hooks
    # test_streaming_with_hooks()

    # # Test 6: Basic crawl without hooks
    # test_basic_without_hooks()

    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()