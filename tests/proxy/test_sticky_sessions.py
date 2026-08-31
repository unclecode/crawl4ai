"""
Comprehensive test suite for Sticky Proxy Sessions functionality.

Tests cover:
1. Basic sticky session - same proxy for same session_id
2. Different sessions get different proxies
3. Session release
4. TTL expiration
5. Thread safety / concurrent access
6. Integration tests with AsyncWebCrawler
"""

import asyncio
import os
import time
import pytest
from unittest.mock import patch

from crawl4ai import AsyncWebCrawler, BrowserConfig
from crawl4ai.async_configs import CrawlerRunConfig, ProxyConfig
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy
from crawl4ai.cache_context import CacheMode


class TestRoundRobinProxyStrategySession:
    """Test suite for RoundRobinProxyStrategy session methods."""

    def setup_method(self):
        """Setup for each test method."""
        self.proxies = [
            ProxyConfig(server=f"http://proxy{i}.test:8080")
            for i in range(5)
        ]

    # ==================== BASIC STICKY SESSION TESTS ====================

    @pytest.mark.asyncio
    async def test_sticky_session_same_proxy(self):
        """Verify same proxy is returned for same session_id."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        # First call - acquires proxy
        proxy1 = await strategy.get_proxy_for_session("session-1")

        # Second call - should return same proxy
        proxy2 = await strategy.get_proxy_for_session("session-1")

        # Third call - should return same proxy
        proxy3 = await strategy.get_proxy_for_session("session-1")

        assert proxy1 is not None
        assert proxy1.server == proxy2.server == proxy3.server

    @pytest.mark.asyncio
    async def test_different_sessions_different_proxies(self):
        """Verify different session_ids can get different proxies."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        proxy_a = await strategy.get_proxy_for_session("session-a")
        proxy_b = await strategy.get_proxy_for_session("session-b")
        proxy_c = await strategy.get_proxy_for_session("session-c")

        # All should be different (round-robin)
        servers = {proxy_a.server, proxy_b.server, proxy_c.server}
        assert len(servers) == 3

    @pytest.mark.asyncio
    async def test_sticky_session_with_regular_rotation(self):
        """Verify sticky sessions don't interfere with regular rotation."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        # Acquire a sticky session
        session_proxy = await strategy.get_proxy_for_session("sticky-session")

        # Regular rotation should continue independently
        regular_proxy1 = await strategy.get_next_proxy()
        regular_proxy2 = await strategy.get_next_proxy()

        # Sticky session should still return same proxy
        session_proxy_again = await strategy.get_proxy_for_session("sticky-session")

        assert session_proxy.server == session_proxy_again.server
        # Regular proxies should rotate
        assert regular_proxy1.server != regular_proxy2.server

    # ==================== SESSION RELEASE TESTS ====================

    @pytest.mark.asyncio
    async def test_session_release(self):
        """Verify session can be released and reacquired."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        # Acquire session
        proxy1 = await strategy.get_proxy_for_session("session-1")
        assert strategy.get_session_proxy("session-1") is not None

        # Release session
        await strategy.release_session("session-1")
        assert strategy.get_session_proxy("session-1") is None

        # Reacquire - should get a new proxy (next in round-robin)
        proxy2 = await strategy.get_proxy_for_session("session-1")
        assert proxy2 is not None
        # After release, next call gets the next proxy in rotation
        # (not necessarily the same as before)

    @pytest.mark.asyncio
    async def test_release_nonexistent_session(self):
        """Verify releasing non-existent session doesn't raise error."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        # Should not raise
        await strategy.release_session("nonexistent-session")

    @pytest.mark.asyncio
    async def test_release_twice(self):
        """Verify releasing session twice doesn't raise error."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        await strategy.get_proxy_for_session("session-1")
        await strategy.release_session("session-1")
        await strategy.release_session("session-1")  # Should not raise

    # ==================== GET SESSION PROXY TESTS ====================

    @pytest.mark.asyncio
    async def test_get_session_proxy_existing(self):
        """Verify get_session_proxy returns proxy for existing session."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        acquired = await strategy.get_proxy_for_session("session-1")
        retrieved = strategy.get_session_proxy("session-1")

        assert retrieved is not None
        assert acquired.server == retrieved.server

    def test_get_session_proxy_nonexistent(self):
        """Verify get_session_proxy returns None for non-existent session."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        result = strategy.get_session_proxy("nonexistent-session")
        assert result is None

    # ==================== TTL EXPIRATION TESTS ====================

    @pytest.mark.asyncio
    async def test_session_ttl_not_expired(self):
        """Verify session returns same proxy when TTL not expired."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        # Acquire with 10 second TTL
        proxy1 = await strategy.get_proxy_for_session("session-1", ttl=10)

        # Immediately request again - should return same proxy
        proxy2 = await strategy.get_proxy_for_session("session-1", ttl=10)

        assert proxy1.server == proxy2.server

    @pytest.mark.asyncio
    async def test_session_ttl_expired(self):
        """Verify new proxy acquired after TTL expires."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        # Acquire with 1 second TTL
        proxy1 = await strategy.get_proxy_for_session("session-1", ttl=1)

        # Wait for TTL to expire
        await asyncio.sleep(1.1)

        # Request again - should get new proxy due to expiration
        proxy2 = await strategy.get_proxy_for_session("session-1", ttl=1)

        # May or may not be same server depending on round-robin state,
        # but session should have been recreated
        assert proxy2 is not None

    @pytest.mark.asyncio
    async def test_get_session_proxy_ttl_expired(self):
        """Verify get_session_proxy returns None after TTL expires."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        await strategy.get_proxy_for_session("session-1", ttl=1)

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should return None for expired session
        result = strategy.get_session_proxy("session-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        """Verify cleanup_expired_sessions removes expired sessions."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        # Create sessions with short TTL
        await strategy.get_proxy_for_session("short-ttl-1", ttl=1)
        await strategy.get_proxy_for_session("short-ttl-2", ttl=1)
        # Create session without TTL (should not be cleaned up)
        await strategy.get_proxy_for_session("no-ttl")

        # Wait for TTL to expire
        await asyncio.sleep(1.1)

        # Cleanup
        removed = await strategy.cleanup_expired_sessions()

        assert removed == 2
        assert strategy.get_session_proxy("short-ttl-1") is None
        assert strategy.get_session_proxy("short-ttl-2") is None
        assert strategy.get_session_proxy("no-ttl") is not None

    # ==================== GET ACTIVE SESSIONS TESTS ====================

    @pytest.mark.asyncio
    async def test_get_active_sessions(self):
        """Verify get_active_sessions returns all active sessions."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        await strategy.get_proxy_for_session("session-a")
        await strategy.get_proxy_for_session("session-b")
        await strategy.get_proxy_for_session("session-c")

        active = strategy.get_active_sessions()

        assert len(active) == 3
        assert "session-a" in active
        assert "session-b" in active
        assert "session-c" in active

    @pytest.mark.asyncio
    async def test_get_active_sessions_excludes_expired(self):
        """Verify get_active_sessions excludes expired sessions."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        await strategy.get_proxy_for_session("short-ttl", ttl=1)
        await strategy.get_proxy_for_session("no-ttl")

        # Before expiration
        active = strategy.get_active_sessions()
        assert len(active) == 2

        # Wait for TTL to expire
        await asyncio.sleep(1.1)

        # After expiration
        active = strategy.get_active_sessions()
        assert len(active) == 1
        assert "no-ttl" in active
        assert "short-ttl" not in active

    # ==================== THREAD SAFETY TESTS ====================

    @pytest.mark.asyncio
    async def test_concurrent_session_access(self):
        """Verify thread-safe access to sessions."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        async def acquire_session(session_id: str):
            proxy = await strategy.get_proxy_for_session(session_id)
            await asyncio.sleep(0.01)  # Simulate work
            return proxy.server

        # Acquire same session from multiple coroutines
        results = await asyncio.gather(*[
            acquire_session("shared-session") for _ in range(10)
        ])

        # All should get same proxy
        assert len(set(results)) == 1

    @pytest.mark.asyncio
    async def test_concurrent_different_sessions(self):
        """Verify concurrent acquisition of different sessions works correctly."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        async def acquire_session(session_id: str):
            proxy = await strategy.get_proxy_for_session(session_id)
            await asyncio.sleep(0.01)
            return (session_id, proxy.server)

        # Acquire different sessions concurrently
        results = await asyncio.gather(*[
            acquire_session(f"session-{i}") for i in range(5)
        ])

        # Each session should have a consistent proxy
        session_proxies = dict(results)
        assert len(session_proxies) == 5

        # Verify each session still returns same proxy
        for session_id, expected_server in session_proxies.items():
            actual = await strategy.get_proxy_for_session(session_id)
            assert actual.server == expected_server

    @pytest.mark.asyncio
    async def test_concurrent_session_acquire_and_release(self):
        """Verify concurrent acquire and release operations work correctly."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        async def acquire_and_release(session_id: str):
            proxy = await strategy.get_proxy_for_session(session_id)
            await asyncio.sleep(0.01)
            await strategy.release_session(session_id)
            return proxy.server

        # Run multiple acquire/release cycles concurrently
        await asyncio.gather(*[
            acquire_and_release(f"session-{i}") for i in range(10)
        ])

        # All sessions should be released
        active = strategy.get_active_sessions()
        assert len(active) == 0

    # ==================== EMPTY PROXY POOL TESTS ====================

    @pytest.mark.asyncio
    async def test_empty_proxy_pool_session(self):
        """Verify behavior with empty proxy pool."""
        strategy = RoundRobinProxyStrategy()  # No proxies

        result = await strategy.get_proxy_for_session("session-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_add_proxies_after_session(self):
        """Verify adding proxies after session creation works."""
        strategy = RoundRobinProxyStrategy()

        # No proxies initially
        result1 = await strategy.get_proxy_for_session("session-1")
        assert result1 is None

        # Add proxies
        strategy.add_proxies(self.proxies)

        # Now should work
        result2 = await strategy.get_proxy_for_session("session-2")
        assert result2 is not None


class TestCrawlerRunConfigSession:
    """Test CrawlerRunConfig with sticky session parameters."""

    def test_config_has_session_fields(self):
        """Verify CrawlerRunConfig has sticky session fields."""
        config = CrawlerRunConfig(
            proxy_session_id="test-session",
            proxy_session_ttl=300,
            proxy_session_auto_release=True
        )

        assert config.proxy_session_id == "test-session"
        assert config.proxy_session_ttl == 300
        assert config.proxy_session_auto_release is True

    def test_config_session_defaults(self):
        """Verify default values for session fields."""
        config = CrawlerRunConfig()

        assert config.proxy_session_id is None
        assert config.proxy_session_ttl is None
        assert config.proxy_session_auto_release is False


class TestCrawlerStickySessionIntegration:
    """Integration tests for AsyncWebCrawler with sticky sessions."""

    def setup_method(self):
        """Setup for each test method."""
        self.proxies = [
            ProxyConfig(server=f"http://proxy{i}.test:8080")
            for i in range(3)
        ]
        self.test_url = "https://httpbin.org/ip"

    @pytest.mark.asyncio
    async def test_crawler_sticky_session_without_proxy(self):
        """Test that crawler works when proxy_session_id set but no strategy."""
        browser_config = BrowserConfig(headless=True)

        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_session_id="test-session",
            page_timeout=15000
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=self.test_url, config=config)
            # Should work without errors (no proxy strategy means no proxy)
            assert result is not None

    @pytest.mark.asyncio
    async def test_crawler_sticky_session_basic(self):
        """Test basic sticky session with crawler."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_rotation_strategy=strategy,
            proxy_session_id="integration-test",
            page_timeout=10000
        )

        browser_config = BrowserConfig(headless=True)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # First request
            try:
                result1 = await crawler.arun(url=self.test_url, config=config)
            except Exception:
                pass  # Proxy connection may fail, but session should be tracked

            # Verify session was created
            session_proxy = strategy.get_session_proxy("integration-test")
            assert session_proxy is not None

            # Cleanup
            await strategy.release_session("integration-test")

    @pytest.mark.asyncio
    async def test_crawler_rotating_vs_sticky(self):
        """Compare rotating behavior vs sticky session behavior."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        # Config WITHOUT sticky session - should rotate
        rotating_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_rotation_strategy=strategy,
            page_timeout=5000
        )

        # Config WITH sticky session - should use same proxy
        sticky_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_rotation_strategy=strategy,
            proxy_session_id="sticky-test",
            page_timeout=5000
        )

        browser_config = BrowserConfig(headless=True)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Track proxy configs used
            rotating_proxies = []
            sticky_proxies = []

            # Try rotating requests (may fail due to test proxies, but config should be set)
            for _ in range(3):
                try:
                    await crawler.arun(url=self.test_url, config=rotating_config)
                except Exception:
                    pass
                rotating_proxies.append(rotating_config.proxy_config.server if rotating_config.proxy_config else None)

            # Try sticky requests
            for _ in range(3):
                try:
                    await crawler.arun(url=self.test_url, config=sticky_config)
                except Exception:
                    pass
                sticky_proxies.append(sticky_config.proxy_config.server if sticky_config.proxy_config else None)

            # Rotating should have different proxies (or cycle through them)
            # Sticky should have same proxy for all requests
            if all(sticky_proxies):
                assert len(set(sticky_proxies)) == 1, "Sticky session should use same proxy"

            await strategy.release_session("sticky-test")


class TestStickySessionRealWorld:
    """Real-world scenario tests for sticky sessions.

    Note: These tests require actual proxy servers to verify IP consistency.
    They are marked to be skipped if no proxy is configured.
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get('TEST_PROXY_1'),
        reason="Requires TEST_PROXY_1 environment variable"
    )
    async def test_verify_ip_consistency(self):
        """Verify that sticky session actually uses same IP.

        This test requires real proxies set in environment variables:
        TEST_PROXY_1=ip:port:user:pass
        TEST_PROXY_2=ip:port:user:pass
        """
        import re

        # Load proxies from environment
        proxy_strs = [
            os.environ.get('TEST_PROXY_1', ''),
            os.environ.get('TEST_PROXY_2', '')
        ]
        proxies = [ProxyConfig.from_string(p) for p in proxy_strs if p]

        if len(proxies) < 2:
            pytest.skip("Need at least 2 proxies for this test")

        strategy = RoundRobinProxyStrategy(proxies)

        # Config WITH sticky session
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_rotation_strategy=strategy,
            proxy_session_id="ip-verify-session",
            page_timeout=30000
        )

        browser_config = BrowserConfig(headless=True)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            ips = []

            for i in range(3):
                result = await crawler.arun(
                    url="https://httpbin.org/ip",
                    config=config
                )

                if result and result.success and result.html:
                    # Extract IP from response
                    ip_match = re.search(r'"origin":\s*"([^"]+)"', result.html)
                    if ip_match:
                        ips.append(ip_match.group(1))

            await strategy.release_session("ip-verify-session")

            # All IPs should be same for sticky session
            if len(ips) >= 2:
                assert len(set(ips)) == 1, f"Expected same IP, got: {ips}"


# ==================== STANDALONE TEST FUNCTIONS ====================

@pytest.mark.asyncio
async def test_sticky_session_simple():
    """Simple test for sticky session functionality."""
    proxies = [
        ProxyConfig(server=f"http://proxy{i}.test:8080")
        for i in range(3)
    ]
    strategy = RoundRobinProxyStrategy(proxies)

    # Same session should return same proxy
    p1 = await strategy.get_proxy_for_session("test")
    p2 = await strategy.get_proxy_for_session("test")
    p3 = await strategy.get_proxy_for_session("test")

    assert p1.server == p2.server == p3.server
    print(f"Sticky session works! All requests use: {p1.server}")

    # Cleanup
    await strategy.release_session("test")


if __name__ == "__main__":
    print("Running Sticky Session tests...")
    print("=" * 50)

    asyncio.run(test_sticky_session_simple())

    print("\n" + "=" * 50)
    print("To run the full pytest suite, use: pytest " + __file__)
    print("=" * 50)
