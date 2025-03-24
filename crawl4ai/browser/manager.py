"""Browser manager module for Crawl4AI.

This module provides a central browser management class that uses the
strategy pattern internally while maintaining the existing API.
It also implements a page pooling mechanism for improved performance.
"""

import asyncio
import time
from typing import Optional, Tuple, List

from playwright.async_api import Page, BrowserContext

from ..async_logger import AsyncLogger
from ..async_configs import BrowserConfig, CrawlerRunConfig

from .strategies import (
    BaseBrowserStrategy,
    PlaywrightBrowserStrategy,
    CDPBrowserStrategy,
    BuiltinBrowserStrategy
)

# Import DockerBrowserStrategy if available
try:
    from .docker_strategy import DockerBrowserStrategy
except ImportError:
    DockerBrowserStrategy = None

class BrowserManager:
    """Main interface for browser management in Crawl4AI.
    
    This class maintains backward compatibility with the existing implementation
    while using the strategy pattern internally for different browser types.
    
    Attributes:
        config (BrowserConfig): Configuration object containing all browser settings
        logger: Logger instance for recording events and errors
        browser: The browser instance
        default_context: The default browser context
        managed_browser: The managed browser instance
        playwright: The Playwright instance
        sessions: Dictionary to store session information
        session_ttl: Session timeout in seconds
    """
    
    def __init__(self, browser_config: Optional[BrowserConfig] = None, logger: Optional[AsyncLogger] = None):
        """Initialize the BrowserManager with a browser configuration.
        
        Args:
            browser_config: Configuration object containing all browser settings
            logger: Logger instance for recording events and errors
        """
        self.config = browser_config or BrowserConfig()
        self.logger = logger
        
        # Create strategy based on configuration
        self._strategy = self._create_strategy()
        
        # Initialize state variables for compatibility with existing code
        self.browser = None
        self.default_context = None
        self.managed_browser = None
        self.playwright = None
        
        # For session management (from existing implementation)
        self.sessions = {}
        self.session_ttl = 1800  # 30 minutes
    
    def _create_strategy(self) -> BaseBrowserStrategy:
        """Create appropriate browser strategy based on configuration.
        
        Returns:
            BaseBrowserStrategy: The selected browser strategy
        """
        if self.config.browser_mode == "builtin":
            return BuiltinBrowserStrategy(self.config, self.logger)
        elif self.config.browser_mode == "docker":
            if DockerBrowserStrategy is None:
                if self.logger:
                    self.logger.error(
                        "Docker browser strategy requested but not available. "
                        "Falling back to PlaywrightBrowserStrategy.",
                        tag="BROWSER"
                    )
                return PlaywrightBrowserStrategy(self.config, self.logger)
            return DockerBrowserStrategy(self.config, self.logger)
        elif self.config.cdp_url or self.config.use_managed_browser:
            return CDPBrowserStrategy(self.config, self.logger)
        else:
            return PlaywrightBrowserStrategy(self.config, self.logger)
    
    async def start(self):
        """Start the browser instance and set up the default context.
        
        Returns:
            self: For method chaining
        """
        # Start the strategy
        await self._strategy.start()
        
        # Update legacy references
        self.browser = self._strategy.browser
        self.default_context = self._strategy.default_context
        
        # Set browser process reference (for CDP strategy)
        if hasattr(self._strategy, 'browser_process'):
            self.managed_browser = self._strategy
        
        # Set Playwright reference
        self.playwright = self._strategy.playwright
        
        # Sync sessions if needed
        if hasattr(self._strategy, 'sessions'):
            self.sessions = self._strategy.sessions
            self.session_ttl = self._strategy.session_ttl
        
        return self
    
    async def get_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[Page, BrowserContext]:
        """Get a page for the given configuration.
        
        Args:
            crawlerRunConfig: Configuration object for the crawler run
            
        Returns:
            Tuple of (Page, BrowserContext)
        """
        # Delegate to strategy
        page, context = await self._strategy.get_page(crawlerRunConfig)
        
        # Sync sessions if needed
        if hasattr(self._strategy, 'sessions'):
            self.sessions = self._strategy.sessions
        
        return page, context
        
    async def get_pages(self, crawlerRunConfig: CrawlerRunConfig, count: int = 1) -> List[Tuple[Page, BrowserContext]]:
        """Get multiple pages with the same configuration.
        
        This method efficiently creates multiple browser pages using the same configuration,
        which is useful for parallel crawling of multiple URLs.
        
        Args:
            crawlerRunConfig: Configuration for the pages
            count: Number of pages to create
            
        Returns:
            List of (Page, Context) tuples
        """
        # Delegate to strategy
        pages = await self._strategy.get_pages(crawlerRunConfig, count)
        
        # Sync sessions if needed
        if hasattr(self._strategy, 'sessions'):
            self.sessions = self._strategy.sessions
            
        return pages
    
    async def kill_session(self, session_id: str):
        """Kill a browser session and clean up resources.
        
        Args:
            session_id: The session ID to kill
        """
        # Handle kill_session via our strategy if it supports it
        if hasattr(self._strategy, '_kill_session'):
            await self._strategy._kill_session(session_id)
        elif session_id in self.sessions:
            context, page, _ = self.sessions[session_id]
            await page.close()
            # Only close context if not using CDP
            if not self.config.use_managed_browser and not self.config.cdp_url and not self.config.browser_mode == "builtin":
                await context.close()
            del self.sessions[session_id]
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions based on TTL."""
        # Use strategy's implementation if available
        if hasattr(self._strategy, '_cleanup_expired_sessions'):
            self._strategy._cleanup_expired_sessions()
            return
        
        # Otherwise use our own implementation
        current_time = time.time()
        expired_sessions = [
            sid
            for sid, (_, _, last_used) in self.sessions.items()
            if current_time - last_used > self.session_ttl
        ]
        for sid in expired_sessions:
            asyncio.create_task(self.kill_session(sid))
    
    async def close(self):
        """Close the browser and clean up resources."""
        # Delegate to strategy
        await self._strategy.close()
        
        # Reset legacy references
        self.browser = None
        self.default_context = None
        self.managed_browser = None
        self.playwright = None
        self.sessions = {}
