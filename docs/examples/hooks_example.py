from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext


async def main():
    print("🔗 Hooks Example: Demonstrating different hook use cases")

    # Configure browser settings
    browser_config = BrowserConfig(headless=True)

    # Configure crawler settings
    crawler_run_config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        wait_for="body",
        cache_mode=CacheMode.BYPASS,
    )

    # Create crawler instance
    crawler = AsyncWebCrawler(config=browser_config)

    # Define and set hook functions
    async def on_browser_created(browser, context: BrowserContext, **kwargs):
        """Hook called after the browser is created"""
        print("[HOOK] on_browser_created - Browser is ready!")
        # Example: Set a cookie that will be used for all requests
        return browser

    async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
        """Hook called after a new page and context are created"""
        print("[HOOK] on_page_context_created - New page created!")
        # Example: Set default viewport size
        await context.add_cookies(
            [
                {
                    "name": "session_id",
                    "value": "example_session",
                    "domain": ".example.com",
                    "path": "/",
                }
            ]
        )
        await page.set_viewport_size({"width": 1080, "height": 800})
        return page

    async def on_user_agent_updated(
        page: Page, context: BrowserContext, user_agent: str, **kwargs
    ):
        """Hook called when the user agent is updated"""
        print(f"[HOOK] on_user_agent_updated - New user agent: {user_agent}")
        return page

    async def on_execution_started(page: Page, context: BrowserContext, **kwargs):
        """Hook called after custom JavaScript execution"""
        print("[HOOK] on_execution_started - Custom JS executed!")
        return page

    async def before_goto(page: Page, context: BrowserContext, url: str, **kwargs):
        """Hook called before navigating to each URL"""
        print(f"[HOOK] before_goto - About to visit: {url}")
        # Example: Add custom headers for the request
        await page.set_extra_http_headers({"Custom-Header": "my-value"})
        return page

    async def after_goto(
        page: Page, context: BrowserContext, url: str, response: dict, **kwargs
    ):
        """Hook called after navigating to each URL"""
        print(f"[HOOK] after_goto - Successfully loaded: {url}")
        # Example: Wait for a specific element to be loaded
        try:
            await page.wait_for_selector(".content", timeout=1000)
            print("Content element found!")
        except:
            print("Content element not found, continuing anyway")
        return page

    async def before_retrieve_html(page: Page, context: BrowserContext, **kwargs):
        """Hook called before retrieving the HTML content"""
        print("[HOOK] before_retrieve_html - About to get HTML content")
        # Example: Scroll to bottom to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        return page

    async def before_return_html(
        page: Page, context: BrowserContext, html: str, **kwargs
    ):
        """Hook called before returning the HTML content"""
        print(f"[HOOK] before_return_html - Got HTML content (length: {len(html)})")
        # Example: You could modify the HTML content here if needed
        return page

    # Set all the hooks
    crawler.crawler_strategy.set_hook("on_browser_created", on_browser_created)
    crawler.crawler_strategy.set_hook(
        "on_page_context_created", on_page_context_created
    )
    crawler.crawler_strategy.set_hook("on_user_agent_updated", on_user_agent_updated)
    crawler.crawler_strategy.set_hook("on_execution_started", on_execution_started)
    crawler.crawler_strategy.set_hook("before_goto", before_goto)
    crawler.crawler_strategy.set_hook("after_goto", after_goto)
    crawler.crawler_strategy.set_hook("before_retrieve_html", before_retrieve_html)
    crawler.crawler_strategy.set_hook("before_return_html", before_return_html)

    await crawler.start()

    # Example usage: crawl a simple website
    url = "https://example.com"
    result = await crawler.arun(url, config=crawler_run_config)
    print(f"\nCrawled URL: {result.url}")
    print(f"HTML length: {len(result.html)}")

    await crawler.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
