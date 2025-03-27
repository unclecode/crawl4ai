"""Browser strategies module for Crawl4AI.

This module implements the browser strategy pattern for different
browser implementations, including Playwright, CDP, and builtin browsers.
"""

import asyncio
import os
import time
import json
from typing import Optional, Tuple

from playwright.async_api import BrowserContext, Page, ProxySettings

from ...async_logger import AsyncLogger
from ...async_configs import BrowserConfig, CrawlerRunConfig
from ..utils import get_playwright, get_browser_disable_options

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
        # Add session management
        self.sessions = {}
        self.session_ttl = 1800  # 30 minutes
    
    async def start(self):
        """Start the browser instance.
        
        Returns:
            self: For method chaining
        """
        self.playwright = await get_playwright()
        browser_args = self._build_browser_args()
        
        # Launch appropriate browser type
        if self.config.browser_type == "firefox":
            self.browser = await self.playwright.firefox.launch(**browser_args)
        elif self.config.browser_type == "webkit":
            self.browser = await self.playwright.webkit.launch(**browser_args)
        else:
            self.browser = await self.playwright.chromium.launch(**browser_args)
            
        self.default_context = self.browser
        return self
    
    def _build_browser_args(self) -> dict:
        """Build browser launch arguments from config.
        
        Returns:
            dict: Browser launch arguments
        """
        args = [
            "--disable-gpu",
            "--disable-gpu-compositing",
            "--disable-software-rasterizer",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--window-position=0,0",
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--disable-blink-features=AutomationControlled",
            "--window-position=400,0",
            "--disable-renderer-backgrounding",
            "--disable-ipc-flooding-protection",
            "--force-color-profile=srgb",
            "--mute-audio",
            "--disable-background-timer-throttling",
            f"--window-size={self.config.viewport_width},{self.config.viewport_height}",
        ]

        if self.config.light_mode:
            args.extend(get_browser_disable_options())

        if self.config.text_mode:
            args.extend(
                [
                    "--blink-settings=imagesEnabled=false",
                    "--disable-remote-fonts",
                    "--disable-images",
                    "--disable-javascript",
                    "--disable-software-rasterizer",
                    "--disable-dev-shm-usage",
                ]
            )

        if self.config.extra_args:
            args.extend(self.config.extra_args)

        browser_args = {"headless": self.config.headless, "args": args}

        if self.config.chrome_channel:
            browser_args["channel"] = self.config.chrome_channel

        if self.config.accept_downloads:
            browser_args["downloads_path"] = self.config.downloads_path or os.path.join(
                os.getcwd(), "downloads"
            )
            os.makedirs(browser_args["downloads_path"], exist_ok=True)

        if self.config.proxy or self.config.proxy_config:
            proxy_settings = (
                ProxySettings(server=self.config.proxy)
                if self.config.proxy
                else ProxySettings(
                    server=self.config.proxy_config.server,
                    username=self.config.proxy_config.username,
                    password=self.config.proxy_config.password,
                )
            )
            browser_args["proxy"] = proxy_settings

        return browser_args
        
    async def create_browser_context(self, crawlerRunConfig: Optional[CrawlerRunConfig] = None) -> BrowserContext:
        """Creates and returns a new browser context with configured settings.
        
        This implementation extends the base class version to handle user_data_dir specifically.
        
        Args:
            crawlerRunConfig: Configuration object for the crawler run
            
        Returns:
            BrowserContext: Browser context object with the specified configurations
        """
        # Handle user_data_dir explicitly to ensure storage persistence
        if self.config.user_data_dir:
            # Create a storage state file path if none exists
            storage_path = os.path.join(self.config.user_data_dir, "Default", "storage_state.json")
            
            # Create the file if it doesn't exist
            if not os.path.exists(storage_path):
                os.makedirs(os.path.dirname(storage_path), exist_ok=True)
                with open(storage_path, "w") as f:
                    json.dump({}, f)
                    
            # Override storage_state with our specific path
            self.config.storage_state = storage_path
            if self.logger:
                self.logger.debug(f"Using persistent storage state at: {storage_path}", tag="BROWSER")
                
        # Now call the base class implementation which handles everything else
        return await super().create_browser_context(crawlerRunConfig)
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions based on TTL."""
        current_time = time.time()
        expired_sessions = [
            sid
            for sid, (_, _, last_used) in self.sessions.items()
            if current_time - last_used > self.session_ttl
        ]
        for sid in expired_sessions:
            asyncio.create_task(self._kill_session(sid))
    
    async def _kill_session(self, session_id: str):
        """Kill a browser session and clean up resources.
        
        Args:
            session_id: The session ID to kill
        """
        if session_id in self.sessions:
            context, page, _ = self.sessions[session_id]
            await page.close()
            del self.sessions[session_id]
    
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
        """Close the browser and clean up resources."""
        if self.config.sleep_on_close:
            await asyncio.sleep(0.5)
            
        # If we have a user_data_dir configured, ensure persistence of storage state
        if self.config.user_data_dir and self.browser and self.default_context:
            for context in self.browser.contexts:
                try:
                    await context.storage_state(path=os.path.join(self.config.user_data_dir, "Default", "storage_state.json"))
                    if self.logger:
                        self.logger.debug("Ensuring storage state is persisted before closing browser", tag="BROWSER")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(
                            message="Failed to ensure storage persistence: {error}",
                            tag="BROWSER", 
                            params={"error": str(e)}
                        )
        
        # Close all sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self._kill_session(session_id)
            
        # Close all contexts we created
        for ctx in self.contexts_by_config.values():
            try:
                await ctx.close()
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        message="Error closing context: {error}",
                        tag="ERROR",
                        params={"error": str(e)}
                    )
        self.contexts_by_config.clear()

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
