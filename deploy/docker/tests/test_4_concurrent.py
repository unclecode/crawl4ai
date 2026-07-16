#!/usr/bin/env python3
"""
Test 4: Concurrent Load Testing
- Tests pool under concurrent load
- Escalates: 10 → 50 → 100 concurrent requests
- Validates latency distribution (P50, P95, P99)
- Monitors memory stability
"""
import asyncio
import time
import docker
import httpx
from threading import Thread, Event
from collections import defaultdict

# Config
IMAGE = "crawl4ai-local:latest"
CONTAINER_NAME = "crawl4ai-test"
PORT = 11235
LOAD_LEVELS = [
    {"name": "Light", "concurrent": 10, "requests": 20},
    {"name": "Medium", "concurrent": 50, "requests": 100},
    {"name": "Heavy", "concurrent": 100, "requests": 200},
]

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

def count_log_markers(container):
    """Extract pool markers."""
    logs = container.logs().decode('utf-8')
    return {
        'permanent': logs.count("🔥 Using permanent browser"),
        'hot': logs.count("♨️  Using hot pool browser"),
        'cold': logs.count("❄️  Using cold pool browser"),
        'new': logs.count("🆕 Creating new browser"),
    }

async def hit_endpoint(client, url, payload, semaphore):
    """Single request with concurrency control."""
    async with semaphore:
        start = time.time()
        try:
            resp = await client.post(url, json=payload, timeout=60.0)
            elapsed = (time.time() - start) * 1000
            return {"success": resp.status_code == 200, "latency_ms": elapsed}
        except Exception as e:
            return {"success": False, "error": str(e)}

async def run_concurrent_test(url, payload, concurrent, total_requests):
    """Run concurrent requests."""
    semaphore = asyncio.Semaphore(concurrent)
    async with httpx.AsyncClient() as client:
        tasks = [hit_endpoint(client, url, payload, semaphore) for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)
    return results

def calculate_percentiles(latencies):
    """Calculate P50, P95, P99."""
    if not latencies:
        return 0, 0, 0
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    return (
        sorted_lat[int(n * 0.50)],
        sorted_lat[int(n * 0.95)],
        sorted_lat[int(n * 0.99)],
    )

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
    print("TEST 4: Concurrent Load Testing")
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

        url = f"http://localhost:{PORT}/html"
        payload = {"url": "https://httpbin.org/html"}

        all_results = []
        level_stats = []

        # Run load levels
        for level in LOAD_LEVELS:
            print(f"{'='*60}")
            print(f"🔄 {level['name']} Load: {level['concurrent']} concurrent, {level['requests']} total")
            print(f"{'='*60}")

            start_time = time.time()
            results = await run_concurrent_test(url, payload, level['concurrent'], level['requests'])
            duration = time.time() - start_time

            successes = sum(1 for r in results if r.get("success"))
            success_rate = (successes / len(results)) * 100
            latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
            p50, p95, p99 = calculate_percentiles(latencies)
            avg_lat = sum(latencies) / len(latencies) if latencies else 0

            print(f"  Duration:     {duration:.1f}s")
            print(f"  Success:      {success_rate:.1f}% ({successes}/{len(results)})")
            print(f"  Avg Latency:  {avg_lat:.0f}ms")
            print(f"  P50/P95/P99:  {p50:.0f}ms / {p95:.0f}ms / {p99:.0f}ms")

            level_stats.append({
                'name': level['name'],
                'concurrent': level['concurrent'],
                'success_rate': success_rate,
                'avg_latency': avg_lat,
                'p50': p50, 'p95': p95, 'p99': p99,
            })
            all_results.extend(results)

            await asyncio.sleep(2)  # Cool down between levels

        # Stop monitoring
        await asyncio.sleep(1)
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Final stats
        pool_stats = count_log_markers(container)
        memory_samples = [s['memory_mb'] for s in stats_history]
        peak_mem = max(memory_samples) if memory_samples else 0
        final_mem = memory_samples[-1] if memory_samples else 0

        print(f"\n{'='*60}")
        print(f"FINAL RESULTS:")
        print(f"{'='*60}")
        print(f"  Total Requests: {len(all_results)}")
        print(f"\n  Pool Utilization:")
        print(f"    🔥 Permanent: {pool_stats['permanent']}")
        print(f"    ♨️  Hot:       {pool_stats['hot']}")
        print(f"    ❄️  Cold:      {pool_stats['cold']}")
        print(f"    🆕 New:       {pool_stats['new']}")
        print(f"\n  Memory:")
        print(f"    Baseline: {baseline_mem:.1f} MB")
        print(f"    Peak:     {peak_mem:.1f} MB")
        print(f"    Final:    {final_mem:.1f} MB")
        print(f"    Delta:    {final_mem - baseline_mem:+.1f} MB")
        print(f"{'='*60}")

        # Pass/Fail
        passed = True
        for ls in level_stats:
            if ls['success_rate'] < 99:
                print(f"❌ FAIL: {ls['name']} success rate {ls['success_rate']:.1f}% < 99%")
                passed = False
            if ls['p99'] > 10000:  # 10s threshold
                print(f"⚠️  WARNING: {ls['name']} P99 latency {ls['p99']:.0f}ms very high")

        if final_mem - baseline_mem > 300:
            print(f"⚠️  WARNING: Memory grew {final_mem - baseline_mem:.1f} MB")

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
