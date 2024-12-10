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
from .utils import create_box_message
from .user_agent_generator import UserAgentGenerator
from .config import SCREENSHOT_HEIGHT_TRESHOLD
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
    "--use-mock-keychain"
]


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


class BrowserManager:
    def __init__(self, use_managed_browser: bool, user_data_dir: Optional[str], headless: bool, logger, browser_type: str, proxy, proxy_config, chrome_channel: str, viewport_width: int, viewport_height: int, accept_downloads: bool, storage_state, ignore_https_errors: bool, java_script_enabled: bool, cookies: List[dict], headers: dict, extra_args: List[str], text_only: bool, light_mode: bool, user_agent: str, browser_hint: str, downloads_path: Optional[str]):
        self.use_managed_browser = use_managed_browser
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.logger = logger
        self.browser_type = browser_type
        self.proxy = proxy
        self.proxy_config = proxy_config
        self.chrome_channel = chrome_channel
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.accept_downloads = accept_downloads
        self.storage_state = storage_state
        self.ignore_https_errors = ignore_https_errors
        self.java_script_enabled = java_script_enabled
        self.cookies = cookies or []
        self.headers = headers or {}
        self.extra_args = extra_args or []
        self.text_only = text_only
        self.light_mode = light_mode
        self.browser = None
        self.default_context : BrowserContext = None
        self.managed_browser = None
        self.sessions = {}
        self.session_ttl = 1800
        self.playwright = None
        self.user_agent = user_agent
        self.browser_hint = browser_hint
        self.downloads_path = downloads_path        

    async def start(self):
        if self.playwright is None:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()

        if self.use_managed_browser:
            self.managed_browser = ManagedBrowser(
                browser_type=self.browser_type,
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                logger=self.logger
            )
            cdp_url = await self.managed_browser.start()
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            contexts = self.browser.contexts
            if contexts:
                self.default_context = contexts[0]
            else:
                self.default_context = await self.browser.new_context(
                    viewport={"width": self.viewport_width, "height": self.viewport_height},
                    storage_state=self.storage_state,
                    user_agent=self.headers.get("User-Agent"),
                    accept_downloads=self.accept_downloads,
                    ignore_https_errors=self.ignore_https_errors,
                    java_script_enabled=self.java_script_enabled
                )
            await self.setup_context(self.default_context)
        else:
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
                    "--ignore-certificate-errors-spki-list",
                    "--disable-blink-features=AutomationControlled",
                    "--window-position=400,0",
                    f"--window-size={self.viewport_width},{self.viewport_height}",
                ]
            }

            if self.light_mode:
                browser_args["args"].extend(BROWSER_DISABLE_OPTIONS)

            if self.text_only:
                browser_args["args"].extend(['--blink-settings=imagesEnabled=false','--disable-remote-fonts'])

            if self.chrome_channel:
                browser_args["channel"] = self.chrome_channel

            if self.extra_args:
                browser_args["args"].extend(self.extra_args)

            if self.accept_downloads:
                browser_args["downloads_path"] = os.path.join(os.getcwd(), "downloads")
                os.makedirs(browser_args["downloads_path"], exist_ok=True)

            if self.proxy:
                from playwright.async_api import ProxySettings
                proxy_settings = ProxySettings(server=self.proxy)
                browser_args["proxy"] = proxy_settings
            elif self.proxy_config:
                from playwright.async_api import ProxySettings
                proxy_settings = ProxySettings(
                    server=self.proxy_config.get("server"),
                    username=self.proxy_config.get("username"),
                    password=self.proxy_config.get("password")
                )
                browser_args["proxy"] = proxy_settings

            if self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(**browser_args)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(**browser_args)
            else:
                self.browser = await self.playwright.chromium.launch(**browser_args)

            self.default_context = self.browser
            # Since default_context in non-managed mode is the browser, no setup needed here.


    async def setup_context(self, context : BrowserContext, is_default=False):
        # Set extra headers
        if self.headers:
            await context.set_extra_http_headers(self.headers)

        # Add cookies if any
        if self.cookies:
            await context.add_cookies(self.cookies)

        # Ensure storage_state if provided
        if self.storage_state:
            # If storage_state is a dictionary or file path, Playwright will handle it.
            await context.storage_state(path=None)

        # If accept_downloads, set timeouts and ensure properties
        if self.accept_downloads:
            await context.set_default_timeout(60000)
            await context.set_default_navigation_timeout(60000)
            if self.downloads_path:
                context._impl_obj._options["accept_downloads"] = True
                context._impl_obj._options["downloads_path"] = self.downloads_path

        # If we have a user_agent, override it along with sec-ch-ua
        if self.user_agent:
            # Merge headers if needed
            combined_headers = {"User-Agent": self.user_agent, "sec-ch-ua": self.browser_hint}
            combined_headers.update(self.headers)
            await context.set_extra_http_headers(combined_headers)
            
    async def close(self):
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

    async def get_page(self, session_id: Optional[str], user_agent: str):
        # Cleanup expired sessions
        self._cleanup_expired_sessions()

        if session_id:
            context, page, _ = self.sessions.get(session_id, (None, None, None))
            if context and page:
                self.sessions[session_id] = (context, page, time.time())
                return page, context

        # Create a new context/page pair
        if self.use_managed_browser:
            context = self.default_context
            page = await context.new_page()
        else:
            context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={"width": self.viewport_width, "height": self.viewport_height},
                proxy={"server": self.proxy} if self.proxy else None,
                accept_downloads=self.accept_downloads,
                storage_state=self.storage_state,
                ignore_https_errors=self.ignore_https_errors
            )
            await self.setup_context(context)
            page = await context.new_page()

        if session_id:
            self.sessions[session_id] = (context, page, time.time())

        return page, context

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

class AsyncCrawlerStrategy(ABC):
    @abstractmethod
    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
        pass # 4 + 3
    
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
        self.text_only = kwargs.get("text_only", False) 
        self.light_mode = kwargs.get("light_mode", False)
        self.logger = logger
        self.use_cached_html = use_cached_html
        self.viewport_width = kwargs.get("viewport_width", 800 if self.text_only else 1920)
        self.viewport_height = kwargs.get("viewport_height", 600 if self.text_only else 1080)   
        
        if self.text_only:
           self.extra_args = kwargs.get("extra_args", []) + [
               '--disable-images',
               '--disable-javascript',
               '--disable-gpu',
               '--disable-software-rasterizer',
               '--disable-dev-shm-usage'
           ]
             
        self.user_agent = kwargs.get(
            "user_agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.187 Safari/604.1 Edg/117.0.2045.47"
            # "Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
        )
        user_agenr_generator = UserAgentGenerator()
        if kwargs.get("user_agent_mode") == "random":
            self.user_agent = user_agenr_generator.generate(
                 **kwargs.get("user_agent_generator_config", {})
            )
        self.pdf = kwargs.get("pdf", False)  # New flag
        self.screenshot_requested = kwargs.get('screenshot', False)
        
        self.proxy = kwargs.get("proxy")
        self.proxy_config = kwargs.get("proxy_config")
        self.headless = kwargs.get("headless", True)
        self.browser_type = kwargs.get("browser_type", "chromium")
        self.headers = kwargs.get("headers", {})
        self.browser_hint = user_agenr_generator.generate_client_hints(self.user_agent)
        self.headers.setdefault("sec-ch-ua", self.browser_hint)
        self.cookies = kwargs.get("cookies", [])
        self.storage_state = kwargs.get("storage_state", None)
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
        if self.use_persistent_context:
            self.use_managed_browser = True
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
        self.ignore_https_errors = kwargs.get("ignore_https_errors", True)
        self.java_script_enabled = kwargs.get("java_script_enabled", True)
        self.accept_downloads = kwargs.get("accept_downloads", False)
        self.downloads_path = kwargs.get("downloads_path")
        self._downloaded_files = []  # Track downloaded files for current crawl
        if self.accept_downloads and not self.downloads_path:
            self.downloads_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(self.downloads_path, exist_ok=True)        

        self.browser_manager = BrowserManager(
            use_managed_browser=self.use_managed_browser,
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            logger=self.logger,
            browser_type=self.browser_type,
            proxy=self.proxy,
            proxy_config=self.proxy_config,
            chrome_channel=self.chrome_channel,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
            accept_downloads=self.accept_downloads,
            storage_state=self.storage_state,
            ignore_https_errors=self.ignore_https_errors,
            java_script_enabled=self.java_script_enabled,
            cookies=self.cookies,
            headers=self.headers,
            extra_args=self.extra_args,
            text_only=self.text_only,
            light_mode=self.light_mode,
            user_agent=self.user_agent,
            browser_hint=self.browser_hint,
            downloads_path=self.downloads_path            
        )        

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        await self.browser_manager.start()
        await self.execute_hook('on_browser_created', self.browser_manager.browser, context = self.browser_manager.default_context)
        
    async def close(self):
        if self.sleep_on_close:
            await asyncio.sleep(0.5)
            
        await self.browser_manager.close()

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
    
    async def create_session(self, **kwargs) -> str:
        """Creates a new browser session and returns its ID."""
        await self.start()
        
        session_id = kwargs.get('session_id') or str(uuid.uuid4())
        
        user_agent = kwargs.get("user_agent", self.user_agent)
        # Use browser_manager to get a fresh page & context assigned to this session_id
        page, context = await self.browser_manager.get_page(session_id, user_agent)
        return session_id
    
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
        screenshot_requested = kwargs.get("screenshot", self.screenshot_requested)
        pdf_requested = kwargs.get("pdf", self.pdf)
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
        response_headers = {}
        status_code = None
        
        screenshot_requested = kwargs.get("screenshot", self.screenshot_requested)
        pdf_requested = kwargs.get("pdf", self.pdf)
        
        # Reset downloaded files list for new crawl
        self._downloaded_files = []
        
        self._cleanup_expired_sessions()
        session_id = kwargs.get("session_id")
        
        # Check if in kwargs we have user_agent that will override the default user_agent
        user_agent = kwargs.get("user_agent", self.user_agent)
        
        # Generate random user agent if magic mode is enabled and user_agent_mode is not random
        if kwargs.get("user_agent_mode") != "random" and kwargs.get("magic", False):
            user_agent = UserAgentGenerator().generate(
                **kwargs.get("user_agent_generator_config", {})
            )
        
        # Handle page creation differently for managed browser
        page, context = await self.browser_manager.get_page(session_id, user_agent)
        await context.add_cookies([{"name": "cookiesEnabled", "value": "true", "url": url}])
        
        if kwargs.get("override_navigator", False) or kwargs.get("simulate_user", False) or kwargs.get("magic", False):
            # Inject scripts to override navigator properties
            await context.add_init_script(load_js_script("navigator_overrider"))
        
        # Add console message and error logging
        if kwargs.get("log_console", False):
            page.on("console", lambda msg: print(f"Console: {msg.text}"))
            page.on("pageerror", lambda exc: print(f"Page Error: {exc}"))
        
        try:
            # Set up download handling if enabled
            if self.accept_downloads:
                page.on("download", lambda download: asyncio.create_task(self._handle_download(download)))

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
                await self.execute_hook('before_goto', page, context = context, **kwargs)

                try:
                    response = await page.goto(
                        url,
                        # wait_until=kwargs.get("wait_until", ["domcontentloaded", "networkidle"]),
                        wait_until=kwargs.get("wait_until", "domcontentloaded"),
                        timeout=kwargs.get("page_timeout", 60000),
                    )
                except Error as e:
                    raise RuntimeError(f"Failed on navigating ACS-GOTO :\n{str(e)}")
                
                await self.execute_hook('after_goto', page, context = context, **kwargs)
                
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
            
            # CONTENT LOADING ASSURANCE
            if not self.text_only and (kwargs.get("wait_for_images", True) or kwargs.get("adjust_viewport_to_content", False)):
                # Wait for network idle after initial load and images to load
                # await page.wait_for_load_state("networkidle")
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(0.1)
                from playwright.async_api import TimeoutError as PlaywrightTimeoutError
                try:
                    await page.wait_for_function("Array.from(document.images).every(img => img.complete)", timeout=1000)
                # Check for TimeoutError and ignore it
                except PlaywrightTimeoutError:
                    pass
            
            # After initial load, adjust viewport to content size
            if not self.text_only and kwargs.get("adjust_viewport_to_content", False):
                try:                       
                    # Get actual page dimensions                        
                    page_width = await page.evaluate("document.documentElement.scrollWidth")
                    page_height = await page.evaluate("document.documentElement.scrollHeight")
                    
                    target_width = self.viewport_width
                    target_height = int(target_width * page_width / page_height * 0.95)
                    await page.set_viewport_size({"width": target_width, "height": target_height})

                    # Compute scale factor
                    # We want the entire page visible: the scale should make both width and height fit
                    scale = min(target_width / page_width, target_height / page_height)

                    # Now we call CDP to set metrics. 
                    # We tell Chrome that the "device" is page_width x page_height in size, 
                    # but we scale it down so everything fits within the real viewport.
                    cdp = await page.context.new_cdp_session(page)
                    await cdp.send('Emulation.setDeviceMetricsOverride', {
                        'width': page_width,          # full page width
                        'height': page_height,        # full page height
                        'deviceScaleFactor': 1,       # keep normal DPR
                        'mobile': False,
                        'scale': scale                # scale the entire rendered content
                    })
                                    
                except Exception as e:
                    self.logger.warning(
                        message="Failed to adjust viewport to content: {error}",
                        tag="VIEWPORT",
                        params={"error": str(e)}
                    )                
            
            # After viewport adjustment, handle page scanning if requested
            if kwargs.get("scan_full_page", False):
                try:
                    viewport_height = page.viewport_size.get("height", self.viewport_height)
                    current_position = viewport_height  # Start with one viewport height
                    scroll_delay = kwargs.get("scroll_delay", 0.2)
                    
                    # Initial scroll
                    await page.evaluate(f"window.scrollTo(0, {current_position})")
                    await asyncio.sleep(scroll_delay)
                    
                    # Get height after first scroll to account for any dynamic content
                    total_height = await page.evaluate("document.documentElement.scrollHeight")
                    
                    while current_position < total_height:
                        current_position = min(current_position + viewport_height, total_height)
                        await page.evaluate(f"window.scrollTo(0, {current_position})")
                        await asyncio.sleep(scroll_delay)
                        
                        # Check for dynamic content
                        new_height = await page.evaluate("document.documentElement.scrollHeight")
                        if new_height > total_height:
                            total_height = new_height
                    
                    # Scroll back to top
                    await page.evaluate("window.scrollTo(0, 0)")
                    
                except Exception as e:
                    self.logger.warning(
                        message="Failed to perform full page scan: {error}",
                        tag="PAGE_SCAN", 
                        params={"error": str(e)}
                    )
                else:
                    # Scroll to the bottom of the page
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
                await self.execute_hook('on_execution_started', page, context = context, **kwargs)
                
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
            if not self.text_only:
                update_image_dimensions_js = load_js_script("update_image_dimensions")
            
                try:
                    try:
                        await page.wait_for_load_state(
                            # state="load",
                            state="domcontentloaded",
                            timeout=5
                        )
                    except PlaywrightTimeoutError:
                        pass
                    await page.evaluate(update_image_dimensions_js)
                except Exception as e:
                    self.logger.error(
                        message="Error updating image dimensions ACS-UPDATE_IMAGE_DIMENSIONS_JS: {error}",
                        tag="ERROR",
                        params={"error": str(e)}
                    )
                    # raise RuntimeError(f"Error updating image dimensions ACS-UPDATE_IMAGE_DIMENSIONS_JS: {str(e)}")

            # Wait a bit for any onload events to complete
            # await page.wait_for_timeout(100)

            # Process iframes
            if kwargs.get("process_iframes", False):
                page = await self.process_iframes(page)
            
            await self.execute_hook('before_retrieve_html', page, context = context, **kwargs)
            # Check if delay_before_return_html is set then wait for that time
            delay_before_return_html = kwargs.get("delay_before_return_html", 0.1)
            if delay_before_return_html:
                await asyncio.sleep(delay_before_return_html)
                
            # Check for remove_overlay_elements parameter
            if kwargs.get("remove_overlay_elements", False):
                await self.remove_overlay_elements(page)
            
            html = await page.content()
            await self.execute_hook('before_return_html', page, html, context = context, **kwargs)
            
            start_export_time = time.perf_counter()
            pdf_data = None
            if pdf_requested:
                # Generate PDF once
                pdf_data = await self.export_pdf(page)            
            
            # Check if kwargs has screenshot=True then take screenshot
            screenshot_data = None
            if screenshot_requested: #kwargs.get("screenshot"):
                # Check we have screenshot_wait_for parameter, if we have simply wait for that time
                screenshot_wait_for = kwargs.get("screenshot_wait_for")
                if screenshot_wait_for:
                    await asyncio.sleep(screenshot_wait_for)
                
                screenshot_data = await self.take_screenshot(page, **kwargs)    
            end_export_time = time.perf_counter()
            if screenshot_data or pdf_data:
                self.logger.info(
                    message="Exporting PDF and taking screenshot took {duration:.2f}s",
                    tag="EXPORT",
                    params={"duration": end_export_time - start_export_time}
                )
           
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
                pdf_data=pdf_data,
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
        remove_overlays_js = load_js_script("remove_overlays")
    
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

    async def export_pdf(self, page: Page) -> bytes:
        """
        Exports the current page as a PDF.
        """
        pdf_data = await page.pdf(print_background=True)
        return pdf_data

    async def take_screenshot(self, page, **kwargs) -> str:
        page_height = await page.evaluate("document.documentElement.scrollHeight")
        if page_height < kwargs.get("screenshot_height_threshold", SCREENSHOT_HEIGHT_TRESHOLD):
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
            final_img = images[0].convert('RGB')
            buffered = BytesIO()
            final_img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            error_message = f"Failed to take PDF-based screenshot: {str(e)}"
            self.logger.error(
                message="PDF Screenshot failed: {error}",
                tag="ERROR",
                params={"error": error_message}
            )
            # Return error image as fallback
            img = Image.new('RGB', (800, 600), color='black')
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')

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
            large_viewport_height = min(page_height, kwargs.get("screenshot_height_threshold", SCREENSHOT_HEIGHT_TRESHOLD))
            await page.set_viewport_size({"width": page_width, "height": large_viewport_height})
            
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
                img = Image.open(BytesIO(seg_shot)).convert('RGB')
                segments.append(img)

            total_height = sum(img.height for img in segments)
            stitched = Image.new('RGB', (segments[0].width, total_height))
            offset = 0
            for img in segments:
                # stitched.paste(img, (0, offset))
                stitched.paste(img.convert('RGB'), (0, offset))
                offset += img.height

            buffered = BytesIO()
            stitched = stitched.convert('RGB')
            stitched.save(buffered, format="BMP", quality=85)
            encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')

            return encoded
        except Exception as e:
            error_message = f"Failed to take large viewport screenshot: {str(e)}"
            self.logger.error(
                message="Large viewport screenshot failed: {error}",
                tag="ERROR",
                params={"error": error_message}
            )
            # return error image
            img = Image.new('RGB', (800, 600), color='black')
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
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
                params={"path": path}
            )
            return state
        else:
            self.logger.warning(
                message="No default_context available to export storage state.",
                tag="WARNING"
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

