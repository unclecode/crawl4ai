#!/usr/bin/env python3
"""
Test 3: Pool Validation - Permanent Browser Reuse
- Tests /html endpoint (should use permanent browser)
- Monitors container logs for pool hit markers
- Validates browser reuse rate
- Checks memory after browser creation
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
REQUESTS = 30

# Stats tracking
stats_history = []
stop_monitoring = Event()

def monitor_stats(container):
    """Background stats collector."""
    for stat in container.stats(decode=True, stream=True):
        if stop_monitoring.is_set():
            break
        try:
            mem_usage = stat['memory_stats'].get('usage', 0) / (1024 * 1024)
            stats_history.append({
                'timestamp': time.time(),
                'memory_mb': mem_usage,
            })
        except:
            pass
        time.sleep(0.5)

def count_log_markers(container):
    """Extract pool usage markers from logs."""
    logs = container.logs().decode('utf-8')

    permanent_hits = logs.count("🔥 Using permanent browser")
    hot_hits = logs.count("♨️  Using hot pool browser")
    cold_hits = logs.count("❄️  Using cold pool browser")
    new_created = logs.count("🆕 Creating new browser")

    return {
        'permanent_hits': permanent_hits,
        'hot_hits': hot_hits,
        'cold_hits': cold_hits,
        'new_created': new_created,
        'total_hits': permanent_hits + hot_hits + cold_hits
    }

async def test_endpoint(url: str, count: int):
    """Hit endpoint multiple times."""
    results = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(count):
            start = time.time()
            try:
                resp = await client.post(url, json={"url": "https://httpbin.org/html"})
                elapsed = (time.time() - start) * 1000
                results.append({
                    "success": resp.status_code == 200,
                    "latency_ms": elapsed,
                })
                if (i + 1) % 10 == 0:
                    print(f"  [{i+1}/{count}] ✓ {resp.status_code} - {elapsed:.0f}ms")
            except Exception as e:
                results.append({"success": False, "error": str(e)})
                print(f"  [{i+1}/{count}] ✗ Error: {e}")
    return results

def start_container(client, image: str, name: str, port: int):
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
        image,
        name=name,
        ports={f"{port}/tcp": port},
        detach=True,
        shm_size="1g",
        mem_limit="4g",
    )

    print(f"⏳ Waiting for health...")
    for _ in range(30):
        time.sleep(1)
        container.reload()
        if container.status == "running":
            try:
                import requests
                resp = requests.get(f"http://localhost:{port}/health", timeout=2)
                if resp.status_code == 200:
                    print(f"✅ Container healthy!")
                    return container
            except:
                pass
    raise TimeoutError("Container failed to start")

def stop_container(container):
    """Stop container."""
    print(f"🛑 Stopping container...")
    container.stop()
    container.remove()

async def main():
    print("="*60)
    print("TEST 3: Pool Validation - Permanent Browser Reuse")
    print("="*60)

    client = docker.from_env()
    container = None
    monitor_thread = None

    try:
        # Start container
        container = start_container(client, IMAGE, CONTAINER_NAME, PORT)

        # Wait for permanent browser initialization
        print(f"\n⏳ Waiting for permanent browser init (3s)...")
        await asyncio.sleep(3)

        # Start stats monitoring
        print(f"📊 Starting stats monitor...")
        stop_monitoring.clear()
        stats_history.clear()
        monitor_thread = Thread(target=monitor_stats, args=(container,), daemon=True)
        monitor_thread.start()

        await asyncio.sleep(1)
        baseline_mem = stats_history[-1]['memory_mb'] if stats_history else 0
        print(f"📏 Baseline (with permanent browser): {baseline_mem:.1f} MB")

        # Test /html endpoint (uses permanent browser for default config)
        print(f"\n🔄 Running {REQUESTS} requests to /html...")
        url = f"http://localhost:{PORT}/html"
        results = await test_endpoint(url, REQUESTS)

        # Wait a bit
        await asyncio.sleep(1)

        # Stop monitoring
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Analyze logs for pool markers
        print(f"\n📋 Analyzing pool usage...")
        pool_stats = count_log_markers(container)

        # Calculate request stats
        successes = sum(1 for r in results if r.get("success"))
        success_rate = (successes / len(results)) * 100
        latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # Memory stats
        memory_samples = [s['memory_mb'] for s in stats_history]
        peak_mem = max(memory_samples) if memory_samples else 0
        final_mem = memory_samples[-1] if memory_samples else 0
        mem_delta = final_mem - baseline_mem

        # Calculate reuse rate
        total_requests = len(results)
        total_pool_hits = pool_stats['total_hits']
        reuse_rate = (total_pool_hits / total_requests * 100) if total_requests > 0 else 0

        # Print results
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Success Rate: {success_rate:.1f}% ({successes}/{len(results)})")
        print(f"  Avg Latency:  {avg_latency:.0f}ms")
        print(f"\n  Pool Stats:")
        print(f"    🔥 Permanent Hits: {pool_stats['permanent_hits']}")
        print(f"    ♨️  Hot Pool Hits:   {pool_stats['hot_hits']}")
        print(f"    ❄️  Cold Pool Hits:  {pool_stats['cold_hits']}")
        print(f"    🆕 New Created:    {pool_stats['new_created']}")
        print(f"    📊 Reuse Rate:     {reuse_rate:.1f}%")
        print(f"\n  Memory Stats:")
        print(f"    Baseline: {baseline_mem:.1f} MB")
        print(f"    Peak:     {peak_mem:.1f} MB")
        print(f"    Final:    {final_mem:.1f} MB")
        print(f"    Delta:    {mem_delta:+.1f} MB")
        print(f"{'='*60}")

        # Pass/Fail
        passed = True
        if success_rate < 100:
            print(f"❌ FAIL: Success rate {success_rate:.1f}% < 100%")
            passed = False
        if reuse_rate < 80:
            print(f"❌ FAIL: Reuse rate {reuse_rate:.1f}% < 80% (expected high permanent browser usage)")
            passed = False
        if pool_stats['permanent_hits'] < (total_requests * 0.8):
            print(f"⚠️  WARNING: Only {pool_stats['permanent_hits']} permanent hits out of {total_requests} requests")
        if mem_delta > 200:
            print(f"⚠️  WARNING: Memory grew by {mem_delta:.1f} MB (possible browser leak)")

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
            stop_container(container)

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
