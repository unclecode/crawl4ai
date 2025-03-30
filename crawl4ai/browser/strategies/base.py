"""Browser strategies module for Crawl4AI.

This module implements the browser strategy pattern for different
browser implementations, including Playwright, CDP, and builtin browsers.
"""

from abc import ABC, abstractmethod
import asyncio
import json
import hashlib
import os
import time
from typing import Optional, Tuple, List

from playwright.async_api import BrowserContext, Page

from ...async_logger import AsyncLogger
from ...async_configs import BrowserConfig, CrawlerRunConfig
from ...config import DOWNLOAD_PAGE_TIMEOUT
from ...js_snippet import load_js_script
from ..utils import get_playwright


class BaseBrowserStrategy(ABC):
    """Base class for all browser strategies.
    
    This abstract class defines the interface that all browser strategies
    must implement. It handles common functionality like context caching,
    browser configuration, and session management.
    """
    
    _playwright_instance = None
    
    @classmethod
    async def get_playwright(cls):
        """Get or create a shared Playwright instance.
        
        Returns:
            Playwright: The shared Playwright instance
        """
        # For now I dont want Singleton pattern for Playwright
        if cls._playwright_instance is None or True:
            cls._playwright_instance = await get_playwright()
        return cls._playwright_instance
        
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
        
        # Context management
        self.contexts_by_config = {}  # config_signature -> context

        self._contexts_lock = asyncio.Lock()
        
        # Session management
        self.sessions = {}
        self.session_ttl = 1800  # 30 minutes default
        
        # Playwright instance
        self.playwright = None
    
    @abstractmethod
    async def start(self):
        """Start the browser.
        
        This method should be implemented by concrete strategies to initialize 
        the browser in the appropriate way (direct launch, CDP connection, etc.)
        
        Returns:
            self: For method chaining
        """
        # Base implementation gets the playwright instance
        self.playwright = await self.get_playwright()
        return self
    
    @abstractmethod
    async def _generate_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[Page, BrowserContext]:
        pass

    async def get_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[Page, BrowserContext]:
        """Get a page with specified configuration.
        
        This method should be implemented by concrete strategies to create
        or retrieve a page according to their browser management approach.
        
        Args:
            crawlerRunConfig: Crawler run configuration
            
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
        
        page, context = await self._generate_page(crawlerRunConfig)

        # If a session_id is specified, store this session so we can reuse later
        if crawlerRunConfig.session_id:
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
            
        return page, context        
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
       
    def _build_browser_args(self) -> dict:
        """Build browser launch arguments from config.
        
        Returns:
            dict: Browser launch arguments for Playwright
        """
        # Define common browser arguments that improve performance and stability
        args = [
            "--no-sandbox",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-position=0,0",
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--window-position=400,0",
            "--force-color-profile=srgb",
            "--mute-audio",
            "--disable-gpu",
            "--disable-gpu-compositing",
            "--disable-software-rasterizer",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--disable-blink-features=AutomationControlled",
            "--disable-renderer-backgrounding",
            "--disable-ipc-flooding-protection",
            "--disable-background-timer-throttling",
            f"--window-size={self.config.viewport_width},{self.config.viewport_height}",
        ]

        # Define browser disable options for light mode
        browser_disable_options = [
            "--disable-backgrounding-occluded-windows",
            "--disable-breakpad",
            "--disable-client-side-phishing-detection",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-features=TranslateUI",
            "--disable-hang-monitor",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-sync",
            "--metrics-recording-only",
            "--password-store=basic",
            "--use-mock-keychain",
        ]

        # Apply light mode settings if enabled
        if self.config.light_mode:
            args.extend(browser_disable_options)

        # Apply text mode settings if enabled (disables images, JS, etc)
        if self.config.text_mode:
            args.extend([
                "--blink-settings=imagesEnabled=false",
                "--disable-remote-fonts",
                "--disable-images",
                "--disable-javascript",
                "--disable-software-rasterizer",
                "--disable-dev-shm-usage",
            ])

        # Add any extra arguments from the config
        if self.config.extra_args:
            args.extend(self.config.extra_args)

        # Build the core browser args dictionary
        browser_args = {"headless": self.config.headless, "args": args}

        # Add chrome channel if specified
        if self.config.chrome_channel:
            browser_args["channel"] = self.config.chrome_channel

        # Configure downloads
        if self.config.accept_downloads:
            browser_args["downloads_path"] = self.config.downloads_path or os.path.join(
                os.getcwd(), "downloads"
            )
            os.makedirs(browser_args["downloads_path"], exist_ok=True)

        # Check for user data directory
        if self.config.user_data_dir:
            # Ensure the directory exists
            os.makedirs(self.config.user_data_dir, exist_ok=True)
            browser_args["user_data_dir"] = self.config.user_data_dir
        
        # Configure proxy settings
        if self.config.proxy or self.config.proxy_config:
            from playwright.async_api import ProxySettings

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
    
    def _make_config_signature(self, crawlerRunConfig: CrawlerRunConfig) -> str:
        """Create a signature hash from configuration for context caching.
        
        Converts the crawlerRunConfig into a dict, excludes ephemeral fields,
        then returns a hash of the sorted JSON. This yields a stable signature
        that identifies configurations requiring a unique browser context.
        
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
            "storage_state": self.config.storage_state,
            "ignore_https_errors": self.config.ignore_https_errors,
            "device_scale_factor": 1.0,
            "java_script_enabled": self.config.java_script_enabled,
        }
        
        # Apply text mode settings if enabled
        if self.config.text_mode:
            text_mode_settings = {
                "has_touch": False,
                "is_mobile": False,
                "java_script_enabled": False,  # Disable javascript in text mode
            }
            # Update context settings with text mode settings
            context_settings.update(text_mode_settings)
            if self.logger:
                self.logger.debug("Text mode enabled for browser context", tag="BROWSER")
        
        # Handle storage state properly - this is key for persistence
        if self.config.storage_state:
            if self.logger:
                if isinstance(self.config.storage_state, str):
                    self.logger.debug(f"Using storage state from file: {self.config.storage_state}", tag="BROWSER")
                else:
                    self.logger.debug("Using storage state from config object", tag="BROWSER")

        if self.config.user_data_dir:
            # For CDP-based browsers, storage persistence is typically handled by the user_data_dir
            # at the browser level, but we'll create a storage_state location for Playwright as well
            storage_path = os.path.join(self.config.user_data_dir, "storage_state.json")
            if not os.path.exists(storage_path):
                # Create parent directory if it doesn't exist
                os.makedirs(os.path.dirname(storage_path), exist_ok=True)
                with open(storage_path, "w") as f:
                    json.dump({}, f)
            self.config.storage_state = storage_path

            if self.logger:
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
        # Set HTTP headers
        if self.config.headers:
            await context.set_extra_http_headers(self.config.headers)

        # Add cookies
        if self.config.cookies:
            await context.add_cookies(self.config.cookies)

        # Apply storage state if provided
        if self.config.storage_state:
            await context.storage_state(path=None)

        # Configure downloads
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
        target_url = (crawlerRunConfig and crawlerRunConfig.url) or "https://crawl4ai.com/"
        await context.add_cookies(
            [
                {
                    "name": "cookiesEnabled",
                    "value": "true",
                    "url": target_url,
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
                
    async def kill_session(self, session_id: str):
        """Kill a browser session and clean up resources.

        Args:
            session_id (str): The session ID to kill.
        """
        if session_id not in self.sessions:
            return
            
        context, page, _ = self.sessions[session_id]
        
        # Close the page
        try:
            await page.close()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error closing page for session {session_id}: {str(e)}", tag="BROWSER")
        
        # Remove session from tracking
        del self.sessions[session_id]
        
        # Clean up any contexts that no longer have pages
        await self._cleanup_unused_contexts()
        
        if self.logger:
            self.logger.debug(f"Killed session: {session_id}", tag="BROWSER")

    async def _cleanup_unused_contexts(self):
        """Clean up contexts that no longer have any pages."""
        async with self._contexts_lock:
            # Get all contexts we're managing
            contexts_to_check = list(self.contexts_by_config.values())
            
            for context in contexts_to_check:
                # Check if the context has any pages left
                if not context.pages:
                    # No pages left, we can close this context
                    config_signature = next((sig for sig, ctx in self.contexts_by_config.items() 
                                           if ctx == context), None)
                    if config_signature:
                        try:
                            await context.close()
                            del self.contexts_by_config[config_signature]
                            if self.logger:
                                self.logger.debug(f"Closed unused context", tag="BROWSER")
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"Error closing unused context: {str(e)}", tag="BROWSER")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions based on TTL."""
        current_time = time.time()
        expired_sessions = [
            sid
            for sid, (_, _, last_used) in self.sessions.items()
            if current_time - last_used > self.session_ttl
        ]
        
        for sid in expired_sessions:
            if self.logger:
                self.logger.debug(f"Session expired: {sid}", tag="BROWSER")
            asyncio.create_task(self.kill_session(sid))

    async def close(self):
        """Close the browser and clean up resources.
        
        This method handles common cleanup tasks like:
        1. Persisting storage state if a user_data_dir is configured
        2. Closing all sessions
        3. Closing all browser contexts
        4. Closing the browser
        5. Stopping Playwright
        
        Child classes should override this method to add their specific cleanup logic,
        but should call super().close() to ensure common cleanup tasks are performed.
        """
        # Set a flag to prevent race conditions during cleanup
        self.shutting_down = True
        
        try:
            # Add brief delay if configured
            if self.config.sleep_on_close:
                await asyncio.sleep(0.5)
                
            # Persist storage state if using a user data directory
            if self.config.user_data_dir and self.browser:
                for context in self.browser.contexts:
                    try:
                        # Ensure the directory exists
                        storage_dir = os.path.join(self.config.user_data_dir, "Default")
                        os.makedirs(storage_dir, exist_ok=True)
                        
                        # Save storage state
                        storage_path = os.path.join(storage_dir, "storage_state.json")
                        await context.storage_state(path=storage_path)
                        
                        if self.logger:
                            self.logger.debug("Storage state persisted before closing browser", tag="BROWSER")
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(
                                message="Failed to ensure storage persistence: {error}",
                                tag="BROWSER", 
                                params={"error": str(e)}
                            )
            
            # Close all active sessions
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                await self.kill_session(session_id)
                
            # Close all cached contexts
            for ctx in self.contexts_by_config.values():
                try:
                    await ctx.close()
                except Exception as e:
                    if self.logger:
                        self.logger.error(
                            message="Error closing context: {error}",
                            tag="BROWSER",
                            params={"error": str(e)}
                        )
            self.contexts_by_config.clear()
            
            # Close the browser if it exists
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
        except Exception as e:
            if self.logger:
                self.logger.error(
                    message="Error during browser cleanup: {error}",
                    tag="BROWSER",
                    params={"error": str(e)}
                )
        finally:
            # Reset shutting down flag
            self.shutting_down = False
    
    