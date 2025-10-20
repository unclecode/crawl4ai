#!/usr/bin/env python3
"""
Monitor Dashboard Demo Script
Generates varied activity to showcase all monitoring features for video recording.
"""
import httpx
import asyncio
import time
from datetime import datetime

BASE_URL = "http://localhost:11235"

async def demo_dashboard():
    print("🎬 Monitor Dashboard Demo - Starting...\n")
    print(f"📊 Dashboard: {BASE_URL}/dashboard")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:

        # Phase 1: Simple requests (permanent browser)
        print("\n🔷 Phase 1: Testing permanent browser pool")
        print("-" * 60)
        for i in range(5):
            print(f"  {i+1}/5 Request to /crawl (default config)...")
            try:
                r = await client.post(
                    f"{BASE_URL}/crawl",
                    json={"urls": [f"https://httpbin.org/html?req={i}"], "crawler_config": {}}
                )
                print(f"     ✅ Status: {r.status_code}, Time: {r.elapsed.total_seconds():.2f}s")
            except Exception as e:
                print(f"     ❌ Error: {e}")
            await asyncio.sleep(1)  # Small delay between requests

        # Phase 2: Create variant browsers (different configs)
        print("\n🔶 Phase 2: Testing cold→hot pool promotion")
        print("-" * 60)
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1280, "height": 720},
            {"width": 800, "height": 600}
        ]

        for idx, viewport in enumerate(viewports):
            print(f"  Viewport {viewport['width']}x{viewport['height']}:")
            for i in range(4):  # 4 requests each to trigger promotion at 3
                try:
                    r = await client.post(
                        f"{BASE_URL}/crawl",
                        json={
                            "urls": [f"https://httpbin.org/json?v={idx}&r={i}"],
                            "browser_config": {"viewport": viewport},
                            "crawler_config": {}
                        }
                    )
                    print(f"    {i+1}/4 ✅ {r.status_code} - Should see cold→hot after 3 uses")
                except Exception as e:
                    print(f"    {i+1}/4 ❌ {e}")
                await asyncio.sleep(0.5)

        # Phase 3: Concurrent burst (stress pool)
        print("\n🔷 Phase 3: Concurrent burst (10 parallel)")
        print("-" * 60)
        tasks = []
        for i in range(10):
            tasks.append(
                client.post(
                    f"{BASE_URL}/crawl",
                    json={"urls": [f"https://httpbin.org/delay/2?burst={i}"], "crawler_config": {}}
                )
            )

        print("  Sending 10 concurrent requests...")
        start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start

        successes = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
        print(f"  ✅ {successes}/10 succeeded in {elapsed:.2f}s")

        # Phase 4: Multi-endpoint coverage
        print("\n🔶 Phase 4: Testing multiple endpoints")
        print("-" * 60)
        endpoints = [
            ("/md", {"url": "https://httpbin.org/html", "f": "fit", "c": "0"}),
            ("/screenshot", {"url": "https://httpbin.org/html"}),
            ("/pdf", {"url": "https://httpbin.org/html"}),
        ]

        for endpoint, payload in endpoints:
            print(f"  Testing {endpoint}...")
            try:
                if endpoint == "/md":
                    r = await client.post(f"{BASE_URL}{endpoint}", json=payload)
                else:
                    r = await client.post(f"{BASE_URL}{endpoint}", json=payload)
                print(f"    ✅ {r.status_code}")
            except Exception as e:
                print(f"    ❌ {e}")
            await asyncio.sleep(1)

        # Phase 5: Intentional error (to populate errors tab)
        print("\n🔷 Phase 5: Generating error examples")
        print("-" * 60)
        print("  Triggering invalid URL error...")
        try:
            r = await client.post(
                f"{BASE_URL}/crawl",
                json={"urls": ["invalid://bad-url"], "crawler_config": {}}
            )
            print(f"    Response: {r.status_code}")
        except Exception as e:
            print(f"    ✅ Error captured: {type(e).__name__}")

        # Phase 6: Wait for janitor activity
        print("\n🔶 Phase 6: Waiting for janitor cleanup...")
        print("-" * 60)
        print("  Idle for 40s to allow janitor to clean cold pool browsers...")
        for i in range(40, 0, -10):
            print(f"    {i}s remaining... (Check dashboard for cleanup events)")
            await asyncio.sleep(10)

        # Phase 7: Final stats check
        print("\n🔷 Phase 7: Final dashboard state")
        print("-" * 60)

        r = await client.get(f"{BASE_URL}/monitor/health")
        health = r.json()
        print(f"  Memory: {health['container']['memory_percent']:.1f}%")
        print(f"  Browsers: Perm={health['pool']['permanent']['active']}, "
              f"Hot={health['pool']['hot']['count']}, Cold={health['pool']['cold']['count']}")

        r = await client.get(f"{BASE_URL}/monitor/endpoints/stats")
        stats = r.json()
        print(f"\n  Endpoint Stats:")
        for endpoint, data in stats.items():
            print(f"    {endpoint}: {data['count']} req, "
                  f"{data['avg_latency_ms']:.0f}ms avg, "
                  f"{data['success_rate_percent']:.1f}% success")

        r = await client.get(f"{BASE_URL}/monitor/browsers")
        browsers = r.json()
        print(f"\n  Pool Efficiency:")
        print(f"    Total browsers: {browsers['summary']['total_count']}")
        print(f"    Memory usage: {browsers['summary']['total_memory_mb']} MB")
        print(f"    Reuse rate: {browsers['summary']['reuse_rate_percent']:.1f}%")

    print("\n" + "=" * 60)
    print("✅ Demo complete! Dashboard is now populated with rich data.")
    print(f"\n📹 Recording tip: Refresh {BASE_URL}/dashboard")
    print("   You should see:")
    print("   • Active & completed requests")
    print("   • Browser pool (permanent + hot/cold)")
    print("   • Janitor cleanup events")
    print("   • Endpoint analytics")
    print("   • Memory timeline")

if __name__ == "__main__":
    try:
        asyncio.run(demo_dashboard())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
