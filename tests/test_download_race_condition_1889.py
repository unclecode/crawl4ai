"""
Tests for #1889: downloaded_files race condition — cross-contamination between CrawlResults.

Verifies that downloads are scoped per crawl invocation using crawl_id,
and that late-completing downloads don't leak to subsequent results.
"""
import asyncio
import os
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.async_configs import BrowserConfig


class FakeDownload:
    """Mock Playwright Download object."""
    def __init__(self, filename, delay=0):
        self.suggested_filename = filename
        self._delay = delay
        self._saved = False

    async def save_as(self, path):
        if self._delay:
            await asyncio.sleep(self._delay)
        self._saved = True


@pytest.fixture
def strategy():
    """Create a strategy with downloads enabled."""
    config = BrowserConfig(
        accept_downloads=True,
        downloads_path="/tmp/test-downloads",
    )
    s = AsyncPlaywrightCrawlerStrategy(browser_config=config)
    return s


class TestDownloadScoping:
    """Verify downloads are scoped per crawl invocation."""

    def test_downloads_by_crawl_initialized_as_dict(self, strategy):
        """_downloads_by_crawl should be a dict, not a list."""
        assert isinstance(strategy._downloads_by_crawl, dict)
        assert len(strategy._downloads_by_crawl) == 0

    @pytest.mark.asyncio
    async def test_handle_download_appends_to_correct_crawl(self, strategy):
        """Download should go to the crawl_id it was associated with."""
        crawl_id = uuid.uuid4().hex
        strategy._downloads_by_crawl[crawl_id] = []

        download = FakeDownload("test.pdf")
        await strategy._handle_download(download, crawl_id)

        assert len(strategy._downloads_by_crawl[crawl_id]) == 1
        assert strategy._downloads_by_crawl[crawl_id][0].endswith("test.pdf")

    @pytest.mark.asyncio
    async def test_two_crawls_isolated(self, strategy):
        """Downloads from crawl A must not appear in crawl B."""
        crawl_a = uuid.uuid4().hex
        crawl_b = uuid.uuid4().hex
        strategy._downloads_by_crawl[crawl_a] = []
        strategy._downloads_by_crawl[crawl_b] = []

        await strategy._handle_download(FakeDownload("file_a.pdf"), crawl_a)
        await strategy._handle_download(FakeDownload("file_b.xlsx"), crawl_b)

        assert len(strategy._downloads_by_crawl[crawl_a]) == 1
        assert "file_a.pdf" in strategy._downloads_by_crawl[crawl_a][0]
        assert len(strategy._downloads_by_crawl[crawl_b]) == 1
        assert "file_b.xlsx" in strategy._downloads_by_crawl[crawl_b][0]

    @pytest.mark.asyncio
    async def test_late_download_does_not_contaminate(self, strategy):
        """If crawl A finishes (pops its list), a late download for A should not go to B."""
        crawl_a = uuid.uuid4().hex
        crawl_b = uuid.uuid4().hex
        strategy._downloads_by_crawl[crawl_a] = []
        strategy._downloads_by_crawl[crawl_b] = []

        # Simulate crawl A finishing — pop its list
        result_a = strategy._downloads_by_crawl.pop(crawl_a, [])
        assert result_a == []

        # Late download for crawl A completes
        await strategy._handle_download(FakeDownload("late_file.pdf"), crawl_a)

        # Crawl B's list must be untouched
        assert len(strategy._downloads_by_crawl[crawl_b]) == 0

    @pytest.mark.asyncio
    async def test_late_download_logged_not_lost(self, strategy):
        """Late download should still be saved to disk, just not attached to results."""
        crawl_id = uuid.uuid4().hex
        # Don't create the crawl entry — simulate it already popped
        download = FakeDownload("orphan.pdf")
        await strategy._handle_download(download, crawl_id)

        # File was still saved (download.save_as was called)
        assert download._saved
        # But no crawl list was contaminated
        assert crawl_id not in strategy._downloads_by_crawl

    @pytest.mark.asyncio
    async def test_multiple_downloads_same_crawl(self, strategy):
        """Multiple downloads for the same crawl should all be captured."""
        crawl_id = uuid.uuid4().hex
        strategy._downloads_by_crawl[crawl_id] = []

        for i in range(5):
            await strategy._handle_download(FakeDownload(f"doc_{i}.pdf"), crawl_id)

        assert len(strategy._downloads_by_crawl[crawl_id]) == 5

    @pytest.mark.asyncio
    async def test_pop_returns_files_and_cleans_up(self, strategy):
        """Popping the crawl_id list should return files and remove the entry."""
        crawl_id = uuid.uuid4().hex
        strategy._downloads_by_crawl[crawl_id] = []

        await strategy._handle_download(FakeDownload("report.pdf"), crawl_id)

        files = strategy._downloads_by_crawl.pop(crawl_id, [])
        assert len(files) == 1
        assert "report.pdf" in files[0]
        assert crawl_id not in strategy._downloads_by_crawl


class TestConcurrentRace:
    """Simulate the actual race condition described in #1889."""

    @pytest.mark.asyncio
    async def test_concurrent_downloads_no_crosscontamination(self, strategy):
        """
        Simulate: crawl A starts slow download, crawl B starts and finishes,
        then A's download completes. B must not get A's file.
        """
        crawl_a = uuid.uuid4().hex
        crawl_b = uuid.uuid4().hex
        strategy._downloads_by_crawl[crawl_a] = []

        # Start slow download for A (won't complete immediately)
        slow_download = FakeDownload("big_file.xlsx", delay=0.2)
        task_a = asyncio.create_task(
            strategy._handle_download(slow_download, crawl_a)
        )

        # Crawl B starts and finishes before A's download completes
        strategy._downloads_by_crawl[crawl_b] = []
        await strategy._handle_download(FakeDownload("page_b.html"), crawl_b)
        result_b = strategy._downloads_by_crawl.pop(crawl_b, [])

        # Wait for A's download to finish
        await task_a
        result_a = strategy._downloads_by_crawl.pop(crawl_a, [])

        # A has its file, B has its file — no cross-contamination
        assert len(result_a) == 1
        assert "big_file.xlsx" in result_a[0]
        assert len(result_b) == 1
        assert "page_b.html" in result_b[0]

    @pytest.mark.asyncio
    async def test_late_download_after_pop_no_crash(self, strategy):
        """
        Simulate: crawl A starts download, crawl A finishes (pops),
        then download completes. Should not crash or contaminate.
        """
        crawl_a = uuid.uuid4().hex
        strategy._downloads_by_crawl[crawl_a] = []

        # Start slow download
        slow_download = FakeDownload("late.pdf", delay=0.1)
        task = asyncio.create_task(
            strategy._handle_download(slow_download, crawl_a)
        )

        # Crawl A finishes before download completes
        result_a = strategy._downloads_by_crawl.pop(crawl_a, [])
        assert result_a == []  # download hadn't completed yet

        # Download finishes — should not crash
        await task

        # Dict is clean
        assert crawl_a not in strategy._downloads_by_crawl
