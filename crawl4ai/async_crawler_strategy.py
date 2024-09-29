import asyncio
import base64, time
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, List, Optional
import os
from playwright.async_api import async_playwright, Page, Browser, Error
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from .utils import sanitize_input_encode, calculate_semaphore_count
import json, uuid
import hashlib
from pathlib import Path
from playwright.async_api import ProxySettings
from pydantic import BaseModel
class AsyncCrawlResponse(BaseModel):
    html: str
    response_headers: Dict[str, str]
    status_code: int

class AsyncCrawlerStrategy(ABC):
    @abstractmethod
    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
        pass
    
    @abstractmethod
    async def crawl_many(self, urls: List[str], **kwargs) -> List[AsyncCrawlResponse]:
        pass
    
    @abstractmethod
    async def take_screenshot(self, url: str) -> str:
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
        self.user_agent = kwargs.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        self.proxy = kwargs.get("proxy")
        self.headless = kwargs.get("headless", True)
        self.headers = {}
        self.sessions = {}
        self.session_ttl = 1800 
        self.js_code = js_code
        self.verbose = kwargs.get("verbose", False)
        self.playwright = None
        self.browser = None
        self.hooks = {
            'on_browser_created': None,
            'on_user_agent_updated': None,
            'on_execution_started': None,
            'before_goto': None,
            'after_goto': None,
            'before_return_html': None
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
            browser_args = {
                "headless": self.headless,
                # "headless": False,
                "args": [
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-setuid-sandbox",
                    "--no-sandbox",
                ]
            }
            
            # Add proxy settings if a proxy is specified
            if self.proxy:
                proxy_settings = ProxySettings(server=self.proxy)
                browser_args["proxy"] = proxy_settings
                
                
            self.browser = await self.playwright.chromium.launch(**browser_args)
            await self.execute_hook('on_browser_created', self.browser)

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
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
        expired_sessions = [sid for sid, (_, _, last_used) in self.sessions.items() 
                            if current_time - last_used > self.session_ttl]
        for sid in expired_sessions:
            asyncio.create_task(self.kill_session(sid))
            
            
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
                    proxy={"server": self.proxy} if self.proxy else None
                )
                await context.set_extra_http_headers(self.headers)
                page = await context.new_page()
                self.sessions[session_id] = (context, page, time.time())
        else:
            context = await self.browser.new_context(
                    user_agent=self.user_agent,
                    proxy={"server": self.proxy} if self.proxy else None
            )
            await context.set_extra_http_headers(self.headers)
            page = await context.new_page()

        try:
            if self.verbose:
                print(f"[LOG] 🕸️ Crawling {url} using AsyncPlaywrightCrawlerStrategy...")

            if self.use_cached_html:
                cache_file_path = os.path.join(Path.home(), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest())
                if os.path.exists(cache_file_path):
                    html = ""
                    with open(cache_file_path, "r") as f:
                        html = f.read()
                    # retrieve response headers and status code from cache
                    with open(cache_file_path + ".meta", "r") as f:
                        meta = json.load(f)
                        response_headers = meta.get("response_headers", {})
                        status_code = meta.get("status_code")
                    response = AsyncCrawlResponse(html=html, response_headers=response_headers, status_code=status_code)
                    return response

            if not kwargs.get("js_only", False):
                await self.execute_hook('before_goto', page)
                response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await self.execute_hook('after_goto', page)
                
                # Get status code and headers
                status_code = response.status
                response_headers = response.headers
            else:
                status_code = 200
                response_headers = {}

            await page.wait_for_selector('body')
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            js_code = kwargs.get("js_code", kwargs.get("js", self.js_code))
            if js_code:
                if isinstance(js_code, str):
                    r = await page.evaluate(js_code)
                elif isinstance(js_code, list):
                    for js in js_code:
                        await page.evaluate(js)
                
                # await page.wait_for_timeout(100)
                await page.wait_for_load_state('networkidle')
                # Check for on execution even
                await self.execute_hook('on_execution_started', page)
                
            # New code to handle the wait_for parameter
            # Example usage:
            # await crawler.crawl(
            #     url,
            #     js_code="// some JavaScript code",
            #     wait_for="""() => {
            #         return document.querySelector('#my-element') !== null;
            #     }"""
            # )
            # Example of using a CSS selector:
            # await crawler.crawl(
            #     url,
            #     wait_for="#my-element"
            # )
            wait_for = kwargs.get("wait_for")
            if wait_for:
                try:
                    await self.csp_compliant_wait(page, wait_for, timeout=kwargs.get("timeout", 30000))
                except Exception as e:
                    raise RuntimeError(f"Custom wait condition failed: {str(e)}")                
                # try:
                #     await page.wait_for_function(wait_for)
                #     # if callable(wait_for):
                #     #     await page.wait_for_function(wait_for)
                #     # elif isinstance(wait_for, str):
                #     #     await page.wait_for_selector(wait_for)
                #     # else:
                #     #     raise ValueError("wait_for must be either a callable or a CSS selector string")
                # except Error as e:
                #     raise Error(f"Custom wait condition failed: {str(e)}")

            html = await page.content()
            page = await self.execute_hook('before_return_html', page, html)

            if self.verbose:
                print(f"[LOG] ✅ Crawled {url} successfully!")

            if self.use_cached_html:
                cache_file_path = os.path.join(Path.home(), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest())
                with open(cache_file_path, "w", encoding="utf-8") as f:
                    f.write(html)
                # store response headers and status code in cache
                with open(cache_file_path + ".meta", "w", encoding="utf-8") as f:
                    json.dump({
                        "response_headers": response_headers,
                        "status_code": status_code
                    }, f)

            response = AsyncCrawlResponse(html=html, response_headers=response_headers, status_code=status_code)
            return response
        except Error as e:
            raise Error(f"Failed to crawl {url}: {str(e)}")
        finally:
            if not session_id:
                await page.close()

        # try:
        #     html = await _crawl()
        #     return sanitize_input_encode(html)
        # except Error as e:
        #     raise Error(f"Failed to crawl {url}: {str(e)}")
        # except Exception as e:
        #     raise Exception(f"Failed to crawl {url}: {str(e)}")

    async def execute_js(self, session_id: str, js_code: str, wait_for_js: str = None, wait_for_css: str = None) -> AsyncCrawlResponse:
        """
        Execute JavaScript code in a specific session and optionally wait for a condition.
        
        :param session_id: The ID of the session to execute the JS code in.
        :param js_code: The JavaScript code to execute.
        :param wait_for_js: JavaScript condition to wait for after execution.
        :param wait_for_css: CSS selector to wait for after execution.
        :return: AsyncCrawlResponse containing the page's HTML and other information.
        :raises ValueError: If the session does not exist.
        """
        if not session_id:
            raise ValueError("Session ID must be provided")
        
        if session_id not in self.sessions:
            raise ValueError(f"No active session found for session ID: {session_id}")
        
        context, page, last_used = self.sessions[session_id]
        
        try:
            await page.evaluate(js_code)
            
            if wait_for_js:
                await page.wait_for_function(wait_for_js)
            
            if wait_for_css:
                await page.wait_for_selector(wait_for_css)
            
            # Get the updated HTML content
            html = await page.content()
            
            # Get response headers and status code (assuming these are available)
            response_headers = await page.evaluate("() => JSON.stringify(performance.getEntriesByType('resource')[0].responseHeaders)")
            status_code = await page.evaluate("() => performance.getEntriesByType('resource')[0].responseStatus")
            
            # Update the last used time for this session
            self.sessions[session_id] = (context, page, time.time())
            
            return AsyncCrawlResponse(html=html, response_headers=response_headers, status_code=status_code)
        except Error as e:
            raise Error(f"Failed to execute JavaScript or wait for condition in session {session_id}: {str(e)}")
    
    
    async def crawl_many(self, urls: List[str], **kwargs) -> List[AsyncCrawlResponse]:
        semaphore_count = kwargs.get('semaphore_count', calculate_semaphore_count())
        semaphore = asyncio.Semaphore(semaphore_count)

        async def crawl_with_semaphore(url):
            async with semaphore:
                return await self.crawl(url, **kwargs)

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [result if not isinstance(result, Exception) else str(result) for result in results]

    async def take_screenshot(self, url: str) -> str:
        async with await self.browser.new_context(user_agent=self.user_agent) as context:
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded")
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