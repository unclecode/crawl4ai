# test_batch_crawl.py

import asyncio
import unittest
from unittest.mock import Mock, patch, AsyncMock
import pytest

from crawl4ai.pipeline import Pipeline, create_pipeline, batch_crawl
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.models import CrawlResult, CrawlResultContainer
from crawl4ai.browser_hub_manager import BrowserHubManager


# Utility function for tests
async def create_mock_result(url, success=True, status_code=200, html="<html></html>"):
    """Create a mock crawl result for testing"""
    result = CrawlResult(
        url=url,
        html=html,
        success=success,
        status_code=status_code,
        error_message="" if success else f"Error crawling {url}"
    )
    return CrawlResultContainer(result)


class TestBatchCrawl(unittest.IsolatedAsyncioTestCase):
    """Test cases for the batch_crawl function"""
    
    async def asyncSetUp(self):
        """Set up test environment"""
        self.logger = AsyncLogger(verbose=False)
        self.browser_config = BrowserConfig(headless=True)
        self.crawler_config = CrawlerRunConfig()
        
        # URLs for testing
        self.test_urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
            "https://example.com/4",
            "https://example.com/5"
        ]
        
        # Mock pipeline to avoid actual crawling
        self.mock_pipeline = AsyncMock()
        self.mock_pipeline.crawl = AsyncMock()
        
        # Set up pipeline to return success for most URLs, but failure for one
        async def mock_crawl(url, config=None):
            if url == "https://example.com/3":
                return await create_mock_result(url, success=False, status_code=404)
            return await create_mock_result(url, success=True)
            
        self.mock_pipeline.crawl.side_effect = mock_crawl
        
        # Patch the create_pipeline function
        self.create_pipeline_patch = patch(
            'crawl4ai.pipeline.create_pipeline', 
            return_value=self.mock_pipeline
        )
        self.mock_create_pipeline = self.create_pipeline_patch.start()
    
    async def asyncTearDown(self):
        """Clean up after tests"""
        self.create_pipeline_patch.stop()
        await BrowserHubManager.shutdown_all()
    
    # === Basic Functionality Tests ===
    
    async def test_simple_batch_with_single_config(self):
        """Test basic batch crawling with one configuration for all URLs"""
        # Call the batch_crawl function with a list of URLs and single config
        results = await batch_crawl(
            urls=self.test_urls,
            browser_config=self.browser_config,
            crawler_config=self.crawler_config
        )
        
        # Verify we got results for all URLs
        self.assertEqual(len(results), len(self.test_urls))
        
        # Check that pipeline.crawl was called for each URL
        self.assertEqual(self.mock_pipeline.crawl.call_count, len(self.test_urls))
        
        # Check success/failure as expected
        success_count = sum(1 for r in results if r.success)
        self.assertEqual(success_count, len(self.test_urls) - 1)  # All except URL 3
        
        # Verify URLs in results match input URLs
        result_urls = sorted([r.url for r in results])
        self.assertEqual(result_urls, sorted(self.test_urls))
    
    async def test_batch_with_crawl_specs(self):
        """Test batch crawling with different configurations per URL"""
        # Create different configs for each URL
        crawl_specs = [
            {"url": url, "crawler_config": CrawlerRunConfig(screenshot=i % 2 == 0)}
            for i, url in enumerate(self.test_urls)
        ]
        
        # Call batch_crawl with crawl specs
        results = await batch_crawl(
            crawl_specs=crawl_specs,
            browser_config=self.browser_config
        )
        
        # Verify results
        self.assertEqual(len(results), len(crawl_specs))
        
        # Verify each URL was crawled with its specific config
        for i, spec in enumerate(crawl_specs):
            call_args = self.mock_pipeline.crawl.call_args_list[i]
            self.assertEqual(call_args[1]['url'], spec['url'])
            self.assertEqual(
                call_args[1]['config'].screenshot, 
                spec['crawler_config'].screenshot
            )
    
    # === Advanced Configuration Tests ===
    
    async def test_with_multiple_browser_configs(self):
        """Test using different browser configurations for different URLs"""
        # Create different browser configs
        browser_config1 = BrowserConfig(headless=True, browser_type="chromium")
        browser_config2 = BrowserConfig(headless=True, browser_type="firefox")
        
        # Create crawl specs with different browser configs
        crawl_specs = [
            {
                "url": self.test_urls[0], 
                "browser_config": browser_config1,
                "crawler_config": self.crawler_config
            },
            {
                "url": self.test_urls[1], 
                "browser_config": browser_config2,
                "crawler_config": self.crawler_config
            }
        ]
        
        # Call batch_crawl with mixed browser configs
        results = await batch_crawl(crawl_specs=crawl_specs)
        
        # Verify results
        self.assertEqual(len(results), len(crawl_specs))
        
        # Verify create_pipeline was called with different browser configs
        self.assertEqual(self.mock_create_pipeline.call_count, 2)
        
        # Check call arguments for create_pipeline
        call_args_list = self.mock_create_pipeline.call_args_list
        self.assertEqual(call_args_list[0][1]['browser_config'], browser_config1)
        self.assertEqual(call_args_list[1][1]['browser_config'], browser_config2)
    
    async def test_with_existing_browser_hub(self):
        """Test using a pre-initialized browser hub"""
        # Create a mock browser hub
        mock_hub = AsyncMock()
        
        # Call batch_crawl with browser hub
        results = await batch_crawl(
            urls=self.test_urls,
            browser_hub=mock_hub,
            crawler_config=self.crawler_config
        )
        
        # Verify create_pipeline was called with the browser hub
        self.mock_create_pipeline.assert_called_with(
            browser_hub=mock_hub,
            logger=self.logger
        )
        
        # Verify results
        self.assertEqual(len(results), len(self.test_urls))
    
    # === Error Handling and Retry Tests ===
    
    async def test_retry_on_failure(self):
        """Test retrying failed URLs up to max_tries"""
        # Modify mock to fail first 2 times for URL 3, then succeed
        attempt_counts = {url: 0 for url in self.test_urls}
        
        async def mock_crawl_with_retries(url, config=None):
            attempt_counts[url] += 1
            if url == "https://example.com/3" and attempt_counts[url] <= 2:
                return await create_mock_result(url, success=False, status_code=500)
            return await create_mock_result(url, success=True)
            
        self.mock_pipeline.crawl.side_effect = mock_crawl_with_retries
        
        # Call batch_crawl with retry configuration
        results = await batch_crawl(
            urls=self.test_urls,
            browser_config=self.browser_config,
            crawler_config=self.crawler_config,
            max_tries=3
        )
        
        # Verify all URLs succeeded after retries
        self.assertTrue(all(r.success for r in results))
        
        # Check retry count for URL 3
        self.assertEqual(attempt_counts["https://example.com/3"], 3)
        
        # Check other URLs were only tried once
        for url in self.test_urls:
            if url != "https://example.com/3":
                self.assertEqual(attempt_counts[url], 1)
    
    async def test_give_up_after_max_tries(self):
        """Test that crawling gives up after max_tries"""
        # Modify mock to always fail for URL 3
        async def mock_crawl_always_fail(url, config=None):
            if url == "https://example.com/3":
                return await create_mock_result(url, success=False, status_code=500)
            return await create_mock_result(url, success=True)
            
        self.mock_pipeline.crawl.side_effect = mock_crawl_always_fail
        
        # Call batch_crawl with retry configuration
        results = await batch_crawl(
            urls=self.test_urls,
            browser_config=self.browser_config,
            crawler_config=self.crawler_config,
            max_tries=3
        )
        
        # Find result for URL 3
        url3_result = next(r for r in results if r.url == "https://example.com/3")
        
        # Verify URL 3 still failed after max retries
        self.assertFalse(url3_result.success)
        
        # Verify retry metadata is present (assuming we add this to the result)
        self.assertEqual(url3_result.attempt_count, 3)
        self.assertTrue(hasattr(url3_result, 'retry_error_messages'))
    
    async def test_exception_during_crawl(self):
        """Test handling exceptions during crawling"""
        # Modify mock to raise exception for URL 4
        async def mock_crawl_with_exception(url, config=None):
            if url == "https://example.com/4":
                raise RuntimeError("Simulated crawler exception")
            return await create_mock_result(url, success=True)
            
        self.mock_pipeline.crawl.side_effect = mock_crawl_with_exception
        
        # Call batch_crawl
        results = await batch_crawl(
            urls=self.test_urls,
            browser_config=self.browser_config,
            crawler_config=self.crawler_config
        )
        
        # Verify we still get results for all URLs
        self.assertEqual(len(results), len(self.test_urls))
        
        # Find result for URL 4
        url4_result = next(r for r in results if r.url == "https://example.com/4")
        
        # Verify URL 4 is marked as failed
        self.assertFalse(url4_result.success)
        
        # Verify exception info is captured
        self.assertIn("Simulated crawler exception", url4_result.error_message)
    
    # === Performance and Control Tests ===
    
    async def test_concurrency_limit(self):
        """Test limiting concurrent crawls"""
        # Create a slow mock crawl function to test concurrency
        crawl_started = {url: asyncio.Event() for url in self.test_urls}
        crawl_proceed = {url: asyncio.Event() for url in self.test_urls}
        
        async def slow_mock_crawl(url, config=None):
            crawl_started[url].set()
            await crawl_proceed[url].wait()
            return await create_mock_result(url)
            
        self.mock_pipeline.crawl.side_effect = slow_mock_crawl
        
        # Start batch_crawl with concurrency limit of 2
        task = asyncio.create_task(
            batch_crawl(
                urls=self.test_urls,
                browser_config=self.browser_config,
                crawler_config=self.crawler_config,
                concurrency=2
            )
        )
        
        # Wait for first 2 crawls to start
        await asyncio.wait(
            [crawl_started[self.test_urls[0]].wait(),
             crawl_started[self.test_urls[1]].wait()],
            timeout=1
        )
        
        # Verify only 2 crawls started
        started_count = sum(1 for url in self.test_urls if crawl_started[url].is_set())
        self.assertEqual(started_count, 2)
        
        # Allow first crawl to complete
        crawl_proceed[self.test_urls[0]].set()
        
        # Wait for next crawl to start
        await asyncio.wait([crawl_started[self.test_urls[2]].wait()], timeout=1)
        
        # Now 3 total should have started (2 running, 1 completed)
        started_count = sum(1 for url in self.test_urls if crawl_started[url].is_set())
        self.assertEqual(started_count, 3)
        
        # Allow all remaining crawls to complete
        for url in self.test_urls:
            crawl_proceed[url].set()
        
        # Wait for batch_crawl to complete
        results = await task
        
        # Verify all URLs were crawled
        self.assertEqual(len(results), len(self.test_urls))
    
    async def test_cancel_batch_crawl(self):
        """Test cancelling a batch crawl operation"""
        # Create a crawl function that won't complete unless signaled
        crawl_started = {url: asyncio.Event() for url in self.test_urls}
        
        async def endless_mock_crawl(url, config=None):
            crawl_started[url].set()
            # This will wait forever unless cancelled
            await asyncio.Future()
            
        self.mock_pipeline.crawl.side_effect = endless_mock_crawl
        
        # Start batch_crawl
        task = asyncio.create_task(
            batch_crawl(
                urls=self.test_urls,
                browser_config=self.browser_config,
                crawler_config=self.crawler_config
            )
        )
        
        # Wait for at least one crawl to start
        await asyncio.wait(
            [crawl_started[self.test_urls[0]].wait()],
            timeout=1
        )
        
        # Cancel the task
        task.cancel()
        
        # Verify task was cancelled
        with self.assertRaises(asyncio.CancelledError):
            await task
    
    # === Edge Cases Tests ===
    
    async def test_empty_url_list(self):
        """Test behavior with empty URL list"""
        results = await batch_crawl(
            urls=[],
            browser_config=self.browser_config,
            crawler_config=self.crawler_config
        )
        
        # Should return empty list
        self.assertEqual(results, [])
        
        # Verify crawl wasn't called
        self.mock_pipeline.crawl.assert_not_called()
    
    async def test_mix_of_valid_and_invalid_urls(self):
        """Test with a mix of valid and invalid URLs"""
        # Include some invalid URLs
        mixed_urls = [
            "https://example.com/valid",
            "invalid-url",
            "http:/missing-slash",
            "https://example.com/valid2"
        ]
        
        # Call batch_crawl
        results = await batch_crawl(
            urls=mixed_urls,
            browser_config=self.browser_config,
            crawler_config=self.crawler_config
        )
        
        # Should have results for all URLs
        self.assertEqual(len(results), len(mixed_urls))
        
        # Check invalid URLs were marked as failed
        for result in results:
            if result.url in ["invalid-url", "http:/missing-slash"]:
                self.assertFalse(result.success)
                self.assertIn("Invalid URL", result.error_message)
            else:
                self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()