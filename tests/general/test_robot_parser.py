from crawl4ai.utils import RobotsParser
            
import asyncio
import aiohttp
from aiohttp import web
import tempfile
import shutil
import os, sys, time, json


async def test_robots_parser():
    print("\n=== Testing RobotsParser ===\n")
    
    # Setup temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Basic setup test
        print("1. Testing basic initialization...")
        parser = RobotsParser(cache_dir=temp_dir)
        assert os.path.exists(parser.db_path), "Database file not created"
        print("✓ Basic initialization passed")

        # 2. Test common cases
        print("\n2. Testing common cases...")
        allowed = await parser.can_fetch("https://www.example.com", "MyBot/1.0")
        print(f"✓ Regular website fetch: {'allowed' if allowed else 'denied'}")
        
        # Test caching
        print("Testing cache...")
        start = time.time()
        await parser.can_fetch("https://www.example.com", "MyBot/1.0")
        duration = time.time() - start
        print(f"✓ Cached lookup took: {duration*1000:.2f}ms")
        assert duration < 0.03, "Cache lookup too slow"

        # 3. Edge cases
        print("\n3. Testing edge cases...")
        
        # Empty URL
        result = await parser.can_fetch("", "MyBot/1.0")
        print(f"✓ Empty URL handled: {'allowed' if result else 'denied'}")
        
        # Invalid URL
        result = await parser.can_fetch("not_a_url", "MyBot/1.0")
        print(f"✓ Invalid URL handled: {'allowed' if result else 'denied'}")
        
        # URL without scheme
        result = await parser.can_fetch("example.com/page", "MyBot/1.0")
        print(f"✓ URL without scheme handled: {'allowed' if result else 'denied'}")

        # 4. Test with local server
        async def start_test_server():
            app = web.Application()
            
            async def robots_txt(request):
                return web.Response(text="""User-agent: *
Disallow: /private/
Allow: /public/
""")
            
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
            app.router.add_get('/robots.txt', robots_txt)
            app.router.add_get('/malformed/robots.txt', malformed_robots)
            app.router.add_get('/timeout/robots.txt', timeout_robots)
            app.router.add_get('/empty/robots.txt', empty_robots)
            app.router.add_get('/giant/robots.txt', giant_robots)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', 8080)
            await site.start()
            return runner

        runner = await start_test_server()
        try:
            print("\n4. Testing robots.txt rules...")
            base_url = "http://localhost:8080"
            
            # Test public access
            result = await parser.can_fetch(f"{base_url}/public/page", "bot")
            print(f"Public access (/public/page): {'allowed' if result else 'denied'}")
            assert result, "Public path should be allowed"
            
            # Test private access
            result = await parser.can_fetch(f"{base_url}/private/secret", "bot")
            print(f"Private access (/private/secret): {'allowed' if result else 'denied'}")
            assert not result, "Private path should be denied"
            
            # Test malformed
            result = await parser.can_fetch("http://localhost:8080/malformed/page", "bot")
            print(f"✓ Malformed robots.txt handled: {'allowed' if result else 'denied'}")
            
            # Test timeout
            start = time.time()
            result = await parser.can_fetch("http://localhost:8080/timeout/page", "bot")
            duration = time.time() - start
            print(f"✓ Timeout handled (took {duration:.2f}s): {'allowed' if result else 'denied'}")
            assert duration < 3, "Timeout not working"
            
            # Test empty
            result = await parser.can_fetch("http://localhost:8080/empty/page", "bot")
            print(f"✓ Empty robots.txt handled: {'allowed' if result else 'denied'}")
            
            # Test giant file
            start = time.time()
            result = await parser.can_fetch("http://localhost:8080/giant/page", "bot")
            duration = time.time() - start
            print(f"✓ Giant robots.txt handled (took {duration:.2f}s): {'allowed' if result else 'denied'}")

        finally:
            await runner.cleanup()

        # 4b. Test query-string disallow (Disallow: /*?) on a separate host port.
        # Plain URLs must stay crawlable while query URLs are denied (RFC 9309).
        async def start_query_server():
            query_app = web.Application()

            async def query_robots(request):
                return web.Response(text="User-agent: *\nDisallow: /*?\n")

            query_app.router.add_get('/robots.txt', query_robots)
            query_runner = web.AppRunner(query_app)
            await query_runner.setup()
            query_site = web.TCPSite(query_runner, 'localhost', 8081)
            await query_site.start()
            return query_runner

        query_runner = await start_query_server()
        try:
            print("\n4b. Testing query-string robots.txt rules...")
            query_base = "http://localhost:8081"

            result = await parser.can_fetch(f"{query_base}/", "bot")
            print(f"Plain root (/): {'allowed' if result else 'denied'}")
            assert result, "Plain root should be allowed with Disallow: /*?"

            result = await parser.can_fetch(f"{query_base}/article", "bot")
            print(f"Plain page (/article): {'allowed' if result else 'denied'}")
            assert result, "Plain page should be allowed with Disallow: /*?"

            result = await parser.can_fetch(f"{query_base}/?page=2", "bot")
            print(f"Query root (/?page=2): {'allowed' if result else 'denied'}")
            assert not result, "Query root should be denied with Disallow: /*?"

            result = await parser.can_fetch(f"{query_base}/article?ref=x", "bot")
            print(f"Query page (/article?ref=x): {'allowed' if result else 'denied'}")
            assert not result, "Query page should be denied with Disallow: /*?"
        finally:
            await query_runner.cleanup()

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
        await custom_parser.can_fetch("https://www.example.com", "bot")
        print("✓ Custom TTL fetch completed")
        await asyncio.sleep(1.1)
        start = time.time()
        await custom_parser.can_fetch("https://www.example.com", "bot")
        print(f"✓ TTL expiry working (refetched after {time.time() - start:.2f}s)")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print("\nTest cleanup completed")

async def main():
    try:
        await test_robots_parser()
    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())