from __future__ import annotations

import asyncio
import base64
import time
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, List, Union
from typing import Optional, AsyncGenerator, Final
import os
from playwright.async_api import Page, Error
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import hashlib
import uuid
from .js_snippet import load_js_script
from .models import AsyncCrawlResponse
from .config import SCREENSHOT_HEIGHT_TRESHOLD
from .async_configs import BrowserConfig, CrawlerRunConfig, HTTPCrawlerConfig
from .async_logger import AsyncLogger
from .ssl_certificate import SSLCertificate
from .user_agent_generator import ValidUAGenerator
from .browser_manager import BrowserManager
from .browser_adapter import BrowserAdapter, PlaywrightAdapter, UndetectedAdapter

import aiofiles
import aiohttp
import chardet
from aiohttp.client import ClientTimeout
from urllib.parse import urlparse
from types import MappingProxyType
import contextlib
from functools import partial

class AsyncCrawlerStrategy(ABC):
    """
    Abstract base class for crawler strategies.
    Subclasses must implement the crawl method.
    """

    @abstractmethod
    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
        pass  # 4 + 3

class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
    """
    Crawler strategy using Playwright.

    Attributes:
        browser_config (BrowserConfig): Configuration object containing browser settings.
        logger (AsyncLogger): Logger instance for recording events and errors.
        _downloaded_files (List[str]): List of downloaded file paths.
        hooks (Dict[str, Callable]): Dictionary of hooks for custom behavior.
        browser_manager (BrowserManager): Manager for browser creation and management.

        Methods:
            __init__(self, browser_config=None, logger=None, **kwargs):
                Initialize the AsyncPlaywrightCrawlerStrategy with a browser configuration.
            __aenter__(self):
                Start the browser and initialize the browser manager.
            __aexit__(self, exc_type, exc_val, exc_tb):
                Close the browser and clean up resources.
            start(self):
                Start the browser and initialize the browser manager.
            close(self):
                Close the browser and clean up resources.
            kill_session(self, session_id):
                Kill a browser session and clean up resources.
            crawl(self, url, **kwargs):
                Run the crawler for a single URL.

    """

    def __init__(
        self, browser_config: BrowserConfig = None, logger: AsyncLogger = None, browser_adapter: BrowserAdapter = None, **kwargs
    ):
        """
        Initialize the AsyncPlaywrightCrawlerStrategy with a browser configuration.

        Args:
            browser_config (BrowserConfig): Configuration object containing browser settings.
                                          If None, will be created from kwargs for backwards compatibility.
            logger: Logger instance for recording events and errors.
            browser_adapter (BrowserAdapter): Browser adapter for handling browser-specific operations.
                                           If None, defaults to PlaywrightAdapter.
            **kwargs: Additional arguments for backwards compatibility and extending functionality.
        """
        # Initialize browser config, either from provided object or kwargs
        self.browser_config = browser_config or BrowserConfig.from_kwargs(kwargs)
        self.logger = logger
        
        # Initialize browser adapter
        self.adapter = browser_adapter or PlaywrightAdapter()

        # Initialize session management
        self._downloaded_files = []

        # Initialize hooks system
        self.hooks = {
            "on_browser_created": None,
            "on_page_context_created": None,
            "on_user_agent_updated": None,
            "on_execution_started": None,
            "on_execution_ended": None,
            "before_goto": None,
            "after_goto": None,
            "before_return_html": None,
            "before_retrieve_html": None,
        }

        # Initialize browser manager with config
        self.browser_manager = BrowserManager(
            browser_config=self.browser_config, 
            logger=self.logger,
            use_undetected=isinstance(self.adapter, UndetectedAdapter)
        )

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """
        Start the browser and initialize the browser manager.
        """
        await self.browser_manager.start()
        await self.execute_hook(
            "on_browser_created",
            self.browser_manager.browser,
            context=self.browser_manager.default_context,
        )

    async def close(self):
        """
        Close the browser and clean up resources.
        """
        await self.browser_manager.close()
        # Explicitly reset the static Playwright instance
        BrowserManager._playwright_instance = None

    async def kill_session(self, session_id: str):
        """
        Kill a browser session and clean up resources.

        Args:
            session_id (str): The ID of the session to kill.

        Returns:
            None
        """
        # Log a warning message and no need kill session, in new version auto kill session
        self.logger.warning(
            message="Session auto-kill is enabled in the new version. No need to manually kill sessions.",
            tag="WARNING",
        )
        await self.browser_manager.kill_session(session_id)

    def set_hook(self, hook_type: str, hook: Callable):
        """
        Set a hook function for a specific hook type. Following are list of hook types:
        - on_browser_created: Called when a new browser instance is created.
        - on_page_context_created: Called when a new page context is created.
        - on_user_agent_updated: Called when the user agent is updated.
        - on_execution_started: Called when the execution starts.
        - before_goto: Called before a goto operation.
        - after_goto: Called after a goto operation.
        - before_return_html: Called before returning HTML content.
        - before_retrieve_html: Called before retrieving HTML content.

        All hooks except on_browser_created accepts a context and a page as arguments and **kwargs. However, on_browser_created accepts a browser and a context as arguments and **kwargs.

        Args:
            hook_type (str): The type of the hook.
            hook (Callable): The hook function to set.

        Returns:
            None
        """
        if hook_type in self.hooks:
            self.hooks[hook_type] = hook
        else:
            raise ValueError(f"Invalid hook type: {hook_type}")

    async def execute_hook(self, hook_type: str, *args, **kwargs):
        """
        Execute a hook function for a specific hook type.

        Args:
            hook_type (str): The type of the hook.
            *args: Variable length positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The return value of the hook function, if any.
        """
        hook = self.hooks.get(hook_type)
        if hook:
            if asyncio.iscoroutinefunction(hook):
                return await hook(*args, **kwargs)
            else:
                return hook(*args, **kwargs)
        return args[0] if args else None

    def update_user_agent(self, user_agent: str):
        """
        Update the user agent for the browser.

        Args:
            user_agent (str): The new user agent string.

        Returns:
            None
        """
        self.user_agent = user_agent

    def set_custom_headers(self, headers: Dict[str, str]):
        """
        Set custom headers for the browser.

        Args:
            headers (Dict[str, str]): A dictionary of headers to set.

        Returns:
            None
        """
        self.headers = headers

    async def smart_wait(self, page: Page, wait_for: str, timeout: float = 30000):
        """
        Wait for a condition in a smart way. This functions works as below:

        1. If wait_for starts with 'js:', it assumes it's a JavaScript function and waits for it to return true.
        2. If wait_for starts with 'css:', it assumes it's a CSS selector and waits for it to be present.
        3. Otherwise, it tries to evaluate wait_for as a JavaScript function and waits for it to return true.
        4. If it's not a JavaScript function, it assumes it's a CSS selector and waits for it to be present.

        This is a more advanced version of the wait_for parameter in CrawlerStrategy.crawl().
        Args:
            page: Playwright page object
            wait_for (str): The condition to wait for. Can be a CSS selector, a JavaScript function, or explicitly prefixed with 'js:' or 'css:'.
            timeout (float): Maximum time to wait in milliseconds

        Returns:
            None
        """
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
        """
        Wait for a condition in a CSP-compliant way.

        Args:
            page: Playwright page object
            user_wait_function: JavaScript function as string that returns boolean
            timeout: Maximum time to wait in milliseconds

        Returns:
            bool: True if condition was met, False if timed out

        Raises:
            RuntimeError: If there's an error evaluating the condition
        """
        wrapper_js = f"""
        async () => {{
            const userFunction = {user_wait_function};
            const startTime = Date.now();
            try {{
                while (true) {{
                    if (await userFunction()) {{
                        return true;
                    }}
                    if (Date.now() - startTime > {timeout}) {{
                        return false;  // Return false instead of throwing
                    }}
                    await new Promise(resolve => setTimeout(resolve, 100));
                }}
            }} catch (error) {{
                throw new Error(`Error evaluating condition: ${{error.message}}`);
            }}
        }}
        """

        try:
            result = await self.adapter.evaluate(page, wrapper_js)
            return result
        except Exception as e:
            if "Error evaluating condition" in str(e):
                raise RuntimeError(f"Failed to evaluate wait condition: {str(e)}")
            # For timeout or other cases, just return False
            return False

    async def process_iframes(self, page):
        """
        Process iframes on a page. This function will extract the content of each iframe and replace it with a div containing the extracted content.

        Args:
            page: Playwright page object

        Returns:
            Playwright page object
        """
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
                    await self.adapter.evaluate(page,
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
        """
        Creates a new browser session and returns its ID. A browse session is a unique openned page can be reused for multiple crawls.
        This function is asynchronous and returns a string representing the session ID.

        Args:
            **kwargs: Optional keyword arguments to configure the session.

        Returns:
            str: The session ID.
        """
        await self.start()

        session_id = kwargs.get("session_id") or str(uuid.uuid4())

        user_agent = kwargs.get("user_agent", self.user_agent)
        # Use browser_manager to get a fresh page & context assigned to this session_id
        page, context = await self.browser_manager.get_page(CrawlerRunConfig(
            session_id=session_id,
            user_agent=user_agent,
            **kwargs,
        ))
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
                - 'raw://': Raw HTML content to process.
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

        if url.startswith(("http://", "https://", "view-source:")):
            return await self._crawl_web(url, config)

        elif url.startswith("file://"):
            # initialize empty lists for console messages
            captured_console = []
            
            # Process local file
            local_file_path = url[7:]  # Remove 'file://' prefix
            if not os.path.exists(local_file_path):
                raise FileNotFoundError(f"Local file not found: {local_file_path}")
            with open(local_file_path, "r", encoding="utf-8") as f:
                html = f.read()
            if config.screenshot:
                screenshot_data = await self._generate_screenshot_from_html(html)
            if config.capture_console_messages:
                page, context = await self.browser_manager.get_page(crawlerRunConfig=config)
                captured_console = await self._capture_console_messages(page, url)

            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                status_code=status_code,
                screenshot=screenshot_data,
                get_delayed_content=None,
                console_messages=captured_console,
            )

        ##### 
        # Since both "raw:" and "raw://" start with "raw:", the first condition is always true for both, so "raw://" will be sliced as "//...", which is incorrect.
        # Fix: Check for "raw://" first, then "raw:"
        # Also, the prefix "raw://" is actually 6 characters long, not 7, so it should be sliced accordingly: url[6:]
        #####
        elif url.startswith("raw://") or url.startswith("raw:"):
            # Process raw HTML content
            # raw_html = url[4:] if url[:4] == "raw:" else url[7:]
            raw_html = url[6:] if url.startswith("raw://") else url[4:]
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
        Includes optional network and console capturing.

        Args:
            url (str): The web URL to crawl
            config (CrawlerRunConfig): Configuration object controlling the crawl behavior

        Returns:
            AsyncCrawlResponse: The response containing HTML, headers, status code, and optional data
        """
        config.url = url
        response_headers = {}
        execution_result = None
        status_code = None
        redirected_url = url 

        # Reset downloaded files list for new crawl
        self._downloaded_files = []
        
        # Initialize capture lists
        captured_requests = []
        captured_console = []

        # Handle user agent with magic mode
        user_agent_to_override = config.user_agent
        if user_agent_to_override:
            self.browser_config.user_agent = user_agent_to_override
        elif config.magic or config.user_agent_mode == "random":
            self.browser_config.user_agent = ValidUAGenerator().generate(
                **(config.user_agent_generator_config or {})
            )

        # Get page for session
        page, context = await self.browser_manager.get_page(crawlerRunConfig=config)

        # await page.goto(URL)

        # Add default cookie
        # await context.add_cookies(
        #     [{"name": "cookiesEnabled", "value": "true", "url": url}]
        # )

        # Handle navigator overrides
        if config.override_navigator or config.simulate_user or config.magic:
            await context.add_init_script(load_js_script("navigator_overrider"))

        # Call hook after page creation
        await self.execute_hook("on_page_context_created", page, context=context, config=config)

        # Network Request Capturing
        if config.capture_network_requests:
            async def handle_request_capture(request):
                try:
                    post_data_str = None
                    try:
                        # Be cautious with large post data
                        post_data = request.post_data_buffer
                        if post_data:
                             # Attempt to decode, fallback to base64 or size indication
                             try:
                                 post_data_str = post_data.decode('utf-8', errors='replace')
                             except UnicodeDecodeError:
                                 post_data_str = f"[Binary data: {len(post_data)} bytes]"
                    except Exception:
                        post_data_str = "[Error retrieving post data]"

                    captured_requests.append({
                        "event_type": "request",
                        "url": request.url,
                        "method": request.method,
                        "headers": dict(request.headers), # Convert Header dict
                        "post_data": post_data_str,
                        "resource_type": request.resource_type,
                        "is_navigation_request": request.is_navigation_request(),
                        "timestamp": time.time()
                    })
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error capturing request details for {request.url}: {e}", tag="CAPTURE")
                    captured_requests.append({"event_type": "request_capture_error", "url": request.url, "error": str(e), "timestamp": time.time()})

            async def handle_response_capture(response):
                try:
                    try:
                        # body = await response.body()
                        # json_body = await response.json()
                        text_body = await response.text()
                    except Exception as e:
                        body = None
                        # json_body = None
                        # text_body = None
                    captured_requests.append({
                        "event_type": "response",
                        "url": response.url,
                        "status": response.status,
                        "status_text": response.status_text,
                        "headers": dict(response.headers), # Convert Header dict
                        "from_service_worker": response.from_service_worker,
                        "request_timing": response.request.timing, # Detailed timing info
                        "timestamp": time.time(),
                        "body" : {
                            # "raw": body,
                            # "json": json_body,
                            "text": text_body
                        }
                    })
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error capturing response details for {response.url}: {e}", tag="CAPTURE")
                    captured_requests.append({"event_type": "response_capture_error", "url": response.url, "error": str(e), "timestamp": time.time()})

            async def handle_request_failed_capture(request):
                 try:
                    captured_requests.append({
                        "event_type": "request_failed",
                        "url": request.url,
                        "method": request.method,
                        "resource_type": request.resource_type,
                        "failure_text": str(request.failure) if request.failure else "Unknown failure",
                        "timestamp": time.time()
                    })
                 except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error capturing request failed details for {request.url}: {e}", tag="CAPTURE")
                    captured_requests.append({"event_type": "request_failed_capture_error", "url": request.url, "error": str(e), "timestamp": time.time()})

            page.on("request", handle_request_capture)
            page.on("response", handle_response_capture)
            page.on("requestfailed", handle_request_failed_capture)

        # Console Message Capturing
        handle_console = None
        handle_error = None
        if config.capture_console_messages:
            # Set up console capture using adapter
            handle_console = await self.adapter.setup_console_capture(page, captured_console)
            handle_error = await self.adapter.setup_error_capture(page, captured_console)

        # Set up console logging if requested
        # Note: For undetected browsers, console logging won't work directly
        # but captured messages can still be logged after retrieval

        try:
            # Get SSL certificate information if requested and URL is HTTPS
            ssl_cert = None
            if config.fetch_ssl_certificate:
                ssl_cert = SSLCertificate.from_url(url)

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
                await self.execute_hook("before_goto", page, context=context, url=url, config=config)

                try:
                    # Generate a unique nonce for this request
                    if config.experimental.get("use_csp_nonce", False):
                        nonce = hashlib.sha256(os.urandom(32)).hexdigest()

                        # Add CSP headers to the request
                        await page.set_extra_http_headers(
                            {
                                "Content-Security-Policy": f"default-src 'self'; script-src 'self' 'nonce-{nonce}' 'strict-dynamic'"
                            }
                        )

                    response = await page.goto(
                        url, wait_until=config.wait_until, timeout=config.page_timeout
                    )
                    redirected_url = page.url
                except Error as e:
                    # Allow navigation to be aborted when downloading files
                    # This is expected behavior for downloads in some browser engines
                    if 'net::ERR_ABORTED' in str(e) and self.browser_config.accept_downloads:
                        self.logger.info(
                            message=f"Navigation aborted, likely due to file download: {url}",
                            tag="GOTO",
                            params={"url": url},
                        )
                        response = None
                    else:
                        raise RuntimeError(f"Failed on navigating ACS-GOTO:\n{str(e)}")

                await self.execute_hook(
                    "after_goto", page, context=context, url=url, response=response, config=config
                )

                # ──────────────────────────────────────────────────────────────
                # Walk the redirect chain.  Playwright returns only the last
                # hop, so we trace the `request.redirected_from` links until the
                # first response that differs from the final one and surface its
                # status-code.
                # ──────────────────────────────────────────────────────────────
                if response is None:
                    status_code = 200
                    response_headers = {}
                else:
                    first_resp = response
                    req = response.request
                    while req and req.redirected_from:
                        prev_req = req.redirected_from
                        prev_resp = await prev_req.response()
                        if prev_resp:                       # keep earliest
                            first_resp = prev_resp
                        req = prev_req
                
                    status_code = first_resp.status
                    response_headers = first_resp.headers
                # if response is None:
                #     status_code = 200
                #     response_headers = {}
                # else:
                #     status_code = response.status
                #     response_headers = response.headers

            else:
                status_code = 200
                response_headers = {}

            # Wait for body element and visibility
            try:
                await page.wait_for_selector("body", state="attached", timeout=30000)

                # Use the new check_visibility function with csp_compliant_wait
                is_visible = await self.csp_compliant_wait(
                    page,
                    """() => {
                        const element = document.body;
                        if (!element) return false;
                        const style = window.getComputedStyle(element);
                        const isVisible = style.display !== 'none' && 
                                        style.visibility !== 'hidden' && 
                                        style.opacity !== '0';
                        return isVisible;
                    }""",
                    timeout=30000,
                )

                if not is_visible and not config.ignore_body_visibility:
                    visibility_info = await self.check_visibility(page)
                    raise Error(f"Body element is hidden: {visibility_info}")

            except Error:
                visibility_info = await self.check_visibility(page)

                if self.browser_config.verbose:
                    self.logger.debug(
                        message="Body visibility info: {info}",
                        tag="DEBUG",
                        params={"info": visibility_info},
                    )

                if not config.ignore_body_visibility:
                    raise Error(f"Body element is hidden: {visibility_info}")

            # try:
            #     await page.wait_for_selector("body", state="attached", timeout=30000)

            #     await page.wait_for_function(
            #         """
            #         () => {
            #             const body = document.body;
            #             const style = window.getComputedStyle(body);
            #             return style.display !== 'none' &&
            #                 style.visibility !== 'hidden' &&
            #                 style.opacity !== '0';
            #         }
            #     """,
            #         timeout=30000,
            #     )
            # except Error as e:
            #     visibility_info = await page.evaluate(
            #         """
            #         () => {
            #             const body = document.body;
            #             const style = window.getComputedStyle(body);
            #             return {
            #                 display: style.display,
            #                 visibility: style.visibility,
            #                 opacity: style.opacity,
            #                 hasContent: body.innerHTML.length,
            #                 classList: Array.from(body.classList)
            #             }
            #         }
            #     """
            #     )

            #     if self.config.verbose:
            #         self.logger.debug(
            #             message="Body visibility info: {info}",
            #             tag="DEBUG",
            #             params={"info": visibility_info},
            #         )

            #     if not config.ignore_body_visibility:
            #         raise Error(f"Body element is hidden: {visibility_info}")

            # Handle content loading and viewport adjustment
            if not self.browser_config.text_mode and (
                config.wait_for_images or config.adjust_viewport_to_content
            ):
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(0.1)

                # Check for image loading with improved error handling
                images_loaded = await self.csp_compliant_wait(
                    page,
                    "() => Array.from(document.getElementsByTagName('img')).every(img => img.complete)",
                    timeout=1000,
                )

                if not images_loaded and self.logger:
                    self.logger.warning(
                        message="Some images failed to load within timeout",
                        tag="SCRAPE",
                    )

            # Adjust viewport if needed
            if not self.browser_config.text_mode and config.adjust_viewport_to_content:
                try:
                    dimensions = await self.get_page_dimensions(page)
                    page_height = dimensions["height"]
                    page_width = dimensions["width"]
                    # page_width = await page.evaluate(
                    #     "document.documentElement.scrollWidth"
                    # )
                    # page_height = await page.evaluate(
                    #     "document.documentElement.scrollHeight"
                    # )

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
                # await self._handle_full_page_scan(page, config.scroll_delay)
                await self._handle_full_page_scan(page, config.scroll_delay, config.max_scroll_steps)

            # Handle virtual scroll if configured
            if config.virtual_scroll_config:
                await self._handle_virtual_scroll(page, config.virtual_scroll_config)

            # Execute JavaScript if provided
            # if config.js_code:
            #     if isinstance(config.js_code, str):
            #         await page.evaluate(config.js_code)
            #     elif isinstance(config.js_code, list):
            #         for js in config.js_code:
            #             await page.evaluate(js)

            if config.js_code:
                # execution_result = await self.execute_user_script(page, config.js_code)
                execution_result = await self.robust_execute_user_script(
                    page, config.js_code
                )

                if not execution_result["success"]:
                    self.logger.warning(
                        message="User script execution had issues: {error}",
                        tag="JS_EXEC",
                        params={"error": execution_result.get("error")},
                    )

                await self.execute_hook("on_execution_started", page, context=context, config=config)
                await self.execute_hook("on_execution_ended", page, context=context, config=config, result=execution_result)

            # Handle user simulation
            if config.simulate_user or config.magic:
                await page.mouse.move(100, 100)
                await page.mouse.down()
                await page.mouse.up()
                await page.keyboard.press("ArrowDown")

            # Handle wait_for condition
            # Todo: Decide how to handle this
            if not config.wait_for and config.css_selector and False:
            # if not config.wait_for and config.css_selector:
                config.wait_for = f"css:{config.css_selector}"

            if config.wait_for:
                try:
                    # Use wait_for_timeout if specified, otherwise fall back to page_timeout
                    timeout = config.wait_for_timeout if config.wait_for_timeout is not None else config.page_timeout
                    await self.smart_wait(
                        page, config.wait_for, timeout=timeout
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
                    await self.adapter.evaluate(page, update_image_dimensions_js)
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
            await self.execute_hook("before_retrieve_html", page, context=context, config=config)
            if config.delay_before_return_html:
                await asyncio.sleep(config.delay_before_return_html)

            # Handle overlay removal
            if config.remove_overlay_elements:
                await self.remove_overlay_elements(page)

            if config.css_selector:
                try:
                    # Handle comma-separated selectors by splitting them
                    selectors = [s.strip() for s in config.css_selector.split(',')]
                    html_parts = []
                    
                    for selector in selectors:
                        try:
                            content = await self.adapter.evaluate(page,
                                f"""Array.from(document.querySelectorAll("{selector}"))
                                    .map(el => el.outerHTML)
                                    .join('')"""
                            )
                            html_parts.append(content)
                        except Error as e:
                            print(f"Warning: Could not get content for selector '{selector}': {str(e)}")
                    
                    # Wrap in a div to create a valid HTML structure
                    html = f"<div class='crawl4ai-result'>\n" + "\n".join(html_parts) + "\n</div>"                    
                except Error as e:
                    raise RuntimeError(f"Failed to extract HTML content: {str(e)}")
            else:
                html = await page.content()
            
            # # Get final HTML content
            # html = await page.content()
            await self.execute_hook(
                "before_return_html", page=page, html=html, context=context, config=config
            )

            # Handle PDF, MHTML and screenshot generation
            start_export_time = time.perf_counter()
            pdf_data = None
            screenshot_data = None
            mhtml_data = None

            if config.pdf:
                pdf_data = await self.export_pdf(page)

            if config.capture_mhtml:
                mhtml_data = await self.capture_mhtml(page)

            if config.screenshot:
                if config.screenshot_wait_for:
                    await asyncio.sleep(config.screenshot_wait_for)
                screenshot_data = await self.take_screenshot(
                    page, screenshot_height_threshold=config.screenshot_height_threshold
                )

            if screenshot_data or pdf_data or mhtml_data:
                self.logger.info(
                    message="Exporting media (PDF/MHTML/screenshot) took {duration:.2f}s",
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

            # For undetected browsers, retrieve console messages before returning
            if config.capture_console_messages and hasattr(self.adapter, 'retrieve_console_messages'):
                final_messages = await self.adapter.retrieve_console_messages(page)
                captured_console.extend(final_messages)

            # Return complete response
            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                js_execution_result=execution_result,
                status_code=status_code,
                screenshot=screenshot_data,
                pdf_data=pdf_data,
                mhtml_data=mhtml_data,
                get_delayed_content=get_delayed_content,
                ssl_certificate=ssl_cert,
                downloaded_files=(
                    self._downloaded_files if self._downloaded_files else None
                ),
                redirected_url=redirected_url,
                # Include captured data if enabled
                network_requests=captured_requests if config.capture_network_requests else None,
                console_messages=captured_console if config.capture_console_messages else None,
            )

        except Exception as e:
            raise e

        finally:
            # If no session_id is given we should close the page
            all_contexts = page.context.browser.contexts
            total_pages = sum(len(context.pages) for context in all_contexts)                
            if config.session_id:
                pass
            elif total_pages <= 1 and (self.browser_config.use_managed_browser or self.browser_config.headless):
                pass
            else:
                # Detach listeners before closing to prevent potential errors during close
                if config.capture_network_requests:
                    page.remove_listener("request", handle_request_capture)
                    page.remove_listener("response", handle_response_capture)
                    page.remove_listener("requestfailed", handle_request_failed_capture)
                if config.capture_console_messages:
                    # Retrieve any final console messages for undetected browsers
                    if hasattr(self.adapter, 'retrieve_console_messages'):
                        final_messages = await self.adapter.retrieve_console_messages(page)
                        captured_console.extend(final_messages)
                    
                    # Clean up console capture
                    await self.adapter.cleanup_console_capture(page, handle_console, handle_error)
                
                # Close the page
                await page.close()

    # async def _handle_full_page_scan(self, page: Page, scroll_delay: float = 0.1):
    async def _handle_full_page_scan(self, page: Page, scroll_delay: float = 0.1, max_scroll_steps: Optional[int] = None):
        """
        Helper method to handle full page scanning.

        How it works:
        1. Get the viewport height.
        2. Scroll to the bottom of the page.
        3. Get the total height of the page.
        4. Scroll back to the top of the page.
        5. Scroll to the bottom of the page again.
        6. Continue scrolling until the bottom of the page is reached.

        Args:
            page (Page): The Playwright page object
            scroll_delay (float): The delay between page scrolls
            max_scroll_steps (Optional[int]): Maximum number of scroll steps to perform. If None, scrolls until end.

        """
        try:
            viewport_size = page.viewport_size
            if viewport_size is None:
                await page.set_viewport_size(
                    {"width": self.browser_config.viewport_width, "height": self.browser_config.viewport_height}
                )
                viewport_size = page.viewport_size

            viewport_height = viewport_size.get(
                "height", self.browser_config.viewport_height
            )
            current_position = viewport_height

            # await page.evaluate(f"window.scrollTo(0, {current_position})")
            await self.safe_scroll(page, 0, current_position, delay=scroll_delay)
            # await self.csp_scroll_to(page, 0, current_position)
            # await asyncio.sleep(scroll_delay)

            # total_height = await page.evaluate("document.documentElement.scrollHeight")
            dimensions = await self.get_page_dimensions(page)
            total_height = dimensions["height"]

            scroll_step_count = 0
            while current_position < total_height:
                #### 
                # NEW FEATURE: Check if we've reached the maximum allowed scroll steps
                # This prevents infinite scrolling on very long pages or infinite scroll scenarios
                # If max_scroll_steps is None, this check is skipped (unlimited scrolling - original behavior)
                ####
                if max_scroll_steps is not None and scroll_step_count >= max_scroll_steps:
                    break
                current_position = min(current_position + viewport_height, total_height)
                await self.safe_scroll(page, 0, current_position, delay=scroll_delay)

                # Increment the step counter for max_scroll_steps tracking
                scroll_step_count += 1
                
                # await page.evaluate(f"window.scrollTo(0, {current_position})")
                # await asyncio.sleep(scroll_delay)

                # new_height = await page.evaluate("document.documentElement.scrollHeight")
                dimensions = await self.get_page_dimensions(page)
                new_height = dimensions["height"]

                if new_height > total_height:
                    total_height = new_height

            # await page.evaluate("window.scrollTo(0, 0)")
            await self.safe_scroll(page, 0, 0)

        except Exception as e:
            self.logger.warning(
                message="Failed to perform full page scan: {error}",
                tag="PAGE_SCAN",
                params={"error": str(e)},
            )
        else:
            # await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.safe_scroll(page, 0, total_height)

    async def _handle_virtual_scroll(self, page: Page, config: "VirtualScrollConfig"):
        """
        Handle virtual scroll containers (e.g., Twitter-like feeds) by capturing
        content at different scroll positions and merging unique elements.
        
        Following the design:
        1. Get container HTML
        2. Scroll by container height
        3. Wait and check if container HTML changed
        4. Three cases:
           - No change: continue scrolling
           - New items added (appended): continue (items already in page)
           - Items replaced: capture HTML chunk and add to list
        5. After N scrolls, merge chunks if any were captured
        
        Args:
            page: The Playwright page object
            config: Virtual scroll configuration
        """
        try:
            # Import VirtualScrollConfig to avoid circular import
            from .async_configs import VirtualScrollConfig
            
            # Ensure config is a VirtualScrollConfig instance
            if isinstance(config, dict):
                config = VirtualScrollConfig.from_dict(config)
            
            self.logger.info(
                message="Starting virtual scroll capture for container: {selector}",
                tag="VSCROLL",
                params={"selector": config.container_selector}
            )
            
            # JavaScript function to handle virtual scroll capture
            virtual_scroll_js = """
            async (config) => {
                const container = document.querySelector(config.container_selector);
                if (!container) {
                    throw new Error(`Container not found: ${config.container_selector}`);
                }
                
                // List to store HTML chunks when content is replaced
                const htmlChunks = [];
                let previousHTML = container.innerHTML;
                let scrollCount = 0;
                
                // Determine scroll amount
                let scrollAmount;
                if (typeof config.scroll_by === 'number') {
                    scrollAmount = config.scroll_by;
                } else if (config.scroll_by === 'page_height') {
                    scrollAmount = window.innerHeight;
                } else { // container_height
                    scrollAmount = container.offsetHeight;
                }
                
                // Perform scrolling
                while (scrollCount < config.scroll_count) {
                    // Scroll the container
                    container.scrollTop += scrollAmount;
                    
                    // Wait for content to potentially load
                    await new Promise(resolve => setTimeout(resolve, config.wait_after_scroll * 1000));
                    
                    // Get current HTML
                    const currentHTML = container.innerHTML;
                    
                    // Determine what changed
                    if (currentHTML === previousHTML) {
                        // Case 0: No change - continue scrolling
                        console.log(`Scroll ${scrollCount + 1}: No change in content`);
                    } else if (currentHTML.startsWith(previousHTML)) {
                        // Case 1: New items appended - content already in page
                        console.log(`Scroll ${scrollCount + 1}: New items appended`);
                    } else {
                        // Case 2: Items replaced - capture the previous HTML
                        console.log(`Scroll ${scrollCount + 1}: Content replaced, capturing chunk`);
                        htmlChunks.push(previousHTML);
                    }
                    
                    // Update previous HTML for next iteration
                    previousHTML = currentHTML;
                    scrollCount++;
                    
                    // Check if we've reached the end
                    if (container.scrollTop + container.clientHeight >= container.scrollHeight - 10) {
                        console.log(`Reached end of scrollable content at scroll ${scrollCount}`);
                        // Capture final chunk if content was replaced
                        if (htmlChunks.length > 0) {
                            htmlChunks.push(currentHTML);
                        }
                        break;
                    }
                }
                
                // If we have chunks (case 2 occurred), merge them
                if (htmlChunks.length > 0) {
                    console.log(`Merging ${htmlChunks.length} HTML chunks`);
                    
                    // Parse all chunks to extract unique elements
                    const tempDiv = document.createElement('div');
                    const seenTexts = new Set();
                    const uniqueElements = [];
                    
                    // Process each chunk
                    for (const chunk of htmlChunks) {
                        tempDiv.innerHTML = chunk;
                        const elements = tempDiv.children;
                        
                        for (let i = 0; i < elements.length; i++) {
                            const element = elements[i];
                            // Normalize text for deduplication
                            const normalizedText = element.innerText
                                .toLowerCase()
                                .replace(/[\\s\\W]/g, ''); // Remove spaces and symbols
                            
                            if (!seenTexts.has(normalizedText)) {
                                seenTexts.add(normalizedText);
                                uniqueElements.push(element.outerHTML);
                            }
                        }
                    }
                    
                    // Replace container content with merged unique elements
                    container.innerHTML = uniqueElements.join('\\n');
                    console.log(`Merged ${uniqueElements.length} unique elements from ${htmlChunks.length} chunks`);
                    
                    return {
                        success: true,
                        chunksCount: htmlChunks.length,
                        uniqueCount: uniqueElements.length,
                        replaced: true
                    };
                } else {
                    console.log('No content replacement detected, all content remains in page');
                    return {
                        success: true,
                        chunksCount: 0,
                        uniqueCount: 0,
                        replaced: false
                    };
                }
            }
            """
            
            # Execute virtual scroll capture
            result = await self.adapter.evaluate(page, virtual_scroll_js, config.to_dict())
            
            if result.get("replaced", False):
                self.logger.success(
                    message="Virtual scroll completed. Merged {unique} unique elements from {chunks} chunks",
                    tag="VSCROLL",
                    params={
                        "unique": result.get("uniqueCount", 0),
                        "chunks": result.get("chunksCount", 0)
                    }
                )
            else:
                self.logger.info(
                    message="Virtual scroll completed. Content was appended, no merging needed",
                    tag="VSCROLL"
                )
            
        except Exception as e:
            self.logger.error(
                message="Virtual scroll capture failed: {error}",
                tag="VSCROLL",
                params={"error": str(e)}
            )
            # Continue with normal flow even if virtual scroll fails

    async def _handle_download(self, download):
        """
        Handle file downloads.

        How it works:
        1. Get the suggested filename.
        2. Get the download path.
        3. Log the download.
        4. Start the download.
        5. Save the downloaded file.
        6. Log the completion.

        Args:
            download (Download): The Playwright download object

        Returns:
            None
        """
        try:
            suggested_filename = download.suggested_filename
            download_path = os.path.join(self.browser_config.downloads_path, suggested_filename)

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

    async def remove_overlay_elements(self, page: Page) -> None:
        """
        Removes popup overlays, modals, cookie notices, and other intrusive elements from the page.

        Args:
            page (Page): The Playwright page instance
        """
        remove_overlays_js = load_js_script("remove_overlay_elements")

        try:
            await self.adapter.evaluate(page,
                f"""
                (() => {{
                    try {{
                        {remove_overlays_js}
                        return {{ success: true }};
                    }} catch (error) {{
                        return {{
                            success: false,
                            error: error.toString(),
                            stack: error.stack
                        }};
                    }}
                }})()
            """
            )
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

        Args:
            page (Page): The Playwright page object

        Returns:
            bytes: The PDF data
        """
        pdf_data = await page.pdf(print_background=True)
        return pdf_data
        
    async def capture_mhtml(self, page: Page) -> Optional[str]:
        """
        Captures the current page as MHTML using CDP.
        
        MHTML (MIME HTML) is a web page archive format that combines the HTML content 
        with its resources (images, CSS, etc.) into a single MIME-encoded file.
        
        Args:
            page (Page): The Playwright page object
            
        Returns:
            Optional[str]: The MHTML content as a string, or None if there was an error
        """
        try:
            # Ensure the page is fully loaded before capturing
            try:
                # Wait for DOM content and network to be idle
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
                await page.wait_for_load_state("networkidle", timeout=5000)
                
                # Give a little extra time for JavaScript execution
                await page.wait_for_timeout(1000)
                
                # Wait for any animations to complete
                await page.evaluate("""
                    () => new Promise(resolve => {
                        // First requestAnimationFrame gets scheduled after the next repaint
                        requestAnimationFrame(() => {
                            // Second requestAnimationFrame gets called after all animations complete
                            requestAnimationFrame(resolve);
                        });
                    })
                """)
            except Error as e:
                if self.logger:
                    self.logger.warning(
                        message="Wait for load state timed out: {error}",
                        tag="MHTML",
                        params={"error": str(e)},
                    )
            
            # Create a new CDP session
            cdp_session = await page.context.new_cdp_session(page)
            
            # Call Page.captureSnapshot with format "mhtml"
            result = await cdp_session.send("Page.captureSnapshot", {"format": "mhtml"})
            
            # The result contains a 'data' field with the MHTML content
            mhtml_content = result.get("data")
            
            # Detach the CDP session to clean up resources
            await cdp_session.detach()
            
            return mhtml_content
        except Exception as e:
            # Log the error but don't raise it - we'll just return None for the MHTML
            if self.logger:
                self.logger.error(
                    message="Failed to capture MHTML: {error}",
                    tag="MHTML",
                    params={"error": str(e)},
                )
            return None

    async def _capture_console_messages(
        self, page: Page, file_path: str
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Captures console messages from the page.
        Args:

            page (Page): The Playwright page object
        Returns:
            List[Dict[str, Union[str, float]]]: A list of captured console messages
        """
        captured_console = []

        def handle_console_message(msg):
            try:
                message_type = msg.type
                message_text = msg.text

                entry = {
                    "type": message_type,
                    "text": message_text,
                    "timestamp": time.time(),
                }
                captured_console.append(entry)
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        f"Error capturing console message: {e}", tag="CAPTURE"
                    )

        page.on("console", handle_console_message)
        
        await page.goto(file_path)

        return captured_console
        
    async def take_screenshot(self, page, **kwargs) -> str:
        """
        Take a screenshot of the current page.

        Args:
            page (Page): The Playwright page object
            kwargs: Additional keyword arguments

        Returns:
            str: The base64-encoded screenshot data
        """
        need_scroll = await self.page_need_scroll(page)

        if not need_scroll:
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

        Args:
            pdf_data (bytes): The PDF data

        Returns:
            str: The base64-encoded screenshot data
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

        Requires pdf2image and poppler.

        Args:
            page (Page): The Playwright page object
            kwargs: Additional keyword arguments

        Returns:
            str: The base64-encoded screenshot data
        """
        try:
            # Get page height
            dimensions = await self.get_page_dimensions(page)
            page_width = dimensions["width"]
            page_height = dimensions["height"]
            # page_height = await page.evaluate("document.documentElement.scrollHeight")
            # page_width = await page.evaluate("document.documentElement.scrollWidth")

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
                # Special handling for the last segment
                if i == num_segments - 1:
                    last_part_height = page_height % viewport_height
                    
                    # If page_height is an exact multiple of viewport_height,
                    # we don't need an extra segment
                    if last_part_height == 0:
                        # Skip last segment if page height is exact multiple of viewport
                        break
                    
                    # Adjust viewport to exactly match the remaining content height
                    await page.set_viewport_size({"width": page_width, "height": last_part_height})
                
                await page.evaluate(f"window.scrollTo(0, {y_offset})")
                await asyncio.sleep(0.01)  # wait for render
                
                # Capture the current segment
                # Note: Using compression options (format, quality) would go here
                seg_shot = await page.screenshot(full_page=False, type="jpeg", quality=85)
                # seg_shot = await page.screenshot(full_page=False)
                img = Image.open(BytesIO(seg_shot)).convert("RGB")
                segments.append(img)

            # Reset viewport to original size after capturing segments
            await page.set_viewport_size({"width": page_width, "height": viewport_height})

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
        # finally:
        #     await page.close()

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
        # finally:
        #     await page.close()

    async def export_storage_state(self, path: str = None) -> dict:
        """
        Exports the current storage state (cookies, localStorage, sessionStorage)
        to a JSON file at the specified path.

        Args:
            path (str): The path to save the storage state JSON file

        Returns:
            dict: The exported storage state
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

    async def robust_execute_user_script(
        self, page: Page, js_code: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Executes user-provided JavaScript code with proper error handling and context,
        supporting both synchronous and async user code, plus navigations.

        How it works:
        1. Wait for load state 'domcontentloaded'
        2. If js_code is a string, execute it directly
        3. If js_code is a list, execute each element in sequence
        4. Wait for load state 'networkidle'
        5. Return results

        Args:
            page (Page): The Playwright page instance
            js_code (Union[str, List[str]]): The JavaScript code to execute

        Returns:
            Dict[str, Any]: The results of the execution
        """
        try:
            await page.wait_for_load_state("domcontentloaded")

            if isinstance(js_code, str):
                scripts = [js_code]
            else:
                scripts = js_code

            results = []
            for script in scripts:
                try:
                    # Attempt the evaluate
                    # If the user code triggers navigation, we catch the "context destroyed" error
                    # then wait for the new page to load before continuing
                    result = None
                    try:
                        # OLD VERSION:
                        # result = await page.evaluate(
                        #     f"""
                        # (async () => {{
                        #     try {{
                        #         const script_result = {script};
                        #         return {{ success: true, result: script_result }};
                        #     }} catch (err) {{
                        #         return {{ success: false, error: err.toString(), stack: err.stack }};
                        #     }}
                        # }})();
                        # """
                        # )
                        
                        # """ NEW VERSION:
                        # When {script} contains statements (e.g., const link = …; link.click();), 
                        # this forms invalid JavaScript, causing Playwright execution error: SyntaxError: Unexpected token 'const'.
                        # """
                        result = await self.adapter.evaluate(page,
                            f"""
                        (async () => {{
                            try {{
                                return await (async () => {{
                                    {script}
                                }})();
                            }} catch (err) {{
                                return {{ success: false, error: err.toString(), stack: err.stack }};
                            }}
                        }})();
                        """
                        )
                    except Error as e:
                        # If it's due to navigation destroying the context, handle gracefully
                        if "Execution context was destroyed" in str(e):
                            self.logger.info(
                                "Navigation triggered by script, waiting for load state",
                                tag="JS_EXEC",
                            )
                            try:
                                await page.wait_for_load_state("load", timeout=30000)
                            except Error as nav_err:
                                self.logger.warning(
                                    message="Navigation wait failed: {error}",
                                    tag="JS_EXEC",
                                    params={"error": str(nav_err)},
                                )
                            try:
                                await page.wait_for_load_state(
                                    "networkidle", timeout=30000
                                )
                            except Error as nav_err:
                                self.logger.warning(
                                    message="Network idle wait failed: {error}",
                                    tag="JS_EXEC",
                                    params={"error": str(nav_err)},
                                )
                            # Return partial success, or adapt as you see fit
                            result = {
                                "success": True,
                                "info": "Navigation triggered, ignoring context destroyed error",
                            }
                        else:
                            # It's some other error, log and continue
                            self.logger.error(
                                message="Playwright execution error: {error}",
                                tag="JS_EXEC",
                                params={"error": str(e)},
                            )
                            result = {"success": False, "error": str(e)}

                    # If we made it this far with no repeated error, do post-load waits
                    t1 = time.time()
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Error as e:
                        self.logger.warning(
                            message="DOM content load timeout: {error}",
                            tag="JS_EXEC",
                            params={"error": str(e)},
                        )

                    # t1 = time.time()
                    # try:
                    #     await page.wait_for_load_state('networkidle', timeout=5000)
                    #     print("Network idle after script execution in", time.time() - t1)
                    # except Error as e:
                    #     self.logger.warning(
                    #         message="Network idle timeout: {error}",
                    #         tag="JS_EXEC",
                    #         params={"error": str(e)}
                    #     )

                    results.append(result if result else {"success": True})

                except Exception as e:
                    # Catch anything else
                    self.logger.error(
                        message="Script chunk failed: {error}",
                        tag="JS_EXEC",
                        params={"error": str(e)},
                    )
                    results.append({"success": False, "error": str(e)})

            return {"success": True, "results": results}

        except Exception as e:
            self.logger.error(
                message="Script execution failed: {error}",
                tag="JS_EXEC",
                params={"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    async def execute_user_script(
        self, page: Page, js_code: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Executes user-provided JavaScript code with proper error handling and context.

        Args:
            page: Playwright page object
            js_code: Single JavaScript string or list of JavaScript code strings

        Returns:
            Dict containing execution status and results/errors
        """
        try:
            # Ensure the page is ready for script execution
            await page.wait_for_load_state("domcontentloaded")

            # Handle single script or multiple scripts
            if isinstance(js_code, str):
                scripts = [js_code]
            else:
                scripts = js_code

            results = []
            for script in scripts:
                try:
                    # Execute the script and wait for network idle
                    result = await self.adapter.evaluate(page,
                        f"""
                        (() => {{
                            return new Promise((resolve) => {{
                                try {{
                                    const result = (function() {{
                                        {script}
                                    }})();
                                    
                                    // If result is a promise, wait for it
                                    if (result instanceof Promise) {{
                                        result.then(() => {{
                                            // Wait a bit for any triggered effects
                                            setTimeout(() => resolve({{ success: true }}), 100);
                                        }}).catch(error => {{
                                            resolve({{
                                                success: false,
                                                error: error.toString(),
                                                stack: error.stack
                                            }});
                                        }});
                                    }} else {{
                                        // For non-promise results, still wait a bit for effects
                                        setTimeout(() => resolve({{ success: true }}), 100);
                                    }}
                                }} catch (error) {{
                                    resolve({{
                                        success: false,
                                        error: error.toString(),
                                        stack: error.stack
                                    }});
                                }}
                            }});
                        }})()
                    """
                    )

                    # Wait for network idle after script execution
                    t1 = time.time()
                    await page.wait_for_load_state("domcontentloaded", timeout=5000)


                    t1 = time.time()
                    await page.wait_for_load_state("networkidle", timeout=5000)

                    results.append(result if result else {"success": True})

                except Error as e:
                    # Handle Playwright-specific errors
                    self.logger.error(
                        message="Playwright execution error: {error}",
                        tag="JS_EXEC",
                        params={"error": str(e)},
                    )
                    results.append({"success": False, "error": str(e)})

            return {"success": True, "results": results}

        except Exception as e:
            self.logger.error(
                message="Script execution failed: {error}",
                tag="JS_EXEC",
                params={"error": str(e)},
            )
            return {"success": False, "error": str(e)}

        except Exception as e:
            self.logger.error(
                message="Script execution failed: {error}",
                tag="JS_EXEC",
                params={"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    async def check_visibility(self, page):
        """
        Checks if an element is visible on the page.

        Args:
            page: Playwright page object

        Returns:
            Boolean indicating visibility
        """
        return await self.adapter.evaluate(page,
            """
            () => {
                const element = document.body;
                if (!element) return false;
                const style = window.getComputedStyle(element);
                const isVisible = style.display !== 'none' && 
                                style.visibility !== 'hidden' && 
                                style.opacity !== '0';
                return isVisible;
            }
        """
        )

    async def safe_scroll(self, page: Page, x: int, y: int, delay: float = 0.1):
        """
        Safely scroll the page with rendering time.

        Args:
            page: Playwright page object
            x: Horizontal scroll position
            y: Vertical scroll position
        """
        result = await self.csp_scroll_to(page, x, y)
        if result["success"]:
            await page.wait_for_timeout(delay * 1000)
        return result

    async def csp_scroll_to(self, page: Page, x: int, y: int) -> Dict[str, Any]:
        """
        Performs a CSP-compliant scroll operation and returns the result status.

        Args:
            page: Playwright page object
            x: Horizontal scroll position
            y: Vertical scroll position

        Returns:
            Dict containing scroll status and position information
        """
        try:
            result = await self.adapter.evaluate(page,
                f"""() => {{
                    try {{
                        const startX = window.scrollX;
                        const startY = window.scrollY;
                        window.scrollTo({x}, {y});
                        
                        // Get final position after scroll
                        const endX = window.scrollX;
                        const endY = window.scrollY;
                        
                        return {{
                            success: true,
                            startPosition: {{ x: startX, y: startY }},
                            endPosition: {{ x: endX, y: endY }},
                            targetPosition: {{ x: {x}, y: {y} }},
                            delta: {{
                                x: Math.abs(endX - {x}),
                                y: Math.abs(endY - {y})
                            }}
                        }};
                    }} catch (e) {{
                        return {{
                            success: false,
                            error: e.toString()
                        }};
                    }}
                }}"""
            )

            if not result["success"]:
                self.logger.warning(
                    message="Scroll operation failed: {error}",
                    tag="SCROLL",
                    params={"error": result.get("error")},
                )

            return result

        except Exception as e:
            self.logger.error(
                message="Failed to execute scroll: {error}",
                tag="SCROLL",
                params={"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    async def get_page_dimensions(self, page: Page):
        """
        Get the dimensions of the page.

        Args:
            page: Playwright page object

        Returns:
            Dict containing width and height of the page
        """
        return await self.adapter.evaluate(page,
            """
            () => {
                const {scrollWidth, scrollHeight} = document.documentElement;
                return {width: scrollWidth, height: scrollHeight};
            }
        """
        )

    async def page_need_scroll(self, page: Page) -> bool:
        """
        Determine whether the page need to scroll

        Args:
            page: Playwright page object

        Returns:
            bool: True if page needs scrolling
        """
        try:
            need_scroll = await self.adapter.evaluate(page,
                """
            () => {
                const scrollHeight = document.documentElement.scrollHeight;
                const viewportHeight = window.innerHeight;
                return scrollHeight > viewportHeight;
            }
            """
            )
            return need_scroll
        except Exception as e:
            self.logger.warning(
                message="Failed to check scroll need: {error}. Defaulting to True for safety.",
                tag="SCROLL",
                params={"error": str(e)},
            )
            return True  # Default to scrolling if check fails


####################################################################################################
# HTTP Crawler Strategy
####################################################################################################

class HTTPCrawlerError(Exception):
    """Base error class for HTTP crawler specific exceptions"""
    pass


class ConnectionTimeoutError(HTTPCrawlerError):
    """Raised when connection timeout occurs"""
    pass


class HTTPStatusError(HTTPCrawlerError):
    """Raised for unexpected status codes"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class AsyncHTTPCrawlerStrategy(AsyncCrawlerStrategy):
    """
    Fast, lightweight HTTP-only crawler strategy optimized for memory efficiency.
    """
    
    __slots__ = ('logger', 'max_connections', 'dns_cache_ttl', 'chunk_size', '_session', 'hooks', 'browser_config')

    DEFAULT_TIMEOUT: Final[int] = 30
    DEFAULT_CHUNK_SIZE: Final[int] = 64 * 1024  
    DEFAULT_MAX_CONNECTIONS: Final[int] = min(32, (os.cpu_count() or 1) * 4)
    DEFAULT_DNS_CACHE_TTL: Final[int] = 300
    VALID_SCHEMES: Final = frozenset({'http', 'https', 'file', 'raw'})

    _BASE_HEADERS: Final = MappingProxyType({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    def __init__(
        self, 
        browser_config: Optional[HTTPCrawlerConfig] = None,
        logger: Optional[AsyncLogger] = None,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        dns_cache_ttl: int = DEFAULT_DNS_CACHE_TTL,
        chunk_size: int = DEFAULT_CHUNK_SIZE
    ):
        """Initialize the HTTP crawler with config"""
        self.browser_config = browser_config or HTTPCrawlerConfig()
        self.logger = logger
        self.max_connections = max_connections
        self.dns_cache_ttl = dns_cache_ttl
        self.chunk_size = chunk_size
        self._session: Optional[aiohttp.ClientSession] = None
        
        self.hooks = {
            k: partial(self._execute_hook, k) 
            for k in ('before_request', 'after_request', 'on_error')
        }

        # Set default hooks
        self.set_hook('before_request', lambda *args, **kwargs: None)
        self.set_hook('after_request', lambda *args, **kwargs: None)
        self.set_hook('on_error', lambda *args, **kwargs: None)
                      

    async def __aenter__(self) -> AsyncHTTPCrawlerStrategy:
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @contextlib.asynccontextmanager
    async def _session_context(self):
        try:
            if not self._session:
                await self.start()
            yield self._session
        finally:
            pass

    def set_hook(self, hook_type: str, hook_func: Callable) -> None:
        if hook_type in self.hooks:
            self.hooks[hook_type] = partial(self._execute_hook, hook_type, hook_func)
        else:
            raise ValueError(f"Invalid hook type: {hook_type}")

    async def _execute_hook(
        self, 
        hook_type: str, 
        hook_func: Callable,
        *args: Any, 
        **kwargs: Any
    ) -> Any:
        if asyncio.iscoroutinefunction(hook_func):
            return await hook_func(*args, **kwargs)
        return hook_func(*args, **kwargs)

    async def start(self) -> None:
        if not self._session:
            connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                ttl_dns_cache=self.dns_cache_ttl,
                use_dns_cache=True,
                force_close=False
            )
            self._session = aiohttp.ClientSession(
                headers=dict(self._BASE_HEADERS),
                connector=connector,
                timeout=ClientTimeout(total=self.DEFAULT_TIMEOUT)
            )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            try:
                await asyncio.wait_for(self._session.close(), timeout=5.0)
            except asyncio.TimeoutError:
                if self.logger:
                    self.logger.warning(
                        message="Session cleanup timed out",
                        tag="CLEANUP"
                    )
            finally:
                self._session = None

    async def _stream_file(self, path: str) -> AsyncGenerator[memoryview, None]:
        async with aiofiles.open(path, mode='rb') as f:
            while chunk := await f.read(self.chunk_size):
                yield memoryview(chunk)

    async def _handle_file(self, path: str) -> AsyncCrawlResponse:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Local file not found: {path}")
            
        chunks = []
        async for chunk in self._stream_file(path):
            chunks.append(chunk.tobytes().decode('utf-8', errors='replace'))
            
        return AsyncCrawlResponse(
            html=''.join(chunks),
            response_headers={},
            status_code=200
        )

    async def _handle_raw(self, content: str) -> AsyncCrawlResponse:
        return AsyncCrawlResponse(
            html=content,
            response_headers={},
            status_code=200
        )


    async def _handle_http(
        self, 
        url: str, 
        config: CrawlerRunConfig
    ) -> AsyncCrawlResponse:
        async with self._session_context() as session:
            timeout = ClientTimeout(
                total=config.page_timeout or self.DEFAULT_TIMEOUT,
                connect=10,
                sock_read=30
            )
            
            headers = dict(self._BASE_HEADERS)
            if self.browser_config.headers:
                headers.update(self.browser_config.headers)

            request_kwargs = {
                'timeout': timeout,
                'allow_redirects': self.browser_config.follow_redirects,
                'ssl': self.browser_config.verify_ssl,
                'headers': headers
            }

            if self.browser_config.method == "POST":
                if self.browser_config.data:
                    request_kwargs['data'] = self.browser_config.data
                if self.browser_config.json:
                    request_kwargs['json'] = self.browser_config.json

            await self.hooks['before_request'](url, request_kwargs)

            try:
                async with session.request(self.browser_config.method, url, **request_kwargs) as response:
                    content = memoryview(await response.read())
                    
                    if not (200 <= response.status < 300):
                        raise HTTPStatusError(
                            response.status,
                            f"Unexpected status code for {url}"
                        )
                    
                    encoding = response.charset
                    if not encoding:
                        encoding = chardet.detect(content.tobytes())['encoding'] or 'utf-8'                    
                    
                    result = AsyncCrawlResponse(
                        html=content.tobytes().decode(encoding, errors='replace'),
                        response_headers=dict(response.headers),
                        status_code=response.status,
                        redirected_url=str(response.url)
                    )
                    
                    await self.hooks['after_request'](result)
                    return result

            except aiohttp.ServerTimeoutError as e:
                await self.hooks['on_error'](e)
                raise ConnectionTimeoutError(f"Request timed out: {str(e)}")
                
            except aiohttp.ClientConnectorError as e:
                await self.hooks['on_error'](e)
                raise ConnectionError(f"Connection failed: {str(e)}")
                
            except aiohttp.ClientError as e:
                await self.hooks['on_error'](e)
                raise HTTPCrawlerError(f"HTTP client error: {str(e)}")
            
            except asyncio.exceptions.TimeoutError as e:
                await self.hooks['on_error'](e)
                raise ConnectionTimeoutError(f"Request timed out: {str(e)}")
            
            except Exception as e:
                await self.hooks['on_error'](e)
                raise HTTPCrawlerError(f"HTTP request failed: {str(e)}")

    async def crawl(
        self, 
        url: str, 
        config: Optional[CrawlerRunConfig] = None, 
        **kwargs
    ) -> AsyncCrawlResponse:
        config = config or CrawlerRunConfig.from_kwargs(kwargs)
        
        parsed = urlparse(url)
        scheme = parsed.scheme.rstrip('/')
        
        if scheme not in self.VALID_SCHEMES:
            raise ValueError(f"Unsupported URL scheme: {scheme}")
            
        try:
            if scheme == 'file':
                return await self._handle_file(parsed.path)
            elif scheme == 'raw':
                return await self._handle_raw(parsed.path)
            else:  # http or https
                return await self._handle_http(url, config)
                
        except Exception as e:
            if self.logger:
                self.logger.error(
                    message="Crawl failed: {error}",
                    tag="CRAWL",
                    params={"error": str(e), "url": url}
                )
            raise
