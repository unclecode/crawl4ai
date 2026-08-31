#!/usr/bin/env python3
"""
Test 6: Multi-Endpoint Testing
- Tests multiple endpoints together: /html, /screenshot, /pdf, /crawl
- Validates each endpoint works correctly
- Monitors success rates per endpoint
"""
import asyncio
import time
import docker
import httpx
from threading import Thread, Event

# Config
IMAGE = "crawl4ai-local:latest"
CONTAINER_NAME = "crawl4ai-test"
PORT = 11235
REQUESTS_PER_ENDPOINT = 10

# Stats
stats_history = []
stop_monitoring = Event()

def monitor_stats(container):
    """Background stats collector."""
    for stat in container.stats(decode=True, stream=True):
        if stop_monitoring.is_set():
            break
        try:
            mem_usage = stat['memory_stats'].get('usage', 0) / (1024 * 1024)
            stats_history.append({'timestamp': time.time(), 'memory_mb': mem_usage})
        except:
            pass
        time.sleep(0.5)

async def test_html(client, base_url, count):
    """Test /html endpoint."""
    url = f"{base_url}/html"
    results = []
    for _ in range(count):
        start = time.time()
        try:
            resp = await client.post(url, json={"url": "https://httpbin.org/html"}, timeout=30.0)
            elapsed = (time.time() - start) * 1000
            results.append({"success": resp.status_code == 200, "latency_ms": elapsed})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    return results

async def test_screenshot(client, base_url, count):
    """Test /screenshot endpoint."""
    url = f"{base_url}/screenshot"
    results = []
    for _ in range(count):
        start = time.time()
        try:
            resp = await client.post(url, json={"url": "https://httpbin.org/html"}, timeout=30.0)
            elapsed = (time.time() - start) * 1000
            results.append({"success": resp.status_code == 200, "latency_ms": elapsed})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    return results

async def test_pdf(client, base_url, count):
    """Test /pdf endpoint."""
    url = f"{base_url}/pdf"
    results = []
    for _ in range(count):
        start = time.time()
        try:
            resp = await client.post(url, json={"url": "https://httpbin.org/html"}, timeout=30.0)
            elapsed = (time.time() - start) * 1000
            results.append({"success": resp.status_code == 200, "latency_ms": elapsed})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    return results

async def test_crawl(client, base_url, count):
    """Test /crawl endpoint."""
    url = f"{base_url}/crawl"
    results = []
    payload = {
        "urls": ["https://httpbin.org/html"],
        "browser_config": {},
        "crawler_config": {}
    }
    for _ in range(count):
        start = time.time()
        try:
            resp = await client.post(url, json=payload, timeout=30.0)
            elapsed = (time.time() - start) * 1000
            results.append({"success": resp.status_code == 200, "latency_ms": elapsed})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    return results

def start_container(client, image, name, port):
    """Start container."""
    try:
        old = client.containers.get(name)
        print(f"🧹 Stopping existing container...")
        old.stop()
        old.remove()
    except docker.errors.NotFound:
        pass

    print(f"🚀 Starting container...")
    container = client.containers.run(
        image, name=name, ports={f"{port}/tcp": port},
        detach=True, shm_size="1g", mem_limit="4g",
    )

    print(f"⏳ Waiting for health...")
    for _ in range(30):
        time.sleep(1)
        container.reload()
        if container.status == "running":
            try:
                import requests
                if requests.get(f"http://localhost:{port}/health", timeout=2).status_code == 200:
                    print(f"✅ Container healthy!")
                    return container
            except:
                pass
    raise TimeoutError("Container failed to start")

async def main():
    print("="*60)
    print("TEST 6: Multi-Endpoint Testing")
    print("="*60)

    client = docker.from_env()
    container = None
    monitor_thread = None

    try:
        container = start_container(client, IMAGE, CONTAINER_NAME, PORT)

        print(f"\n⏳ Waiting for permanent browser init (3s)...")
        await asyncio.sleep(3)

        # Start monitoring
        stop_monitoring.clear()
        stats_history.clear()
        monitor_thread = Thread(target=monitor_stats, args=(container,), daemon=True)
        monitor_thread.start()

        await asyncio.sleep(1)
        baseline_mem = stats_history[-1]['memory_mb'] if stats_history else 0
        print(f"📏 Baseline: {baseline_mem:.1f} MB\n")

        base_url = f"http://localhost:{PORT}"

        # Test each endpoint
        endpoints = {
            "/html": test_html,
            "/screenshot": test_screenshot,
            "/pdf": test_pdf,
            "/crawl": test_crawl,
        }

        all_endpoint_stats = {}

        async with httpx.AsyncClient() as http_client:
            for endpoint_name, test_func in endpoints.items():
                print(f"🔄 Testing {endpoint_name} ({REQUESTS_PER_ENDPOINT} requests)...")
                results = await test_func(http_client, base_url, REQUESTS_PER_ENDPOINT)

                successes = sum(1 for r in results if r.get("success"))
                success_rate = (successes / len(results)) * 100
                latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
                avg_lat = sum(latencies) / len(latencies) if latencies else 0

                all_endpoint_stats[endpoint_name] = {
                    'success_rate': success_rate,
                    'avg_latency': avg_lat,
                    'total': len(results),
                    'successes': successes
                }

                print(f"  ✓ Success: {success_rate:.1f}% ({successes}/{len(results)}), Avg: {avg_lat:.0f}ms")

        # Stop monitoring
        await asyncio.sleep(1)
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Final stats
        memory_samples = [s['memory_mb'] for s in stats_history]
        peak_mem = max(memory_samples) if memory_samples else 0
        final_mem = memory_samples[-1] if memory_samples else 0

        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"{'='*60}")
        for endpoint, stats in all_endpoint_stats.items():
            print(f"  {endpoint:12} Success: {stats['success_rate']:5.1f}%  Avg: {stats['avg_latency']:6.0f}ms")

        print(f"\n  Memory:")
        print(f"    Baseline: {baseline_mem:.1f} MB")
        print(f"    Peak:     {peak_mem:.1f} MB")
        print(f"    Final:    {final_mem:.1f} MB")
        print(f"    Delta:    {final_mem - baseline_mem:+.1f} MB")
        print(f"{'='*60}")

        # Pass/Fail
        passed = True
        for endpoint, stats in all_endpoint_stats.items():
            if stats['success_rate'] < 100:
                print(f"❌ FAIL: {endpoint} success rate {stats['success_rate']:.1f}% < 100%")
                passed = False

        if passed:
            print(f"✅ TEST PASSED")
            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        stop_monitoring.set()
        if container:
            print(f"🛑 Stopping container...")
            container.stop()
            container.remove()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
