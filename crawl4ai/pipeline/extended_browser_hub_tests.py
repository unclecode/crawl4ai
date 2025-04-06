# extended_browser_hub_tests.py

import asyncio

from crawl4ai.browser.browser_hub import BrowserHub
from pipeline import create_pipeline
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.cache_context import CacheMode

# Common test URLs
TEST_URLS = [
    "https://example.com",
    "https://example.com/page1",
    "https://httpbin.org/html",
    "https://httpbin.org/headers",
    "https://httpbin.org/ip",
    "https://httpstat.us/200"
]

class TestResults:
    """Simple container for test results"""
    def __init__(self, name: str):
        self.name = name
        self.results = []
        self.start_time = None
        self.end_time = None
        self.errors = []
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0
        return sum(1 for r in self.results if r.success) / len(self.results) * 100

    def log_summary(self, logger: AsyncLogger):
        logger.info(f"=== Test: {self.name} ===", tag="SUMMARY")
        logger.info(
            message="Duration: {duration:.2f}s, Success rate: {success_rate:.1f}%, Results: {count}",
            tag="SUMMARY",
            params={
                "duration": self.duration,
                "success_rate": self.success_rate,
                "count": len(self.results)
            }
        )
        
        if self.errors:
            logger.error(
                message="Errors ({count}): {errors}",
                tag="SUMMARY",
                params={
                    "count": len(self.errors),
                    "errors": "; ".join(str(e) for e in self.errors)
                }
            )

# ======== TEST SCENARIO 1: Simple default configuration ========
async def test_default_configuration():
    """
    Test Scenario 1: Simple default configuration
    
    This tests the basic case where the user does not provide any specific
    browser configuration, relying on default auto-setup.
    """
    logger = AsyncLogger(verbose=True)
    results = TestResults("Default Configuration")
    
    try:
        # Create pipeline with no browser config
        pipeline = await create_pipeline(logger=logger)
        
        # Start timing
        results.start_time = asyncio.get_event_loop().time()
        
        # Create basic crawler config
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_until="domcontentloaded"
        )
        
        # Process each URL sequentially
        for url in TEST_URLS:
            try:
                logger.info(f"Crawling {url} with default configuration", tag="TEST")
                result = await pipeline.crawl(url=url, config=crawler_config)
                results.results.append(result)
                
                logger.success(
                    message="Result: url={url}, success={success}, content_length={length}",
                    tag="TEST",
                    params={
                        "url": url,
                        "success": result.success,
                        "length": len(result.html) if result.html else 0
                    }
                )
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}", tag="TEST")
                results.errors.append(e)
        
        # End timing
        results.end_time = asyncio.get_event_loop().time()
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", tag="TEST")
        results.errors.append(e)
    
    # Log summary
    results.log_summary(logger)
    
    return results

# ======== TEST SCENARIO 2: Detailed custom configuration ========
async def test_custom_configuration():
    """
    Test Scenario 2: Detailed custom configuration
    
    This tests the case where the user provides detailed browser configuration
    to customize the browser behavior.
    """
    logger = AsyncLogger(verbose=True)
    results = TestResults("Custom Configuration")
    
    try:
        # Create custom browser config
        browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            light_mode=True,
            ignore_https_errors=True,
            extra_args=["--disable-extensions"]
        )
        
        # Create custom crawler config
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_until="networkidle",
            page_timeout=30000,
            screenshot=True,
            pdf=False,
            screenshot_wait_for=0.5,
            wait_for_images=True,
            scan_full_page=True,
            scroll_delay=0.2,
            process_iframes=True,
            remove_overlay_elements=True
        )
        
        # Create pipeline with custom configuration
        pipeline = await create_pipeline(
            browser_config=browser_config,
            logger=logger
        )
        
        # Start timing
        results.start_time = asyncio.get_event_loop().time()
        
        # Process each URL sequentially
        for url in TEST_URLS:
            try:
                logger.info(f"Crawling {url} with custom configuration", tag="TEST")
                result = await pipeline.crawl(url=url, config=crawler_config)
                results.results.append(result)
                
                has_screenshot = result.screenshot is not None
                
                logger.success(
                    message="Result: url={url}, success={success}, screenshot={screenshot}, content_length={length}",
                    tag="TEST",
                    params={
                        "url": url,
                        "success": result.success,
                        "screenshot": has_screenshot,
                        "length": len(result.html) if result.html else 0
                    }
                )
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}", tag="TEST")
                results.errors.append(e)
        
        # End timing
        results.end_time = asyncio.get_event_loop().time()
        
        # Get browser hub status from context
        try:
            # Run a dummy crawl to get the context with browser hub
            context = await pipeline.process({"url": "about:blank", "config": crawler_config})
            browser_hub = context.get("browser_hub")
            if browser_hub:
                status = await browser_hub.get_pool_status()
                logger.info(
                    message="Browser hub status: {status}",
                    tag="TEST",
                    params={"status": status}
                )
        except Exception as e:
            logger.error(f"Failed to get browser hub status: {str(e)}", tag="TEST")
    
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", tag="TEST")
        results.errors.append(e)
    
    # Log summary
    results.log_summary(logger)
    
    return results

# ======== TEST SCENARIO 3: Using pre-initialized browser hub ========
async def test_preinitalized_browser_hub():
    """
    Test Scenario 3: Using pre-initialized browser hub
    
    This tests the case where a browser hub is initialized separately
    and then passed to the pipeline.
    """
    logger = AsyncLogger(verbose=True)
    results = TestResults("Pre-initialized Browser Hub")
    
    browser_hub = None
    try:
        # Create and initialize browser hub separately
        logger.info("Initializing browser hub separately", tag="TEST")
        
        browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            verbose=True
        )
        
        browser_hub = await BrowserHub.get_browser_manager(
            config=browser_config,
            hub_id="test_preinitalized",
            logger=logger,
            max_browsers_per_config=2,
            max_pages_per_browser=3,
            initial_pool_size=2
        )
        
        # Display initial status
        status = await browser_hub.get_pool_status()
        logger.info(
            message="Initial browser hub status: {status}",
            tag="TEST",
            params={"status": status}
        )
        
        # Create pipeline with pre-initialized browser hub
        pipeline = await create_pipeline(
            browser_hub=browser_hub,
            logger=logger
        )
        
        # Create crawler config
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_until="networkidle",
            screenshot=True
        )
        
        # Start timing
        results.start_time = asyncio.get_event_loop().time()
        
        # Process URLs in parallel
        async def crawl_url(url):
            try:
                logger.info(f"Crawling {url} with pre-initialized hub", tag="TEST")
                result = await pipeline.crawl(url=url, config=crawler_config)
                logger.success(f"Completed crawl of {url}", tag="TEST")
                return result
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}", tag="TEST")
                results.errors.append(e)
                return None
        
        # Create tasks for all URLs
        tasks = [crawl_url(url) for url in TEST_URLS]
        
        # Execute all tasks in parallel and collect results
        all_results = await asyncio.gather(*tasks)
        results.results = [r for r in all_results if r is not None]
        
        # End timing
        results.end_time = asyncio.get_event_loop().time()
        
        # Display final status
        status = await browser_hub.get_pool_status()
        logger.info(
            message="Final browser hub status: {status}",
            tag="TEST",
            params={"status": status}
        )
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", tag="TEST")
        results.errors.append(e)
    
    # Log summary
    results.log_summary(logger)
    
    return results, browser_hub

# ======== TEST SCENARIO 4: Parallel pipelines sharing browser hub ========
async def test_parallel_pipelines():
    """
    Test Scenario 4: Multiple parallel pipelines sharing browser hub
    
    This tests the case where multiple pipelines share the same browser hub,
    demonstrating resource sharing and parallel operation.
    """
    logger = AsyncLogger(verbose=True)
    results = TestResults("Parallel Pipelines")
    
    # We'll reuse the browser hub from the previous test
    _, browser_hub = await test_preinitalized_browser_hub()
    
    try:
        # Create 3 pipelines that all share the same browser hub
        pipelines = []
        for i in range(3):
            pipeline = await create_pipeline(
                browser_hub=browser_hub,
                logger=logger
            )
            pipelines.append(pipeline)
        
        logger.info(f"Created {len(pipelines)} pipelines sharing the same browser hub", tag="TEST")
        
        # Create crawler configs with different settings
        configs = [
            CrawlerRunConfig(wait_until="domcontentloaded", screenshot=False),
            CrawlerRunConfig(wait_until="networkidle", screenshot=True),
            CrawlerRunConfig(wait_until="load", scan_full_page=True)
        ]
        
        # Start timing
        results.start_time = asyncio.get_event_loop().time()
        
        # Function to process URLs with a specific pipeline
        async def process_with_pipeline(pipeline_idx, urls):
            pipeline_results = []
            for url in urls:
                try:
                    logger.info(f"Pipeline {pipeline_idx} crawling {url}", tag="TEST")
                    result = await pipelines[pipeline_idx].crawl(
                        url=url, 
                        config=configs[pipeline_idx]
                    )
                    pipeline_results.append(result)
                    logger.success(
                        message="Pipeline {idx} completed: url={url}, success={success}",
                        tag="TEST",
                        params={
                            "idx": pipeline_idx,
                            "url": url,
                            "success": result.success
                        }
                    )
                except Exception as e:
                    logger.error(
                        message="Pipeline {idx} error: {error}",
                        tag="TEST",
                        params={
                            "idx": pipeline_idx,
                            "error": str(e)
                        }
                    )
                    results.errors.append(e)
            return pipeline_results
        
        # Distribute URLs among pipelines
        pipeline_urls = [
            TEST_URLS[:2],
            TEST_URLS[2:4],
            TEST_URLS[4:5] * 2  # Duplicate the last URL to have 2 for pipeline 3
        ]
        
        # Execute all pipelines in parallel
        tasks = [
            process_with_pipeline(i, urls) 
            for i, urls in enumerate(pipeline_urls)
        ]
        
        pipeline_results = await asyncio.gather(*tasks)
        
        # Flatten results
        for res_list in pipeline_results:
            results.results.extend(res_list)
        
        # End timing
        results.end_time = asyncio.get_event_loop().time()
        
        # Display browser hub status
        status = await browser_hub.get_pool_status()
        logger.info(
            message="Browser hub status after parallel pipelines: {status}",
            tag="TEST",
            params={"status": status}
        )
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", tag="TEST")
        results.errors.append(e)
    
    # Log summary
    results.log_summary(logger)
    
    return results

# ======== TEST SCENARIO 5: Browser hub with connection string ========
async def test_connection_string():
    """
    Test Scenario 5: Browser hub with connection string
    
    This tests the case where a browser hub is initialized from a connection string,
    simulating connecting to a running browser hub service.
    """
    logger = AsyncLogger(verbose=True)
    results = TestResults("Connection String")
    
    try:
        # Create pipeline with connection string
        # Note: In a real implementation, this would connect to an existing service
        # For this test, we're using a simulated connection
        connection_string = "localhost:9222"  # Simulated connection string
        
        pipeline = await create_pipeline(
            browser_hub_connection=connection_string,
            logger=logger
        )
        
        # Create crawler config
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_until="networkidle"
        )
        
        # Start timing
        results.start_time = asyncio.get_event_loop().time()
        
        # Test with a single URL
        url = TEST_URLS[0]
        try:
            logger.info(f"Crawling {url} with connection string hub", tag="TEST")
            result = await pipeline.crawl(url=url, config=crawler_config)
            results.results.append(result)
            
            logger.success(
                message="Result: url={url}, success={success}, content_length={length}",
                tag="TEST",
                params={
                    "url": url,
                    "success": result.success,
                    "length": len(result.html) if result.html else 0
                }
            )
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}", tag="TEST")
            results.errors.append(e)
        
        # End timing
        results.end_time = asyncio.get_event_loop().time()
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", tag="TEST")
        results.errors.append(e)
    
    # Log summary
    results.log_summary(logger)
    
    return results

# ======== RUN ALL TESTS ========
async def run_all_tests():
    """Run all test scenarios"""
    logger = AsyncLogger(verbose=True)
    logger.info("=== STARTING BROWSER HUB TESTS ===", tag="MAIN")
    
    try:
        # Run each test scenario
        await test_default_configuration()
        # await test_custom_configuration()
        # await test_preinitalized_browser_hub()
        # await test_parallel_pipelines()
        # await test_connection_string()
        
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}", tag="MAIN")
    finally:
        # Clean up all browser hubs
        logger.info("Shutting down all browser hubs...", tag="MAIN")
        await BrowserHub.shutdown_all()
        logger.success("All tests completed", tag="MAIN")

if __name__ == "__main__":
    asyncio.run(run_all_tests())