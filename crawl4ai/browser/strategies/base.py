"""Browser strategies module for Crawl4AI.

This module implements the browser strategy pattern for different
browser implementations, including Playwright, CDP, and builtin browsers.
"""

from abc import ABC, abstractmethod
import asyncio
import json
import hashlib
from typing import Optional, Tuple, List

from playwright.async_api import BrowserContext, Page

from ...async_logger import AsyncLogger
from ...async_configs import BrowserConfig, CrawlerRunConfig
from ...config import DOWNLOAD_PAGE_TIMEOUT
from ...js_snippet import load_js_script

class BaseBrowserStrategy(ABC):
    """Base class for all browser strategies.
    
    This abstract class defines the interface that all browser strategies
    must implement. It handles common functionality like context caching.
    """
    
    def __init__(self, config: BrowserConfig, logger: Optional[AsyncLogger] = None):
        """Initialize the strategy with configuration and logger.
        
        Args:
            config: Browser configuration
            logger: Logger for recording events and errors
        """
        self.config = config
        self.logger = logger
        self.browser = None
        self.default_context = None
        self.contexts_by_config = {}
        self._contexts_lock = asyncio.Lock()
        self.playwright = None
        
    @abstractmethod
    async def start(self):
        """Start the browser.
        
        Returns:
            self: For method chaining
        """
        pass
    
    @abstractmethod
    async def get_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[Page, BrowserContext]:
        """Get a page with specified configuration.
        
        Args:
            crawlerRunConfig: Crawler run configuration
            
        Returns:
            Tuple of (Page, BrowserContext)
        """
        pass
    
    async def get_pages(self, crawlerRunConfig: CrawlerRunConfig, count: int = 1) -> List[Tuple[Page, BrowserContext]]:
        """Get multiple pages with the same configuration.
        
        Args:
            crawlerRunConfig: Configuration for the pages
            count: Number of pages to create
            
        Returns:
            List of (Page, Context) tuples
        """
        pages = []
        for _ in range(count):
            page, context = await self.get_page(crawlerRunConfig)
            pages.append((page, context))
        return pages
    
    @abstractmethod
    async def close(self):
        """Close the browser and clean up resources."""
        pass
    
    def _make_config_signature(self, crawlerRunConfig: CrawlerRunConfig) -> str:
        """Create a signature hash from configuration for context caching.
        
        Args:
            crawlerRunConfig: Crawler run configuration
            
        Returns:
            str: Unique hash for this configuration
        """
        config_dict = crawlerRunConfig.__dict__.copy()
        # Exclude items that do not affect browser-level setup
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
        signature_json = json.dumps(config_dict, sort_keys=True, default=str)

        # Hash the JSON so we get a compact, unique string
        signature_hash = hashlib.sha256(signature_json.encode("utf-8")).hexdigest()
        return signature_hash
        
    async def create_browser_context(self, crawlerRunConfig: Optional[CrawlerRunConfig] = None) -> BrowserContext:
        """Creates and returns a new browser context with configured settings.
        
        Args:
            crawlerRunConfig: Configuration object for the crawler run
            
        Returns:
            BrowserContext: Browser context object with the specified configurations
        """
        if not self.browser:
            raise ValueError("Browser must be initialized before creating context")
            
        # Base settings
        user_agent = self.config.headers.get("User-Agent", self.config.user_agent) 
        viewport_settings = {
            "width": self.config.viewport_width,
            "height": self.config.viewport_height,
        }
        proxy_settings = {"server": self.config.proxy} if self.config.proxy else None
        
        # Define blocked extensions for resource optimization
        blocked_extensions = [
            # Images
            "jpg", "jpeg", "png", "gif", "webp", "svg", "ico", "bmp", "tiff", "psd",
            # Fonts
            "woff", "woff2", "ttf", "otf", "eot",
            # Media
            "mp4", "webm", "ogg", "avi", "mov", "wmv", "flv", "m4v", "mp3", "wav", "aac",
            "m4a", "opus", "flac",
            # Documents
            "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
            # Archives
            "zip", "rar", "7z", "tar", "gz",
            # Scripts and data
            "xml", "swf", "wasm",
        ]

        # Common context settings
        context_settings = {
            "user_agent": user_agent,
            "viewport": viewport_settings,
            "proxy": proxy_settings,
            "accept_downloads": self.config.accept_downloads,
            "ignore_https_errors": self.config.ignore_https_errors,
            "device_scale_factor": 1.0,
            "java_script_enabled": self.config.java_script_enabled,
        }
        
        # Apply text mode settings if enabled
        if self.config.text_mode:
            text_mode_settings = {
                "has_touch": False,
                "is_mobile": False,
                # Disable javascript in text mode
                "java_script_enabled": False
            }
            # Update context settings with text mode settings
            context_settings.update(text_mode_settings)
            if self.logger:
                self.logger.debug("Text mode enabled for browser context", tag="BROWSER")
        
        # Handle storage state properly - this is key for persistence
        if self.config.storage_state:
            context_settings["storage_state"] = self.config.storage_state
            if self.logger:
                if isinstance(self.config.storage_state, str):
                    self.logger.debug(f"Using storage state from file: {self.config.storage_state}", tag="BROWSER")
                else:
                    self.logger.debug("Using storage state from config object", tag="BROWSER")
                    
        # If user_data_dir is specified, browser persistence should be automatic
        if self.config.user_data_dir and self.logger:
            self.logger.debug(f"Using user data directory: {self.config.user_data_dir}", tag="BROWSER")
        
        # Apply crawler-specific configurations if provided
        if crawlerRunConfig:
            # Check if there is value for crawlerRunConfig.proxy_config set add that to context
            if crawlerRunConfig.proxy_config:
                proxy_settings = {
                    "server": crawlerRunConfig.proxy_config.server,
                }
                if crawlerRunConfig.proxy_config.username:
                    proxy_settings.update({
                        "username": crawlerRunConfig.proxy_config.username,
                        "password": crawlerRunConfig.proxy_config.password,
                    })
                context_settings["proxy"] = proxy_settings
                
        # Create and return the context
        try:
            # Create the context with appropriate settings
            context = await self.browser.new_context(**context_settings)
            
            # Apply text mode resource blocking if enabled
            if self.config.text_mode:
                # Create and apply route patterns for each extension
                for ext in blocked_extensions:
                    await context.route(f"**/*.{ext}", lambda route: route.abort())
                    
            return context
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating browser context: {str(e)}", tag="BROWSER")
            # Fallback to basic context creation if the advanced settings fail
            return await self.browser.new_context()
        
    async def setup_context(self, context: BrowserContext, crawlerRunConfig: Optional[CrawlerRunConfig] = None):
        """Set up a browser context with the configured options.
        
        Args:
            context: The browser context to set up
            crawlerRunConfig: Configuration object containing all browser settings
        """
        if self.config.headers:
            await context.set_extra_http_headers(self.config.headers)

        if self.config.cookies:
            await context.add_cookies(self.config.cookies)

        if self.config.accept_downloads:
            context.set_default_timeout(DOWNLOAD_PAGE_TIMEOUT)
            context.set_default_navigation_timeout(DOWNLOAD_PAGE_TIMEOUT)
            if self.config.downloads_path:
                context._impl_obj._options["accept_downloads"] = True
                context._impl_obj._options["downloads_path"] = self.config.downloads_path

        # Handle user agent and browser hints
        if self.config.user_agent:
            combined_headers = {
                "User-Agent": self.config.user_agent,
                "sec-ch-ua": self.config.browser_hint,
            }
            combined_headers.update(self.config.headers)
            await context.set_extra_http_headers(combined_headers)

        # Add default cookie
        await context.add_cookies(
            [
                {
                    "name": "cookiesEnabled",
                    "value": "true",
                    "url": crawlerRunConfig and crawlerRunConfig.url or "https://crawl4ai.com/",
                }
            ]
        )

        # Handle navigator overrides
        if crawlerRunConfig:
            if (
                crawlerRunConfig.override_navigator
                or crawlerRunConfig.simulate_user
                or crawlerRunConfig.magic
            ):
                await context.add_init_script(load_js_script("navigator_overrider"))
