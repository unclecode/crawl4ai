"""Browser strategies module for Crawl4AI.

This module implements the browser strategy pattern for different
browser implementations, including Playwright, CDP, and builtin browsers.
"""

import time
from typing import Optional, Tuple

from playwright.async_api import BrowserContext, Page

from ...async_logger import AsyncLogger
from ...async_configs import BrowserConfig, CrawlerRunConfig

from playwright_stealth import StealthConfig

from .base import BaseBrowserStrategy

stealth_config = StealthConfig(
    webdriver=True,
    chrome_app=True,
    chrome_csi=True,
    chrome_load_times=True,
    chrome_runtime=True,
    navigator_languages=True,
    navigator_plugins=True,
    navigator_permissions=True,
    webgl_vendor=True,
    outerdimensions=True,
    navigator_hardware_concurrency=True,
    media_codecs=True,
)

class PlaywrightBrowserStrategy(BaseBrowserStrategy):
    """Standard Playwright browser strategy.
    
    This strategy launches a new browser instance using Playwright
    and manages browser contexts.
    """
    
    def __init__(self, config: BrowserConfig, logger: Optional[AsyncLogger] = None):
        """Initialize the Playwright browser strategy.
        
        Args:
            config: Browser configuration
            logger: Logger for recording events and errors
        """
        super().__init__(config, logger)
        # No need to re-initialize sessions and session_ttl as they're now in the base class
    
    async def start(self):
        """Start the browser instance.
        
        Returns:
            self: For method chaining
        """
        # Call the base class start to initialize Playwright
        await super().start()
        
        # Build browser arguments using the base class method
        browser_args = self._build_browser_args()
        
        try:
            # Launch appropriate browser type
            if self.config.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(**browser_args)
            elif self.config.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(**browser_args)
            else:
                self.browser = await self.playwright.chromium.launch(**browser_args)
                
            self.default_context = self.browser
            
            if self.logger:
                self.logger.debug(f"Launched {self.config.browser_type} browser", tag="BROWSER")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to launch browser: {str(e)}", tag="BROWSER")
            raise
            
        return self
    
    async def get_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[Page, BrowserContext]:
        """Get a page for the given configuration.
        
        Args:
            crawlerRunConfig: Configuration object for the crawler run
            
        Returns:
            Tuple of (Page, BrowserContext)
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()
        
        # If a session_id is provided and we already have it, reuse that page + context
        if crawlerRunConfig.session_id and crawlerRunConfig.session_id in self.sessions:
            context, page, _ = self.sessions[crawlerRunConfig.session_id]
            # Update last-used timestamp
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
            return page, context
        
        # Otherwise, check if we have an existing context for this config
        config_signature = self._make_config_signature(crawlerRunConfig)
        
        async with self._contexts_lock:
            if config_signature in self.contexts_by_config:
                context = self.contexts_by_config[config_signature]
            else:
                # Create and setup a new context
                context = await self.create_browser_context(crawlerRunConfig)
                await self.setup_context(context, crawlerRunConfig)
                self.contexts_by_config[config_signature] = context

        # Create a new page from the chosen context
        page = await context.new_page()
        
        # If a session_id is specified, store this session so we can reuse later
        if crawlerRunConfig.session_id:
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
            
        return page, context
        
    async def close(self):
        """Close the Playwright browser and clean up resources."""
        # The base implementation already handles everything needed for Playwright
        # including storage persistence, sessions, contexts, browser and playwright
        await super().close()