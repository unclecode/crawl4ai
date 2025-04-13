#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify fixes for:
1. Memory leaks during long-running crawl operations
2. Empty StreamingResponse issues
"""

import os
import sys
import time
import asyncio
import tracemalloc
import gc
import psutil
import argparse
from typing import List, Dict, Any, Optional
import logging
import json
import aiohttp
from urllib.parse import urljoin
from datetime import datetime

# Add project to path to allow running from the tests directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    MemoryAdaptiveDispatcher,
    RateLimiter,
)
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Default test URLs
DEFAULT_TEST_URLS = [
    "https://en.wikipedia.org/wiki/Web_crawler",
    "https://en.wikipedia.org/wiki/Memory_leak",
    "https://en.wikipedia.org/wiki/Streaming_media",
    "https://docs.python.org/3/library/asyncio.html",
    "https://developer.mozilla.org/en-US/docs/Web/API/Streams_API",
]

class MemoryUsageTracker:
    """Tracks memory usage during tests"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = 0
        self.peak_memory = 0
        self.current_memory = 0
        self.samples = []
        
    def start(self):
        """Start tracking memory usage"""
        tracemalloc.start()
        gc.collect()  # Force collection before starting
        self.start_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        self.peak_memory = self.start_memory
        self.samples = [self.start_memory]
        logger.info(f"Initial memory usage: {self.start_memory:.2f} MB")
        return self
        
    def sample(self):
        """Take a memory usage sample"""
        self.current_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        self.samples.append(self.current_memory)
        if self.current_memory > self.peak_memory:
            self.peak_memory = self.current_memory
        return self.current_memory
        
    def stop(self):
        """Stop tracking and return statistics"""
        self.sample()  # Take final sample
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc_peak = peak / (1024 * 1024)  # MB
        tracemalloc.stop()
        
        return {
            "start_memory_mb": self.start_memory,
            "end_memory_mb": self.current_memory,
            "peak_memory_mb": self.peak_memory,
            "tracemalloc_peak_mb": tracemalloc_peak,
            "memory_increase_mb": self.current_memory - self.start_memory,
            "memory_increase_percent": ((self.current_memory - self.start_memory) / self.start_memory) * 100,
            "has_leak": self._detect_probable_leak(),
            "samples": self.samples
        }
    
    def _detect_probable_leak(self):
        """Heuristic to detect if there's likely a memory leak"""
        # If memory usage increased by more than 50% and we're above 200MB, it might be a leak
        memory_increase = self.current_memory - self.start_memory
        return memory_increase > 50 and self.current_memory > 200


async def test_streaming_memory_usage(
    urls: List[str], 
    iterations: int = 3,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Test memory usage during streaming crawl operations
    
    Args:
        urls: List of URLs to crawl
        iterations: Number of times to repeat the crawl
        verbose: Whether to print detailed logs
        
    Returns:
        Dictionary containing memory usage statistics
    """
    memory_tracker = MemoryUsageTracker().start()
    stats = {
        "start_time": datetime.now().isoformat(),
        "iterations": iterations,
        "url_count": len(urls),
        "total_urls_processed": 0,
        "results": []
    }
    
    for i in range(iterations):
        iteration_start = time.time()
        memory_before = memory_tracker.sample()
        logger.info(f"Starting iteration {i+1}/{iterations} with {len(urls)} URLs")
        
        # Configure the crawler with optimized settings
        browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            verbose=verbose,
            ignore_https_errors=True,
            viewport_width=1280,
            viewport_height=720,
            text_mode=True  # Save memory by disabling images
        )
        
        # Using valid parameters from the CrawlerRunConfig
        crawler_config = CrawlerRunConfig(
            stream=True,  # Enable streaming mode for arun_many
            scraping_strategy=LXMLWebScrapingStrategy(),
            verbose=verbose,
            word_count_threshold=100  # Lower threshold for test purposes
        )
        
        # Use memory adaptive dispatcher with conservative settings
        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=80,
            rate_limiter=RateLimiter(
                base_delay=(1.0, 3.0),
                max_retries=3
            )
        )
        
        # Process URLs using the AsyncWebCrawler
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result_count = 0
            empty_count = 0
            
            # Force garbage collection before starting
            gc.collect()
            
            async for result in await crawler.arun_many(
                urls=urls,
                config=crawler_config,
                dispatcher=dispatcher
            ):
                result_count += 1
                
                # Check for empty results
                if not result or not result.html:
                    empty_count += 1
                
                # Force GC periodically
                if result_count % 5 == 0:
                    gc.collect()
                    
                # Sample memory occasionally
                if result_count % 10 == 0:
                    current_mem = memory_tracker.sample()
                    if verbose:
                        logger.info(f"Processed {result_count} URLs, current memory: {current_mem:.2f} MB")
        
        # Force GC after iteration
        gc.collect()
        memory_after = memory_tracker.sample()
        iteration_time = time.time() - iteration_start
        
        # Record statistics for this iteration
        iteration_stats = {
            "iteration": i + 1,
            "urls_processed": result_count,
            "empty_results": empty_count,
            "memory_before_mb": memory_before,
            "memory_after_mb": memory_after,
            "memory_delta_mb": memory_after - memory_before,
            "time_seconds": iteration_time,
        }
        
        stats["total_urls_processed"] += result_count
        stats["results"].append(iteration_stats)
        
        logger.info(
            f"Iteration {i+1} completed: processed {result_count} URLs "
            f"({empty_count} empty) in {iteration_time:.2f}s. "
            f"Memory: {memory_before:.2f} MB → {memory_after:.2f} MB "
            f"(delta: {memory_after - memory_before:.2f} MB)"
        )
        
        # Delay between iterations to let system stabilize
        await asyncio.sleep(2)
        gc.collect()
    
    # Final memory statistics
    memory_stats = memory_tracker.stop()
    stats.update({
        "end_time": datetime.now().isoformat(),
        "memory_stats": memory_stats
    })
    
    # Determine if we have memory leaks
    has_leak = memory_stats["has_leak"]
    logger.info(f"Memory leak detection: {'POSSIBLE LEAK DETECTED' if has_leak else 'No significant leak detected'}")
    logger.info(f"Final memory: {memory_stats['end_memory_mb']:.2f} MB (started at {memory_stats['start_memory_mb']:.2f} MB)")
    logger.info(f"Peak memory usage: {memory_stats['peak_memory_mb']:.2f} MB")
    
    return stats


async def test_stream_response_api(
    base_url: str = "http://localhost:8000", 
    urls: List[str] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Test the /crawl/stream endpoint to verify it doesn't return empty responses
    
    Args:
        base_url: Base URL of the API server
        urls: List of URLs to crawl
        max_retries: Maximum number of retries for API calls
        
    Returns:
        Dictionary containing API response statistics
    """
    if urls is None:
        urls = DEFAULT_TEST_URLS[:2]  # Use only 2 URLs for API testing
        
    stats = {
        "api_url": urljoin(base_url, "/crawl/stream"),
        "urls_tested": urls,
        "requests": 0,
        "success": 0,
        "errors": 0,
        "empty_responses": 0,
        "chunked_responses": 0,
        "response_times": [],
        "empty_chunks": 0,
        "total_chunks": 0,
    }
    
    logger.info(f"Testing StreamingResponse API at {stats['api_url']} with {len(urls)} URLs")
    
    # Create a session for connection pooling
    async with aiohttp.ClientSession() as session:
        for i in range(max_retries):
            start_time = time.time()
            stats["requests"] += 1
            
            try:
                async with session.post(
                    stats["api_url"],
                    json={"urls": urls},
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/x-ndjson"
                    },
                    timeout=60  # 60 second timeout
                ) as response:
                    if response.status != 200:
                        stats["errors"] += 1
                        logger.error(f"API error: {response.status} - {await response.text()}")
                        continue
                        
                    # Track if we've received any data
                    received_data = False
                    chunk_count = 0
                    empty_chunk_count = 0
                    
                    # Process streaming response
                    async for chunk in response.content.iter_any():
                        chunk_count += 1
                        
                        # Check for empty chunks
                        if not chunk or chunk == b'':
                            empty_chunk_count += 1
                            logger.warning(f"Received empty chunk ({empty_chunk_count})")
                            continue
                            
                        received_data = True
                        
                        # Log chunks for debugging
                        if chunk_count % 10 == 0:
                            logger.debug(f"Received chunk #{chunk_count}: {len(chunk)} bytes")
                    
                    # Update statistics
                    stats["total_chunks"] += chunk_count
                    stats["empty_chunks"] += empty_chunk_count
                    
                    if not received_data:
                        stats["empty_responses"] += 1
                        logger.error(f"Empty response received in attempt {i+1}/{max_retries}")
                    else:
                        stats["chunked_responses"] += 1
                        stats["success"] += 1
                        logger.info(
                            f"Success! Received {chunk_count} chunks "
                            f"({empty_chunk_count} empty) in {time.time() - start_time:.2f}s"
                        )
                    
                    stats["response_times"].append(time.time() - start_time)
                    
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"API exception: {str(e)}")
                
            # If we got a successful response, no need to retry
            if stats["success"] > 0:
                break
                
            # Wait before retry
            await asyncio.sleep(2)
    
    # Calculate statistics
    if stats["response_times"]:
        stats["avg_response_time"] = sum(stats["response_times"]) / len(stats["response_times"])
    else:
        stats["avg_response_time"] = 0
        
    stats["success_rate"] = (stats["success"] / stats["requests"]) * 100
    
    logger.info(f"API test completed: {stats['success']}/{stats['requests']} successful, {stats['empty_responses']} empty responses")
    return stats


async def main(args):
    results = {}
    
    # Run memory leak test
    if args.test_memory:
        logger.info("Starting memory leak test...")
        memory_test_urls = args.urls if args.urls else DEFAULT_TEST_URLS
        memory_results = await test_streaming_memory_usage(
            urls=memory_test_urls,
            iterations=args.iterations,
            verbose=args.verbose
        )
        results["memory_test"] = memory_results
    
    # Run API streaming test if server is available
    if args.test_api and args.api_url:
        logger.info("Starting API streaming test...")
        api_test_urls = args.urls[:2] if args.urls else DEFAULT_TEST_URLS[:2]
        api_results = await test_stream_response_api(
            base_url=args.api_url,
            urls=api_test_urls,
            max_retries=args.api_retries
        )
        results["api_test"] = api_results
    
    # Save results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    # Print summary
    logger.info("=== TEST SUMMARY ===")
    
    if "memory_test" in results:
        mem_stats = results["memory_test"]["memory_stats"]
        leak_detected = mem_stats["has_leak"]
        logger.info(
            f"Memory Test: {'❌ POSSIBLE LEAK' if leak_detected else '✓ No significant leak'} - "
            f"Started: {mem_stats['start_memory_mb']:.2f}MB, "
            f"Ended: {mem_stats['end_memory_mb']:.2f}MB, "
            f"Delta: {mem_stats['memory_increase_mb']:.2f}MB "
            f"({mem_stats['memory_increase_percent']:.2f}%)"
        )
    
    if "api_test" in results:
        api_stats = results["api_test"]
        empty_responses = api_stats["empty_responses"] > 0
        logger.info(
            f"API Test: {'❌ Empty responses detected' if empty_responses else '✓ No empty responses'} - "
            f"Success rate: {api_stats['success_rate']:.2f}%, "
            f"Empty chunks: {api_stats['empty_chunks']}/{api_stats['total_chunks']}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test memory leaks and streaming response issues in crawl4ai")
    parser.add_argument("--urls", nargs="+", help="URLs to test")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations for memory test")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL for streaming test")
    parser.add_argument("--api-retries", type=int, default=3, help="Number of retries for API test")
    parser.add_argument("--test-memory", action="store_true", default=True, help="Run memory leak test")
    parser.add_argument("--test-api", action="store_true", help="Run API streaming test")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output", help="Path to save JSON results")
    
    args = parser.parse_args()
    
    # Ensure at least one test is selected
    if not args.test_memory and not args.test_api:
        args.test_memory = True
    
    asyncio.run(main(args))