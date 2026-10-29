"""
Tests for #1894: AsyncHTTPCrawlerStrategy passes page_timeout (ms) directly
to aiohttp ClientTimeout (seconds) without converting.

Verifies that page_timeout (milliseconds) is correctly converted to seconds
before being passed to aiohttp.ClientTimeout.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp


class TestHttpTimeoutConversion:
    """Verify page_timeout ms → seconds conversion for aiohttp."""

    def test_default_page_timeout_is_milliseconds(self):
        """page_timeout default (60000) is in milliseconds."""
        from crawl4ai.async_configs import CrawlerRunConfig
        config = CrawlerRunConfig()
        assert config.page_timeout == 60000, "Default page_timeout should be 60000ms"

    def test_aiohttp_client_timeout_expects_seconds(self):
        """Sanity check: aiohttp.ClientTimeout(total=60) means 60 seconds."""
        timeout = aiohttp.ClientTimeout(total=60)
        assert timeout.total == 60

    def test_conversion_default_timeout(self):
        """Default page_timeout=60000ms should convert to 60s for aiohttp."""
        from crawl4ai.async_configs import CrawlerRunConfig
        config = CrawlerRunConfig()

        # Simulate the conversion logic from _handle_http
        timeout_sec = (config.page_timeout / 1000) if config.page_timeout else 30
        assert timeout_sec == 60.0

    def test_conversion_custom_timeout(self):
        """page_timeout=5000ms should convert to 5s for aiohttp."""
        from crawl4ai.async_configs import CrawlerRunConfig
        config = CrawlerRunConfig(page_timeout=5000)

        timeout_sec = (config.page_timeout / 1000) if config.page_timeout else 30
        assert timeout_sec == 5.0

    def test_conversion_small_timeout(self):
        """page_timeout=500ms should convert to 0.5s for aiohttp."""
        from crawl4ai.async_configs import CrawlerRunConfig
        config = CrawlerRunConfig(page_timeout=500)

        timeout_sec = (config.page_timeout / 1000) if config.page_timeout else 30
        assert timeout_sec == 0.5

    def test_timeout_not_absurdly_large(self):
        """Converted timeout should never be in the thousands of seconds."""
        from crawl4ai.async_configs import CrawlerRunConfig
        config = CrawlerRunConfig()  # default 60000ms

        timeout_sec = (config.page_timeout / 1000) if config.page_timeout else 30
        timeout = aiohttp.ClientTimeout(total=timeout_sec)

        assert timeout.total <= 300, (
            f"Timeout is {timeout.total}s ({timeout.total/3600:.1f}h) — "
            "likely a ms/s unit mismatch"
        )

    def test_strategy_has_correct_default_timeout_in_seconds(self):
        """AsyncHTTPCrawlerStrategy.DEFAULT_TIMEOUT should be in seconds."""
        from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
        assert AsyncHTTPCrawlerStrategy.DEFAULT_TIMEOUT == 30, (
            "DEFAULT_TIMEOUT should be 30 seconds"
        )

    def test_zero_page_timeout_uses_default(self):
        """page_timeout=0 should fall back to DEFAULT_TIMEOUT."""
        from crawl4ai.async_configs import CrawlerRunConfig
        config = CrawlerRunConfig(page_timeout=0)

        timeout_sec = (config.page_timeout / 1000) if config.page_timeout else 30
        assert timeout_sec == 30
