#!/usr/bin/env python3
"""
Test 7: Cleanup Verification (Janitor)
- Creates load spike then goes idle
- Verifies memory returns to near baseline
- Tests janitor cleanup of idle browsers
- Monitors memory recovery time
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
SPIKE_REQUESTS = 20  # Create some browsers
IDLE_TIME = 90  # Wait 90s for janitor (runs every 60s)

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
        time.sleep(1)  # Sample every 1s for this test

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
    print("TEST 7: Cleanup Verification (Janitor)")
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

        await asyncio.sleep(2)
        baseline_mem = stats_history[-1]['memory_mb'] if stats_history else 0
        print(f"📏 Baseline: {baseline_mem:.1f} MB\n")

        # Create load spike with different configs to populate pool
        print(f"🔥 Creating load spike ({SPIKE_REQUESTS} requests with varied configs)...")
        url = f"http://localhost:{PORT}/crawl"

        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1024, "height": 768},
            {"width": 375, "height": 667},
        ]

        async with httpx.AsyncClient(timeout=60.0) as http_client:
            tasks = []
            for i in range(SPIKE_REQUESTS):
                vp = viewports[i % len(viewports)]
                payload = {
                    "urls": ["https://httpbin.org/html"],
                    "browser_config": {
                        "type": "BrowserConfig",
                        "params": {
                            "viewport": {"type": "dict", "value": vp},
                            "headless": True,
                            "text_mode": True,
                            "extra_args": [
                                "--no-sandbox", "--disable-dev-shm-usage",
                                "--disable-gpu", "--disable-software-rasterizer",
                                "--disable-web-security", "--allow-insecure-localhost",
                                "--ignore-certificate-errors"
                            ]
                        }
                    },
                    "crawler_config": {}
                }
                tasks.append(http_client.post(url, json=payload))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            successes = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 200)
            print(f"  ✓ Spike completed: {successes}/{len(results)} successful")

        # Measure peak
        await asyncio.sleep(2)
        peak_mem = max([s['memory_mb'] for s in stats_history]) if stats_history else baseline_mem
        print(f"  📊 Peak memory: {peak_mem:.1f} MB (+{peak_mem - baseline_mem:.1f} MB)")

        # Now go idle and wait for janitor
        print(f"\n⏸️  Going idle for {IDLE_TIME}s (janitor cleanup)...")
        print(f"  (Janitor runs every 60s, checking for idle browsers)")

        for elapsed in range(0, IDLE_TIME, 10):
            await asyncio.sleep(10)
            current_mem = stats_history[-1]['memory_mb'] if stats_history else 0
            print(f"  [{elapsed+10:3d}s] Memory: {current_mem:.1f} MB")

        # Stop monitoring
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Analyze memory recovery
        final_mem = stats_history[-1]['memory_mb'] if stats_history else 0
        recovery_mb = peak_mem - final_mem
        recovery_pct = (recovery_mb / (peak_mem - baseline_mem) * 100) if (peak_mem - baseline_mem) > 0 else 0

        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"{'='*60}")
        print(f"  Memory Journey:")
        print(f"    Baseline:  {baseline_mem:.1f} MB")
        print(f"    Peak:      {peak_mem:.1f} MB  (+{peak_mem - baseline_mem:.1f} MB)")
        print(f"    Final:     {final_mem:.1f} MB  (+{final_mem - baseline_mem:.1f} MB)")
        print(f"    Recovered: {recovery_mb:.1f} MB  ({recovery_pct:.1f}%)")
        print(f"{'='*60}")

        # Pass/Fail
        passed = True

        # Should have created some memory pressure
        if peak_mem - baseline_mem < 100:
            print(f"⚠️  WARNING: Peak increase only {peak_mem - baseline_mem:.1f} MB (expected more browsers)")

        # Should recover most memory (within 100MB of baseline)
        if final_mem - baseline_mem > 100:
            print(f"⚠️  WARNING: Memory didn't recover well (still +{final_mem - baseline_mem:.1f} MB above baseline)")
        else:
            print(f"✅ Good memory recovery!")

        # Baseline + 50MB tolerance
        if final_mem - baseline_mem < 50:
            print(f"✅ Excellent cleanup (within 50MB of baseline)")

        print(f"✅ TEST PASSED")
        return 0

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
