#!/usr/bin/env python3
"""
Test 2: Docker Stats Monitoring
- Extends Test 1 with real-time container stats
- Monitors memory % and CPU during requests
- Reports baseline, peak, and final memory
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
REQUESTS = 20  # More requests to see memory usage

# Stats tracking
stats_history = []
stop_monitoring = Event()

def monitor_stats(container):
    """Background thread to collect container stats."""
    for stat in container.stats(decode=True, stream=True):
        if stop_monitoring.is_set():
            break

        try:
            # Extract memory stats
            mem_usage = stat['memory_stats'].get('usage', 0) / (1024 * 1024)  # MB
            mem_limit = stat['memory_stats'].get('limit', 1) / (1024 * 1024)
            mem_percent = (mem_usage / mem_limit * 100) if mem_limit > 0 else 0

            # Extract CPU stats (handle missing fields on Mac)
            cpu_percent = 0
            try:
                cpu_delta = stat['cpu_stats']['cpu_usage']['total_usage'] - \
                           stat['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stat['cpu_stats'].get('system_cpu_usage', 0) - \
                              stat['precpu_stats'].get('system_cpu_usage', 0)
                if system_delta > 0:
                    num_cpus = stat['cpu_stats'].get('online_cpus', 1)
                    cpu_percent = (cpu_delta / system_delta * num_cpus * 100.0)
            except (KeyError, ZeroDivisionError):
                pass

            stats_history.append({
                'timestamp': time.time(),
                'memory_mb': mem_usage,
                'memory_percent': mem_percent,
                'cpu_percent': cpu_percent
            })
        except Exception as e:
            # Skip malformed stats
            pass

        time.sleep(0.5)  # Sample every 500ms

async def test_endpoint(url: str, count: int):
    """Hit endpoint, return stats."""
    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(count):
            start = time.time()
            try:
                resp = await client.get(url)
                elapsed = (time.time() - start) * 1000
                results.append({
                    "success": resp.status_code == 200,
                    "latency_ms": elapsed,
                })
                if (i + 1) % 5 == 0:  # Print every 5 requests
                    print(f"  [{i+1}/{count}] ✓ {resp.status_code} - {elapsed:.0f}ms")
            except Exception as e:
                results.append({"success": False, "error": str(e)})
                print(f"  [{i+1}/{count}] ✗ Error: {e}")
    return results

def start_container(client, image: str, name: str, port: int):
    """Start container."""
    try:
        old = client.containers.get(name)
        print(f"🧹 Stopping existing container '{name}'...")
        old.stop()
        old.remove()
    except docker.errors.NotFound:
        pass

    print(f"🚀 Starting container '{name}'...")
    container = client.containers.run(
        image,
        name=name,
        ports={f"{port}/tcp": port},
        detach=True,
        shm_size="1g",
        mem_limit="4g",  # Set explicit memory limit
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
    print("TEST 2: Docker Stats Monitoring")
    print("="*60)

    client = docker.from_env()
    container = None
    monitor_thread = None

    try:
        # Start container
        container = start_container(client, IMAGE, CONTAINER_NAME, PORT)

        # Start stats monitoring in background
        print(f"\n📊 Starting stats monitor...")
        stop_monitoring.clear()
        stats_history.clear()
        monitor_thread = Thread(target=monitor_stats, args=(container,), daemon=True)
        monitor_thread.start()

        # Wait a bit for baseline
        await asyncio.sleep(2)
        baseline_mem = stats_history[-1]['memory_mb'] if stats_history else 0
        print(f"📏 Baseline memory: {baseline_mem:.1f} MB")

        # Test /health endpoint
        print(f"\n🔄 Running {REQUESTS} requests to /health...")
        url = f"http://localhost:{PORT}/health"
        results = await test_endpoint(url, REQUESTS)

        # Wait a bit to capture peak
        await asyncio.sleep(1)

        # Stop monitoring
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Calculate stats
        successes = sum(1 for r in results if r.get("success"))
        success_rate = (successes / len(results)) * 100
        latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # Memory stats
        memory_samples = [s['memory_mb'] for s in stats_history]
        peak_mem = max(memory_samples) if memory_samples else 0
        final_mem = memory_samples[-1] if memory_samples else 0
        mem_delta = final_mem - baseline_mem

        # Print results
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Success Rate: {success_rate:.1f}% ({successes}/{len(results)})")
        print(f"  Avg Latency:  {avg_latency:.0f}ms")
        print(f"\n  Memory Stats:")
        print(f"    Baseline: {baseline_mem:.1f} MB")
        print(f"    Peak:     {peak_mem:.1f} MB")
        print(f"    Final:    {final_mem:.1f} MB")
        print(f"    Delta:    {mem_delta:+.1f} MB")
        print(f"{'='*60}")

        # Pass/Fail
        if success_rate >= 100 and mem_delta < 100:  # No significant memory growth
            print(f"✅ TEST PASSED")
            return 0
        else:
            if success_rate < 100:
                print(f"❌ TEST FAILED (success rate < 100%)")
            if mem_delta >= 100:
                print(f"⚠️  WARNING: Memory grew by {mem_delta:.1f} MB")
            return 1

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        return 1
    finally:
        stop_monitoring.set()
        if container:
            stop_container(container)

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
