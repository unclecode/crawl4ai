"""Browser manager module for Crawl4AI.

This module provides a central browser management class that uses the
strategy pattern internally while maintaining the existing API.
It also implements browser pooling for improved performance.
"""

import asyncio
import hashlib
import json
import math
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

from playwright.async_api import Page, BrowserContext

from ..async_logger import AsyncLogger
from ..async_configs import BrowserConfig, CrawlerRunConfig

from .strategies import (
    BaseBrowserStrategy,
    PlaywrightBrowserStrategy,
    CDPBrowserStrategy,
    BuiltinBrowserStrategy,
    DockerBrowserStrategy
)

class UnavailableBehavior(Enum):
    """Behavior when no browser is available."""
    ON_DEMAND = "on_demand"  # Create new browser on demand
    PENDING = "pending"      # Wait until a browser is available
    EXCEPTION = "exception"  # Raise an exception


class BrowserManager:
    """Main interface for browser management and pooling in Crawl4AI.
    
    This class maintains backward compatibility with the existing implementation
    while using the strategy pattern internally for different browser types.
    It also implements browser pooling for improved performance.
    
    Attributes:
        config (BrowserConfig): Default configuration object for browsers
        logger (AsyncLogger): Logger instance for recording events and errors
        browser_pool (Dict): Dictionary to store browser instances by configuration
        browser_in_use (Dict): Dictionary to track which browsers are in use
        request_queues (Dict): Queues for pending requests by configuration
        unavailable_behavior (UnavailableBehavior): Behavior when no browser is available
    """
    
    def __init__(
        self, 
        browser_config: Optional[BrowserConfig] = None, 
        logger: Optional[AsyncLogger] = None,
        unavailable_behavior: UnavailableBehavior = UnavailableBehavior.EXCEPTION,
        max_browsers_per_config: int = 10,
        max_pages_per_browser: int = 5
        ):
        """Initialize the BrowserManager with a browser configuration.
        
        Args:
            browser_config: Configuration object containing all browser settings
            logger: Logger instance for recording events and errors
            unavailable_behavior: Behavior when no browser is available
            max_browsers_per_config: Maximum number of browsers per configuration
            max_pages_per_browser: Maximum number of pages per browser
        """
        self.config = browser_config or BrowserConfig()
        self.logger = logger
        self.unavailable_behavior = unavailable_behavior
        self.max_browsers_per_config = max_browsers_per_config
        self.max_pages_per_browser = max_pages_per_browser
        
        # Browser pool management
        self.browser_pool = {}            # config_hash -> list of browser strategies
        self.browser_in_use = {}          # strategy instance -> Boolean
        self.request_queues = {}          # config_hash -> asyncio.Queue()
        self._browser_locks = {}          # config_hash -> asyncio.Lock()
        self._browser_pool_lock = asyncio.Lock()  # Global lock for pool modifications
        
        # Page pool management
        self.page_pool = {}  # (browser_config_hash, crawler_config_hash) -> list of (page, context, strategy)
        self._page_pool_lock = asyncio.Lock()
            
        self.browser_page_counts = {}  # strategy instance -> current page count
        self._page_count_lock = asyncio.Lock()  # Lock for thread-safe access to page counts

        # For session management (from existing implementation)
        self.sessions = {}
        self.session_ttl = 1800  # 30 minutes

        # For legacy compatibility
        self.browser = None
        self.default_context = None
        self.managed_browser = None
        self.playwright = None
        self.strategy = None
    
    def _create_browser_config_hash(self, browser_config: BrowserConfig) -> str:
        """Create a hash of the browser configuration for browser pooling.
        
        Args:
            browser_config: Browser configuration
            
        Returns:
            str: Hash of the browser configuration
        """
        # Convert config to dictionary, excluding any callable objects
        config_dict = browser_config.__dict__.copy()
        for key in list(config_dict.keys()):
            if callable(config_dict[key]):
                del config_dict[key]
        
        # Convert to canonical JSON string
        config_json = json.dumps(config_dict, sort_keys=True, default=str)
        
        # Hash the JSON
        config_hash = hashlib.sha256(config_json.encode()).hexdigest()
        return config_hash
    
    def _create_strategy(self, browser_config: BrowserConfig) -> BaseBrowserStrategy:
        """Create appropriate browser strategy based on configuration.
        
        Args:
            browser_config: Browser configuration
            
        Returns:
            BaseBrowserStrategy: The selected browser strategy
        """
        if browser_config.browser_mode == "builtin":
            return BuiltinBrowserStrategy(browser_config, self.logger)
        elif browser_config.browser_mode == "docker":
            if DockerBrowserStrategy is None:
                if self.logger:
                    self.logger.error(
                        "Docker browser strategy requested but not available. "
                        "Falling back to PlaywrightBrowserStrategy.",
                        tag="BROWSER"
                    )
                return PlaywrightBrowserStrategy(browser_config, self.logger)
            return DockerBrowserStrategy(browser_config, self.logger)
        elif browser_config.browser_mode == "cdp" or browser_config.cdp_url or browser_config.use_managed_browser:
            return CDPBrowserStrategy(browser_config, self.logger)
        else:
            return PlaywrightBrowserStrategy(browser_config, self.logger)
    
    async def initialize_pool(
        self, 
        browser_configs: List[BrowserConfig] = None,
        browsers_per_config: int = 1,
        page_configs: Optional[List[Tuple[BrowserConfig, CrawlerRunConfig, int]]] = None
    ):
        """Initialize the browser pool with multiple browser configurations.
        
        Args:
            browser_configs: List of browser configurations to initialize
            browsers_per_config: Number of browser instances per configuration
            page_configs: Optional list of (browser_config, crawler_run_config, count) tuples
                for pre-warming pages
                
        Returns:
            self: For method chaining
        """
        if not browser_configs:
            browser_configs = [self.config]
        
        # Calculate how many browsers we'll need based on page_configs
        browsers_needed = {}
        if page_configs:
            for browser_config, _, page_count in page_configs:
                config_hash = self._create_browser_config_hash(browser_config)
                # Calculate browsers based on max_pages_per_browser
                browsers_needed_for_config = math.ceil(page_count / self.max_pages_per_browser)
                browsers_needed[config_hash] = max(
                    browsers_needed.get(config_hash, 0),
                    browsers_needed_for_config
                )
        
        # Adjust browsers_per_config if needed to ensure enough capacity
        config_browsers_needed = {}
        for browser_config in browser_configs:
            config_hash = self._create_browser_config_hash(browser_config)
            
            # Estimate browsers needed based on page requirements
            browsers_for_config = browsers_per_config
            if config_hash in browsers_needed:
                browsers_for_config = max(browsers_for_config, browsers_needed[config_hash])
            
            config_browsers_needed[config_hash] = browsers_for_config
            
            # Update max_browsers_per_config if needed
            if browsers_for_config > self.max_browsers_per_config:
                self.max_browsers_per_config = browsers_for_config
                if self.logger:
                    self.logger.info(
                        f"Increased max_browsers_per_config to {browsers_for_config} to accommodate page requirements",
                        tag="POOL"
                    )
        
        # Initialize locks and queues for each config
        async with self._browser_pool_lock:
            for browser_config in browser_configs:
                config_hash = self._create_browser_config_hash(browser_config)
                
                # Initialize lock for this config if needed
                if config_hash not in self._browser_locks:
                    self._browser_locks[config_hash] = asyncio.Lock()
                
                # Initialize queue for this config if needed
                if config_hash not in self.request_queues:
                    self.request_queues[config_hash] = asyncio.Queue()
                
                # Initialize pool for this config if needed
                if config_hash not in self.browser_pool:
                    self.browser_pool[config_hash] = []
        
        # Create browser instances for each configuration in parallel
        browser_tasks = []
        
        for browser_config in browser_configs:
            config_hash = self._create_browser_config_hash(browser_config)
            browsers_to_create = config_browsers_needed.get(
                config_hash, 
                browsers_per_config
            ) - len(self.browser_pool.get(config_hash, []))
            
            if browsers_to_create <= 0:
                continue
                
            for _ in range(browsers_to_create):
                # Create a task for each browser initialization
                task = self._create_and_add_browser(browser_config, config_hash)
                browser_tasks.append(task)
        
        # Wait for all browser initializations to complete
        if browser_tasks:
            if self.logger:
                self.logger.info(f"Initializing {len(browser_tasks)} browsers in parallel...", tag="POOL")
            await asyncio.gather(*browser_tasks)
        
        # Pre-warm pages if requested
        if page_configs:
            page_tasks = []
            for browser_config, crawler_run_config, count in page_configs:
                task = self._prewarm_pages(browser_config, crawler_run_config, count)
                page_tasks.append(task)
            
            if page_tasks:
                if self.logger:
                    self.logger.info(f"Pre-warming pages with {len(page_tasks)} configurations...", tag="POOL")
                await asyncio.gather(*page_tasks)
        
        # Update legacy references
        if self.browser_pool and next(iter(self.browser_pool.values()), []):
            strategy = next(iter(self.browser_pool.values()))[0]
            self.strategy = strategy
            self.browser = strategy.browser
            self.default_context = strategy.default_context
            self.playwright = strategy.playwright
        
        return self

    async def _create_and_add_browser(self, browser_config: BrowserConfig, config_hash: str):
        """Create and add a browser to the pool.
        
        Args:
            browser_config: Browser configuration
            config_hash: Hash of the configuration
        """
        try:
            strategy = self._create_strategy(browser_config)
            await strategy.start()
            
            async with self._browser_pool_lock:
                if config_hash not in self.browser_pool:
                    self.browser_pool[config_hash] = []
                self.browser_pool[config_hash].append(strategy)
                self.browser_in_use[strategy] = False
            
            if self.logger:
                self.logger.debug(
                    f"Added browser to pool: {browser_config.browser_type} "
                    f"({browser_config.browser_mode})", 
                    tag="POOL"
                )
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to create browser: {str(e)}", 
                    tag="POOL"
                )
            raise

    def _make_config_signature(self, crawlerRunConfig: CrawlerRunConfig) -> str:
        """Create a signature hash from crawler configuration.
        
        Args:
            crawlerRunConfig: Crawler run configuration
            
        Returns:
            str: Hash of the crawler configuration
        """
        config_dict = crawlerRunConfig.__dict__.copy()
        # Exclude items that do not affect page creation
        ephemeral_keys = [
            "session_id",
            "js_code",
            "scraping_strategy",
            "extraction_strategy",
            "chunking_strategy",
            "cache_mode",
            "content_filter",
            "semaphore_count",
            "url"
        ]
        for key in ephemeral_keys:
            if key in config_dict:
                del config_dict[key]
                
        # Convert to canonical JSON string
        config_json = json.dumps(config_dict, sort_keys=True, default=str)

        # Hash the JSON
        config_hash = hashlib.sha256(config_json.encode("utf-8")).hexdigest()
        return config_hash            

    async def _prewarm_pages(
        self, 
        browser_config: BrowserConfig, 
        crawler_run_config: CrawlerRunConfig, 
        count: int
    ):
        """Pre-warm pages for a specific configuration.
        
        Args:
            browser_config: Browser configuration
            crawler_run_config: Crawler run configuration
            count: Number of pages to pre-warm
        """
        try:
            # Create individual page tasks and run them in parallel
            browser_config_hash = self._create_browser_config_hash(browser_config)
            crawler_config_hash = self._make_config_signature(crawler_run_config)            
            async def get_single_page():
                strategy = await self.get_available_browser(browser_config)
                try:
                    page, context = await strategy.get_page(crawler_run_config)
                    # Store config hashes on the page object for later retrieval
                    setattr(page, "_browser_config_hash", browser_config_hash)
                    setattr(page, "_crawler_config_hash", crawler_config_hash)                    
                    return page, context, strategy
                except Exception as e:
                    # Release the browser back to the pool
                    await self.release_browser(strategy, browser_config)
                    raise e
                
            # Create tasks for parallel execution
            page_tasks = [get_single_page() for _ in range(count)]
            
            # Execute all page creation tasks in parallel
            pages_contexts_strategies = await asyncio.gather(*page_tasks)
            
            # Add pages to the page pool
            browser_config_hash = self._create_browser_config_hash(browser_config)
            crawler_config_hash = self._make_config_signature(crawler_run_config)
            pool_key = (browser_config_hash, crawler_config_hash)
            
            async with self._page_pool_lock:
                if pool_key not in self.page_pool:
                    self.page_pool[pool_key] = []
                
                # Add all pages to the pool
                self.page_pool[pool_key].extend(pages_contexts_strategies)
                
            if self.logger:
                self.logger.debug(
                    f"Pre-warmed {count} pages in parallel with config {crawler_run_config}", 
                    tag="POOL"
                )
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to pre-warm pages: {str(e)}", 
                    tag="POOL"
                )
            raise
    
    async def get_available_browser(
        self, 
        browser_config: Optional[BrowserConfig] = None
    ) -> BaseBrowserStrategy:
        """Get an available browser from the pool for the given configuration.
        
        Args:
            browser_config: Browser configuration to match
            
        Returns:
            BaseBrowserStrategy: An available browser strategy
            
        Raises:
            Exception: If no browser is available and behavior is EXCEPTION
        """
        browser_config = browser_config or self.config
        config_hash = self._create_browser_config_hash(browser_config)
        
        async with self._browser_locks.get(config_hash, asyncio.Lock()):
            # Check if we have browsers for this config
            if config_hash not in self.browser_pool or not self.browser_pool[config_hash]:
                if self.unavailable_behavior == UnavailableBehavior.ON_DEMAND:
                    # Create a new browser on demand
                    if self.logger:
                        self.logger.info(
                            f"1> Creating new browser on demand for config {config_hash[:8]}",
                            tag="POOL"
                        )
                    
                    # Initialize pool for this config if needed
                    async with self._browser_pool_lock:
                        if config_hash not in self.browser_pool:
                            self.browser_pool[config_hash] = []
                        
                        strategy = self._create_strategy(browser_config)
                        await strategy.start()

                        self.browser_pool[config_hash].append(strategy)
                        self.browser_in_use[strategy] = False

                elif self.unavailable_behavior == UnavailableBehavior.EXCEPTION:
                    raise Exception(f"No browsers available for configuration {config_hash[:8]}")
            
            # Check for an available browser with capacity in the pool
            for strategy in self.browser_pool[config_hash]:
                # Check if this browser has capacity for more pages
                async with self._page_count_lock:
                    current_pages = self.browser_page_counts.get(strategy, 0)

                    if current_pages < self.max_pages_per_browser:
                        # Increment the page count
                        self.browser_page_counts[strategy] = current_pages + 1

                        self.browser_in_use[strategy] = True

                        # Get browser information for better logging
                        browser_type = getattr(strategy.config, 'browser_type', 'unknown')
                        browser_mode = getattr(strategy.config, 'browser_mode', 'unknown')
                        strategy_id = id(strategy)  # Use object ID as a unique identifier

                        if self.logger:
                            self.logger.debug(
                                f"Selected browser #{strategy_id} ({browser_type}/{browser_mode}) - " 
                                f"pages: {current_pages+1}/{self.max_pages_per_browser}",
                                tag="POOL"
                            )                        

                        return strategy
            
            # All browsers are at capacity or in use
            if self.unavailable_behavior == UnavailableBehavior.ON_DEMAND:
                # Check if we've reached the maximum number of browsers
                if len(self.browser_pool[config_hash]) >= self.max_browsers_per_config:
                    if self.logger:
                        self.logger.warning(
                            f"Maximum browsers reached for config {config_hash[:8]} and all at page capacity",
                            tag="POOL"
                        )
                    if self.unavailable_behavior == UnavailableBehavior.EXCEPTION:
                        raise Exception("Maximum browsers reached and all at page capacity")
                
                # Create a new browser on demand
                if self.logger:
                    self.logger.info(
                        f"2> Creating new browser on demand for config {config_hash[:8]}",
                        tag="POOL"
                    )
                
                strategy = self._create_strategy(browser_config)
                await strategy.start()
                
                async with self._browser_pool_lock:
                    self.browser_pool[config_hash].append(strategy)
                    self.browser_in_use[strategy] = True
                
                return strategy
            
            # If we get here, either behavior is EXCEPTION or PENDING
            if self.unavailable_behavior == UnavailableBehavior.EXCEPTION:
                raise Exception(f"All browsers in use or at page capacity for configuration {config_hash[:8]}")
            
            # For PENDING behavior, set up waiting mechanism
            if config_hash not in self.request_queues:
                self.request_queues[config_hash] = asyncio.Queue()
            
            # Create a future to wait on
            future = asyncio.Future()
            await self.request_queues[config_hash].put(future)
            
            if self.logger:
                self.logger.debug(
                    f"Waiting for available browser for config {config_hash[:8]}",
                    tag="POOL"
                )
            
            # Wait for a browser to become available
            strategy = await future
            return strategy

    async def get_page(
        self, 
        crawlerRunConfig: CrawlerRunConfig,
        browser_config: Optional[BrowserConfig] = None
    ) -> Tuple[Page, BrowserContext, BaseBrowserStrategy]:
        """Get a page from the browser pool."""
        browser_config = browser_config or self.config
        
        # Check if we have a pre-warmed page available
        browser_config_hash = self._create_browser_config_hash(browser_config)
        crawler_config_hash = self._make_config_signature(crawlerRunConfig)
        pool_key = (browser_config_hash, crawler_config_hash)
        
        # Try to get a page from the pool
        async with self._page_pool_lock:
            if pool_key in self.page_pool and self.page_pool[pool_key]:
                # Get a page from the pool
                page, context, strategy = self.page_pool[pool_key].pop()
                
                # Mark browser as in use (it already is, but ensure consistency)
                self.browser_in_use[strategy] = True
                
                if self.logger:
                    self.logger.debug(
                        f"Using pre-warmed page for config {crawler_config_hash[:8]}", 
                        tag="POOL"
                    )
                    
                # Note: We don't increment page count since it was already counted when created
                
                return page, context, strategy
        
        # No pre-warmed page available, create a new one
        # get_available_browser already increments the page count
        strategy = await self.get_available_browser(browser_config)
        
        try:
            # Get a page from the browser
            page, context = await strategy.get_page(crawlerRunConfig)
            
            # Store config hashes on the page object for later retrieval
            setattr(page, "_browser_config_hash", browser_config_hash)
            setattr(page, "_crawler_config_hash", crawler_config_hash)
            
            return page, context, strategy
        except Exception as e:
            # Release the browser back to the pool and decrement the page count
            await self.release_browser(strategy, browser_config, decrement_page_count=True)
            raise e
        
    async def release_page(
        self, 
        page: Page, 
        strategy: BaseBrowserStrategy, 
        browser_config: Optional[BrowserConfig] = None,
        keep_alive: bool = True,
        return_to_pool: bool = True
    ):
        """Release a page back to the pool."""
        browser_config = browser_config or self.config

        page_url = page.url if page else None
        
        # If not keeping the page alive, close it and decrement count
        if not keep_alive:
            try:
                await page.close()
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"Error closing page: {str(e)}",
                        tag="POOL"
                    )
            # Release the browser with page count decrement
            await self.release_browser(strategy, browser_config, decrement_page_count=True)
            return
        
        # If returning to pool
        if return_to_pool:
            # Get the configuration hashes from the page object
            browser_config_hash = getattr(page, "_browser_config_hash", None)
            crawler_config_hash = getattr(page, "_crawler_config_hash", None)
            
            if browser_config_hash and crawler_config_hash:
                pool_key = (browser_config_hash, crawler_config_hash)
                
                async with self._page_pool_lock:
                    if pool_key not in self.page_pool:
                        self.page_pool[pool_key] = []
                    
                    # Add page back to the pool
                    self.page_pool[pool_key].append((page, page.context, strategy))
                    
                    if self.logger:
                        self.logger.debug(
                            f"Returned page to pool for config {crawler_config_hash[:8]}, url: {page_url}", 
                            tag="POOL"
                        )
                    
                    # Note: We don't decrement the page count here since the page is still "in use" 
                    # from the browser's perspective, just in our pool
                    return
            else:
                # If we can't identify the configuration, log a warning
                if self.logger:
                    self.logger.warning(
                        "Cannot return page to pool - missing configuration hashes", 
                        tag="POOL"
                    )
        
        # If we got here, we couldn't return to pool, so just release the browser
        await self.release_browser(strategy, browser_config, decrement_page_count=True)
    
    async def release_browser(
        self, 
        strategy: BaseBrowserStrategy, 
        browser_config: Optional[BrowserConfig] = None,
        decrement_page_count: bool = True
    ):
        """Release a browser back to the pool."""
        browser_config = browser_config or self.config
        config_hash = self._create_browser_config_hash(browser_config)
        
        # Decrement page count
        if decrement_page_count:
            async with self._page_count_lock:
                current_count = self.browser_page_counts.get(strategy, 1)
                self.browser_page_counts[strategy] = max(0, current_count - 1)
                
                if self.logger:
                    self.logger.debug(
                        f"Decremented page count for browser (now: {self.browser_page_counts[strategy]})",
                        tag="POOL"
                    )
        
        # Mark as not in use
        self.browser_in_use[strategy] = False
        
        # Process any waiting requests
        if config_hash in self.request_queues and not self.request_queues[config_hash].empty():
            future = await self.request_queues[config_hash].get()
            if not future.done():
                future.set_result(strategy)

    async def get_pages(
        self, 
        crawlerRunConfig: CrawlerRunConfig, 
        count: int = 1,
        browser_config: Optional[BrowserConfig] = None
    ) -> List[Tuple[Page, BrowserContext, BaseBrowserStrategy]]:
        """Get multiple pages from the browser pool.
        
        Args:
            crawlerRunConfig: Configuration for the crawler run
            count: Number of pages to get
            browser_config: Browser configuration to use
            
        Returns:
            List of (Page, Context, Strategy) tuples
        """
        results = []
        for _ in range(count):
            try:
                result = await self.get_page(crawlerRunConfig, browser_config)
                results.append(result)
            except Exception as e:
                # Release any pages we've already gotten
                for page, _, strategy in results:
                    await self.release_page(page, strategy, browser_config)
                raise e
        
        return results

    async def get_page_pool_status(self) -> Dict[str, Any]:
        """Get information about the page pool status.
        
        Returns:
            Dict with page pool status information
        """
        status = {
            "total_pooled_pages": 0,
            "configs": {}
        }
        
        async with self._page_pool_lock:
            for (browser_hash, crawler_hash), pages in self.page_pool.items():
                config_key = f"{browser_hash[:8]}_{crawler_hash[:8]}"
                status["configs"][config_key] = len(pages)
                status["total_pooled_pages"] += len(pages)
        
        if self.logger:
            self.logger.debug(
                f"Page pool status: {status['total_pooled_pages']} pages available",
                tag="POOL"
            )
        
        return status

    async def get_pool_status(self) -> Dict[str, Any]:
        """Get information about the browser pool status.
        
        Returns:
            Dict with pool status information
        """
        status = {
            "total_browsers": 0,
            "browsers_in_use": 0,
            "total_pages": 0,
            "configs": {}
        }
        
        for config_hash, strategies in self.browser_pool.items():
            config_pages = 0
            in_use = 0
            
            for strategy in strategies:
                is_in_use = self.browser_in_use.get(strategy, False)
                if is_in_use:
                    in_use += 1
                
                # Get page count for this browser
                try:
                    page_count = len(await strategy.get_opened_pages())
                    config_pages += page_count
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error getting page count: {str(e)}", tag="POOL")
            
            config_status = {
                "total_browsers": len(strategies),
                "browsers_in_use": in_use,
                "pages_open": config_pages,
                "waiting_requests": self.request_queues.get(config_hash, asyncio.Queue()).qsize(),
                "max_capacity": len(strategies) * self.max_pages_per_browser,
                "utilization_pct": round((config_pages / (len(strategies) * self.max_pages_per_browser)) * 100, 1) 
                    if strategies else 0
            }
            
            status["configs"][config_hash] = config_status
            status["total_browsers"] += config_status["total_browsers"]
            status["browsers_in_use"] += config_status["browsers_in_use"]
            status["total_pages"] += config_pages
        
        # Add overall utilization
        if status["total_browsers"] > 0:
            max_capacity = status["total_browsers"] * self.max_pages_per_browser
            status["overall_utilization_pct"] = round((status["total_pages"] / max_capacity) * 100, 1)
        else:
            status["overall_utilization_pct"] = 0
        
        return status


    async def start(self):
        """Start at least one browser instance in the pool.
        
        This method is kept for backward compatibility.
        
        Returns:
            self: For method chaining
        """
        await self.initialize_pool([self.config], 1)
        return self
        
    async def kill_session(self, session_id: str):
        """Kill a browser session and clean up resources.
        
        Delegated to the strategy. This method is kept for backward compatibility.
        
        Args:
            session_id: The session ID to kill
        """
        if not self.strategy:
            return
            
        await self.strategy.kill_session(session_id)
        
        # Sync sessions
        if hasattr(self.strategy, 'sessions'):
            self.sessions = self.strategy.sessions
    
    async def close(self):
        """Close all browsers in the pool and clean up resources."""
        # Close all browsers in the pool
        for strategies in self.browser_pool.values():
            for strategy in strategies:
                try:
                    await strategy.close()
                except Exception as e:
                    if self.logger:
                        self.logger.error(
                            f"Error closing browser: {str(e)}",
                            tag="POOL"
                        )
        
        # Clear pool data
        self.browser_pool = {}
        self.browser_in_use = {}
        
        # Reset legacy references
        self.browser = None
        self.default_context = None
        self.managed_browser = None
        self.playwright = None
        self.strategy = None
        self.sessions = {}


async def create_browser_manager(
    browser_config: Optional[BrowserConfig] = None,
    logger: Optional[AsyncLogger] = None,
    unavailable_behavior: UnavailableBehavior = UnavailableBehavior.EXCEPTION,
    max_browsers_per_config: int = 10,
    initial_pool_size: int = 1,
    page_configs: Optional[List[Tuple[BrowserConfig, CrawlerRunConfig, int]]] = None
) -> BrowserManager:
    """Factory function to create and initialize a BrowserManager.
    
    Args:
        browser_config: Configuration for the browsers
        logger: Logger for recording events
        unavailable_behavior: Behavior when no browser is available
        max_browsers_per_config: Maximum browsers per configuration
        initial_pool_size: Initial number of browsers per configuration
        page_configs: Optional configurations for pre-warming pages
        
    Returns:
        Initialized BrowserManager
    """
    manager = BrowserManager(
        browser_config=browser_config,
        logger=logger,
        unavailable_behavior=unavailable_behavior,
        max_browsers_per_config=max_browsers_per_config
    )
    
    await manager.initialize_pool(
        [browser_config] if browser_config else None,
        initial_pool_size,
        page_configs
    )
    
    return manager





