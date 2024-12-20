import asyncio
import base64
import time
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, List, Optional, Awaitable
import os, sys, shutil
import tempfile, subprocess
from playwright.async_api import async_playwright, Page, Browser, Error, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from playwright.async_api import ProxySettings
from pydantic import BaseModel
import hashlib
import json
import uuid
from .js_snippet import load_js_script
from .models import AsyncCrawlResponse
from .utils import get_error_context
from .user_agent_generator import UserAgentGenerator
from .config import SCREENSHOT_HEIGHT_TRESHOLD, DOWNLOAD_PAGE_TIMEOUT
from .async_configs import BrowserConfig, CrawlerRunConfig
from .async_logger import AsyncLogger
from playwright_stealth import StealthConfig, stealth_async


from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont

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

BROWSER_DISABLE_OPTIONS = [
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--disable-component-extensions-with-background-pages",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-features=TranslateUI",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-sync",
    "--force-color-profile=srgb",
    "--metrics-recording-only",
    "--no-first-run",
    "--password-store=basic",
    "--use-mock-keychain",
]


class ManagedBrowser:
    def __init__(
        self,
        browser_type: str = "chromium",
        user_data_dir: Optional[str] = None,
        headless: bool = False,
        logger=None,
        host: str = "localhost",
        debugging_port: int = 9222,
    ):
        self.browser_type = browser_type
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.browser_process = None
        self.temp_dir = None
        self.debugging_port = debugging_port
        self.host = host
        self.logger = logger
        self.shutting_down = False

    async def start(self) -> str:
        """
        Starts the browser process and returns the CDP endpoint URL.
        If user_data_dir is not provided, creates a temporary directory.
        """

        # Create temp dir if needed
        if not self.user_data_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="browser-profile-")
            self.user_data_dir = self.temp_dir

        # Get browser path and args based on OS and browser type
        browser_path = self._get_browser_path()
        args = self._get_browser_args()

        # Start browser process
        try:
            self.browser_process = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            # Monitor browser process output for errors
            asyncio.create_task(self._monitor_browser_process())
            await asyncio.sleep(2)  # Give browser time to start
            return f"http://{self.host}:{self.debugging_port}"
        except Exception as e:
            await self.cleanup()
            raise Exception(f"Failed to start browser: {e}")

    async def _monitor_browser_process(self):
        """Monitor the browser process for unexpected termination."""
        if self.browser_process:
            try:
                stdout, stderr = await asyncio.gather(
                    asyncio.to_thread(self.browser_process.stdout.read),
                    asyncio.to_thread(self.browser_process.stderr.read),
                )

                # Check shutting_down flag BEFORE logging anything
                if self.browser_process.poll() is not None:
                    if not self.shutting_down:
                        self.logger.error(
                            message="Browser process terminated unexpectedly | Code: {code} | STDOUT: {stdout} | STDERR: {stderr}",
                            tag="ERROR",
                            params={
                                "code": self.browser_process.returncode,
                                "stdout": stdout.decode(),
                                "stderr": stderr.decode(),
                            },
                        )
                        await self.cleanup()
                    else:
                        self.logger.info(
                            message="Browser process terminated normally | Code: {code}",
                            tag="INFO",
                            params={"code": self.browser_process.returncode},
                        )
            except Exception as e:
                if not self.shutting_down:
                    self.logger.error(
                        message="Error monitoring browser process: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )

    def _get_browser_path(self) -> str:
        """Returns the browser executable path based on OS and browser type"""
        if sys.platform == "darwin":  # macOS
            paths = {
                "chromium": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
                "webkit": "/Applications/Safari.app/Contents/MacOS/Safari",
            }
        elif sys.platform == "win32":  # Windows
            paths = {
                "chromium": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                "webkit": None,  # WebKit not supported on Windows
            }
        else:  # Linux
            paths = {
                "chromium": "google-chrome",
                "firefox": "firefox",
                "webkit": None,  # WebKit not supported on Linux
            }

        return paths.get(self.browser_type)

    def _get_browser_args(self) -> List[str]:
        """Returns browser-specific command line arguments"""
        base_args = [self._get_browser_path()]

        if self.browser_type == "chromium":
            args = [
                f"--remote-debugging-port={self.debugging_port}",
                f"--user-data-dir={self.user_data_dir}",
            ]
            if self.headless:
                args.append("--headless=new")
        elif self.browser_type == "firefox":
            args = [
                "--remote-debugging-port",
                str(self.debugging_port),
                "--profile",
                self.user_data_dir,
            ]
            if self.headless:
                args.append("--headless")
        else:
            raise NotImplementedError(f"Browser type {self.browser_type} not supported")

        return base_args + args

    async def cleanup(self):
        """Cleanup browser process and temporary directory"""
        # Set shutting_down flag BEFORE any termination actions
        self.shutting_down = True

        if self.browser_process:
            try:
                self.browser_process.terminate()
                # Wait for process to end gracefully
                for _ in range(10):  # 10 attempts, 100ms each
                    if self.browser_process.poll() is not None:
                        break
                    await asyncio.sleep(0.1)

                # Force kill if still running
                if self.browser_process.poll() is None:
                    self.browser_process.kill()
                    await asyncio.sleep(0.1)  # Brief wait for kill to take effect

            except Exception as e:
                self.logger.error(
                    message="Error terminating browser: {error}",
                    tag="ERROR",
                    params={"error": str(e)},
                )

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self.logger.error(
                    message="Error removing temporary directory: {error}",
                    tag="ERROR",
                    params={"error": str(e)},
                )


class BrowserManager:
    def __init__(self, browser_config: BrowserConfig, logger=None):
        """
        Initialize the BrowserManager with a browser configuration.

        Args:
            browser_config (BrowserConfig): Configuration object containing all browser settings
            logger: Logger instance for recording events and errors
        """
        self.config: BrowserConfig = browser_config
        self.logger = logger

        # Browser state
        self.browser = None
        self.default_context = None
        self.managed_browser = None
        self.playwright = None

        # Session management
        self.sessions = {}
        self.session_ttl = 1800  # 30 minutes

        # Initialize ManagedBrowser if needed
        if self.config.use_managed_browser:
            self.managed_browser = ManagedBrowser(
                browser_type=self.config.browser_type,
                user_data_dir=self.config.user_data_dir,
                headless=self.config.headless,
                logger=self.logger,
                debugging_port=self.config.debugging_port,
            )

    async def start(self):
        """Start the browser instance and set up the default context."""
        if self.playwright is None:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

        if self.config.use_managed_browser:
            cdp_url = await self.managed_browser.start()
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            contexts = self.browser.contexts
            if contexts:
                self.default_context = contexts[0]
            else:
                self.default_context = await self.create_browser_context()
                # self.default_context = await self.browser.new_context(
                #     viewport={
                #         "width": self.config.viewport_width,
                #         "height": self.config.viewport_height,
                #     },
                #     storage_state=self.config.storage_state,
                #     user_agent=self.config.headers.get(
                #         "User-Agent", self.config.user_agent
                #     ),
                #     accept_downloads=self.config.accept_downloads,
                #     ignore_https_errors=self.config.ignore_https_errors,
                #     java_script_enabled=self.config.java_script_enabled,
                # )
            await self.setup_context(self.default_context)
        else:
            browser_args = self._build_browser_args()

            # Launch appropriate browser type
            if self.config.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(**browser_args)
            elif self.config.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(**browser_args)
            else:
                self.browser = await self.playwright.chromium.launch(**browser_args)

            self.default_context = self.browser

    def _build_browser_args(self) -> dict:
        """Build browser launch arguments from config."""
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
            # "--single-process",
            f"--window-size={self.config.viewport_width},{self.config.viewport_height}",
        ]

        if self.config.light_mode:
            args.extend(BROWSER_DISABLE_OPTIONS)

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
            from playwright.async_api import ProxySettings

            proxy_settings = (
                ProxySettings(server=self.config.proxy)
                if self.config.proxy
                else ProxySettings(
                    server=self.config.proxy_config.get("server"),
                    username=self.config.proxy_config.get("username"),
                    password=self.config.proxy_config.get("password"),
                )
            )
            browser_args["proxy"] = proxy_settings

        return browser_args

    async def setup_context(
        self,
        context: BrowserContext,
        crawlerRunConfig: CrawlerRunConfig,
        is_default=False,
    ):
        """Set up a browser context with the configured options."""
        if self.config.headers:
            await context.set_extra_http_headers(self.config.headers)

        if self.config.cookies:
            await context.add_cookies(self.config.cookies)

        if self.config.storage_state:
            await context.storage_state(path=None)

        if self.config.accept_downloads:
            context.set_default_timeout(DOWNLOAD_PAGE_TIMEOUT)
            context.set_default_navigation_timeout(DOWNLOAD_PAGE_TIMEOUT)
            if self.config.downloads_path:
                context._impl_obj._options["accept_downloads"] = True
                context._impl_obj._options["downloads_path"] = (
                    self.config.downloads_path
                )

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
            [{"name": "cookiesEnabled", "value": "true", "url": crawlerRunConfig.url}]
        )

        # Handle navigator overrides
        if (
            crawlerRunConfig.override_navigator
            or crawlerRunConfig.simulate_user
            or crawlerRunConfig.magic
        ):
            await context.add_init_script(load_js_script("navigator_overrider"))

    async def create_browser_context(self):
        """
        Creates and returns a new browser context with configured settings.
        Applies text-only mode settings if text_mode is enabled in config.
        
        Returns:
            Context: Browser context object with the specified configurations
        """
        # Base settings
        user_agent = self.config.headers.get("User-Agent", self.config.user_agent)
        viewport_settings = {
            "width": self.config.viewport_width,
            "height": self.config.viewport_height,
        }
        proxy_settings = {"server": self.config.proxy} if self.config.proxy else None
        
        blocked_extensions = [
            # Images
            'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico', 'bmp', 'tiff', 'psd',
            # Fonts
            'woff', 'woff2', 'ttf', 'otf', 'eot',
            # Styles
            # 'css', 'less', 'scss', 'sass',
            # Media
            'mp4', 'webm', 'ogg', 'avi', 'mov', 'wmv', 'flv', 'm4v',
            'mp3', 'wav', 'aac', 'm4a', 'opus', 'flac',
            # Documents
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            # Archives
            'zip', 'rar', '7z', 'tar', 'gz',
            # Scripts and data
            'xml', 'swf', 'wasm'
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
        
        if self.config.text_mode:
            text_mode_settings = {
                "has_touch": False,
                "is_mobile": False,
            }
            # Update context settings with text mode settings
            context_settings.update(text_mode_settings)
            
        # Create and return the context with all settings
        context = await self.browser.new_context(**context_settings)
        
        # Apply text mode settings if enabled
        if self.config.text_mode:
            # Create and apply route patterns for each extension
            for ext in blocked_extensions:
                await context.route(f"**/*.{ext}", lambda route: route.abort())
        return context
    
    # async def get_page(self, session_id: Optional[str], user_agent: str):
    async def get_page(self, crawlerRunConfig: CrawlerRunConfig):
        """Get a page for the given session ID, creating a new one if needed."""
        self._cleanup_expired_sessions()

        if crawlerRunConfig.session_id and crawlerRunConfig.session_id in self.sessions:
            context, page, _ = self.sessions[crawlerRunConfig.session_id]
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
            return page, context

        if self.config.use_managed_browser:
            context = self.default_context
            page = await context.new_page()
        else:
            context = await self.create_browser_context()
            await self.setup_context(context, crawlerRunConfig)
            page = await context.new_page()

        if crawlerRunConfig.session_id:
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())

        return page, context

    async def kill_session(self, session_id: str):
        """Kill a browser session and clean up resources."""
        if session_id in self.sessions:
            context, page, _ = self.sessions[session_id]
            await page.close()
            if not self.config.use_managed_browser:
                await context.close()
            del self.sessions[session_id]

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions based on TTL."""
        current_time = time.time()
        expired_sessions = [
            sid
            for sid, (_, _, last_used) in self.sessions.items()
            if current_time - last_used > self.session_ttl
        ]
        for sid in expired_sessions:
            asyncio.create_task(self.kill_session(sid))

    async def close(self):
        """Close all browser resources and clean up."""
        if self.config.sleep_on_close:
            await asyncio.sleep(0.5)

        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.kill_session(session_id)

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.managed_browser:
            await asyncio.sleep(0.5)
            await self.managed_browser.cleanup()
            self.managed_browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None


class AsyncCrawlerStrategy(ABC):
    @abstractmethod
    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
        pass  # 4 + 3

    @abstractmethod
    async def crawl_many(self, urls: List[str], **kwargs) -> List[AsyncCrawlResponse]:
        pass

    @abstractmethod
    async def take_screenshot(self, **kwargs) -> str:
        pass

    @abstractmethod
    def update_user_agent(self, user_agent: str):
        pass

    @abstractmethod
    def set_hook(self, hook_type: str, hook: Callable):
        pass


class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
    def __init__(
        self, browser_config: BrowserConfig = None, logger: AsyncLogger = None, **kwargs
    ):
        """
        Initialize the AsyncPlaywrightCrawlerStrategy with a browser configuration.

        Args:
            browser_config (BrowserConfig): Configuration object containing browser settings.
                                          If None, will be created from kwargs for backwards compatibility.
            logger: Logger instance for recording events and errors.
            **kwargs: Additional arguments for backwards compatibility and extending functionality.
        """
        # Initialize browser config, either from provided object or kwargs
        self.browser_config = browser_config or BrowserConfig.from_kwargs(kwargs)
        self.logger = logger

        # Initialize session management
        self._downloaded_files = []

        # Initialize hooks system
        self.hooks = {
            "on_browser_created": None,
            "on_page_context_created": None,
            "on_user_agent_updated": None,
            "on_execution_started": None,
            "before_goto": None,
            "after_goto": None,
            "before_return_html": None,
            "before_retrieve_html": None,
        }

        # Initialize browser manager with config
        self.browser_manager = BrowserManager(
            browser_config=self.browser_config, logger=self.logger
        )

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        await self.browser_manager.start()
        await self.execute_hook(
            "on_browser_created",
            self.browser_manager.browser,
            context=self.browser_manager.default_context,
        )

    async def close(self):
        await self.browser_manager.close()

    async def kill_session(self, session_id: str):
        # Log a warning message and no need kill session, in new version auto kill session
        self.logger.warning(
            message="Session auto-kill is enabled in the new version. No need to manually kill sessions.",
            tag="WARNING",
        )
        await self.browser_manager.kill_session(session_id)

    def set_hook(self, hook_type: str, hook: Callable):
        if hook_type in self.hooks:
            self.hooks[hook_type] = hook
        else:
            raise ValueError(f"Invalid hook type: {hook_type}")

    async def execute_hook(self, hook_type: str, *args, **kwargs):
        hook = self.hooks.get(hook_type)
        if hook:
            if asyncio.iscoroutinefunction(hook):
                return await hook(*args, **kwargs)
            else:
                return hook(*args, **kwargs)
        return args[0] if args else None

    def update_user_agent(self, user_agent: str):
        self.user_agent = user_agent

    def set_custom_headers(self, headers: Dict[str, str]):
        self.headers = headers

    async def smart_wait(self, page: Page, wait_for: str, timeout: float = 30000):
        wait_for = wait_for.strip()

        if wait_for.startswith("js:"):
            # Explicitly specified JavaScript
            js_code = wait_for[3:].strip()
            return await self.csp_compliant_wait(page, js_code, timeout)
        elif wait_for.startswith("css:"):
            # Explicitly specified CSS selector
            css_selector = wait_for[4:].strip()
            try:
                await page.wait_for_selector(css_selector, timeout=timeout)
            except Error as e:
                if "Timeout" in str(e):
                    raise TimeoutError(
                        f"Timeout after {timeout}ms waiting for selector '{css_selector}'"
                    )
                else:
                    raise ValueError(f"Invalid CSS selector: '{css_selector}'")
        else:
            # Auto-detect based on content
            if wait_for.startswith("()") or wait_for.startswith("function"):
                # It's likely a JavaScript function
                return await self.csp_compliant_wait(page, wait_for, timeout)
            else:
                # Assume it's a CSS selector first
                try:
                    await page.wait_for_selector(wait_for, timeout=timeout)
                except Error as e:
                    if "Timeout" in str(e):
                        raise TimeoutError(
                            f"Timeout after {timeout}ms waiting for selector '{wait_for}'"
                        )
                    else:
                        # If it's not a timeout error, it might be an invalid selector
                        # Let's try to evaluate it as a JavaScript function as a fallback
                        try:
                            return await self.csp_compliant_wait(
                                page, f"() => {{{wait_for}}}", timeout
                            )
                        except Error:
                            raise ValueError(
                                f"Invalid wait_for parameter: '{wait_for}'. "
                                "It should be either a valid CSS selector, a JavaScript function, "
                                "or explicitly prefixed with 'js:' or 'css:'."
                            )

    async def csp_compliant_wait(
        self, page: Page, user_wait_function: str, timeout: float = 30000
    ):
        wrapper_js = f"""
        async () => {{
            const userFunction = {user_wait_function};
            const startTime = Date.now();
            while (true) {{
                if (await userFunction()) {{
                    return true;
                }}
                if (Date.now() - startTime > {timeout}) {{
                    throw new Error('Timeout waiting for condition');
                }}
                await new Promise(resolve => setTimeout(resolve, 100));
            }}
        }}
        """

        try:
            await page.evaluate(wrapper_js)
        except TimeoutError:
            raise TimeoutError(f"Timeout after {timeout}ms waiting for condition")
        except Exception as e:
            raise RuntimeError(f"Error in wait condition: {str(e)}")

    async def process_iframes(self, page):
        # Find all iframes
        iframes = await page.query_selector_all("iframe")

        for i, iframe in enumerate(iframes):
            try:
                # Add a unique identifier to the iframe
                await iframe.evaluate(f'(element) => element.id = "iframe-{i}"')

                # Get the frame associated with this iframe
                frame = await iframe.content_frame()

                if frame:
                    # Wait for the frame to load
                    await frame.wait_for_load_state(
                        "load", timeout=30000
                    )  # 30 seconds timeout

                    # Extract the content of the iframe's body
                    iframe_content = await frame.evaluate(
                        "() => document.body.innerHTML"
                    )

                    # Generate a unique class name for this iframe
                    class_name = f"extracted-iframe-content-{i}"

                    # Replace the iframe with a div containing the extracted content
                    _iframe = iframe_content.replace("`", "\\`")
                    await page.evaluate(
                        f"""
                        () => {{
                            const iframe = document.getElementById('iframe-{i}');
                            const div = document.createElement('div');
                            div.innerHTML = `{_iframe}`;
                            div.className = '{class_name}';
                            iframe.replaceWith(div);
                        }}
                    """
                    )
                else:
                    self.logger.warning(
                        message="Could not access content frame for iframe {index}",
                        tag="SCRAPE",
                        params={"index": i},
                    )
            except Exception as e:
                self.logger.error(
                    message="Error processing iframe {index}: {error}",
                    tag="ERROR",
                    params={"index": i, "error": str(e)},
                )

        # Return the page object
        return page

    async def create_session(self, **kwargs) -> str:
        """Creates a new browser session and returns its ID. A browse session is a unique openned page can be reused for multiple crawls."""
        await self.start()

        session_id = kwargs.get("session_id") or str(uuid.uuid4())

        user_agent = kwargs.get("user_agent", self.user_agent)
        # Use browser_manager to get a fresh page & context assigned to this session_id
        page, context = await self.browser_manager.get_page(session_id, user_agent)
        return session_id

    async def crawl(
        self, url: str, config: CrawlerRunConfig, **kwargs
    ) -> AsyncCrawlResponse:
        """
        Crawls a given URL or processes raw HTML/local file content based on the URL prefix.

        Args:
            url (str): The URL to crawl. Supported prefixes:
                - 'http://' or 'https://': Web URL to crawl.
                - 'file://': Local file path to process.
                - 'raw:': Raw HTML content to process.
            **kwargs: Additional parameters:
                - 'screenshot' (bool): Whether to take a screenshot.
                - ... [other existing parameters]

        Returns:
            AsyncCrawlResponse: The response containing HTML, headers, status code, and optional screenshot.
        """
        config = config or CrawlerRunConfig.from_kwargs(kwargs)
        response_headers = {}
        status_code = 200  # Default for local/raw HTML
        screenshot_data = None

        if url.startswith(("http://", "https://")):
            return await self._crawl_web(url, config)

        elif url.startswith("file://"):
            # Process local file
            local_file_path = url[7:]  # Remove 'file://' prefix
            if not os.path.exists(local_file_path):
                raise FileNotFoundError(f"Local file not found: {local_file_path}")
            with open(local_file_path, "r", encoding="utf-8") as f:
                html = f.read()
            if config.screenshot:
                screenshot_data = await self._generate_screenshot_from_html(html)
            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                status_code=status_code,
                screenshot=screenshot_data,
                get_delayed_content=None,
            )

        elif url.startswith("raw:"):
            # Process raw HTML content
            raw_html = url[4:]  # Remove 'raw:' prefix
            html = raw_html
            if config.screenshot:
                screenshot_data = await self._generate_screenshot_from_html(html)
            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                status_code=status_code,
                screenshot=screenshot_data,
                get_delayed_content=None,
            )
        else:
            raise ValueError(
                "URL must start with 'http://', 'https://', 'file://', or 'raw:'"
            )

    async def _crawl_web(
        self, url: str, config: CrawlerRunConfig
    ) -> AsyncCrawlResponse:
        """
        Internal method to crawl web URLs with the specified configuration.

        Args:
            url (str): The web URL to crawl
            config (CrawlerRunConfig): Configuration object controlling the crawl behavior

        Returns:
            AsyncCrawlResponse: The response containing HTML, headers, status code, and optional data
        """
        config.url = url
        response_headers = {}
        status_code = None

        # Reset downloaded files list for new crawl
        self._downloaded_files = []

        # Handle user agent with magic mode
        user_agent = self.browser_config.user_agent
        if config.magic and self.browser_config.user_agent_mode != "random":
            self.browser_config.user_agent = UserAgentGenerator().generate(
                **(self.browser_config.user_agent_generator_config or {})
            )

        # Get page for session
        page, context = await self.browser_manager.get_page(crawlerRunConfig=config)

        # Add default cookie
        await context.add_cookies(
            [{"name": "cookiesEnabled", "value": "true", "url": url}]
        )

        # Handle navigator overrides
        if config.override_navigator or config.simulate_user or config.magic:
            await context.add_init_script(load_js_script("navigator_overrider"))

        # Call hook after page creation
        await self.execute_hook("on_page_context_created", page, context=context)

        # Set up console logging if requested
        if config.log_console:

            def log_consol(
                msg, console_log_type="debug"
            ):  # Corrected the parameter syntax
                if console_log_type == "error":
                    self.logger.error(
                        message=f"Console error: {msg}",  # Use f-string for variable interpolation
                        tag="CONSOLE",
                        params={"msg": msg.text},
                    )
                elif console_log_type == "debug":
                    self.logger.debug(
                        message=f"Console: {msg}",  # Use f-string for variable interpolation
                        tag="CONSOLE",
                        params={"msg": msg.text},
                    )

            page.on("console", log_consol)
            page.on("pageerror", lambda e: log_consol(e, "error"))

        try:
            # Set up download handling
            if self.browser_config.accept_downloads:
                page.on(
                    "download",
                    lambda download: asyncio.create_task(
                        self._handle_download(download)
                    ),
                )

            # Handle page navigation and content loading
            if not config.js_only:
                await self.execute_hook("before_goto", page, context=context)

                try:
                    response = await page.goto(
                        url, wait_until=config.wait_until, timeout=config.page_timeout
                    )
                except Error as e:
                    raise RuntimeError(f"Failed on navigating ACS-GOTO:\n{str(e)}")

                await self.execute_hook("after_goto", page, context=context)

                if response is None:
                    status_code = 200
                    response_headers = {}
                else:
                    status_code = response.status
                    response_headers = response.headers

            else:
                status_code = 200
                response_headers = {}

            # Wait for body element and visibility
            try:
                await page.wait_for_selector("body", state="attached", timeout=30000)
                await page.wait_for_function(
                    """
                    () => {
                        const body = document.body;
                        const style = window.getComputedStyle(body);
                        return style.display !== 'none' && 
                            style.visibility !== 'hidden' && 
                            style.opacity !== '0';
                    }
                """,
                    timeout=30000,
                )
            except Error as e:
                visibility_info = await page.evaluate(
                    """
                    () => {
                        const body = document.body;
                        const style = window.getComputedStyle(body);
                        return {
                            display: style.display,
                            visibility: style.visibility,
                            opacity: style.opacity,
                            hasContent: body.innerHTML.length,
                            classList: Array.from(body.classList)
                        }
                    }
                """
                )

                if self.config.verbose:
                    self.logger.debug(
                        message="Body visibility info: {info}",
                        tag="DEBUG",
                        params={"info": visibility_info},
                    )

                if not config.ignore_body_visibility:
                    raise Error(f"Body element is hidden: {visibility_info}")

            # Handle content loading and viewport adjustment
            if not self.browser_config.text_mode and (
                config.wait_for_images or config.adjust_viewport_to_content
            ):
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(0.1)
                try:
                    await page.wait_for_function(
                        "Array.from(document.images).every(img => img.complete)",
                        timeout=1000,
                    )
                except PlaywrightTimeoutError:
                    pass

            # Adjust viewport if needed
            if not self.browser_config.text_mode and config.adjust_viewport_to_content:
                try:
                    page_width = await page.evaluate(
                        "document.documentElement.scrollWidth"
                    )
                    page_height = await page.evaluate(
                        "document.documentElement.scrollHeight"
                    )

                    target_width = self.browser_config.viewport_width
                    target_height = int(target_width * page_width / page_height * 0.95)
                    await page.set_viewport_size(
                        {"width": target_width, "height": target_height}
                    )

                    scale = min(target_width / page_width, target_height / page_height)
                    cdp = await page.context.new_cdp_session(page)
                    await cdp.send(
                        "Emulation.setDeviceMetricsOverride",
                        {
                            "width": page_width,
                            "height": page_height,
                            "deviceScaleFactor": 1,
                            "mobile": False,
                            "scale": scale,
                        },
                    )
                except Exception as e:
                    self.logger.warning(
                        message="Failed to adjust viewport to content: {error}",
                        tag="VIEWPORT",
                        params={"error": str(e)},
                    )

            # Handle full page scanning
            if config.scan_full_page:
                await self._handle_full_page_scan(page, config.scroll_delay)

            # Execute JavaScript if provided
            if config.js_code:
                if isinstance(config.js_code, str):
                    await page.evaluate(config.js_code)
                elif isinstance(config.js_code, list):
                    for js in config.js_code:
                        await page.evaluate(js)

                await self.execute_hook("on_execution_started", page, context=context)

            # Handle user simulation
            if config.simulate_user or config.magic:
                await page.mouse.move(100, 100)
                await page.mouse.down()
                await page.mouse.up()
                await page.keyboard.press("ArrowDown")

            # Handle wait_for condition
            if config.wait_for:
                try:
                    await self.smart_wait(
                        page, config.wait_for, timeout=config.page_timeout
                    )
                except Exception as e:
                    raise RuntimeError(f"Wait condition failed: {str(e)}")

            # Update image dimensions if needed
            if not self.browser_config.text_mode:
                update_image_dimensions_js = load_js_script("update_image_dimensions")
                try:
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=5)
                    except PlaywrightTimeoutError:
                        pass
                    await page.evaluate(update_image_dimensions_js)
                except Exception as e:
                    self.logger.error(
                        message="Error updating image dimensions: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )

            # Process iframes if needed
            if config.process_iframes:
                page = await self.process_iframes(page)

            # Pre-content retrieval hooks and delay
            await self.execute_hook("before_retrieve_html", page, context=context)
            if config.delay_before_return_html:
                await asyncio.sleep(config.delay_before_return_html)

            # Handle overlay removal
            if config.remove_overlay_elements:
                await self.remove_overlay_elements(page)

            # Get final HTML content
            html = await page.content()
            await self.execute_hook("before_return_html", page, html, context=context)

            # Handle PDF and screenshot generation
            start_export_time = time.perf_counter()
            pdf_data = None
            screenshot_data = None

            if config.pdf:
                pdf_data = await self.export_pdf(page)

            if config.screenshot:
                if config.screenshot_wait_for:
                    await asyncio.sleep(config.screenshot_wait_for)
                screenshot_data = await self.take_screenshot(
                    page, screenshot_height_threshold=config.screenshot_height_threshold
                )

            if screenshot_data or pdf_data:
                self.logger.info(
                    message="Exporting PDF and taking screenshot took {duration:.2f}s",
                    tag="EXPORT",
                    params={"duration": time.perf_counter() - start_export_time},
                )

            # Define delayed content getter
            async def get_delayed_content(delay: float = 5.0) -> str:
                self.logger.info(
                    message="Waiting for {delay} seconds before retrieving content for {url}",
                    tag="INFO",
                    params={"delay": delay, "url": url},
                )
                await asyncio.sleep(delay)
                return await page.content()

            # Return complete response
            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                status_code=status_code,
                screenshot=screenshot_data,
                pdf_data=pdf_data,
                get_delayed_content=get_delayed_content,
                downloaded_files=(
                    self._downloaded_files if self._downloaded_files else None
                ),
            )

        except Exception as e:
            raise e

    async def _handle_full_page_scan(self, page: Page, scroll_delay: float):
        """Helper method to handle full page scanning"""
        try:
            viewport_height = page.viewport_size.get(
                "height", self.browser_config.viewport_height
            )
            current_position = viewport_height

            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await asyncio.sleep(scroll_delay)

            total_height = await page.evaluate("document.documentElement.scrollHeight")

            while current_position < total_height:
                current_position = min(current_position + viewport_height, total_height)
                await page.evaluate(f"window.scrollTo(0, {current_position})")
                await asyncio.sleep(scroll_delay)

                new_height = await page.evaluate(
                    "document.documentElement.scrollHeight"
                )
                if new_height > total_height:
                    total_height = new_height

            await page.evaluate("window.scrollTo(0, 0)")

        except Exception as e:
            self.logger.warning(
                message="Failed to perform full page scan: {error}",
                tag="PAGE_SCAN",
                params={"error": str(e)},
            )
        else:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    async def _handle_download(self, download):
        """Handle file downloads."""
        try:
            suggested_filename = download.suggested_filename
            download_path = os.path.join(self.downloads_path, suggested_filename)

            self.logger.info(
                message="Downloading {filename} to {path}",
                tag="FETCH",
                params={"filename": suggested_filename, "path": download_path},
            )

            start_time = time.perf_counter()
            await download.save_as(download_path)
            end_time = time.perf_counter()
            self._downloaded_files.append(download_path)

            self.logger.success(
                message="Downloaded {filename} successfully",
                tag="COMPLETE",
                params={
                    "filename": suggested_filename,
                    "path": download_path,
                    "duration": f"{end_time - start_time:.2f}s",
                },
            )
        except Exception as e:
            self.logger.error(
                message="Failed to handle download: {error}",
                tag="ERROR",
                params={"error": str(e)},
            )

    async def crawl_many(self, urls: List[str], **kwargs) -> List[AsyncCrawlResponse]:
        semaphore_count = kwargs.get("semaphore_count", 5)  # Adjust as needed
        semaphore = asyncio.Semaphore(semaphore_count)

        async def crawl_with_semaphore(url):
            async with semaphore:
                return await self.crawl(url, **kwargs)

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            result if not isinstance(result, Exception) else str(result)
            for result in results
        ]

    async def remove_overlay_elements(self, page: Page) -> None:
        """
        Removes popup overlays, modals, cookie notices, and other intrusive elements from the page.

        Args:
            page (Page): The Playwright page instance
        """
        remove_overlays_js = load_js_script("remove_overlay_elements")

        try:
            await page.evaluate(remove_overlays_js)
            await page.wait_for_timeout(500)  # Wait for any animations to complete
        except Exception as e:
            self.logger.warning(
                message="Failed to remove overlay elements: {error}",
                tag="SCRAPE",
                params={"error": str(e)},
            )

    async def export_pdf(self, page: Page) -> bytes:
        """
        Exports the current page as a PDF.
        """
        pdf_data = await page.pdf(print_background=True)
        return pdf_data

    async def take_screenshot(self, page, **kwargs) -> str:
        page_height = await page.evaluate("document.documentElement.scrollHeight")
        if page_height < kwargs.get(
            "screenshot_height_threshold", SCREENSHOT_HEIGHT_TRESHOLD
        ):
            # Page is short enough, just take a screenshot
            return await self.take_screenshot_naive(page)
        else:
            # Page is too long, try to take a full-page screenshot
            return await self.take_screenshot_scroller(page, **kwargs)
            # return await self.take_screenshot_from_pdf(await self.export_pdf(page))

    async def take_screenshot_from_pdf(self, pdf_data: bytes) -> str:
        """
        Convert the first page of the PDF to a screenshot.
        Requires pdf2image and poppler.
        """
        try:
            from pdf2image import convert_from_bytes

            images = convert_from_bytes(pdf_data)
            final_img = images[0].convert("RGB")
            buffered = BytesIO()
            final_img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            error_message = f"Failed to take PDF-based screenshot: {str(e)}"
            self.logger.error(
                message="PDF Screenshot failed: {error}",
                tag="ERROR",
                params={"error": error_message},
            )
            # Return error image as fallback
            img = Image.new("RGB", (800, 600), color="black")
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

    async def take_screenshot_scroller(self, page: Page, **kwargs) -> str:
        """
        Attempt to set a large viewport and take a full-page screenshot.
        If still too large, segment the page as before.
        """
        try:
            # Get page height
            page_height = await page.evaluate("document.documentElement.scrollHeight")
            page_width = await page.evaluate("document.documentElement.scrollWidth")

            # Set a large viewport
            large_viewport_height = min(
                page_height,
                kwargs.get("screenshot_height_threshold", SCREENSHOT_HEIGHT_TRESHOLD),
            )
            await page.set_viewport_size(
                {"width": page_width, "height": large_viewport_height}
            )

            # Page still too long, segment approach
            segments = []
            viewport_size = page.viewport_size
            viewport_height = viewport_size["height"]

            num_segments = (page_height // viewport_height) + 1
            for i in range(num_segments):
                y_offset = i * viewport_height
                await page.evaluate(f"window.scrollTo(0, {y_offset})")
                await asyncio.sleep(0.01)  # wait for render
                seg_shot = await page.screenshot(full_page=False)
                img = Image.open(BytesIO(seg_shot)).convert("RGB")
                segments.append(img)

            total_height = sum(img.height for img in segments)
            stitched = Image.new("RGB", (segments[0].width, total_height))
            offset = 0
            for img in segments:
                # stitched.paste(img, (0, offset))
                stitched.paste(img.convert("RGB"), (0, offset))
                offset += img.height

            buffered = BytesIO()
            stitched = stitched.convert("RGB")
            stitched.save(buffered, format="BMP", quality=85)
            encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")

            return encoded
        except Exception as e:
            error_message = f"Failed to take large viewport screenshot: {str(e)}"
            self.logger.error(
                message="Large viewport screenshot failed: {error}",
                tag="ERROR",
                params={"error": error_message},
            )
            # return error image
            img = Image.new("RGB", (800, 600), color="black")
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        finally:
            await page.close()

    async def take_screenshot_naive(self, page: Page) -> str:
        """
        Takes a screenshot of the current page.

        Args:
            page (Page): The Playwright page instance

        Returns:
            str: Base64-encoded screenshot image
        """
        try:
            # The page is already loaded, just take the screenshot
            screenshot = await page.screenshot(full_page=False)
            return base64.b64encode(screenshot).decode("utf-8")
        except Exception as e:
            error_message = f"Failed to take screenshot: {str(e)}"
            self.logger.error(
                message="Screenshot failed: {error}",
                tag="ERROR",
                params={"error": error_message},
            )

            # Generate an error image
            img = Image.new("RGB", (800, 600), color="black")
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)

            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        finally:
            await page.close()

    async def export_storage_state(self, path: str = None) -> dict:
        """
        Exports the current storage state (cookies, localStorage, sessionStorage)
        to a JSON file at the specified path.
        """
        if self.default_context:
            state = await self.default_context.storage_state(path=path)
            self.logger.info(
                message="Exported storage state to {path}",
                tag="INFO",
                params={"path": path},
            )
            return state
        else:
            self.logger.warning(
                message="No default_context available to export storage state.",
                tag="WARNING",
            )

    async def _generate_screenshot_from_html(self, html: str) -> Optional[str]:
        """
        Generates a screenshot from raw HTML content.

        Args:
            html (str): The HTML content to render and capture.

        Returns:
            Optional[str]: Base64-encoded screenshot image or an error image if failed.
        """
        try:
            await self.start()
            # Create a temporary page without a session_id
            page, context = await self.browser_manager.get_page(None, self.user_agent)

            await page.set_content(html, wait_until="networkidle")
            screenshot = await page.screenshot(full_page=True)
            await page.close()
            return base64.b64encode(screenshot).decode("utf-8")
        except Exception as e:
            error_message = f"Failed to take screenshot: {str(e)}"
            self.logger.error(
                message="Screenshot failed: {error}",
                tag="ERROR",
                params={"error": error_message},
            )

            # Generate an error image
            img = Image.new("RGB", (800, 600), color="black")
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)

            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
