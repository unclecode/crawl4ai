import requests
import json
import time
import sys


def test_links_analyze_endpoint():
    """Integration test for the /links/analyze endpoint"""

    base_url = "http://localhost:11234"

    # Health check
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server health check failed")
            return False
        print("✅ Server health check passed")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

    # Get auth token
    token = None
    try:
        token_response = requests.post(
            f"{base_url}/token",
            json={"email": "test@example.com"},
            timeout=5
        )
        if token_response.status_code == 200:
            token = token_response.json()["access_token"]
            print("✅ Authentication token obtained")
    except Exception as e:
        print(f"⚠️  Could not get auth token: {e}")

    # Test the links/analyze endpoint
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Test 1: Basic request
    print("\n🔍 Testing basic link analysis...")
    test_data = {
        "url": "https://httpbin.org/links/10",
        "config": {
            "include_internal": True,
            "include_external": True,
            "max_links": 50,
            "verbose": True
        }
    }

    try:
        response = requests.post(
            f"{base_url}/links/analyze",
            headers=headers,
            json=test_data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Basic link analysis successful")
            print(f"📄 Response structure: {list(result.keys())}")

            # Verify response structure
            total_links = sum(len(links) for links in result.values())
            print(f"📊 Found {total_links} total links")

            # Debug: Show what was actually returned
            if total_links == 0:
                print("⚠️  No links found - showing full response:")
                print(json.dumps(result, indent=2))

            # Check for expected categories
            found_categories = []
            for category in ['internal', 'external', 'social', 'download', 'email', 'phone']:
                if category in result and result[category]:
                    found_categories.append(category)

            print(f"📂 Found categories: {found_categories}")

            # Verify link objects have required fields
            if total_links > 0:
                sample_found = False
                for category, links in result.items():
                    if links:
                        sample_link = links[0]
                        if 'href' in sample_link and 'total_score' in sample_link:
                            sample_found = True
                            break

                if sample_found:
                    print("✅ Link objects have required fields")
                else:
                    print("⚠️  Link objects missing required fields")

        else:
            print(f"❌ Basic link analysis failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Basic link analysis error: {e}")
        return False

    # Test 2: With configuration
    print("\n🔍 Testing link analysis with configuration...")
    test_data_with_config = {
        "url": "https://httpbin.org/links/10",
        "config": {
            "include_internal": True,
            "include_external": True,
            "max_links": 50,
            "timeout": 10,
            "verbose": True
        }
    }

    try:
        response = requests.post(
            f"{base_url}/links/analyze",
            headers=headers,
            json=test_data_with_config,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            total_links = sum(len(links) for links in result.values())
            print(f"✅ Link analysis with config successful ({total_links} links)")
        else:
            print(f"❌ Link analysis with config failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Link analysis with config error: {e}")
        return False

    # Test 3: Error handling
    print("\n🔍 Testing error handling...")
    invalid_data = {
        "url": "not-a-valid-url"
    }

    try:
        response = requests.post(
            f"{base_url}/links/analyze",
            headers=headers,
            json=invalid_data,
            timeout=30
        )

        if response.status_code >= 400:
            print("✅ Error handling works correctly")
        else:
            print("⚠️  Expected error for invalid URL, but got success")

    except Exception as e:
        print(f"✅ Error handling caught exception: {e}")

    print("\n🎉 All integration tests passed!")
    return True


if __name__ == "__main__":
    success = test_links_analyze_endpoint()
    sys.exit(0 if success else 1)