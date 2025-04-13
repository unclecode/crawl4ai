#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simplified test script to verify fixes for memory leaks and empty StreamingResponse
"""

import os
import sys
import time
import asyncio
import tracemalloc
import gc
import psutil
from typing import List, Dict, Any
import logging
from datetime import datetime

# Add project to path to allow running from the tests directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class MemoryTracker:
    """Simple memory usage tracker"""
    
    def __init__(self):
        self.process = psutil.Process()
        
    def get_memory_mb(self):
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / (1024 * 1024)

async def test_streaming_crawl(url: str):
    """
    Test a streaming crawl to verify memory leak and empty response fixes
    
    Args:
        url: URL to test
    """
    memory_tracker = MemoryTracker()
    
    # Force garbage collection before starting
    gc.collect()
    
    # Track memory before the test
    memory_before = memory_tracker.get_memory_mb()
    logger.info(f"Memory before test: {memory_before:.2f} MB")
    
    # Start memory tracing
    tracemalloc.start()
    
    try:
        # Configure the crawler
        browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            verbose=True,
            text_mode=True  # Disable images to save memory
        )
        
        # Configure the crawl
        crawler_config = CrawlerRunConfig(
            stream=True,  # Enable streaming mode
            cache_mode=CacheMode.BYPASS,  # Disable caching to test actual crawling
            scraping_strategy=LXMLWebScrapingStrategy(),
            word_count_threshold=100  # Lower threshold for test purposes
        )
        
        # Create a crawler and process the URL
        result_count = 0
        empty_count = 0
        data_count = 0
        start_time = time.time()
        
        logger.info(f"Starting crawl of {url}")
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Run a streaming crawl
            async for result in await crawler.arun_many(
                urls=[url],
                config=crawler_config
            ):
                result_count += 1
                
                # Check if the result is empty
                if not result or not result.html:
                    empty_count += 1
                    logger.warning("Received empty result")
                else:
                    data_count += 1
                    content_length = len(result.html or "")
                    logger.info(f"Received valid content: {content_length} bytes")
                
                # Force GC periodically
                if result_count % 3 == 0:
                    gc.collect()
        
        # Final garbage collection
        gc.collect()
        
        # Calculate statistics
        elapsed_time = time.time() - start_time
        memory_after = memory_tracker.get_memory_mb()
        memory_increase = memory_after - memory_before
        
        # Get tracemalloc statistics
        current_size, peak_size = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Log results
        logger.info("====== TEST RESULTS ======")
        logger.info(f"Total results: {result_count}")
        logger.info(f"Empty results: {empty_count}")
        logger.info(f"Valid results: {data_count}")
        logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
        logger.info(f"Memory before: {memory_before:.2f} MB")
        logger.info(f"Memory after: {memory_after:.2f} MB")
        logger.info(f"Memory increase: {memory_increase:.2f} MB ({(memory_increase / memory_before) * 100:.2f}%)")
        logger.info(f"Peak memory traced: {peak_size / (1024 * 1024):.2f} MB")
        
        # Determine if the test was successful
        success = data_count > 0 and empty_count == 0
        logger.info(f"TEST {'PASSED' if success else 'FAILED'}: "
                   f"{'No empty responses' if empty_count == 0 else 'Found empty responses'}")
        
        # Determine if there's a significant memory leak
        has_leak = memory_increase > 50 and memory_after > 200
        logger.info(f"MEMORY TEST {'FAILED' if has_leak else 'PASSED'}: "
                   f"{'Possible memory leak detected' if has_leak else 'No significant memory leak'}")
        
        return success and not has_leak
        
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        tracemalloc.stop()
        return False

async def main():
    url = "https://www.ory-berlin.de/"
    success = await test_streaming_crawl(url)
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)