"""Crawler utility class for simplified crawling operations.

This module provides a high-level utility class for crawling web pages
with support for both single and multiple URL processing.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Union, Callable

from crawl4ai.models import CrawlResultContainer, CrawlResult
from crawl4ai.pipeline.pipeline import create_pipeline
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.browser.browser_hub import BrowserHub

# Type definitions
UrlList = List[str]
UrlBatch = Tuple[List[str], CrawlerRunConfig]
UrlFullBatch = Tuple[List[str], BrowserConfig, CrawlerRunConfig]
BatchType = Union[UrlList, UrlBatch, UrlFullBatch]
ProgressCallback = Callable[[str, str, Optional[CrawlResultContainer]], None]
RetryStrategy = Callable[[str, int, Exception], Tuple[bool, float]]

class Crawler:
    """High-level utility class for crawling web pages.
    
    This class provides simplified methods for crawling both single URLs
    and batches of URLs, with parallel processing capabilities.
    """
    
    @classmethod
    async def crawl(
        cls, 
        urls: Union[str, List[str]],
        browser_config: Optional[BrowserConfig] = None,
        crawler_config: Optional[CrawlerRunConfig] = None,
        browser_hub: Optional[BrowserHub] = None,
        logger: Optional[AsyncLogger] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        use_new_loop: bool = True  # By default use a new loop for safety
    ) -> Union[CrawlResultContainer, Dict[str, CrawlResultContainer]]:
        """Crawl one or more URLs with the specified configurations.
        
        Args:
            urls: Single URL or list of URLs to crawl
            browser_config: Optional browser configuration
            crawler_config: Optional crawler run configuration
            browser_hub: Optional shared browser hub
            logger: Optional logger instance
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            
        Returns:
            For a single URL: CrawlResultContainer with crawl results
            For multiple URLs: Dict mapping URLs to their CrawlResultContainer results
        """
        # Handle single URL case
        if isinstance(urls, str):
            return await cls._crawl_single_url(
                urls,
                browser_config,
                crawler_config,
                browser_hub,
                logger,
                max_retries,
                retry_delay,
                use_new_loop
            )
        
        # Handle multiple URLs case (sequential processing)
        results = {}
        for url in urls:
            results[url] = await cls._crawl_single_url(
                url,
                browser_config,
                crawler_config,
                browser_hub,
                logger,
                max_retries,
                retry_delay,
                use_new_loop
            )
        
        return results
    
    @classmethod
    async def _crawl_single_url(
        cls,
        url: str,
        browser_config: Optional[BrowserConfig] = None,
        crawler_config: Optional[CrawlerRunConfig] = None,
        browser_hub: Optional[BrowserHub] = None,
        logger: Optional[AsyncLogger] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        use_new_loop: bool = False
    ) -> CrawlResultContainer:
        """Internal method to crawl a single URL with retry logic."""
        # Create a logger if none provided
        if logger is None:
            logger = AsyncLogger(verbose=True)
            
        # Create or use the provided crawler config
        if crawler_config is None:
            crawler_config = CrawlerRunConfig()
            
        attempts = 0
        last_error = None
        
        # For testing purposes, each crawler gets a new event loop to avoid conflicts
        # This is especially important in test suites where multiple tests run in sequence
        if use_new_loop:
            old_loop = asyncio.get_event_loop()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        while attempts <= max_retries:
            try:
                # Create a pipeline
                pipeline_args = {}
                if browser_config:
                    pipeline_args["browser_config"] = browser_config
                if browser_hub:
                    pipeline_args["browser_hub"] = browser_hub
                if logger:
                    pipeline_args["logger"] = logger
                    
                pipeline = await create_pipeline(**pipeline_args)
                
                # Perform the crawl
                result = await pipeline.crawl(url=url, config=crawler_config)
                
                # Close the pipeline if we created it (not using a shared hub)
                if not browser_hub:
                    await pipeline.close()
                    
                # Restore the original event loop if we created a new one
                if use_new_loop:
                    asyncio.set_event_loop(old_loop)
                    loop.close()
                    
                return result
                
            except Exception as e:
                last_error = e
                attempts += 1
                
                if attempts <= max_retries:
                    logger.warning(
                        message="Crawl attempt {attempt} failed for {url}: {error}. Retrying in {delay}s...",
                        tag="RETRY",
                        params={
                            "attempt": attempts,
                            "url": url,
                            "error": str(e),
                            "delay": retry_delay
                        }
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(
                        message="All {attempts} crawl attempts failed for {url}: {error}",
                        tag="FAILED",
                        params={
                            "attempts": attempts,
                            "url": url,
                            "error": str(e)
                        }
                    )
        
        # If we get here, all attempts failed
        result = CrawlResultContainer(
            CrawlResult(
                url=url,
                html="",
                success=False,
                error_message=f"All {attempts} crawl attempts failed: {str(last_error)}"
            )
        )
        
        # Restore the original event loop if we created a new one
        if use_new_loop:
            asyncio.set_event_loop(old_loop)
            loop.close()
            
        return result
    
    @classmethod
    async def parallel_crawl(
        cls,
        url_batches: Union[List[str], List[Union[UrlBatch, UrlFullBatch]]],
        browser_config: Optional[BrowserConfig] = None,
        crawler_config: Optional[CrawlerRunConfig] = None,
        browser_hub: Optional[BrowserHub] = None,
        logger: Optional[AsyncLogger] = None,
        concurrency: int = 5,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        retry_strategy: Optional[RetryStrategy] = None,
        progress_callback: Optional[ProgressCallback] = None,
        use_new_loop: bool = True  # By default use a new loop for safety
    ) -> Dict[str, CrawlResultContainer]:
        """Crawl multiple URLs in parallel with concurrency control.
        
        Args:
            url_batches: List of URLs or list of URL batches with configurations
            browser_config: Default browser configuration (used if not in batch)
            crawler_config: Default crawler configuration (used if not in batch)
            browser_hub: Optional shared browser hub for resource efficiency
            logger: Optional logger instance
            concurrency: Maximum number of concurrent crawls
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            retry_strategy: Optional custom retry strategy function
            progress_callback: Optional callback for progress reporting
            
        Returns:
            Dict mapping URLs to their CrawlResultContainer results
        """
        # Create a logger if none provided
        if logger is None:
            logger = AsyncLogger(verbose=True)
        
        # For testing purposes, each crawler gets a new event loop to avoid conflicts
        # This is especially important in test suites where multiple tests run in sequence
        if use_new_loop:
            old_loop = asyncio.get_event_loop()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # Process batches to consistent format
        processed_batches = cls._process_url_batches(
            url_batches, browser_config, crawler_config
        )
        
        # Initialize results dictionary
        results = {}
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)
        
        # Create shared browser hub if not provided
        shared_hub = browser_hub
        if not shared_hub:
            shared_hub = await BrowserHub.get_browser_manager(
                config=browser_config or BrowserConfig(),
                logger=logger,
                max_browsers_per_config=concurrency,
                max_pages_per_browser=1,
                initial_pool_size=min(concurrency, 3)  # Start with a reasonable number
            )
        
        try:
            # Create worker function for each URL
            async def process_url(url, b_config, c_config):
                async with semaphore:
                    # Report start if callback provided
                    if progress_callback:
                        await progress_callback("started", url)
                    
                    attempts = 0
                    last_error = None
                    
                    while attempts <= max_retries:
                        try:
                            # Create a pipeline using the shared hub
                            pipeline = await create_pipeline(
                                browser_config=b_config,
                                browser_hub=shared_hub,
                                logger=logger
                            )
                            
                            # Perform the crawl
                            result = await pipeline.crawl(url=url, config=c_config)
                            
                            # Report completion if callback provided
                            if progress_callback:
                                await progress_callback("completed", url, result)
                                
                            return url, result
                            
                        except Exception as e:
                            last_error = e
                            attempts += 1
                            
                            # Determine if we should retry and with what delay
                            should_retry = attempts <= max_retries
                            delay = retry_delay
                            
                            # Use custom retry strategy if provided
                            if retry_strategy and should_retry:
                                try:
                                    should_retry, delay = await retry_strategy(url, attempts, e)
                                except Exception as strategy_error:
                                    logger.error(
                                        message="Error in retry strategy: {error}",
                                        tag="RETRY",
                                        params={"error": str(strategy_error)}
                                    )
                            
                            if should_retry:
                                logger.warning(
                                    message="Crawl attempt {attempt} failed for {url}: {error}. Retrying in {delay}s...",
                                    tag="RETRY",
                                    params={
                                        "attempt": attempts,
                                        "url": url,
                                        "error": str(e),
                                        "delay": delay
                                    }
                                )
                                await asyncio.sleep(delay)
                            else:
                                logger.error(
                                    message="All {attempts} crawl attempts failed for {url}: {error}",
                                    tag="FAILED",
                                    params={
                                        "attempts": attempts,
                                        "url": url,
                                        "error": str(e)
                                    }
                                )
                                break
                    
                    # If we get here, all attempts failed
                    error_result = CrawlResultContainer(
                        CrawlResult(
                            url=url,
                            html="",
                            success=False,
                            error_message=f"All {attempts} crawl attempts failed: {str(last_error)}"
                        )
                    )
                    
                    # Report completion with error if callback provided
                    if progress_callback:
                        await progress_callback("completed", url, error_result)
                        
                    return url, error_result
            
            # Create tasks for all URLs
            tasks = []
            for urls, b_config, c_config in processed_batches:
                for url in urls:
                    tasks.append(process_url(url, b_config, c_config))
            
            # Run all tasks and collect results
            for completed_task in asyncio.as_completed(tasks):
                url, result = await completed_task
                results[url] = result
                
            return results
            
        finally:
            # Clean up the hub only if we created it
            if not browser_hub and shared_hub:
                await shared_hub.close()
                
            # Restore the original event loop if we created a new one
            if use_new_loop:
                asyncio.set_event_loop(old_loop)
                loop.close()
    
    @classmethod
    def _process_url_batches(
        cls,
        url_batches: Union[List[str], List[Union[UrlBatch, UrlFullBatch]]],
        default_browser_config: Optional[BrowserConfig],
        default_crawler_config: Optional[CrawlerRunConfig]
    ) -> List[Tuple[List[str], BrowserConfig, CrawlerRunConfig]]:
        """Process URL batches into a consistent format.
        
        Converts various input formats into a consistent list of
        (urls, browser_config, crawler_config) tuples.
        """
        processed_batches = []
        
        # Handle case where input is just a list of URLs
        if all(isinstance(item, str) for item in url_batches):
            urls = url_batches
            browser_config = default_browser_config or BrowserConfig()
            crawler_config = default_crawler_config or CrawlerRunConfig()
            processed_batches.append((urls, browser_config, crawler_config))
            return processed_batches
        
        # Process each batch
        for batch in url_batches:
            # Handle case: (urls, crawler_config)
            if len(batch) == 2 and isinstance(batch[1], CrawlerRunConfig):
                urls, c_config = batch
                b_config = default_browser_config or BrowserConfig()
                processed_batches.append((urls, b_config, c_config))
                
            # Handle case: (urls, browser_config, crawler_config)
            elif len(batch) == 3 and isinstance(batch[1], BrowserConfig) and isinstance(batch[2], CrawlerRunConfig):
                processed_batches.append(batch)
                
            # Fallback for unknown formats - assume it's just a list of URLs
            else:
                urls = batch
                browser_config = default_browser_config or BrowserConfig()
                crawler_config = default_crawler_config or CrawlerRunConfig()
                processed_batches.append((urls, browser_config, crawler_config))
                
        return processed_batches