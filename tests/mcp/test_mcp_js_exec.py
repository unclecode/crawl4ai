#!/usr/bin/env python3
"""
Test script to verify JavaScript execution returns actual values.
This test can be run against a running Docker server.
"""

import requests
import json
import time

def test_js_execution_returns_values():
    """Test that JavaScript execution returns actual values"""

    # Test with a simple HTML page (using httpbin which returns HTML)
    url = "https://httpbin.org/html"

    # Scripts that should return actual values
    scripts = [
        "return document.title || 'No title found'",  # Handle empty title case
        "return document.querySelectorAll('h1').length",
        "return Array.from(document.querySelectorAll('p')).map(p => p.textContent.substring(0, 50))",
        "return 'test string'",  # Simple string test
        "return 42"  # Simple number test
    ]

    response = requests.post("http://localhost:11235/execute_js", json={
        "url": url,
        "scripts": scripts
    })

    if response.status_code != 200:
        print(f"❌ Request failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False

    result = response.json()

    # Check if js_execution_result exists
    js_result = result.get('js_execution_result')
    if not js_result:
        print("❌ No js_execution_result in response")
        return False

    # Check if return_values exists (our fix)
    return_values = js_result.get('return_values')
    if not return_values:
        print("❌ No return_values in js_execution_result")
        print(f"js_execution_result keys: {list(js_result.keys())}")
        return False

    print("✅ return_values found in response!")
    print(f"Number of return values: {len(return_values)}")

    # Verify we have the expected number of return values
    if len(return_values) != len(scripts):
        print(f"❌ Expected {len(scripts)} return values, got {len(return_values)}")
        return False

    # Print the actual return values
    for i, value in enumerate(return_values):
        print(f"Script {i+1} returned: {repr(value)}")

    # Verify the first script (document.title) returns a string
    title = return_values[0]
    if title is None:
        print("⚠️  Title is None (empty title on this page)")
    elif not isinstance(title, str):
        print(f"❌ Expected title to be string, got {type(title)}")
        return False
    else:
        print(f"✅ Page title: '{title}'")

    # Verify the second script (h1 count) returns a number
    h1_count = return_values[1]
    if not isinstance(h1_count, (int, float)):
        print(f"❌ Expected h1_count to be number, got {type(h1_count)}")
        return False

    print(f"✅ H1 count: {h1_count}")

    # Verify the third script returns an array
    paragraphs = return_values[2]
    if not isinstance(paragraphs, list):
        print(f"❌ Expected paragraphs to be list, got {type(paragraphs)}")
        return False

    print(f"✅ Found {len(paragraphs)} paragraph excerpts")

    # Verify the fourth script (simple string) returns a string
    test_str = return_values[3]
    if test_str != 'test string':
        print(f"❌ Expected 'test string', got {repr(test_str)}")
        return False

    print(f"✅ Simple string test: '{test_str}'")

    # Verify the fifth script (simple number) returns a number
    test_num = return_values[4]
    if test_num != 42:
        print(f"❌ Expected 42, got {repr(test_num)}")
        return False

    print(f"✅ Simple number test: {test_num}")

    print("🎉 All tests passed! JavaScript execution now returns actual values.")
    return True

def test_error_handling():
    """Test that errors are still properly handled"""

    scripts = [
        "return document.title || 'No title found'",  # This should work
        "throw new Error('Test error')",  # This should fail
        "return 'success after error'"  # This should still work
    ]

    response = requests.post("http://localhost:11235/execute_js", json={
        "url": "https://httpbin.org/html",
        "scripts": scripts
    })

    if response.status_code != 200:
        print(f"❌ Error test request failed with status {response.status_code}")
        return False

    result = response.json()
    js_result = result.get('js_execution_result', {})
    return_values = js_result.get('return_values', [])

    print(f"Error test return values: {return_values}")

    # Should have 3 entries: success, error object, success
    if len(return_values) != 3:
        print(f"❌ Expected 3 return values in error test, got {len(return_values)}")
        return False

    # First should be the title (string)
    if not isinstance(return_values[0], str):
        print(f"❌ First value should be title string, got {type(return_values[0])}")
        return False

    # Second should be an error object
    if not isinstance(return_values[1], dict) or 'error' not in str(return_values[1]).lower():
        print(f"❌ Second value should be error object, got {return_values[1]}")
        return False

    # Third should be success string
    if return_values[2] != 'success after error':
        print(f"❌ Third value should be 'success after error', got {return_values[2]}")
        return False

    print("✅ Error handling test passed!")
    return True

if __name__ == "__main__":
    print("Testing JavaScript execution fix...")
    print("Make sure the Docker server is running on localhost:11235")
    print()

    # Test basic functionality
    success1 = test_js_execution_returns_values()
    print()

    # Test error handling
    success2 = test_error_handling()
    print()

    if success1 and success2:
        print("🎉 All tests passed! The fix is working correctly.")
    else:
        print("❌ Some tests failed. Check the output above.")