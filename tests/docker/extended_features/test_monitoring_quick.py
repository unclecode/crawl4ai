#!/usr/bin/env python3
"""
Quick test to verify monitoring endpoints are working
"""
import requests
import sys

BASE_URL = "http://localhost:11234"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/monitoring/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check: PASSED")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check: FAILED (status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Health check: ERROR - {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/monitoring/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Stats endpoint: PASSED")
            print(f"   Active crawls: {stats.get('active_crawls', 'N/A')}")
            print(f"   Total crawls: {stats.get('total_crawls', 'N/A')}")
            return True
        else:
            print(f"❌ Stats endpoint: FAILED (status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Stats endpoint: ERROR - {e}")
        return False

def test_url_stats():
    """Test URL stats endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/monitoring/stats/urls", timeout=5)
        if response.status_code == 200:
            print("✅ URL stats endpoint: PASSED")
            url_stats = response.json()
            print(f"   URLs tracked: {len(url_stats)}")
            return True
        else:
            print(f"❌ URL stats endpoint: FAILED (status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ URL stats endpoint: ERROR - {e}")
        return False

def main():
    print("=" * 60)
    print("Monitoring Endpoints Quick Test")
    print("=" * 60)
    print(f"\nTesting server at: {BASE_URL}")
    print("\nMake sure the server is running:")
    print("  cd deploy/docker && python server.py")
    print("\n" + "-" * 60 + "\n")
    
    results = []
    results.append(test_health())
    print()
    results.append(test_stats())
    print()
    results.append(test_url_stats())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed! ({passed}/{total})")
        print("\nMonitoring endpoints are working correctly! 🎉")
        return 0
    else:
        print(f"❌ Some tests failed ({passed}/{total} passed)")
        print("\nPlease check the server logs for errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
