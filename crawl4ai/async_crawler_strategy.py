import asyncio
import base64
import time
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, List, Optional, Awaitable
import os, sys, shutil
import tempfile, subprocess
from playwright.async_api import async_playwright, Page, Browser, Error
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from playwright.async_api import ProxySettings
from pydantic import BaseModel
import hashlib
import json
import uuid
from .models import AsyncCrawlResponse
from .utils import create_box_message
from playwright_stealth import StealthConfig, stealth_async

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


class ManagedBrowser:
    def __init__(self, browser_type: str = "chromium", user_data_dir: Optional[str] = None, headless: bool = False, logger = None, host: str = "localhost", debugging_port: int = 9222):
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
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
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
                    asyncio.to_thread(self.browser_process.stderr.read)
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
                                "stderr": stderr.decode()
                            }
                        )                
                        await self.cleanup()
                    else:
                        self.logger.info(
                            message="Browser process terminated normally | Code: {code}",
                            tag="INFO",
                            params={"code": self.browser_process.returncode}
                        )
            except Exception as e:
                if not self.shutting_down:
                    self.logger.error(
                        message="Error monitoring browser process: {error}",
                        tag="ERROR",
                        params={"error": str(e)}
                    )

    def _get_browser_path(self) -> str:
        """Returns the browser executable path based on OS and browser type"""
        if sys.platform == "darwin":  # macOS
            paths = {
                "chromium": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
                "webkit": "/Applications/Safari.app/Contents/MacOS/Safari"
            }
        elif sys.platform == "win32":  # Windows
            paths = {
                "chromium": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                "webkit": None  # WebKit not supported on Windows
            }
        else:  # Linux
            paths = {
                "chromium": "google-chrome",
                "firefox": "firefox",
                "webkit": None  # WebKit not supported on Linux
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
                "--remote-debugging-port", str(self.debugging_port),
                "--profile", self.user_data_dir,
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
                    params={"error": str(e)}
                )

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self.logger.error(
                    message="Error removing temporary directory: {error}",
                    tag="ERROR",
                    params={"error": str(e)}
                )


class AsyncCrawlerStrategy(ABC):
    @abstractmethod
    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
        pass
    
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
    def __init__(self, use_cached_html=False, js_code=None, logger = None, **kwargs):
        self.logger = logger
        self.use_cached_html = use_cached_html
        self.user_agent = kwargs.get(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.proxy = kwargs.get("proxy")
        self.proxy_config = kwargs.get("proxy_config")
        self.headless = kwargs.get("headless", True)
        self.browser_type = kwargs.get("browser_type", "chromium")
        self.headers = kwargs.get("headers", {})
        self.cookies = kwargs.get("cookies", [])
        self.sessions = {}
        self.session_ttl = 1800 
        self.js_code = js_code
        self.verbose = kwargs.get("verbose", False)
        self.playwright = None
        self.browser = None
        self.sleep_on_close = kwargs.get("sleep_on_close", False)
        self.use_managed_browser = kwargs.get("use_managed_browser", False)
        self.user_data_dir = kwargs.get("user_data_dir", None)
        self.use_persistent_context = kwargs.get("use_persistent_context", False)
        self.chrome_channel = kwargs.get("chrome_channel", "chrome")
        self.managed_browser = None
        self.default_context = None
        self.hooks = {
            'on_browser_created': None,
            'on_user_agent_updated': None,
            'on_execution_started': None,
            'before_goto': None,
            'after_goto': None,
            'before_return_html': None,
            'before_retrieve_html': None
        }
        self.extra_args = kwargs.get("extra_args", [])
        self.accept_downloads = kwargs.get("accept_downloads", False)
        self.downloads_path = kwargs.get("downloads_path")
        self._downloaded_files = []  # Track downloaded files for current crawl
        if self.accept_downloads and not self.downloads_path:
            self.downloads_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(self.downloads_path, exist_ok=True)        
        

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        if self.playwright is None:
            self.playwright = await async_playwright().start()
        if self.browser is None:
            if self.use_managed_browser:
                # Use managed browser approach
                self.managed_browser = ManagedBrowser(
                    browser_type=self.browser_type,
                    user_data_dir=self.user_data_dir,
                    headless=self.headless,
                    logger=self.logger
                )
                cdp_url = await self.managed_browser.start()
                self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
                
                # Get the default context that maintains the user profile
                contexts = self.browser.contexts
                if contexts:
                    self.default_context = contexts[0]
                else:
                    # If no default context exists, create one
                    self.default_context = await self.browser.new_context(
                        viewport={"width": 1920, "height": 1080}
                    )
                
                # Set up the default context
                if self.default_context:
                    await self.default_context.set_extra_http_headers(self.headers)
                    if self.cookies:
                        await self.default_context.add_cookies(self.cookies)                    
                    if self.accept_downloads:
                        await self.default_context.set_default_timeout(60000)
                        await self.default_context.set_default_navigation_timeout(60000)
                        self.default_context._impl_obj._options["accept_downloads"] = True
                        self.default_context._impl_obj._options["downloads_path"] = self.downloads_path
                        
                    if self.user_agent:
                        await self.default_context.set_extra_http_headers({
                            "User-Agent": self.user_agent
                        })
            else:
                # Base browser arguments
                browser_args = {
                    "headless": self.headless,
                    "args": [
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-infobars",
                        "--window-position=0,0",
                        "--ignore-certificate-errors",
                        "--ignore-certificate-errors-spki-list"
                    ]
                }
                
                # Add channel if specified (try Chrome first)
                if self.chrome_channel:
                    browser_args["channel"] = self.chrome_channel
                
                # Add extra args if provided
                if self.extra_args:
                    browser_args["args"].extend(self.extra_args)
                    
                # Add downloads path if downloads are enabled
                if self.accept_downloads:
                    browser_args["downloads_path"] = self.downloads_path
                
                # Add proxy settings if a proxy is specified
                if self.proxy:
                    proxy_settings = ProxySettings(server=self.proxy)
                    browser_args["proxy"] = proxy_settings
                elif self.proxy_config:
                    proxy_settings = ProxySettings(
                        server=self.proxy_config.get("server"),
                        username=self.proxy_config.get("username"),
                        password=self.proxy_config.get("password")
                    )
                    browser_args["proxy"] = proxy_settings
                    
                try:
                    # Select the appropriate browser based on the browser_type
                    if self.browser_type == "firefox":
                        self.browser = await self.playwright.firefox.launch(**browser_args)
                    elif self.browser_type == "webkit":
                        self.browser = await self.playwright.webkit.launch(**browser_args)
                    else:
                        if self.use_persistent_context and self.user_data_dir:
                            self.browser = await self.playwright.chromium.launch_persistent_context(
                                user_data_dir=self.user_data_dir,
                                accept_downloads=self.accept_downloads,
                                downloads_path=self.downloads_path if self.accept_downloads else None,                                
                                **browser_args
                            )
                            self.default_context = self.browser
                        else:
                            self.browser = await self.playwright.chromium.launch(**browser_args)
                                
                except Exception as e:
                    # Fallback to chromium if Chrome channel fails
                    if "chrome" in str(e) and browser_args.get("channel") == "chrome":
                        browser_args["channel"] = "chromium"
                        if self.use_persistent_context and self.user_data_dir:
                            self.browser = await self.playwright.chromium.launch_persistent_context(
                                user_data_dir=self.user_data_dir,
                                **browser_args
                            )
                            self.default_context = self.browser
                        else:
                            self.browser = await self.playwright.chromium.launch(**browser_args)
                    else:
                        raise

            await self.execute_hook('on_browser_created', self.browser)

    async def close(self):
        if self.sleep_on_close:
            await asyncio.sleep(0.5)
            
        # Close all active sessions
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

    # Issue #256: Remove __del__ method to avoid potential issues with async cleanup
    # def __del__(self):
    #     if self.browser or self.playwright:
    #         asyncio.get_event_loop().run_until_complete(self.close())

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

    async def kill_session(self, session_id: str):
        if session_id in self.sessions:
            context, page, _ = self.sessions[session_id]
            await page.close()
            if not self.use_managed_browser:
                await context.close()
            del self.sessions[session_id]

    def _cleanup_expired_sessions(self):
        current_time = time.time()
        expired_sessions = [
            sid for sid, (_, _, last_used) in self.sessions.items() 
            if current_time - last_used > self.session_ttl
        ]
        for sid in expired_sessions:
            asyncio.create_task(self.kill_session(sid))
            
    async def smart_wait(self, page: Page, wait_for: str, timeout: float = 30000):
        wait_for = wait_for.strip()
        
        if wait_for.startswith('js:'):
            # Explicitly specified JavaScript
            js_code = wait_for[3:].strip()
            return await self.csp_compliant_wait(page, js_code, timeout)
        elif wait_for.startswith('css:'):
            # Explicitly specified CSS selector
            css_selector = wait_for[4:].strip()
            try:
                await page.wait_for_selector(css_selector, timeout=timeout)
            except Error as e:
                if 'Timeout' in str(e):
                    raise TimeoutError(f"Timeout after {timeout}ms waiting for selector '{css_selector}'")
                else:
                    raise ValueError(f"Invalid CSS selector: '{css_selector}'")
        else:
            # Auto-detect based on content
            if wait_for.startswith('()') or wait_for.startswith('function'):
                # It's likely a JavaScript function
                return await self.csp_compliant_wait(page, wait_for, timeout)
            else:
                # Assume it's a CSS selector first
                try:
                    await page.wait_for_selector(wait_for, timeout=timeout)
                except Error as e:
                    if 'Timeout' in str(e):
                        raise TimeoutError(f"Timeout after {timeout}ms waiting for selector '{wait_for}'")
                    else:
                        # If it's not a timeout error, it might be an invalid selector
                        # Let's try to evaluate it as a JavaScript function as a fallback
                        try:
                            return await self.csp_compliant_wait(page, f"() => {{{wait_for}}}", timeout)
                        except Error:
                            raise ValueError(f"Invalid wait_for parameter: '{wait_for}'. "
                                             "It should be either a valid CSS selector, a JavaScript function, "
                                             "or explicitly prefixed with 'js:' or 'css:'.")
    
    async def csp_compliant_wait(self, page: Page, user_wait_function: str, timeout: float = 30000):
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
        iframes = await page.query_selector_all('iframe')
        
        for i, iframe in enumerate(iframes):
            try:
                # Add a unique identifier to the iframe
                await iframe.evaluate(f'(element) => element.id = "iframe-{i}"')
                
                # Get the frame associated with this iframe
                frame = await iframe.content_frame()
                
                if frame:
                    # Wait for the frame to load
                    await frame.wait_for_load_state('load', timeout=30000)  # 30 seconds timeout
                    
                    # Extract the content of the iframe's body
                    iframe_content = await frame.evaluate('() => document.body.innerHTML')
                    
                    # Generate a unique class name for this iframe
                    class_name = f'extracted-iframe-content-{i}'
                    
                    # Replace the iframe with a div containing the extracted content
                    _iframe = iframe_content.replace('`', '\\`')
                    await page.evaluate(f"""
                        () => {{
                            const iframe = document.getElementById('iframe-{i}');
                            const div = document.createElement('div');
                            div.innerHTML = `{_iframe}`;
                            div.className = '{class_name}';
                            iframe.replaceWith(div);
                        }}
                    """)
                else:
                    # print(f"Warning: Could not access content frame for iframe {i}")
                    self.logger.warning(
                        message="Could not access content frame for iframe {index}",
                        tag="SCRAPE",
                        params={"index": i}
                    )                    
            except Exception as e:
                self.logger.error(
                    message="Error processing iframe {index}: {error}",
                    tag="ERROR",
                    params={"index": i, "error": str(e)}
                )                
                # print(f"Error processing iframe {i}: {str(e)}")

        # Return the page object
        return page  
    
    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
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
        response_headers = {}
        status_code = 200  # Default to 200 for local/raw HTML
        screenshot_requested = kwargs.get('screenshot', False)
        screenshot_data = None

        if url.startswith(('http://', 'https://')):
            # Proceed with standard web crawling
            return await self._crawl_web(url, **kwargs)

        elif url.startswith('file://'):
            # Process local file
            local_file_path = url[7:]  # Remove 'file://' prefix
            if not os.path.exists(local_file_path):
                raise FileNotFoundError(f"Local file not found: {local_file_path}")
            with open(local_file_path, 'r', encoding='utf-8') as f:
                html = f.read()
            if screenshot_requested:
                screenshot_data = await self._generate_screenshot_from_html(html)
            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                status_code=status_code,
                screenshot=screenshot_data,
                get_delayed_content=None
            )

        elif url.startswith('raw:'):
            # Process raw HTML content
            raw_html = url[4:]  # Remove 'raw:' prefix
            html = raw_html
            if screenshot_requested:
                screenshot_data = await self._generate_screenshot_from_html(html)
            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                status_code=status_code,
                screenshot=screenshot_data,
                get_delayed_content=None
            )
        else:
            raise ValueError("URL must start with 'http://', 'https://', 'file://', or 'raw:'")


    async def _crawl_web(self, url: str, **kwargs) -> AsyncCrawlResponse:
        """
        Existing web crawling logic remains unchanged.

        Args:
            url (str): The web URL to crawl.
            **kwargs: Additional parameters.

        Returns:
            AsyncCrawlResponse: The response containing HTML, headers, status code, and optional screenshot.
        """
        response_headers = {}
        status_code = None
        
        # Reset downloaded files list for new crawl
        self._downloaded_files = []
        
        self._cleanup_expired_sessions()
        session_id = kwargs.get("session_id")
        
        # Handle page creation differently for managed browser
        context = None
        if self.use_managed_browser:
            if session_id:
                # Reuse existing session if available
                context, page, _ = self.sessions.get(session_id, (None, None, None))
                if not page:
                    # Create new page in default context if session doesn't exist
                    page = await self.default_context.new_page()
                    self.sessions[session_id] = (self.default_context, page, time.time())
            else:
                # Create new page in default context for non-session requests
                page = await self.default_context.new_page()
        else:
            if session_id:
                context, page, _ = self.sessions.get(session_id, (None, None, None))
                if not context:
                    if self.use_persistent_context and self.browser_type in ["chrome", "chromium"]:
                        # In persistent context, browser is the context
                        context = self.browser
                        page = await context.new_page()
                    else:
                        # Normal context creation for non-persistent or non-Chrome browsers
                        context = await self.browser.new_context(
                            user_agent=self.user_agent,
                            viewport={"width": 1200, "height": 800},
                            proxy={"server": self.proxy} if self.proxy else None,
                            java_script_enabled=True,
                            accept_downloads=self.accept_downloads,
                            # downloads_path=self.downloads_path if self.accept_downloads else None
                        )
                        await context.add_cookies([{"name": "cookiesEnabled", "value": "true", "url": url}])
                        if self.cookies:
                            await context.add_cookies(self.cookies)
                        await context.set_extra_http_headers(self.headers)
                        page = await context.new_page()
                    self.sessions[session_id] = (context, page, time.time())
            else:
                if self.use_persistent_context and self.browser_type in ["chrome", "chromium"]:
                    # In persistent context, browser is the context
                    context = self.browser
                else:
                    # Normal context creation
                    context = await self.browser.new_context(
                        user_agent=self.user_agent,
                        viewport={"width": 1920, "height": 1080},
                        proxy={"server": self.proxy} if self.proxy else None,
                        accept_downloads=self.accept_downloads,
                    )
                    if self.cookies:
                            await context.add_cookies(self.cookies)
                    await context.set_extra_http_headers(self.headers)
                
                if kwargs.get("override_navigator", False) or kwargs.get("simulate_user", False) or kwargs.get("magic", False):
                    # Inject scripts to override navigator properties
                    await context.add_init_script("""
                        // Pass the Permissions Test.
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        window.navigator.chrome = {
                            runtime: {},
                            // Add other properties if necessary
                        };
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5],
                        });
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en'],
                        });
                        Object.defineProperty(document, 'hidden', {
                            get: () => false
                        });
                        Object.defineProperty(document, 'visibilityState', {
                            get: () => 'visible'
                        });
                    """)
                
                page = await context.new_page()
                if kwargs.get("magic", False):
                    await stealth_async(page, stealth_config)

        # Add console message and error logging
        if kwargs.get("log_console", False):
            page.on("console", lambda msg: print(f"Console: {msg.text}"))
            page.on("pageerror", lambda exc: print(f"Page Error: {exc}"))
        
        try:
            # Set up download handling if enabled
            if self.accept_downloads:
                page.on("download", lambda download: asyncio.create_task(self._handle_download(download)))

            # if self.verbose:
            #     print(f"[LOG] 🕸️ Crawling {url} using AsyncPlaywrightCrawlerStrategy...")

            if self.use_cached_html:
                cache_file_path = os.path.join(
                    os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home()), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest()
                )
                if os.path.exists(cache_file_path):
                    html = ""
                    with open(cache_file_path, "r") as f:
                        html = f.read()
                    # retrieve response headers and status code from cache
                    with open(cache_file_path + ".meta", "r") as f:
                        meta = json.load(f)
                        response_headers = meta.get("response_headers", {})
                        status_code = meta.get("status_code")
                    response = AsyncCrawlResponse(
                        html=html, response_headers=response_headers, status_code=status_code
                    )
                    return response

            if not kwargs.get("js_only", False):
                await self.execute_hook('before_goto', page, context = context)
                

                try:
                    response = await page.goto(
                        url,
                        # wait_until=kwargs.get("wait_until", ["domcontentloaded", "networkidle"]),
                        wait_until=kwargs.get("wait_until", "domcontentloaded"),
                        timeout=kwargs.get("page_timeout", 60000),
                    )
                except Error as e:
                    raise RuntimeError(f"Failed on navigating ACS-GOTO :\n{str(e)}")
                
                # response = await page.goto("about:blank")
                # await page.evaluate(f"window.location.href = '{url}'")
                
                await self.execute_hook('after_goto', page, context = context)
                
                # Get status code and headers
                status_code = response.status
                response_headers = response.headers
            else:
                status_code = 200
                response_headers = {}

            # Replace the current wait_for_selector line with this more robust check:
            try:
                # First wait for body to exist, regardless of visibility
                await page.wait_for_selector('body', state='attached', timeout=30000)
                
                # Then wait for it to become visible by checking CSS
                await page.wait_for_function("""
                    () => {
                        const body = document.body;
                        const style = window.getComputedStyle(body);
                        return style.display !== 'none' && 
                            style.visibility !== 'hidden' && 
                            style.opacity !== '0';
                    }
                """, timeout=30000)
                
            except Error as e:
                # If waiting fails, let's try to diagnose the issue
                visibility_info = await page.evaluate("""
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
                """)
                
                if self.verbose:
                    print(f"Body visibility debug info: {visibility_info}")
                
                # Even if body is hidden, we might still want to proceed
                if kwargs.get('ignore_body_visibility', True):
                    if self.verbose:
                        print("Proceeding despite hidden body...")
                    pass
                else:
                    raise Error(f"Body element is hidden: {visibility_info}")
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            js_code = kwargs.get("js_code", kwargs.get("js", self.js_code))
            if js_code:
                if isinstance(js_code, str):
                    await page.evaluate(js_code)
                elif isinstance(js_code, list):
                    for js in js_code:
                        await page.evaluate(js)
                
                # await page.wait_for_timeout(100)
                
                # Check for on execution event
                await self.execute_hook('on_execution_started', page, context = context)
                
            if kwargs.get("simulate_user", False) or kwargs.get("magic", False):
                # Simulate user interactions
                await page.mouse.move(100, 100)
                await page.mouse.down()
                await page.mouse.up()
                await page.keyboard.press('ArrowDown')

            # Handle the wait_for parameter
            wait_for = kwargs.get("wait_for")
            if wait_for:
                try:
                    await self.smart_wait(page, wait_for, timeout=kwargs.get("page_timeout", 60000))
                except Exception as e:
                    raise RuntimeError(f"Wait condition failed: {str(e)}")
            
            # if not wait_for and js_code:
            #     await page.wait_for_load_state('networkidle', timeout=5000)

            # Update image dimensions
            update_image_dimensions_js = """
            () => {
                return new Promise((resolve) => {
                    const filterImage = (img) => {
                        // Filter out images that are too small
                        if (img.width < 100 && img.height < 100) return false;
                        
                        // Filter out images that are not visible
                        const rect = img.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) return false;
                        
                        // Filter out images with certain class names (e.g., icons, thumbnails)
                        if (img.classList.contains('icon') || img.classList.contains('thumbnail')) return false;
                        
                        // Filter out images with certain patterns in their src (e.g., placeholder images)
                        if (img.src.includes('placeholder') || img.src.includes('icon')) return false;
                        
                        return true;
                    };

                    const images = Array.from(document.querySelectorAll('img')).filter(filterImage);
                    let imagesLeft = images.length;
                    
                    if (imagesLeft === 0) {
                        resolve();
                        return;
                    }

                    const checkImage = (img) => {
                        if (img.complete && img.naturalWidth !== 0) {
                            img.setAttribute('width', img.naturalWidth);
                            img.setAttribute('height', img.naturalHeight);
                            imagesLeft--;
                            if (imagesLeft === 0) resolve();
                        }
                    };

                    images.forEach(img => {
                        checkImage(img);
                        if (!img.complete) {
                            img.onload = () => {
                                checkImage(img);
                            };
                            img.onerror = () => {
                                imagesLeft--;
                                if (imagesLeft === 0) resolve();
                            };
                        }
                    });

                    // Fallback timeout of 5 seconds
                    // setTimeout(() => resolve(), 5000);
                    resolve();
                });
            }
            """
            await page.evaluate(update_image_dimensions_js)

            # Wait a bit for any onload events to complete
            await page.wait_for_timeout(100)

            # Process iframes
            if kwargs.get("process_iframes", False):
                page = await self.process_iframes(page)
            
            await self.execute_hook('before_retrieve_html', page, context = context)
            # Check if delay_before_return_html is set then wait for that time
            delay_before_return_html = kwargs.get("delay_before_return_html")
            if delay_before_return_html:
                await asyncio.sleep(delay_before_return_html)
                
            # Check for remove_overlay_elements parameter
            if kwargs.get("remove_overlay_elements", False):
                await self.remove_overlay_elements(page)
            
            html = await page.content()
            await self.execute_hook('before_return_html', page, html, context = context)
            
            # Check if kwargs has screenshot=True then take screenshot
            screenshot_data = None
            if kwargs.get("screenshot"):
                # Check we have screenshot_wait_for parameter, if we have simply wait for that time
                screenshot_wait_for = kwargs.get("screenshot_wait_for")
                if screenshot_wait_for:
                    await asyncio.sleep(screenshot_wait_for)
                screenshot_data = await self.take_screenshot(page)          

            # if self.verbose:
            #     print(f"[LOG] ✅ Crawled {url} successfully!")
           
            if self.use_cached_html:
                cache_file_path = os.path.join(
                    os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home()), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest()
                )
                with open(cache_file_path, "w", encoding="utf-8") as f:
                    f.write(html)
                # store response headers and status code in cache
                with open(cache_file_path + ".meta", "w", encoding="utf-8") as f:
                    json.dump({
                        "response_headers": response_headers,
                        "status_code": status_code
                    }, f)

            async def get_delayed_content(delay: float = 5.0) -> str:
                if self.verbose:
                    print(f"[LOG] Waiting for {delay} seconds before retrieving content for {url}")
                await asyncio.sleep(delay)
                return await page.content()
                
            response = AsyncCrawlResponse(
                html=html, 
                response_headers=response_headers, 
                status_code=status_code,
                screenshot=screenshot_data,
                get_delayed_content=get_delayed_content,
                downloaded_files=self._downloaded_files if self._downloaded_files else None
            )
            return response
        except Error as e:
            raise Error(f"async_crawler_strategy.py:_crawleb(): {str(e)}")
        # finally:
        #     if not session_id:
        #         await page.close()
        #         await context.close()

    async def _handle_download(self, download):
        """Handle file downloads."""
        try:
            suggested_filename = download.suggested_filename
            download_path = os.path.join(self.downloads_path, suggested_filename)
            
            self.logger.info(
                message="Downloading {filename} to {path}",
                tag="FETCH",
                params={"filename": suggested_filename, "path": download_path}
            )
                
            start_time = time.perf_counter()
            await download.save_as(download_path)
            end_time = time.perf_counter()
            self._downloaded_files.append(download_path)

            self.logger.success(
                message="Downloaded {filename} successfully",
                tag="COMPLETE",
                params={"filename": suggested_filename, "path": download_path, "duration": f"{end_time - start_time:.2f}s"}
            )            
        except Exception as e:
            self.logger.error(
                message="Failed to handle download: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            
            # if self.verbose:
            #     print(f"[ERROR] Failed to handle download: {str(e)}")
    
    async def crawl_many(self, urls: List[str], **kwargs) -> List[AsyncCrawlResponse]:
        semaphore_count = kwargs.get('semaphore_count', 5)  # Adjust as needed
        semaphore = asyncio.Semaphore(semaphore_count)

        async def crawl_with_semaphore(url):
            async with semaphore:
                return await self.crawl(url, **kwargs)

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [result if not isinstance(result, Exception) else str(result) for result in results]

    async def remove_overlay_elements(self, page: Page) -> None:
        """
        Removes popup overlays, modals, cookie notices, and other intrusive elements from the page.
        
        Args:
            page (Page): The Playwright page instance
        """
        remove_overlays_js = """
        async () => {
            // Function to check if element is visible
            const isVisible = (elem) => {
                const style = window.getComputedStyle(elem);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       style.opacity !== '0';
            };

            // Common selectors for popups and overlays
            const commonSelectors = [
                // Close buttons first
                'button[class*="close" i]', 'button[class*="dismiss" i]', 
                'button[aria-label*="close" i]', 'button[title*="close" i]',
                'a[class*="close" i]', 'span[class*="close" i]',
                
                // Cookie notices
                '[class*="cookie-banner" i]', '[id*="cookie-banner" i]',
                '[class*="cookie-consent" i]', '[id*="cookie-consent" i]',
                
                // Newsletter/subscription dialogs
                '[class*="newsletter" i]', '[class*="subscribe" i]',
                
                // Generic popups/modals
                '[class*="popup" i]', '[class*="modal" i]', 
                '[class*="overlay" i]', '[class*="dialog" i]',
                '[role="dialog"]', '[role="alertdialog"]'
            ];

            // Try to click close buttons first
            for (const selector of commonSelectors.slice(0, 6)) {
                const closeButtons = document.querySelectorAll(selector);
                for (const button of closeButtons) {
                    if (isVisible(button)) {
                        try {
                            button.click();
                            await new Promise(resolve => setTimeout(resolve, 100));
                        } catch (e) {
                            console.log('Error clicking button:', e);
                        }
                    }
                }
            }

            // Remove remaining overlay elements
            const removeOverlays = () => {
                // Find elements with high z-index
                const allElements = document.querySelectorAll('*');
                for (const elem of allElements) {
                    const style = window.getComputedStyle(elem);
                    const zIndex = parseInt(style.zIndex);
                    const position = style.position;
                    
                    if (
                        isVisible(elem) && 
                        (zIndex > 999 || position === 'fixed' || position === 'absolute') &&
                        (
                            elem.offsetWidth > window.innerWidth * 0.5 ||
                            elem.offsetHeight > window.innerHeight * 0.5 ||
                            style.backgroundColor.includes('rgba') ||
                            parseFloat(style.opacity) < 1
                        )
                    ) {
                        elem.remove();
                    }
                }

                // Remove elements matching common selectors
                for (const selector of commonSelectors) {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(elem => {
                        if (isVisible(elem)) {
                            elem.remove();
                        }
                    });
                }
            };

            // Remove overlay elements
            removeOverlays();

            // Remove any fixed/sticky position elements at the top/bottom
            const removeFixedElements = () => {
                const elements = document.querySelectorAll('*');
                elements.forEach(elem => {
                    const style = window.getComputedStyle(elem);
                    if (
                        (style.position === 'fixed' || style.position === 'sticky') &&
                        isVisible(elem)
                    ) {
                        elem.remove();
                    }
                });
            };

            removeFixedElements();
            
            // Remove empty block elements as: div, p, span, etc.
            const removeEmptyBlockElements = () => {
                const blockElements = document.querySelectorAll('div, p, span, section, article, header, footer, aside, nav, main, ul, ol, li, dl, dt, dd, h1, h2, h3, h4, h5, h6');
                blockElements.forEach(elem => {
                    if (elem.innerText.trim() === '') {
                        elem.remove();
                    }
                });
            };

            // Remove margin-right and padding-right from body (often added by modal scripts)
            document.body.style.marginRight = '0px';
            document.body.style.paddingRight = '0px';
            document.body.style.overflow = 'auto';

            // Wait a bit for any animations to complete
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        """
        
        try:
            await page.evaluate(remove_overlays_js)
            await page.wait_for_timeout(500)  # Wait for any animations to complete
        except Exception as e:
            self.logger.warning(
                message="Failed to remove overlay elements: {error}",
                tag="SCRAPE",
                params={"error": str(e)}
            )            
            # if self.verbose:
            #     print(f"Warning: Failed to remove overlay elements: {str(e)}")

    async def take_screenshot(self, page: Page) -> str:
        """
        Takes a screenshot of the current page.
        
        Args:
            page (Page): The Playwright page instance
            
        Returns:
            str: Base64-encoded screenshot image
        """
        try:
            # The page is already loaded, just take the screenshot
            screenshot = await page.screenshot(full_page=True)
            return base64.b64encode(screenshot).decode('utf-8')
        except Exception as e:
            error_message = f"Failed to take screenshot: {str(e)}"
            self.logger.error(
                message="Screenshot failed: {error}",
                tag="ERROR",
                params={"error": error_message}
            )
            

            # Generate an error image
            img = Image.new('RGB', (800, 600), color='black')
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
            
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        finally:
            await page.close()
            
    async def _generate_screenshot_from_html(self, html: str) -> Optional[str]:
        """
        Generates a screenshot from raw HTML content.

        Args:
            html (str): The HTML content to render and capture.

        Returns:
            Optional[str]: Base64-encoded screenshot image or an error image if failed.
        """
        try:
            if not self.browser:
                await self.start()
            page = await self.browser.new_page()
            await page.set_content(html, wait_until='networkidle')
            screenshot = await page.screenshot(full_page=True)
            await page.close()
            return base64.b64encode(screenshot).decode('utf-8')
        except Exception as e:
            error_message = f"Failed to take screenshot: {str(e)}"
            # print(error_message)
            self.logger.error(
                message="Screenshot failed: {error}",
                tag="ERROR",
                params={"error": error_message}
            )            

            # Generate an error image
            img = Image.new('RGB', (800, 600), color='black')
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)

            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')

