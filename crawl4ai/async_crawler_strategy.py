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
    def __init__(self, browser_type: str = "chromium", user_data_dir: Optional[str] = None, headless: bool = False):
        self.browser_type = browser_type
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.browser_process = None
        self.temp_dir = None
        self.debugging_port = 9222

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
            await asyncio.sleep(2)  # Give browser time to start
            return f"http://localhost:{self.debugging_port}"
        except Exception as e:
            await self.cleanup()
            raise Exception(f"Failed to start browser: {e}")

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
        if self.browser_process:
            try:
                self.browser_process.terminate()
                await asyncio.sleep(1)
                if self.browser_process.poll() is None:
                    self.browser_process.kill()
            except Exception as e:
                print(f"Error terminating browser: {e}")

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Error removing temporary directory: {e}")

class AsyncCrawlResponse(BaseModel):
    html: str
    response_headers: Dict[str, str]
    status_code: int
    screenshot: Optional[str] = None
    get_delayed_content: Optional[Callable[[Optional[float]], Awaitable[str]]] = None

    class Config:
        arbitrary_types_allowed = True

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
    def __init__(self, use_cached_html=False, js_code=None, **kwargs):
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
        self.sessions = {}
        self.session_ttl = 1800 
        self.js_code = js_code
        self.verbose = kwargs.get("verbose", False)
        self.playwright = None
        self.browser = None
        self.sleep_on_close = kwargs.get("sleep_on_close", False)
        self.use_managed_browser = kwargs.get("use_managed_browser", False)
        self.user_data_dir = kwargs.get("user_data_dir", None)
        self.managed_browser = None
        self.hooks = {
            'on_browser_created': None,
            'on_user_agent_updated': None,
            'on_execution_started': None,
            'before_goto': None,
            'after_goto': None,
            'before_return_html': None,
            'before_retrieve_html': None
        }

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
                    headless=self.headless
                )
                cdp_url = await self.managed_browser.start()
                self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            else:
                browser_args = {
                    "headless": self.headless,
                    "args": [
                        "--disable-gpu",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--window-position=0,0",
                        "--ignore-certificate-errors",
                        "--ignore-certificate-errors-spki-list",
                        # "--headless=new",  # Use the new headless mode
                    ]
                }
                
                # Add proxy settings if a proxy is specified
                if self.proxy:
                    proxy_settings = ProxySettings(server=self.proxy)
                    browser_args["proxy"] = proxy_settings
                elif self.proxy_config:
                    proxy_settings = ProxySettings(server=self.proxy_config.get("server"), username=self.proxy_config.get("username"), password=self.proxy_config.get("password"))
                    browser_args["proxy"] = proxy_settings
                    
                # Select the appropriate browser based on the browser_type
                if self.browser_type == "firefox":
                    self.browser = await self.playwright.firefox.launch(**browser_args)
                elif self.browser_type == "webkit":
                    self.browser = await self.playwright.webkit.launch(**browser_args)
                else:
                    self.browser = await self.playwright.chromium.launch(**browser_args)

            await self.execute_hook('on_browser_created', self.browser)

    async def close(self):
        if self.sleep_on_close:
            await asyncio.sleep(0.5)
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.managed_browser:
            await self.managed_browser.cleanup()
            self.managed_browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def __del__(self):
        if self.browser or self.playwright:
            asyncio.get_event_loop().run_until_complete(self.close())

    def set_hook(self, hook_type: str, hook: Callable):
        if hook_type in self.hooks:
            self.hooks[hook_type] = hook
        else:
            raise ValueError(f"Invalid hook type: {hook_type}")

    async def execute_hook(self, hook_type: str, *args):
        hook = self.hooks.get(hook_type)
        if hook:
            if asyncio.iscoroutinefunction(hook):
                return await hook(*args)
            else:
                return hook(*args)
        return args[0] if args else None

    def update_user_agent(self, user_agent: str):
        self.user_agent = user_agent

    def set_custom_headers(self, headers: Dict[str, str]):
        self.headers = headers

    async def kill_session(self, session_id: str):
        if session_id in self.sessions:
            context, page, _ = self.sessions[session_id]
            await page.close()
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
                    print(f"Warning: Could not access content frame for iframe {i}")
            except Exception as e:
                print(f"Error processing iframe {i}: {str(e)}")

        # Return the page object
        return page  
    
    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
        response_headers = {}
        status_code = None
        
        self._cleanup_expired_sessions()
        session_id = kwargs.get("session_id")
        if session_id:
            context, page, _ = self.sessions.get(session_id, (None, None, None))
            if not context:
                context = await self.browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1920, "height": 1080},
                    proxy={"server": self.proxy} if self.proxy else None,
                    accept_downloads=True,
                    java_script_enabled=True
                )
                await context.add_cookies([{"name": "cookiesEnabled", "value": "true", "url": url}])
                await context.set_extra_http_headers(self.headers)
                page = await context.new_page()
                self.sessions[session_id] = (context, page, time.time())
        else:
            context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
                proxy={"server": self.proxy} if self.proxy else None
            )
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
            # await stealth_async(page) #, stealth_config)

        # Add console message and error logging
        if kwargs.get("log_console", False):
            page.on("console", lambda msg: print(f"Console: {msg.text}"))
            page.on("pageerror", lambda exc: print(f"Page Error: {exc}"))
        
        try:
            if self.verbose:
                print(f"[LOG] 🕸️ Crawling {url} using AsyncPlaywrightCrawlerStrategy...")

            if self.use_cached_html:
                cache_file_path = os.path.join(
                    Path.home(), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest()
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
                await self.execute_hook('before_goto', page)
                
                response = await page.goto(
                    url, wait_until="domcontentloaded", timeout=kwargs.get("page_timeout", 60000)
                )
                
                # response = await page.goto("about:blank")
                # await page.evaluate(f"window.location.href = '{url}'")
                
                await self.execute_hook('after_goto', page)
                
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
                
                await page.wait_for_load_state('networkidle')
                # Check for on execution event
                await self.execute_hook('on_execution_started', page)
                
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
            
            await self.execute_hook('before_retrieve_html', page)
            # Check if delay_before_return_html is set then wait for that time
            delay_before_return_html = kwargs.get("delay_before_return_html")
            if delay_before_return_html:
                await asyncio.sleep(delay_before_return_html)
                
            # Check for remove_overlay_elements parameter
            if kwargs.get("remove_overlay_elements", False):
                await self.remove_overlay_elements(page)
            
            html = await page.content()
            await self.execute_hook('before_return_html', page, html)
            
            # Check if kwargs has screenshot=True then take screenshot
            screenshot_data = None
            if kwargs.get("screenshot"):
                # Check we have screenshot_wait_for parameter, if we have simply wait for that time
                screenshot_wait_for = kwargs.get("screenshot_wait_for")
                if screenshot_wait_for:
                    await asyncio.sleep(screenshot_wait_for)
                screenshot_data = await self.take_screenshot(page)          

            if self.verbose:
                print(f"[LOG] ✅ Crawled {url} successfully!")

            if self.use_cached_html:
                cache_file_path = os.path.join(
                    Path.home(), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest()
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
                get_delayed_content=get_delayed_content
            )
            return response
        except Error as e:
            raise Error(f"[ERROR] 🚫 crawl(): Failed to crawl {url}: {str(e)}")
        # finally:
        #     if not session_id:
        #         await page.close()
        #         await context.close()

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
            if self.verbose:
                print(f"Warning: Failed to remove overlay elements: {str(e)}")

    async def take_screenshot(self, page: Page) -> str:
        try:
            # The page is already loaded, just take the screenshot
            screenshot = await page.screenshot(full_page=True)
            return base64.b64encode(screenshot).decode('utf-8')
        except Exception as e:
            error_message = f"Failed to take screenshot: {str(e)}"
            print(error_message)

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

