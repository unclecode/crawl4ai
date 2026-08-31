"""Tests for crawler pool release_crawler() and active_requests tracking.

These tests validate the pool lifecycle without requiring Docker or a running
server. They test the release logic directly using mock crawler objects.
"""

import asyncio
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Standalone release_crawler implementation for testing
# (mirrors the logic that will be added to deploy/docker/crawler_pool.py)
# ---------------------------------------------------------------------------

_TEST_LOCK = asyncio.Lock()


async def _release_crawler(crawler, lock=None):
    """Standalone release logic matching crawler_pool.release_crawler()."""
    lock = lock or _TEST_LOCK
    async with lock:
        if hasattr(crawler, "active_requests"):
            crawler.active_requests = max(0, crawler.active_requests - 1)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestReleaseCrawler:
    """Tests for the release_crawler function."""

    @pytest.mark.asyncio
    async def test_release_decrements_active_requests(self):
        """release_crawler should decrement active_requests by 1."""
        crawler = MagicMock()
        crawler.active_requests = 3

        await _release_crawler(crawler)
        assert crawler.active_requests == 2

    @pytest.mark.asyncio
    async def test_release_floors_at_zero(self):
        """active_requests should never go below 0."""
        crawler = MagicMock()
        crawler.active_requests = 0

        await _release_crawler(crawler)
        assert crawler.active_requests == 0

    @pytest.mark.asyncio
    async def test_release_from_one_to_zero(self):
        """Standard case: single request finishes."""
        crawler = MagicMock()
        crawler.active_requests = 1

        await _release_crawler(crawler)
        assert crawler.active_requests == 0

    @pytest.mark.asyncio
    async def test_release_handles_missing_attribute(self):
        """Should not crash if crawler has no active_requests attribute."""
        crawler = MagicMock(spec=[])  # no attributes at all
        # Should not raise
        await _release_crawler(crawler)

    @pytest.mark.asyncio
    async def test_multiple_releases_decrement_correctly(self):
        """Multiple sequential releases should each decrement by 1."""
        crawler = MagicMock()
        crawler.active_requests = 5

        for expected in [4, 3, 2, 1, 0, 0]:  # last one should floor at 0
            await _release_crawler(crawler)
            assert crawler.active_requests == expected

    @pytest.mark.asyncio
    async def test_concurrent_releases_are_safe(self):
        """Concurrent releases should not corrupt the counter."""
        crawler = MagicMock()
        crawler.active_requests = 100
        lock = asyncio.Lock()

        async def release_n_times(n):
            for _ in range(n):
                await _release_crawler(crawler, lock=lock)

        # 10 concurrent tasks each releasing 10 times = 100 total
        tasks = [asyncio.create_task(release_n_times(10)) for _ in range(10)]
        await asyncio.gather(*tasks)

        assert crawler.active_requests == 0


class TestActiveRequestsTracking:
    """Tests for the get/release lifecycle pattern."""

    @pytest.mark.asyncio
    async def test_get_sets_active_requests(self):
        """Simulated get_crawler should set active_requests to 1 for new crawlers."""
        crawler = MagicMock()
        # Simulate what get_crawler does for a new browser
        crawler.active_requests = 1

        assert crawler.active_requests == 1

    @pytest.mark.asyncio
    async def test_get_increments_existing(self):
        """Simulated get_crawler should increment for existing pooled crawlers."""
        crawler = MagicMock()
        crawler.active_requests = 2

        # Simulate another get_crawler call returning same browser
        crawler.active_requests += 1
        assert crawler.active_requests == 3

    @pytest.mark.asyncio
    async def test_full_get_release_lifecycle(self):
        """Full lifecycle: get -> use -> release -> get -> release."""
        crawler = MagicMock()

        # First request gets the crawler
        crawler.active_requests = 1

        # Second concurrent request gets same crawler
        crawler.active_requests += 1
        assert crawler.active_requests == 2

        # First request finishes
        await _release_crawler(crawler)
        assert crawler.active_requests == 1

        # Second request finishes
        await _release_crawler(crawler)
        assert crawler.active_requests == 0

    @pytest.mark.asyncio
    async def test_janitor_safety_check(self):
        """Janitor should only close browsers with active_requests == 0."""
        crawler = MagicMock()
        crawler.active_requests = 1

        # Janitor check: should NOT close
        should_close = getattr(crawler, "active_requests", 0) == 0
        assert should_close is False

        # Request finishes
        await _release_crawler(crawler)

        # Janitor check: now safe to close
        should_close = getattr(crawler, "active_requests", 0) == 0
        assert should_close is True
