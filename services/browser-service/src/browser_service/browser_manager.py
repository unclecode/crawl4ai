"""Browser manager for handling Playwright browser instances."""

import logging
from typing import Any, Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser instances and page actions."""

    def __init__(self):
        """Initialize the browser manager."""
        self.playwright = None
        self.browser: Optional[Browser] = None
        self._active_pages = 0

    async def start(self):
        """Start the browser manager and launch browser."""
        logger.info("Starting Playwright browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        logger.info("Browser launched successfully")

    async def stop(self):
        """Stop the browser manager and close browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser stopped")

    def active_count(self) -> int:
        """Get count of active pages."""
        return self._active_pages

    async def navigate(
        self,
        url: str,
        action: str = "navigate",
        headless: bool = True,
        timeout: int = 30,
        wait_time: float = 0,
        user_agent: Optional[str] = None,
        viewport: Optional[Dict[str, int]] = None,
        javascript: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Navigate to URL and perform action.

        Args:
            url: URL to navigate to
            action: Action to perform
            headless: Run in headless mode
            timeout: Timeout in milliseconds
            wait_time: Wait time after action in seconds
            user_agent: Custom user agent
            viewport: Viewport size
            javascript: JavaScript to execute
            cookies: Cookies to set
            headers: Custom headers
            proxy: Proxy URL

        Returns:
            Dictionary with action results
        """
        context: Optional[BrowserContext] = None
        page: Optional[Page] = None

        try:
            self._active_pages += 1

            # Create context with options
            context_options = {}
            if user_agent:
                context_options["user_agent"] = user_agent
            if viewport:
                context_options["viewport"] = viewport
            if headers:
                context_options["extra_http_headers"] = headers

            context = await self.browser.new_context(**context_options)

            # Set cookies if provided
            if cookies:
                await context.add_cookies(
                    [{"name": k, "value": v, "url": url} for k, v in cookies.items()]
                )

            # Create new page
            page = await context.new_page()

            # Navigate to URL
            await page.goto(url, timeout=timeout * 1000, wait_until="networkidle")

            # Wait if requested
            if wait_time > 0:
                await page.wait_for_timeout(int(wait_time * 1000))

            result = {"url": page.url}

            # Perform action
            if action == "get_html":
                result["html"] = await page.content()

            elif action == "screenshot":
                screenshot_bytes = await page.screenshot(full_page=True)
                import base64

                result["screenshot"] = base64.b64encode(screenshot_bytes).decode()

            elif action == "execute_js" and javascript:
                result["javascript_result"] = await page.evaluate(javascript)
                result["html"] = await page.content()

            else:  # navigate
                result["html"] = await page.content()

            # Get cookies
            result["cookies"] = {
                cookie["name"]: cookie["value"] for cookie in await context.cookies()
            }

            return result

        finally:
            self._active_pages -= 1
            if page:
                await page.close()
            if context:
                await context.close()
