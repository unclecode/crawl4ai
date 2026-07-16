#!/usr/bin/env python3
"""Quick test to generate monitor dashboard activity"""
import httpx
import asyncio

async def test_dashboard():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("📊 Generating dashboard activity...")

        # Test 1: Simple crawl
        print("\n1️⃣ Running simple crawl...")
        r1 = await client.post(
            "http://localhost:11235/crawl",
            json={"urls": ["https://httpbin.org/html"], "crawler_config": {}}
        )
        print(f"   Status: {r1.status_code}")

        # Test 2: Multiple URLs
        print("\n2️⃣ Running multi-URL crawl...")
        r2 = await client.post(
            "http://localhost:11235/crawl",
            json={
                "urls": [
                    "https://httpbin.org/html",
                    "https://httpbin.org/json"
                ],
                "crawler_config": {}
            }
        )
        print(f"   Status: {r2.status_code}")

        # Test 3: Check monitor health
        print("\n3️⃣ Checking monitor health...")
        r3 = await client.get("http://localhost:11235/monitor/health")
        health = r3.json()
        print(f"   Memory: {health['container']['memory_percent']}%")
        print(f"   Browsers: {health['pool']['permanent']['active']}")

        # Test 4: Check requests
        print("\n4️⃣ Checking request log...")
        r4 = await client.get("http://localhost:11235/monitor/requests")
        reqs = r4.json()
        print(f"   Active: {len(reqs['active'])}")
        print(f"   Completed: {len(reqs['completed'])}")

        # Test 5: Check endpoint stats
        print("\n5️⃣ Checking endpoint stats...")
        r5 = await client.get("http://localhost:11235/monitor/endpoints/stats")
        stats = r5.json()
        for endpoint, data in stats.items():
            print(f"   {endpoint}: {data['count']} requests, {data['avg_latency_ms']}ms avg")

        print("\n✅ Dashboard should now show activity!")
        print(f"\n🌐 Open: http://localhost:11235/dashboard")

if __name__ == "__main__":
    asyncio.run(test_dashboard())
