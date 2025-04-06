
import time
from typing import Callable, Dict, List, Any, Optional, Awaitable

from middlewares import create_default_middleware_list, handle_error_middleware
from crawl4ai.models import CrawlResultContainer
from crawl4ai.async_crawler_strategy import AsyncCrawlerStrategy, AsyncPlaywrightCrawlerStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger


class Pipeline:
    """
    A pipeline processor that executes a series of async middleware functions.
    Each middleware function receives a context dictionary, updates it,
    and returns 1 for success or 0 for failure.
    """

    def __init__(
        self, 
        middleware: List[Callable[[Dict[str, Any]], Awaitable[int]]] = None,
        error_handler: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None,
        after_middleware_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None,
        crawler_strategy: Optional[AsyncCrawlerStrategy] = None,
        browser_config: Optional[BrowserConfig] = None,
        logger: Optional[AsyncLogger] = None,
        _initial_context: Optional[Dict[str, Any]] = None
    ):
        self.middleware = middleware or create_default_middleware_list()
        self.error_handler = error_handler or handle_error_middleware
        self.after_middleware_callback = after_middleware_callback
        self.browser_config = browser_config or BrowserConfig()
        self.logger = logger or AsyncLogger(verbose=self.browser_config.verbose)
        self.crawler_strategy = crawler_strategy or AsyncPlaywrightCrawlerStrategy(
            browser_config=self.browser_config,
            logger=self.logger
        )
        self._initial_context = _initial_context
        self._strategy_initialized = False
    
    async def _initialize_strategy__(self):
        """Initialize the crawler strategy if not already initialized"""
        if not self.crawler_strategy:
            self.crawler_strategy = AsyncPlaywrightCrawlerStrategy(
                browser_config=self.browser_config,
                logger=self.logger
            )
        
        if not self._strategy_initialized:
            await self.crawler_strategy.__aenter__()
            self._strategy_initialized = True
    
    async def _initialize_strategy(self):
        """Initialize the crawler strategy if not already initialized"""
        # With our new approach, we don't need to create the crawler strategy here
        # as it will be created on-demand in fetch_content_middleware
        
        # Just ensure browser hub is available if needed
        if hasattr(self, "_initial_context") and "browser_hub" not in self._initial_context:
            # If a browser_config was provided but no browser_hub yet, 
            # we'll let the browser_hub_middleware handle creating it
            pass
        
        # Mark as initialized to prevent repeated initialization attempts
        self._strategy_initialized = True

    async def start(self):
        """Start the crawler strategy and prepare it for use"""
        if not self._strategy_initialized:
            await self._initialize_strategy()
            self._strategy_initialized = True
        if self.crawler_strategy:
            await self.crawler_strategy.__aenter__()
            self._strategy_initialized = True
        else:
            raise ValueError("Crawler strategy is not initialized.")
    
    async def close(self):
        """Close the crawler strategy and clean up resources"""
        await self.stop()

    async def stop(self):
        """Close the crawler strategy and clean up resources"""
        if self._strategy_initialized and self.crawler_strategy:
            await self.crawler_strategy.__aexit__(None, None, None)
            self._strategy_initialized = False
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def crawl(self, url: str, config: Optional[CrawlerRunConfig] = None, **kwargs) -> CrawlResultContainer:
        """
        Crawl a URL and process it through the pipeline.
        
        Args:
            url: The URL to crawl
            config: Optional configuration for the crawl
            **kwargs: Additional arguments to pass to the middleware
            
        Returns:
            CrawlResultContainer: The result of the crawl
        """
        # Initialize strategy if needed
        await self._initialize_strategy()
        
        # Create the initial context
        context = {
            "url": url,
            "config": config or CrawlerRunConfig(),
            "browser_config": self.browser_config,
            "logger": self.logger,
            "crawler_strategy": self.crawler_strategy,
            "kwargs": kwargs
        }
        
        # Process the pipeline
        result_context = await self.process(context)
        
        # Return the final result
        return result_context.get("final_result")
    
    async def process(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process all middleware functions with the given context.
        
        Args:
            initial_context: Initial context dictionary, defaults to empty dict
            
        Returns:
            Updated context dictionary after all middleware have been processed
        """
        context = {**self._initial_context}
        if initial_context:
            context.update(initial_context)
        
        # Record pipeline start time
        context["_pipeline_start_time"] = time.perf_counter()
        
        for middleware_fn in self.middleware:
            # Get middleware name for logging
            middleware_name = getattr(middleware_fn, '__name__', str(middleware_fn))
            
            # Record start time for this middleware
            start_time = time.perf_counter()
            context[f"_timing_start_{middleware_name}"] = start_time
            
            try:
                # Execute middleware (all middleware functions are async)
                result = await middleware_fn(context)
                
                # Record completion time
                end_time = time.perf_counter()
                context[f"_timing_end_{middleware_name}"] = end_time
                context[f"_timing_duration_{middleware_name}"] = end_time - start_time
                
                # Execute after-middleware callback if provided
                if self.after_middleware_callback:
                    await self.after_middleware_callback(middleware_name, context)
                
                # Convert boolean returns to int (True->1, False->0)
                if isinstance(result, bool):
                    result = 1 if result else 0
                
                # Handle failure
                if result == 0:
                    if self.error_handler:
                        context["_error_in"] = middleware_name
                        context["_error_at"] = time.perf_counter()
                        return await self._handle_error(context)
                    else:
                        context["success"] = False
                        context["error_message"] = f"Pipeline failed at {middleware_name}"
                        break
            except Exception as e:
                # Record error information
                context["_error_in"] = middleware_name
                context["_error_at"] = time.perf_counter()
                context["_exception"] = e
                context["success"] = False
                context["error_message"] = f"Exception in {middleware_name}: {str(e)}"
                
                # Call error handler if available
                if self.error_handler:
                    return await self._handle_error(context)
                break
        
        # Record pipeline completion time
        pipeline_end_time = time.perf_counter()
        context["_pipeline_end_time"] = pipeline_end_time
        context["_pipeline_duration"] = pipeline_end_time - context["_pipeline_start_time"]
        
        # Set success to True if not already set (no failures)
        if "success" not in context:
            context["success"] = True
        
        return context
    
    async def _handle_error(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle errors by calling the error handler"""
        try:
            return await self.error_handler(context)
        except Exception as e:
            # If error handler fails, update context with this new error
            context["_error_handler_exception"] = e
            context["error_message"] = f"Error handler failed: {str(e)}"
            return context



async def create_pipeline(
    middleware_list=None, 
    error_handler=None,
    after_middleware_callback=None,
    browser_config=None,
    browser_hub_id=None,
    browser_hub_connection=None,
    browser_hub=None,
    logger=None
) -> Pipeline:
    """
    Factory function to create a pipeline with Browser-Hub integration.
    
    Args:
        middleware_list: List of middleware functions
        error_handler: Error handler middleware
        after_middleware_callback: Callback after middleware execution
        browser_config: Configuration for the browser
        browser_hub_id: ID for browser hub instance
        browser_hub_connection: Connection string for existing browser hub
        browser_hub: Existing browser hub instance to use
        logger: Logger instance
        
    Returns:
        Pipeline: Configured pipeline instance
    """
    # Use default middleware list if none provided
    middleware = middleware_list or create_default_middleware_list()
    
    # Create the pipeline
    pipeline = Pipeline(
        middleware=middleware,
        error_handler=error_handler,
        after_middleware_callback=after_middleware_callback,
        logger=logger
    )
    
    # Set browser-related attributes in the initial context
    pipeline._initial_context = {
        "browser_config": browser_config,
        "browser_hub_id": browser_hub_id,
        "browser_hub_connection": browser_hub_connection,
        "browser_hub": browser_hub,
        "logger": logger
    }
    
    return pipeline




# async def create_pipeline(
#     middleware_list: Optional[List[Callable[[Dict[str, Any]], Awaitable[int]]]] = None, 
#     error_handler: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None,
#     after_middleware_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None,
#     crawler_strategy = None,
#     browser_config = None,
#     logger = None
# ) -> Pipeline:
#     """Factory function to create a pipeline with the given middleware"""
#     return Pipeline(
#         middleware=middleware_list,
#         error_handler=error_handler,
#         after_middleware_callback=after_middleware_callback,
#         crawler_strategy=crawler_strategy,
#         browser_config=browser_config,
#         logger=logger
#     )