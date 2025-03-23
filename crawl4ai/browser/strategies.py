"""Browser strategies module for Crawl4AI.

This module implements the browser strategy pattern for different
browser implementations, including Playwright, CDP, and builtin browsers.
"""

from abc import ABC, abstractmethod
import asyncio
import os
import time
import json
import hashlib
import subprocess
import shutil
import signal
from typing import Optional, Dict, Tuple, List, Any

from playwright.async_api import BrowserContext, Page, ProxySettings

from ..async_logger import AsyncLogger
from ..async_configs import BrowserConfig, CrawlerRunConfig
from ..config import DOWNLOAD_PAGE_TIMEOUT
from ..js_snippet import load_js_script
from ..utils import get_home_folder
from .utils import get_playwright, get_browser_executable, get_browser_disable_options, create_temp_directory, is_windows, is_browser_running

from playwright_stealth import StealthConfig

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

class CDPBrowserStrategy(BaseBrowserStrategy):
    """CDP-based browser strategy.
    
    This strategy connects to an existing browser using CDP protocol or
    launches and connects to a browser using CDP.
    """
    
    def __init__(self, config: BrowserConfig, logger: Optional[AsyncLogger] = None):
        """Initialize the CDP browser strategy.
        
        Args:
            config: Browser configuration
            logger: Logger for recording events and errors
        """
        super().__init__(config, logger)
        self.sessions = {}
        self.session_ttl = 1800  # 30 minutes
        self.browser_process = None
        self.temp_dir = None
        self.shutting_down = False
        
    async def start(self):
        """Start or connect to the browser using CDP.
        
        Returns:
            self: For method chaining
        """
        self.playwright = await get_playwright()
        
        # Get or create CDP URL
        cdp_url = await self._get_or_create_cdp_url()
        
        # Connect to the browser using CDP
        self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
        
        # Get or create default context
        contexts = self.browser.contexts
        if contexts:
            self.default_context = contexts[0]
        else:
            self.default_context = await self.create_browser_context()
        
        await self.setup_context(self.default_context)
        return self
    
    async def _get_or_create_cdp_url(self) -> str:
        """Get existing CDP URL or launch a browser and return its CDP URL.
        
        Returns:
            str: CDP URL for connecting to the browser
        """
        # If CDP URL is provided, just return it
        if self.config.cdp_url:
            return self.config.cdp_url

        # Create temp dir if needed
        if not self.config.user_data_dir:
            self.temp_dir = create_temp_directory()
            user_data_dir = self.temp_dir
        else:
            user_data_dir = self.config.user_data_dir

        # Get browser args based on OS and browser type
        args = await self._get_browser_args(user_data_dir)

        # Start browser process
        try:
            # Use DETACHED_PROCESS flag on Windows to fully detach the process
            # On Unix, we'll use preexec_fn=os.setpgrp to start the process in a new process group
            if is_windows():
                self.browser_process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.browser_process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setpgrp  # Start in a new process group
                )
                
            # Monitor for a short time to make sure it starts properly
            await asyncio.sleep(0.5)  # Give browser time to start
            await self._initial_startup_check()
            await asyncio.sleep(2)  # Give browser more time to start
            return f"http://localhost:{self.config.debugging_port}"
        except Exception as e:
            await self._cleanup_process()
            raise Exception(f"Failed to start browser: {e}")
    
    async def _initial_startup_check(self):
        """Perform a quick check to make sure the browser started successfully."""
        if not self.browser_process:
            return
            
        # Check that process started without immediate termination
        await asyncio.sleep(0.5)
        if self.browser_process.poll() is not None:
            # Process already terminated
            stdout, stderr = b"", b""
            try:
                stdout, stderr = self.browser_process.communicate(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
                
            if self.logger:
                self.logger.error(
                    message="Browser process terminated during startup | Code: {code} | STDOUT: {stdout} | STDERR: {stderr}",
                    tag="ERROR",
                    params={
                        "code": self.browser_process.returncode,
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else "",
                    },
                )
    
    async def _get_browser_args(self, user_data_dir: str) -> List[str]:
        """Returns browser-specific command line arguments.
        
        Args:
            user_data_dir: Path to user data directory
            
        Returns:
            List of command-line arguments for the browser
        """
        browser_path = await get_browser_executable(self.config.browser_type)
        base_args = [browser_path]

        if self.config.browser_type == "chromium":
            args = [
                f"--remote-debugging-port={self.config.debugging_port}",
                f"--user-data-dir={user_data_dir}",
            ]
            if self.config.headless:
                args.append("--headless=new")
        elif self.config.browser_type == "firefox":
            args = [
                "--remote-debugging-port",
                str(self.config.debugging_port),
                "--profile",
                user_data_dir,
            ]
            if self.config.headless:
                args.append("--headless")
        else:
            raise NotImplementedError(f"Browser type {self.config.browser_type} not supported")

        return base_args + args

    async def _cleanup_process(self):
        """Cleanup browser process and temporary directory."""
        # Set shutting_down flag BEFORE any termination actions
        self.shutting_down = True

        if self.browser_process:
            try:
                # Only terminate if we have proper control over the process
                if not self.browser_process.poll():
                    # Process is still running
                    self.browser_process.terminate()
                    # Wait for process to end gracefully
                    for _ in range(10):  # 10 attempts, 100ms each
                        if self.browser_process.poll() is not None:
                            break
                        await asyncio.sleep(0.1)

                    # Force kill if still running
                    if self.browser_process.poll() is None:
                        if is_windows():
                            # On Windows we might need taskkill for detached processes
                            try:
                                subprocess.run(["taskkill", "/F", "/PID", str(self.browser_process.pid)])
                            except Exception:
                                self.browser_process.kill()
                        else:
                            self.browser_process.kill()
                        await asyncio.sleep(0.1)  # Brief wait for kill to take effect

            except Exception as e:
                if self.logger:
                    self.logger.error(
                        message="Error terminating browser: {error}",
                        tag="ERROR", 
                        params={"error": str(e)},
                    )

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        message="Error removing temporary directory: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )
    
    async def create_browser_context(self, crawlerRunConfig: Optional[CrawlerRunConfig] = None) -> BrowserContext:
        """Create a new browser context.
        
        Uses the base class implementation which handles all configurations.
        
        Args:
            crawlerRunConfig: Configuration object for the crawler run
            
        Returns:
            BrowserContext: Browser context object
        """
        # Handle user_data_dir for CDP browsers
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
            
        # Use the base class implementation
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
        self._cleanup_expired_sessions()
        
        # If a session_id is provided and we already have it, reuse that page + context
        if crawlerRunConfig.session_id and crawlerRunConfig.session_id in self.sessions:
            context, page, _ = self.sessions[crawlerRunConfig.session_id]
            # Update last-used timestamp
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
            return page, context
        
        # For CDP, we typically use the shared default_context
        context = self.default_context
        pages = context.pages
        page = next((p for p in pages if p.url == crawlerRunConfig.url), None)
        if not page:
            page = await context.new_page()
        
        # If a session_id is specified, store this session so we can reuse later
        if crawlerRunConfig.session_id:
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
        
        return page, context
    
    async def close(self):
        """Close the browser and clean up resources."""
        # Skip cleanup if using external CDP URL and not launched by us
        if self.config.cdp_url and not self.browser_process:
            return
        
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

        # Close browser
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        # Clean up managed browser if we created it
        if self.browser_process:
            await asyncio.sleep(0.5)
            await self._cleanup_process()
            self.browser_process = None
        
        # Close temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        message="Error removing temporary directory: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )
        
        # Stop playwright
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

class BuiltinBrowserStrategy(CDPBrowserStrategy):
    """Built-in browser strategy.
    
    This strategy extends the CDP strategy to use the built-in browser.
    """
    
    def __init__(self, config: BrowserConfig, logger: Optional[AsyncLogger] = None):
        """Initialize the built-in browser strategy.
        
        Args:
            config: Browser configuration
            logger: Logger for recording events and errors
        """
        super().__init__(config, logger)
        self.builtin_browser_dir = os.path.join(get_home_folder(), "builtin-browser") if not self.config.user_data_dir else self.config.user_data_dir
        self.builtin_config_file = os.path.join(self.builtin_browser_dir, "browser_config.json")

        # Raise error if user data dir is already engaged
        if self._check_user_dir_is_engaged(self.builtin_browser_dir):
            raise Exception(f"User data directory {self.builtin_browser_dir} is already engaged by another browser instance.")

        os.makedirs(self.builtin_browser_dir, exist_ok=True)
    
    def _check_user_dir_is_engaged(self, user_data_dir: str) -> bool:
        """Check if the user data directory is already in use.
        
        Returns:
            bool: True if the directory is engaged, False otherwise
        """
        # Load browser config file, then iterate in port_map values, check "user_data_dir" key if it matches
        # the current user data directory
        if os.path.exists(self.builtin_config_file):
            try:
                with open(self.builtin_config_file, 'r') as f:
                    browser_info_dict = json.load(f)
                
                # Check if user data dir is already engaged
                for port_str, browser_info in browser_info_dict.get("port_map", {}).items():
                    if browser_info.get("user_data_dir") == user_data_dir:
                        return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error reading built-in browser config: {str(e)}", tag="BUILTIN")
        return False

    async def start(self):
        """Start or connect to the built-in browser.
        
        Returns:
            self: For method chaining
        """
        # Check for existing built-in browser (get_browser_info already checks if running)
        browser_info = self.get_browser_info()
        if browser_info:
            if self.logger:
                self.logger.info(f"Using existing built-in browser at {browser_info.get('cdp_url')}", tag="BROWSER")
            self.config.cdp_url = browser_info.get('cdp_url')
        else:
            if self.logger:
                self.logger.info("Built-in browser not found, launching new instance...", tag="BROWSER")
            cdp_url = await self.launch_builtin_browser(
                browser_type=self.config.browser_type,
                debugging_port=self.config.debugging_port,
                headless=self.config.headless,
            )
            if not cdp_url:
                if self.logger:
                    self.logger.warning("Failed to launch built-in browser, falling back to regular CDP strategy", tag="BROWSER")
                return await super().start()
            self.config.cdp_url = cdp_url
        
        # Call parent class implementation with updated CDP URL
        return await super().start()
    
    @classmethod
    def get_builtin_browser_info(cls, debugging_port: int, config_file: str, logger: Optional[AsyncLogger] = None) -> Optional[Dict[str, Any]]:
        """Get information about the built-in browser for a specific debugging port.
        
        Args:
            debugging_port: The debugging port to look for
            config_file: Path to the config file
            logger: Optional logger for recording events
            
        Returns:
            dict: Browser information or None if no running browser is configured for this port
        """
        if not os.path.exists(config_file):
            return None
            
        try:
            with open(config_file, 'r') as f:
                browser_info_dict = json.load(f)
            
            # Get browser info from port map
            if isinstance(browser_info_dict, dict) and "port_map" in browser_info_dict:
                port_str = str(debugging_port)
                if port_str in browser_info_dict["port_map"]:
                    browser_info = browser_info_dict["port_map"][port_str]
                    
                    # Check if the browser is still running
                    if not is_browser_running(browser_info.get('pid')):
                        if logger:
                            logger.warning(f"Built-in browser on port {debugging_port} is not running", tag="BUILTIN")
                        # Remove this port from the dictionary
                        del browser_info_dict["port_map"][port_str]
                        with open(config_file, 'w') as f:
                            json.dump(browser_info_dict, f, indent=2)
                        return None
                    
                    return browser_info
            
            return None
                
        except Exception as e:
            if logger:
                logger.error(f"Error reading built-in browser config: {str(e)}", tag="BUILTIN")
            return None
            
    def get_browser_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current built-in browser instance.
        
        Returns:
            dict: Browser information or None if no running browser is configured
        """
        return self.get_builtin_browser_info(
            debugging_port=self.config.debugging_port,
            config_file=self.builtin_config_file,
            logger=self.logger
        )
    
    
    async def launch_builtin_browser(self, 
                               browser_type: str = "chromium",
                               debugging_port: int = 9222,
                               headless: bool = True) -> Optional[str]:
        """Launch a browser in the background for use as the built-in browser.
        
        Args:
            browser_type: Type of browser to launch ('chromium' or 'firefox')
            debugging_port: Port to use for CDP debugging
            headless: Whether to run in headless mode
            
        Returns:
            str: CDP URL for the browser, or None if launch failed
        """
        # Check if there's an existing browser still running
        browser_info = self.get_builtin_browser_info(
            debugging_port=debugging_port,
            config_file=self.builtin_config_file,
            logger=self.logger
        )
        if browser_info:
            if self.logger:
                self.logger.info(f"Built-in browser is already running on port {debugging_port}", tag="BUILTIN")
            return browser_info.get('cdp_url')
        
        # Create a user data directory for the built-in browser
        user_data_dir = os.path.join(self.builtin_browser_dir, "user_data")
        # Raise error if user data dir is already engaged
        if self._check_user_dir_is_engaged(user_data_dir):
            raise Exception(f"User data directory {user_data_dir} is already engaged by another browser instance.")
            
        # Create the user data directory if it doesn't exist
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Prepare browser launch arguments
        browser_path = await get_browser_executable(browser_type)
        if browser_type == "chromium":
            args = [
                browser_path,
                f"--remote-debugging-port={debugging_port}",
                f"--user-data-dir={user_data_dir}",
            ]
            if headless:
                args.append("--headless=new")
        elif browser_type == "firefox":
            args = [
                browser_path,
                "--remote-debugging-port",
                str(debugging_port),
                "--profile",
                user_data_dir,
            ]
            if headless:
                args.append("--headless")
        else:
            if self.logger:
                self.logger.error(f"Browser type {browser_type} not supported for built-in browser", tag="BUILTIN")
            return None
        
        try:
            # Start the browser process detached
            if is_windows():
                process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setpgrp  # Start in a new process group
                )
            
            # Wait briefly to ensure the process starts successfully
            await asyncio.sleep(2.0)
            
            # Check if the process is still running
            if process.poll() is not None:
                if self.logger:
                    self.logger.error(f"Browser process exited immediately with code {process.returncode}", tag="BUILTIN")
                return None
            
            # Construct CDP URL
            cdp_url = f"http://localhost:{debugging_port}"
            
            # Try to verify browser is responsive by fetching version info
            import aiohttp
            json_url = f"{cdp_url}/json/version"
            config_json = None
            
            try:
                async with aiohttp.ClientSession() as session:
                    for _ in range(10):  # Try multiple times
                        try:
                            async with session.get(json_url) as response:
                                if response.status == 200:
                                    config_json = await response.json()
                                    break
                        except Exception:
                            pass
                        await asyncio.sleep(0.5)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Could not verify browser: {str(e)}", tag="BUILTIN")
            
            # Create browser info
            browser_info = {
                'pid': process.pid,
                'cdp_url': cdp_url,
                'user_data_dir': user_data_dir,
                'browser_type': browser_type,
                'debugging_port': debugging_port,
                'start_time': time.time(),
                'config': config_json
            }
            
            # Read existing config file if it exists
            port_map = {}
            if os.path.exists(self.builtin_config_file):
                try:
                    with open(self.builtin_config_file, 'r') as f:
                        existing_data = json.load(f)
                    
                    # Check if it already uses port mapping
                    if isinstance(existing_data, dict) and "port_map" in existing_data:
                        port_map = existing_data["port_map"]
                    # Convert legacy format to port mapping
                    elif isinstance(existing_data, dict) and "debugging_port" in existing_data:
                        old_port = str(existing_data.get("debugging_port"))
                        if self._is_browser_running(existing_data.get("pid")):
                            port_map[old_port] = existing_data
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Could not read existing config: {str(e)}", tag="BUILTIN")
            
            # Add/update this browser in the port map
            port_map[str(debugging_port)] = browser_info
            
            # Write updated config
            with open(self.builtin_config_file, 'w') as f:
                json.dump({"port_map": port_map}, f, indent=2)
                
            # Detach from the browser process - don't keep any references
            # This is important to allow the Python script to exit while the browser continues running
            process = None
                
            if self.logger:
                self.logger.success(f"Built-in browser launched at CDP URL: {cdp_url}", tag="BUILTIN")
            return cdp_url
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error launching built-in browser: {str(e)}", tag="BUILTIN")
            return None
    
    async def kill_builtin_browser(self) -> bool:
        """Kill the built-in browser if it's running.
        
        Returns:
            bool: True if the browser was killed, False otherwise
        """
        browser_info = self.get_browser_info()
        if not browser_info:
            if self.logger:
                self.logger.warning(f"No built-in browser found on port {self.config.debugging_port}", tag="BUILTIN")
            return False
            
        pid = browser_info.get('pid')
        if not pid:
            return False
            
        try:
            if is_windows():
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
            else:
                os.kill(pid, signal.SIGTERM)
                # Wait for termination
                for _ in range(5):
                    if not is_browser_running(pid):
                        break
                    await asyncio.sleep(0.5)
                else:
                    # Force kill if still running
                    os.kill(pid, signal.SIGKILL)
                    
            # Update config file to remove this browser
            with open(self.builtin_config_file, 'r') as f:
                browser_info_dict = json.load(f)
            # Remove this port from the dictionary
            port_str = str(self.config.debugging_port)
            if port_str in browser_info_dict.get("port_map", {}):
                del browser_info_dict["port_map"][port_str]
            with open(self.builtin_config_file, 'w') as f:
                json.dump(browser_info_dict, f, indent=2)
            # Remove user data directory if it exists
            if os.path.exists(self.builtin_browser_dir):
                shutil.rmtree(self.builtin_browser_dir)
            # Clear the browser info cache
            self.browser = None
            self.temp_dir = None
            self.shutting_down = True
                
            if self.logger:
                self.logger.success("Built-in browser terminated", tag="BUILTIN")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error killing built-in browser: {str(e)}", tag="BUILTIN")
            return False
    
    async def get_builtin_browser_status(self) -> Dict[str, Any]:
        """Get status information about the built-in browser.
        
        Returns:
            dict: Status information with running, cdp_url, and info fields
        """
        browser_info = self.get_browser_info()
        
        if not browser_info:
            return {
                'running': False,
                'cdp_url': None,
                'info': None,
                'port': self.config.debugging_port
            }
            
        return {
            'running': True,
            'cdp_url': browser_info.get('cdp_url'),
            'info': browser_info,
            'port': self.config.debugging_port
        }

    # Override the close method to handle built-in browser cleanup
    async def close(self):
        """Close the built-in browser and clean up resources."""
        # Call parent class close method
        await super().close()
        
        # Clean up built-in browser if we created it
        if self.shutting_down:
            await self.kill_builtin_browser()
