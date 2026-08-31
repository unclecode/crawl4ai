#!/usr/bin/env python3
"""
Test 1: Basic Container Health + Single Endpoint
- Starts container
- Hits /health endpoint 10 times
- Reports success rate and basic latency
"""
import asyncio
import time
import docker
import httpx

# Config
IMAGE = "crawl4ai-local:latest"
CONTAINER_NAME = "crawl4ai-test"
PORT = 11235
REQUESTS = 10

async def test_endpoint(url: str, count: int):
    """Hit endpoint multiple times, return stats."""
    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(count):
            start = time.time()
            try:
                resp = await client.get(url)
                elapsed = (time.time() - start) * 1000  # ms
                results.append({
                    "success": resp.status_code == 200,
                    "latency_ms": elapsed,
                    "status": resp.status_code
                })
                print(f"  [{i+1}/{count}] ✓ {resp.status_code} - {elapsed:.0f}ms")
            except Exception as e:
                results.append({
                    "success": False,
                    "latency_ms": None,
                    "error": str(e)
                })
                print(f"  [{i+1}/{count}] ✗ Error: {e}")
    return results

def start_container(client, image: str, name: str, port: int):
    """Start container, return container object."""
    # Clean up existing
    try:
        old = client.containers.get(name)
        print(f"🧹 Stopping existing container '{name}'...")
        old.stop()
        old.remove()
    except docker.errors.NotFound:
        pass

    print(f"🚀 Starting container '{name}' from image '{image}'...")
    container = client.containers.run(
        image,
        name=name,
        ports={f"{port}/tcp": port},
        detach=True,
        shm_size="1g",
        environment={"PYTHON_ENV": "production"}
    )

    # Wait for health
    print(f"⏳ Waiting for container to be healthy...")
    for _ in range(30):  # 30s timeout
        time.sleep(1)
        container.reload()
        if container.status == "running":
            try:
                # Quick health check
                import requests
                resp = requests.get(f"http://localhost:{port}/health", timeout=2)
                if resp.status_code == 200:
                    print(f"✅ Container healthy!")
                    return container
            except:
                pass
    raise TimeoutError("Container failed to start")

def stop_container(container):
    """Stop and remove container."""
    print(f"🛑 Stopping container...")
    container.stop()
    container.remove()
    print(f"✅ Container removed")

async def main():
    print("="*60)
    print("TEST 1: Basic Container Health + Single Endpoint")
    print("="*60)

    client = docker.from_env()
    container = None

    try:
        # Start container
        container = start_container(client, IMAGE, CONTAINER_NAME, PORT)

        # Test /health endpoint
        print(f"\n📊 Testing /health endpoint ({REQUESTS} requests)...")
        url = f"http://localhost:{PORT}/health"
        results = await test_endpoint(url, REQUESTS)

        # Calculate stats
        successes = sum(1 for r in results if r["success"])
        success_rate = (successes / len(results)) * 100
        latencies = [r["latency_ms"] for r in results if r["latency_ms"] is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # Print results
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Success Rate: {success_rate:.1f}% ({successes}/{len(results)})")
        print(f"  Avg Latency:  {avg_latency:.0f}ms")
        if latencies:
            print(f"  Min Latency:  {min(latencies):.0f}ms")
            print(f"  Max Latency:  {max(latencies):.0f}ms")
        print(f"{'='*60}")

        # Pass/Fail
        if success_rate >= 100:
            print(f"✅ TEST PASSED")
            return 0
        else:
            print(f"❌ TEST FAILED (expected 100% success rate)")
            return 1

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        return 1
    finally:
        if container:
            stop_container(container)

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
