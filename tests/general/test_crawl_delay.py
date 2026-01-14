"""
Test cases for Crawl-delay directive support in crawl4ai.

This module tests the respect_crawl_delay feature which allows the crawler
to honor Crawl-delay directives from robots.txt files.
"""

import asyncio
import tempfile
import shutil
import time
import os

import pytest
import pytest_asyncio
from aiohttp import web

from crawl4ai.utils import RobotsParser
from crawl4ai.async_dispatcher import RateLimiter
from crawl4ai.models import DomainState


class TestRobotsParserCrawlDelay:
    """Test cases for RobotsParser.get_crawl_delay() method."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest_asyncio.fixture
    async def test_server_with_delay(self):
        """Start a test HTTP server with crawl-delay in robots.txt."""
        app = web.Application()
        
        async def robots_with_delay(request):
            return web.Response(text="""User-agent: *
Crawl-delay: 5
Disallow: /private/
""")
        
        app.router.add_get('/robots.txt', robots_with_delay)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8181)
        await site.start()
        
        yield "http://localhost:8181"
        
        await runner.cleanup()
    
    @pytest_asyncio.fixture
    async def test_server_bot_specific(self):
        """Start a test HTTP server with bot-specific crawl-delay."""
        app = web.Application()
        
        async def robots_with_bot_specific_delay(request):
            return web.Response(text="""User-agent: MyBot
Crawl-delay: 10

User-agent: *
Crawl-delay: 2
Disallow: /admin/
""")
        
        app.router.add_get('/robots.txt', robots_with_bot_specific_delay)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8183)
        await site.start()
        
        yield "http://localhost:8183"
        
        await runner.cleanup()
    
    @pytest_asyncio.fixture
    async def test_server_no_delay(self):
        """Start a test HTTP server without crawl-delay."""
        app = web.Application()
        
        async def robots_no_delay(request):
            return web.Response(text="""User-agent: *
Disallow: /private/
""")
        
        app.router.add_get('/robots.txt', robots_no_delay)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8184)
        await site.start()
        
        yield "http://localhost:8184"
        
        await runner.cleanup()
    
    @pytest_asyncio.fixture
    async def test_server_empty(self):
        """Start a test HTTP server with empty robots.txt."""
        app = web.Application()
        
        async def robots_empty(request):
            return web.Response(text="")
        
        app.router.add_get('/robots.txt', robots_empty)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8185)
        await site.start()
        
        yield "http://localhost:8185"
        
        await runner.cleanup()
    
    @pytest.mark.asyncio
    async def test_get_crawl_delay_returns_value(self, temp_cache_dir, test_server_with_delay):
        """Test that get_crawl_delay returns the correct delay value."""
        parser = RobotsParser(cache_dir=temp_cache_dir)
        
        delay = await parser.get_crawl_delay(f"{test_server_with_delay}/page", "*")
        await parser.close()
        assert delay == 5.0
    
    @pytest.mark.asyncio
    async def test_get_crawl_delay_bot_specific(self, temp_cache_dir, test_server_bot_specific):
        """Test that get_crawl_delay respects bot-specific delays."""
        parser = RobotsParser(cache_dir=temp_cache_dir)
        
        # MyBot should get 10 second delay
        delay = await parser.get_crawl_delay(f"{test_server_bot_specific}/page", "MyBot")
        assert delay == 10.0
        
        # Clear cache to fetch again
        parser.clear_cache()
        
        # Other bots should get 2 second delay
        delay = await parser.get_crawl_delay(f"{test_server_bot_specific}/page", "OtherBot")
        await parser.close()
        assert delay == 2.0
    
    @pytest.mark.asyncio
    async def test_get_crawl_delay_returns_none_when_not_specified(self, temp_cache_dir, test_server_no_delay):
        """Test that get_crawl_delay returns None when no delay is specified."""
        parser = RobotsParser(cache_dir=temp_cache_dir)
        
        delay = await parser.get_crawl_delay(f"{test_server_no_delay}/page", "*")
        await parser.close()
        assert delay is None
    
    @pytest.mark.asyncio
    async def test_get_crawl_delay_returns_none_for_empty_robots(self, temp_cache_dir, test_server_empty):
        """Test that get_crawl_delay returns None for empty robots.txt."""
        parser = RobotsParser(cache_dir=temp_cache_dir)
        
        delay = await parser.get_crawl_delay(f"{test_server_empty}/page", "*")
        await parser.close()
        assert delay is None
    
    @pytest.mark.asyncio
    async def test_get_crawl_delay_returns_none_for_invalid_url(self, temp_cache_dir):
        """Test that get_crawl_delay handles invalid URLs gracefully."""
        parser = RobotsParser(cache_dir=temp_cache_dir)
        
        delay = await parser.get_crawl_delay("", "*")
        assert delay is None
        
        delay = await parser.get_crawl_delay("not_a_url", "*")
        await parser.close()
        assert delay is None
    
    @pytest.mark.asyncio
    async def test_get_crawl_delay_caches_result(self, temp_cache_dir, test_server_with_delay):
        """Test that get_crawl_delay uses cached results."""
        parser = RobotsParser(cache_dir=temp_cache_dir)
        
        # First call - should fetch
        start = time.time()
        delay1 = await parser.get_crawl_delay(f"{test_server_with_delay}/page", "*")
        first_duration = time.time() - start
        
        # Second call - should be cached and faster
        start = time.time()
        delay2 = await parser.get_crawl_delay(f"{test_server_with_delay}/page", "*")
        second_duration = time.time() - start
        
        await parser.close()
        assert delay1 == delay2 == 5.0
        # Cached lookup should be significantly faster
        assert second_duration < first_duration


class TestRateLimiterWithCrawlDelay:
    """Test cases for RateLimiter with crawl-delay support."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest_asyncio.fixture
    async def test_server(self):
        """Start a test HTTP server with robots.txt that has crawl-delay."""
        app = web.Application()
        
        async def robots_with_delay(request):
            return web.Response(text="""User-agent: *
Crawl-delay: 2
""")
        
        async def page(request):
            return web.Response(text="OK")
        
        app.router.add_get('/robots.txt', robots_with_delay)
        app.router.add_get('/page', page)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8182)
        await site.start()
        
        yield "http://localhost:8182"
        
        await runner.cleanup()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_respects_crawl_delay(self, temp_cache_dir, test_server):
        """Test that RateLimiter waits for crawl-delay between requests."""
        parser = RobotsParser(cache_dir=temp_cache_dir)
        
        rate_limiter = RateLimiter(
            base_delay=(0.1, 0.2),  # Small base delay
            robots_parser=parser,
            respect_crawl_delay=True,
            default_user_agent="*"
        )
        
        url = f"{test_server}/page"
        
        # First request
        start = time.time()
        await rate_limiter.wait_if_needed(url)
        first_request_time = time.time()
        
        # Second request - should wait for crawl-delay (2 seconds)
        await rate_limiter.wait_if_needed(url)
        second_request_time = time.time()
        
        await parser.close()
        
        elapsed = second_request_time - first_request_time
        # Should have waited approximately 2 seconds (crawl-delay)
        assert elapsed >= 1.9, f"Expected ~2s delay, got {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_without_crawl_delay_uses_base_delay(self, temp_cache_dir):
        """Test that RateLimiter uses base_delay when crawl-delay is disabled."""
        parser = RobotsParser(cache_dir=temp_cache_dir)
        
        rate_limiter = RateLimiter(
            base_delay=(0.1, 0.2),
            robots_parser=parser,
            respect_crawl_delay=False,  # Disabled
            default_user_agent="*"
        )
        
        url = "http://example.com/page"
        
        # First request
        await rate_limiter.wait_if_needed(url)
        first_request_time = time.time()
        
        # Second request - should use base_delay (0.1-0.2 seconds)
        await rate_limiter.wait_if_needed(url)
        second_request_time = time.time()
        
        await parser.close()
        
        elapsed = second_request_time - first_request_time
        # Should have waited base_delay (0.1-0.2 seconds)
        assert elapsed < 1.0, f"Expected small delay, got {elapsed}s"
    
    def test_domain_state_has_crawl_delay_field(self):
        """Test that DomainState includes crawl_delay field."""
        state = DomainState()
        assert hasattr(state, 'crawl_delay')
        assert state.crawl_delay is None
        
        state.crawl_delay = 5.0
        assert state.crawl_delay == 5.0


class TestCrawlerRunConfigWithCrawlDelay:
    """Test cases for CrawlerRunConfig.respect_crawl_delay parameter."""
    
    def test_config_has_respect_crawl_delay_parameter(self):
        """Test that CrawlerRunConfig has respect_crawl_delay parameter."""
        from crawl4ai.async_configs import CrawlerRunConfig
        
        config = CrawlerRunConfig()
        assert hasattr(config, 'respect_crawl_delay')
        assert config.respect_crawl_delay is False
    
    def test_config_respect_crawl_delay_can_be_set(self):
        """Test that respect_crawl_delay can be set to True."""
        from crawl4ai.async_configs import CrawlerRunConfig
        
        config = CrawlerRunConfig(respect_crawl_delay=True)
        assert config.respect_crawl_delay is True
    
    def test_config_to_dict_includes_respect_crawl_delay(self):
        """Test that to_dict includes respect_crawl_delay."""
        from crawl4ai.async_configs import CrawlerRunConfig
        
        config = CrawlerRunConfig(respect_crawl_delay=True)
        config_dict = config.to_dict()
        assert 'respect_crawl_delay' in config_dict
        assert config_dict['respect_crawl_delay'] is True
    
    def test_config_from_kwargs_includes_respect_crawl_delay(self):
        """Test that from_kwargs handles respect_crawl_delay."""
        from crawl4ai.async_configs import CrawlerRunConfig
        
        config = CrawlerRunConfig.from_kwargs({"respect_crawl_delay": True})
        assert config.respect_crawl_delay is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
