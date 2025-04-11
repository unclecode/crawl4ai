import asyncio
import os
from pathlib import Path
import sys
import time

import pytest
from aiohttp import web

from crawl4ai.utils import RobotsParser


@pytest.mark.asyncio
async def test_robots_parser(tmp_path: Path   ):
    print("\n=== Testing RobotsParser ===\n")
    temp_dir = tmp_path.as_posix()
    # 1. Basic setup test
    print("1. Testing basic initialization...")
    parser = RobotsParser(cache_dir=temp_dir)
    assert os.path.exists(parser.db_path), "Database file not created"
    print("✓ Basic initialization passed")

    # 2. Test common cases
    print("\n2. Testing common cases...")
    start = time.time()
    allowed = await parser.can_fetch("https://httpbin.org", "MyBot/1.0")
    uncached_duration: float = time.time() - start
    assert allowed
    print(f"✓ Regular website fetch: {'allowed' if allowed else 'denied'} took: {uncached_duration * 1000:.2f}ms")

    # Test caching
    print("Testing cache...")
    start = time.time()
    await parser.can_fetch("https://httpbin.org", "MyBot/1.0")
    duration = time.time() - start
    print(f"✓ Cached lookup took: {duration * 1000:.2f}ms")
    # Using a hardcoded threshold results in flaky tests so
    # we just check that the cached lookup is faster than the uncached one.
    assert duration < uncached_duration, "Cache lookup too slow" #

    # 3. Edge cases
    print("\n3. Testing edge cases...")

    # Empty URL
    result = await parser.can_fetch("", "MyBot/1.0")
    assert result
    print(f"✓ Empty URL handled: {'allowed' if result else 'denied'}")

    # Invalid URL
    result = await parser.can_fetch("not_a_url", "MyBot/1.0")
    assert result
    print(f"✓ Invalid URL handled: {'allowed' if result else 'denied'}")

    # URL without scheme
    result = await parser.can_fetch("example.com/page", "MyBot/1.0")
    assert result
    print(f"✓ URL without scheme handled: {'allowed' if result else 'denied'}")

    # 4. Test with local server
    async def start_test_server():
        app = web.Application()

        async def robots_txt(request):
            return web.Response(
                text="""User-agent: *
Disallow: /private/
Allow: /public/
"""
            )

        async def malformed_robots(request):
            return web.Response(text="<<<malformed>>>")

        async def timeout_robots(request):
            await asyncio.sleep(5)
            return web.Response(text="Should timeout")

        async def empty_robots(request):
            return web.Response(text="")

        async def giant_robots(request):
            return web.Response(text="User-agent: *\nDisallow: /\n" * 10000)

        # Mount all handlers at root level
        app.router.add_get("/robots.txt", robots_txt)
        app.router.add_get("/malformed/robots.txt", malformed_robots)
        app.router.add_get("/timeout/robots.txt", timeout_robots)
        app.router.add_get("/empty/robots.txt", empty_robots)
        app.router.add_get("/giant/robots.txt", giant_robots)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 0)
        await site.start()
        return runner

    runner = await start_test_server()
    try:
        print("\n4. Testing robots.txt rules...")
        # Addresses are either IPv4 or IPv6, in both types the port is the second element.
        port: int = runner.addresses[0][1]
        base_url = f"http://localhost:{port}"

        # Test public access
        result = await parser.can_fetch(f"{base_url}/public/page", "bot")
        print(f"Public access (/public/page): {'allowed' if result else 'denied'}")
        assert result, "Public path should be allowed"

        # Test private access
        result = await parser.can_fetch(f"{base_url}/private/secret", "bot")
        assert not result, "Private path should be denied"

        # Test malformed
        result = await parser.can_fetch(
            f"{base_url}/malformed/page", "bot"
        )
        assert result, "Malformed robots.txt should be handled as allowed"

        # Test timeout
        start = time.time()
        result = await parser.can_fetch(f"{base_url}/timeout/page", "bot")
        duration = time.time() - start
        assert result, "Timeout should be handled as allowed"
        assert duration < 3, "Timeout not working"

        # Test empty
        result = await parser.can_fetch(f"{base_url}/empty/page", "bot")
        assert result, "Empty robots.txt should be handled as allowed"

        # Test giant file
        start = time.time()
        result = await parser.can_fetch(f"{base_url}/giant/page", "bot")
        assert result, "Giant robots.txt should be handled as allowed"

    finally:
        await runner.cleanup()

    # 5. Cache manipulation
    print("\n5. Testing cache manipulation...")

    # Clear expired
    parser.clear_expired()
    print("✓ Clear expired entries completed")

    # Clear all
    parser.clear_cache()
    print("✓ Clear all cache completed")

    # Test with custom TTL
    custom_parser = RobotsParser(cache_dir=temp_dir, cache_ttl=1)  # 1 second TTL
    result = await custom_parser.can_fetch("https://www.example.com", "bot")
    assert result, "Custom TTL fetch failed"

    await asyncio.sleep(1.1)
    start = time.time()
    result = await custom_parser.can_fetch("https://www.example.com", "bot")
    assert result, "Custom TTL fetch failed after expiry"


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
