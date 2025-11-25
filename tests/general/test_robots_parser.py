import pytest

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import web

from crawl4ai.utils import RobotsParser
from tests.helpers import EXAMPLE_URL, TestCacheClient


@pytest.mark.asyncio
async def test_robots_parser_cache():
    cache_client = TestCacheClient()
    parser = RobotsParser(cache_client=cache_client)
    
    mock_response = MagicMock(status=200)
    mock_response.text = AsyncMock(return_value="User-agent: *\nAllow: /\n")
    
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    mock_session.__aenter__.return_value = mock_session
    
    try:
        with patch('crawl4ai.utils.aiohttp.ClientSession', return_value=mock_session):
            allowed = await parser.can_fetch(EXAMPLE_URL, "MyBot/1.0")
            assert allowed
            assert cache_client.count() == 1

            await parser.can_fetch(EXAMPLE_URL, "MyBot/1.0")
            assert cache_client.count() == 1

            await parser.can_fetch("https://docs.crawl4ai.com", "MyBot/1.0")
            assert cache_client.count() == 2
    finally:
        cache_client.cleanup()


@pytest.mark.asyncio
async def test_robots_parser_local_server():
    cache_client = TestCacheClient()
    parser = RobotsParser(cache_client=cache_client, cache_ttl=1)

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
        site = web.TCPSite(runner, "localhost", 8080)
        await site.start()
        return runner

    runner = await start_test_server()
    
    try:
        base_url = "http://localhost:8080"

        # Test public access
        result = await parser.can_fetch(f"{base_url}/public/page", "bot")
        assert result, "Public path should be allowed"

        # Test private access
        result = await parser.can_fetch(f"{base_url}/private/secret", "bot")
        assert not result, "Private path should be denied"

        # Test malformed
        result = await parser.can_fetch("http://localhost:8080/malformed/page", "bot")

        # Test timeout
        start = time.time()
        result = await parser.can_fetch("http://localhost:8080/timeout/page", "bot")
        duration = time.time() - start
        assert duration < 3, "Timeout not working"

        # Test empty
        result = await parser.can_fetch("http://localhost:8080/empty/page", "bot")

        # Test giant file
        start = time.time()
        result = await parser.can_fetch("http://localhost:8080/giant/page", "bot")
        duration = time.time() - start

        # Test with custom TTL
        await parser.can_fetch("https://www.example.com", "bot")
        await asyncio.sleep(1.1)
        start = time.time()
        await parser.can_fetch("https://www.example.com", "bot")

    finally:
        await runner.cleanup()
        cache_client.cleanup()
