#!/usr/bin/env python3
"""
Quick test script for Table Extraction feature
Tests the /tables/extract endpoint with sample HTML

Usage:
1. Start the server: python deploy/docker/server.py
2. Run this script: python tests/docker/test_table_extraction_quick.py
"""

import requests
import json
import sys

# Sample HTML with tables
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<body>
    <h1>Test Tables</h1>
    
    <table id="simple">
        <tr><th>Name</th><th>Age</th><th>City</th></tr>
        <tr><td>Alice</td><td>25</td><td>New York</td></tr>
        <tr><td>Bob</td><td>30</td><td>San Francisco</td></tr>
        <tr><td>Charlie</td><td>35</td><td>Los Angeles</td></tr>
    </table>
    
    <table id="financial">
        <thead>
            <tr><th>Quarter</th><th>Revenue</th><th>Profit</th></tr>
        </thead>
        <tbody>
            <tr><td>Q1 2024</td><td>$1,250,000.00</td><td>$400,000.00</td></tr>
            <tr><td>Q2 2024</td><td>$1,500,000.00</td><td>$600,000.00</td></tr>
            <tr><td>Q3 2024</td><td>$1,750,000.00</td><td>$700,000.00</td></tr>
        </tbody>
    </table>
</body>
</html>
"""

BASE_URL = "http://localhost:11234"


def test_server_health():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not reachable: {e}")
        print("\n💡 Start the server with: python deploy/docker/server.py")
        return False


def test_default_strategy():
    """Test default table extraction strategy"""
    print("\n📊 Testing DEFAULT strategy...")
    
    response = requests.post(f"{BASE_URL}/tables/extract", json={
        "html": SAMPLE_HTML,
        "config": {
            "strategy": "default"
        }
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Default strategy works!")
        print(f"   - Table count: {data['table_count']}")
        print(f"   - Strategy: {data['strategy']}")
        
        if data['tables']:
            for idx, table in enumerate(data['tables']):
                print(f"   - Table {idx + 1}: {len(table.get('rows', []))} rows")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def test_financial_strategy():
    """Test financial table extraction strategy"""
    print("\n💰 Testing FINANCIAL strategy...")
    
    response = requests.post(f"{BASE_URL}/tables/extract", json={
        "html": SAMPLE_HTML,
        "config": {
            "strategy": "financial",
            "preserve_formatting": True,
            "extract_metadata": True
        }
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Financial strategy works!")
        print(f"   - Table count: {data['table_count']}")
        print(f"   - Strategy: {data['strategy']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def test_none_strategy():
    """Test none strategy (no extraction)"""
    print("\n🚫 Testing NONE strategy...")
    
    response = requests.post(f"{BASE_URL}/tables/extract", json={
        "html": SAMPLE_HTML,
        "config": {
            "strategy": "none"
        }
    })
    
    if response.status_code == 200:
        data = response.json()
        if data['table_count'] == 0:
            print(f"✅ None strategy works (correctly extracted 0 tables)")
            return True
        else:
            print(f"❌ None strategy returned {data['table_count']} tables (expected 0)")
            return False
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_batch_extraction():
    """Test batch extraction"""
    print("\n📦 Testing BATCH extraction...")
    
    response = requests.post(f"{BASE_URL}/tables/extract/batch", json={
        "html_list": [
            SAMPLE_HTML,
            "<table><tr><th>Col1</th></tr><tr><td>Val1</td></tr></table>"
        ],
        "config": {
            "strategy": "default"
        }
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Batch extraction works!")
        print(f"   - Total processed: {data['summary']['total_processed']}")
        print(f"   - Successful: {data['summary']['successful']}")
        print(f"   - Total tables: {data['summary']['total_tables_extracted']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def test_error_handling():
    """Test error handling"""
    print("\n⚠️  Testing ERROR handling...")
    
    # Test with both html and url (should fail)
    response = requests.post(f"{BASE_URL}/tables/extract", json={
        "html": "<table></table>",
        "url": "https://example.com",
        "config": {"strategy": "default"}
    })
    
    if response.status_code == 400:
        print(f"✅ Error handling works (correctly rejected invalid input)")
        return True
    else:
        print(f"❌ Expected 400 error, got: {response.status_code}")
        return False


def main():
    print("=" * 60)
    print("Table Extraction Feature - Quick Test")
    print("=" * 60)
    
    # Check server
    if not test_server_health():
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Default Strategy", test_default_strategy()))
    results.append(("Financial Strategy", test_financial_strategy()))
    results.append(("None Strategy", test_none_strategy()))
    results.append(("Batch Extraction", test_batch_extraction()))
    results.append(("Error Handling", test_error_handling()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Table extraction is working correctly!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
