# Hooks & Auth for AsyncWebCrawler

Crawl4AI's `AsyncWebCrawler` allows you to customize the behavior of the web crawler using hooks. Hooks are asynchronous functions called at specific points in the crawling process, allowing you to modify the crawler's behavior or perform additional actions. This updated documentation demonstrates how to use hooks, including the new `on_page_context_created` hook, and ensures compatibility with `BrowserConfig` and `CrawlerRunConfig`.

## Example: Using Crawler Hooks with AsyncWebCrawler

In this example, we'll:

1. Configure the browser and set up authentication when it's created.
2. Apply custom routing and initial actions when the page context is created.
3. Add custom headers before navigating to the URL.
4. Log the current URL after navigation.
5. Perform actions after JavaScript execution.
6. Log the length of the HTML before returning it.

### Hook Definitions

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from playwright.async_api import Page, Browser, BrowserContext

def log_routing(route):
    # Example: block loading images
    if route.request.resource_type == "image":
        print(f"[HOOK] Blocking image request: {route.request.url}")
        asyncio.create_task(route.abort())
    else:
        asyncio.create_task(route.continue_())

async def on_browser_created(browser: Browser, **kwargs):
    print("[HOOK] on_browser_created")
    # Example: Set browser viewport size and log in
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()
    await page.goto("https://example.com/login")
    await page.fill("input[name='username']", "testuser")
    await page.fill("input[name='password']", "password123")
    await page.click("button[type='submit']")
    await page.wait_for_selector("#welcome")
    await context.add_cookies([{"name": "auth_token", "value": "abc123", "url": "https://example.com"}])
    await page.close()
    await context.close()

async def on_page_context_created(context: BrowserContext, page: Page, **kwargs):
    print("[HOOK] on_page_context_created")
    await context.route("**", log_routing)

async def before_goto(page: Page, context: BrowserContext, **kwargs):
    print("[HOOK] before_goto")
    await page.set_extra_http_headers({"X-Test-Header": "test"})

async def after_goto(page: Page, context: BrowserContext, **kwargs):
    print("[HOOK] after_goto")
    print(f"Current URL: {page.url}")

async def on_execution_started(page: Page, context: BrowserContext, **kwargs):
    print("[HOOK] on_execution_started")
    await page.evaluate("console.log('Custom JS executed')")

async def before_return_html(page: Page, context: BrowserContext, html: str, **kwargs):
    print("[HOOK] before_return_html")
    print(f"HTML length: {len(html)}")
    return page
```

### Using the Hooks with AsyncWebCrawler

```python
async def main():
    print("\n🔗 Using Crawler Hooks: Customize AsyncWebCrawler with hooks!")

    # Configure browser and crawler settings
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1920,
        viewport_height=1080
    )
    
    crawler_run_config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        wait_for="footer"
    )

    # Initialize crawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler.crawler_strategy.set_hook("on_browser_created", on_browser_created)
        crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)
        crawler.crawler_strategy.set_hook("before_goto", before_goto)
        crawler.crawler_strategy.set_hook("after_goto", after_goto)
        crawler.crawler_strategy.set_hook("on_execution_started", on_execution_started)
        crawler.crawler_strategy.set_hook("before_return_html", before_return_html)

        # Run the crawler
        result = await crawler.arun(url="https://example.com", config=crawler_run_config)

    print("\n📦 Crawler Hooks Result:")
    print(result)

asyncio.run(main())
```

### Explanation of Hooks

- **`on_browser_created`**: Called when the browser is created. Use this to configure the browser or handle authentication (e.g., logging in and setting cookies).
- **`on_page_context_created`**: Called when a new page context is created. Use this to apply routing, block resources, or inject custom logic before navigating to the URL.
- **`before_goto`**: Called before navigating to the URL. Use this to add custom headers or perform other pre-navigation actions.
- **`after_goto`**: Called after navigation. Use this to verify content or log the URL.
- **`on_execution_started`**: Called after executing custom JavaScript. Use this to perform additional actions.
- **`before_return_html`**: Called before returning the HTML content. Use this to log details or preprocess the content.

### Additional Customizations

- **Resource Management**: Use `on_page_context_created` to block or modify requests (e.g., block images, fonts, or third-party scripts).
- **Dynamic Headers**: Use `before_goto` to add or modify headers dynamically based on the URL.
- **Authentication**: Use `on_browser_created` to handle login processes and set authentication cookies or tokens.
- **Content Analysis**: Use `before_return_html` to analyze or modify the extracted HTML content.

These hooks provide powerful customization options for tailoring the crawling process to your needs.

