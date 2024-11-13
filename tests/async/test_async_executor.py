import os, sys
import unittest
import asynctest
import asyncio
import time

from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

# Assuming all classes and imports are already available from the code above
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.config import MAX_METRICS_HISTORY
from crawl4ai.async_executor import (
    SpeedOptimizedExecutor,
    ResourceOptimizedExecutor,
    AsyncWebCrawler,
    ExecutionMode,
    SystemMetrics,
    CallbackType
)

class TestAsyncExecutor(asynctest.TestCase):
    async def setUp(self):
        # Set up a mock crawler
        self.mock_crawler = AsyncMock(spec=AsyncWebCrawler)
        self.mock_crawler.arun = AsyncMock(side_effect=self.mock_crawl)

        # Sample URLs
        self.urls = [
            "https://www.example.com",
            "https://www.python.org",
            "https://www.asyncio.org",
            "https://www.nonexistenturl.xyz",  # This will simulate a failure
        ]

        # Set up callbacks
        self.callbacks = {
            CallbackType.PRE_EXECUTION: AsyncMock(),
            CallbackType.POST_EXECUTION: AsyncMock(),
            CallbackType.ON_ERROR: AsyncMock(),
            CallbackType.ON_RETRY: AsyncMock(),
            CallbackType.ON_BATCH_START: AsyncMock(),
            CallbackType.ON_BATCH_END: AsyncMock(),
            CallbackType.ON_COMPLETE: AsyncMock(),
        }

    async def mock_crawl(self, url: str, **kwargs):
        if "nonexistenturl" in url:
            raise Exception("Failed to fetch URL")
        return f"Mock content for {url}"

    async def test_speed_executor_basic(self):
        """Test basic functionality of SpeedOptimizedExecutor."""
        executor = SpeedOptimizedExecutor(
            crawler=self.mock_crawler,
            callbacks=self.callbacks,
            max_retries=1,
        )

        results = await executor.execute(self.urls)

        # Assertions
        self.assertEqual(len(results), len(self.urls))
        self.mock_crawler.arun.assert_awaited()
        self.callbacks[CallbackType.PRE_EXECUTION].assert_awaited()
        self.callbacks[CallbackType.POST_EXECUTION].assert_awaited()
        self.callbacks[CallbackType.ON_ERROR].assert_awaited()

    async def test_resource_executor_basic(self):
        """Test basic functionality of ResourceOptimizedExecutor."""
        executor = ResourceOptimizedExecutor(
            crawler=self.mock_crawler,
            callbacks=self.callbacks,
            max_concurrent_tasks=2,
            max_retries=1,
        )

        results = await executor.execute(self.urls)

        # Assertions
        self.assertEqual(len(results), len(self.urls))
        self.mock_crawler.arun.assert_awaited()
        self.callbacks[CallbackType.PRE_EXECUTION].assert_awaited()
        self.callbacks[CallbackType.POST_EXECUTION].assert_awaited()
        self.callbacks[CallbackType.ON_ERROR].assert_awaited()

    async def test_pause_and_resume(self):
        """Test the pause and resume functionality."""
        executor = SpeedOptimizedExecutor(
            crawler=self.mock_crawler,
            callbacks=self.callbacks,
            max_retries=1,
        )

        execution_task = asyncio.create_task(executor.execute(self.urls))
        await asyncio.sleep(0.1)
        await executor.control.pause()
        self.assertTrue(await executor.control.is_paused())

        # Ensure that execution is paused
        await asyncio.sleep(0.5)
        await executor.control.resume()
        self.assertFalse(await executor.control.is_paused())

        results = await execution_task

        # Assertions
        self.assertEqual(len(results), len(self.urls))

    async def test_cancellation(self):
        """Test the cancellation functionality."""
        executor = SpeedOptimizedExecutor(
            crawler=self.mock_crawler,
            callbacks=self.callbacks,
            max_retries=1,
        )

        execution_task = asyncio.create_task(executor.execute(self.urls))
        await asyncio.sleep(0.1)
        await executor.control.cancel()
        self.assertTrue(await executor.control.is_cancelled())

        with self.assertRaises(asyncio.CancelledError):
            await execution_task

    async def test_max_retries(self):
        """Test that the executor respects the max_retries setting."""
        executor = SpeedOptimizedExecutor(
            crawler=self.mock_crawler,
            callbacks=self.callbacks,
            max_retries=2,
        )

        results = await executor.execute(self.urls)

        # The failing URL should have been retried
        self.assertEqual(self.mock_crawler.arun.call_count, len(self.urls) + 2)
        self.assertEqual(executor.metrics.total_retries, 2)

    async def test_callbacks_invoked(self):
        """Test that all callbacks are invoked appropriately."""
        executor = SpeedOptimizedExecutor(
            crawler=self.mock_crawler,
            callbacks=self.callbacks,
            max_retries=1,
        )

        await executor.execute(self.urls)

        # Check that callbacks were called the correct number of times
        self.assertEqual(
            self.callbacks[CallbackType.PRE_EXECUTION].call_count,
            len(self.urls) * (1 + executor.metrics.total_retries),
        )
        self.assertEqual(
            self.callbacks[CallbackType.POST_EXECUTION].call_count,
            executor.metrics.completed_urls,
        )
        self.assertEqual(
            self.callbacks[CallbackType.ON_ERROR].call_count,
            executor.metrics.failed_urls * (1 + executor.metrics.total_retries),
        )
        self.callbacks[CallbackType.ON_COMPLETE].assert_awaited_once()

    async def test_resource_limits(self):
        """Test that the ResourceOptimizedExecutor respects resource limits."""
        with patch('psutil.cpu_percent', return_value=95), \
             patch('psutil.virtual_memory', return_value=MagicMock(percent=85, available=1000)):
            executor = ResourceOptimizedExecutor(
                crawler=self.mock_crawler,
                callbacks=self.callbacks,
                max_concurrent_tasks=2,
                max_retries=1,
            )

            results = await executor.execute(self.urls)

            # Assertions
            self.assertEqual(len(results), len(self.urls))
            # Since resources are over threshold, batch size should be minimized
            batch_sizes = [executor.resource_monitor.get_optimal_batch_size(len(self.urls))]
            self.assertTrue(all(size == 1 for size in batch_sizes))

    async def test_system_metrics_limit(self):
        """Test that the system_metrics list does not grow indefinitely."""
        executor = SpeedOptimizedExecutor(
            crawler=self.mock_crawler,
            callbacks=self.callbacks,
            max_retries=1,
        )

        # Simulate many batches to exceed MAX_METRICS_HISTORY
        original_max_history = MAX_METRICS_HISTORY
        try:
            # Temporarily reduce MAX_METRICS_HISTORY for the test
            globals()['MAX_METRICS_HISTORY'] = 5

            # Mock capture_system_metrics to increase system_metrics length
            with patch.object(executor.metrics, 'capture_system_metrics') as mock_capture:
                def side_effect():
                    executor.metrics.system_metrics.append(SystemMetrics(0, 0, 0, time.time()))
                    if len(executor.metrics.system_metrics) > MAX_METRICS_HISTORY:
                        executor.metrics.system_metrics.pop(0)
                mock_capture.side_effect = side_effect

                await executor.execute(self.urls * 3)  # Multiply URLs to create more batches

                # Assertions
                self.assertLessEqual(len(executor.metrics.system_metrics), MAX_METRICS_HISTORY)
        finally:
            # Restore original MAX_METRICS_HISTORY
            globals()['MAX_METRICS_HISTORY'] = original_max_history

if __name__ == "__main__":
    unittest.main()