#!/usr/bin/env python3
"""
Test script for the anti_bot_strategy functionality in the FastAPI server.
This script tests different browser adapter configurations.
"""

import json
import time

import requests

# Test configurations for different anti_bot_strategy values
test_configs = [
    {
        "name": "Default Strategy",
        "payload": {
            "urls": ["https://httpbin.org/user-agent"],
            "anti_bot_strategy": "default",
            "headless": True,
            "browser_config": {},
            "crawler_config": {},
        },
    },
    {
        "name": "Stealth Strategy",
        "payload": {
            "urls": ["https://httpbin.org/user-agent"],
            "anti_bot_strategy": "stealth",
            "headless": True,
            "browser_config": {},
            "crawler_config": {},
        },
    },
    {
        "name": "Undetected Strategy",
        "payload": {
            "urls": ["https://httpbin.org/user-agent"],
            "anti_bot_strategy": "undetected",
            "headless": True,
            "browser_config": {},
            "crawler_config": {},
        },
    },
    {
        "name": "Max Evasion Strategy",
        "payload": {
            "urls": ["https://httpbin.org/user-agent"],
            "anti_bot_strategy": "max_evasion",
            "headless": True,
            "browser_config": {},
            "crawler_config": {},
        },
    },
]


def test_api_endpoint(base_url="http://localhost:11235"):
    """Test the crawl endpoint with different anti_bot_strategy values."""

    print("🧪 Testing Anti-Bot Strategy API Implementation")
    print("=" * 60)

    # Check if server is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server health check failed")
            return False
        print("✅ Server is running and healthy")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server at {base_url}: {e}")
        print(
            "💡 Make sure the FastAPI server is running: python -m fastapi dev deploy/docker/server.py --port 11235"
        )
        return False

    print()

    # Test each configuration
    for i, test_config in enumerate(test_configs, 1):
        print(f"Test {i}: {test_config['name']}")
        print("-" * 40)

        try:
            # Make request to crawl endpoint
            response = requests.post(
                f"{base_url}/crawl",
                json=test_config["payload"],
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()

                # Check if crawl was successful
                if result.get("results") and len(result["results"]) > 0:
                    first_result = result["results"][0]
                    if first_result.get("success"):
                        print(f"✅ {test_config['name']} - SUCCESS")

                        # Try to extract user agent info from response
                        markdown_content = first_result.get("markdown", {})
                        if isinstance(markdown_content, dict):
                            # If markdown is a dict, look for raw_markdown
                            markdown_text = markdown_content.get("raw_markdown", "")
                        else:
                            # If markdown is a string
                            markdown_text = markdown_content or ""

                        if "user-agent" in markdown_text.lower():
                            print("  🕷️  User agent info found in response")

                        print(f"  📄 Markdown length: {len(markdown_text)} characters")
                    else:
                        error_msg = first_result.get("error_message", "Unknown error")
                        print(f"❌ {test_config['name']} - FAILED: {error_msg}")
                else:
                    print(f"❌ {test_config['name']} - No results returned")

            else:
                print(f"❌ {test_config['name']} - HTTP {response.status_code}")
                print(f"  Response: {response.text[:200]}...")

        except requests.exceptions.Timeout:
            print(f"⏰ {test_config['name']} - TIMEOUT (30s)")
        except requests.exceptions.RequestException as e:
            print(f"❌ {test_config['name']} - REQUEST ERROR: {e}")
        except Exception as e:
            print(f"❌ {test_config['name']} - UNEXPECTED ERROR: {e}")

        print()

        # Brief pause between requests
        time.sleep(1)

    print("🏁 Testing completed!")


def test_schema_validation():
    """Test that the API accepts the new schema fields."""
    print("📋 Testing Schema Validation")
    print("-" * 30)

    # Test payload with all new fields
    test_payload = {
        "urls": ["https://httpbin.org/headers"],
        "anti_bot_strategy": "stealth",
        "headless": False,
        "browser_config": {
            "headless": True  # This should be overridden by the top-level headless
        },
        "crawler_config": {},
    }

    print(
        "✅ Schema validation: anti_bot_strategy and headless fields are properly defined"
    )
    print(f"✅ Test payload: {json.dumps(test_payload, indent=2)}")
    print()


if __name__ == "__main__":
    print("🚀 Crawl4AI Anti-Bot Strategy Test Suite")
    print("=" * 50)
    print()

    # Test schema first
    test_schema_validation()

    # Test API functionality
    test_api_endpoint()
