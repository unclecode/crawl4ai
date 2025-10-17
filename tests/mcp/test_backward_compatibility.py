#!/usr/bin/env python3
"""
Test backward compatibility for /md endpoint parameters
Tests both new (filter/query/cache) and old (f/q/c) parameter formats
"""


import asyncio
import httpx
import json

# Test configurations
BASE_URL = "http://localhost:11235"
TEST_URL = "https://example.com"

async def test_new_parameters():
    """Test new parameter format (filter/query/cache in body)"""
    print("Testing new parameter format...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/md",
            json={
                "url": TEST_URL,
                "filter": "raw",
                "query": "test query",
                "cache": "123"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ New format works: filter={data.get('filter')}, query={data.get('query')}, cache={data.get('cache')}")
            return True
        else:
            print(f"✗ New format failed: {response.status_code} - {response.text}")
            return False

async def test_old_parameters():
    """Test old parameter format (f/q/c as query params)"""
    print("Testing old parameter format...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/md?f=raw&q=test%20query&c=456",
            json={
                "url": TEST_URL
            }
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Old format works: filter={data.get('filter')}, query={data.get('query')}, cache={data.get('cache')}")
            return True
        else:
            print(f"✗ Old format failed: {response.status_code} - {response.text}")
            return False

async def test_parameter_precedence():
    """Test that body parameters take precedence over query parameters"""
    print("Testing parameter precedence...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/md?f=bm25&q=old%20query&c=999",
            json={
                "url": TEST_URL,
                "filter": "raw",
                "query": "new query",
                "cache": "123"
            }
        )

        if response.status_code == 200:
            data = response.json()
            expected_filter = "raw"
            expected_query = "new query"
            expected_cache = "123"

            if (data.get('filter') == expected_filter and
                data.get('query') == expected_query and
                data.get('cache') == expected_cache):
                print("✓ Precedence works: body params override query params")
                return True
            else:
                print(f"✗ Precedence failed: got filter={data.get('filter')}, query={data.get('query')}, cache={data.get('cache')}")
                return False
        else:
            print(f"✗ Precedence test failed: {response.status_code} - {response.text}")
            return False

async def test_default_fallback():
    """Test that query params are used when body has defaults"""
    print("Testing default fallback...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/md?f=bm25&q=fallback%20query",
            json={
                "url": TEST_URL,
                # Using defaults for filter (fit), query (None), cache (0)
            }
        )

        if response.status_code == 200:
            data = response.json()
            expected_filter = "bm25"
            expected_query = "fallback query"

            if (data.get('filter') == expected_filter and
                data.get('query') == expected_query):
                print("✓ Default fallback works: query params used when body has defaults")
                return True
            else:
                print(f"✗ Default fallback failed: got filter={data.get('filter')}, query={data.get('query')}")
                return False
        else:
            print(f"✗ Default fallback test failed: {response.status_code} - {response.text}")
            return False

async def main():
    """Run all backward compatibility tests"""
    print("Starting backward compatibility tests for /md endpoint...")
    print("=" * 60)

    tests = [
        test_new_parameters,
        test_old_parameters,
        test_parameter_precedence,
        test_default_fallback
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} errored: {e}")
            results.append(False)
        print()

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests: {passed}/{total} passed")

    if passed == total:
        print("🎉 All backward compatibility tests passed!")
    else:
        print("❌ Some tests failed. Check server logs for details.")

    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
