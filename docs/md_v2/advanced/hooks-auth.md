# Hooks & Auth for AsyncWebCrawler

Crawl4AI's AsyncWebCrawler allows you to customize the behavior of the web crawler using hooks. Hooks are asynchronous functions that are called at specific points in the crawling process, allowing you to modify the crawler's behavior or perform additional actions. This example demonstrates how to use various hooks to customize the asynchronous crawling process.

## Example: Using Crawler Hooks with AsyncWebCrawler

Let's see how we can customize the AsyncWebCrawler using hooks! In this example, we'll:

1. Configure the browser when it's created.
2. Add custom headers before navigating to the URL.
3. Log the current URL after navigation.
4. Perform actions after JavaScript execution.
5. Log the length of the HTML before returning it.

### Hook Definitions

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from playwright.async_api import Page, Browser

async def on_browser_created(browser: Browser):
    print("[HOOK] on_browser_created")
    # Example customization: set browser viewport size
    context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = await context.new_page()
    
    # Example customization: logging in to a hypothetical website
    await page.goto('https://example.com/login')
    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.wait_for_selector('#welcome')
    
    # Add a custom cookie
    await context.add_cookies([{'name': 'test_cookie', 'value': 'cookie_value', 'url': 'https://example.com'}])
    
    await page.close()
    await context.close()

async def before_goto(page: Page):
    print("[HOOK] before_goto")
    # Example customization: add custom headers
    await page.set_extra_http_headers({'X-Test-Header': 'test'})

async def after_goto(page: Page):
    print("[HOOK] after_goto")
    # Example customization: log the URL
    print(f"Current URL: {page.url}")

async def on_execution_started(page: Page):
    print("[HOOK] on_execution_started")
    # Example customization: perform actions after JS execution
    await page.evaluate("console.log('Custom JS executed')")

async def before_return_html(page: Page, html: str):
    print("[HOOK] before_return_html")
    # Example customization: log the HTML length
    print(f"HTML length: {len(html)}")
    return page
```

### Using the Hooks with the AsyncWebCrawler

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

async def main():
    print("\n🔗 Using Crawler Hooks: Let's see how we can customize the AsyncWebCrawler using hooks!")
    
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(verbose=True)
    crawler_strategy.set_hook('on_browser_created', on_browser_created)
    crawler_strategy.set_hook('before_goto', before_goto)
    crawler_strategy.set_hook('after_goto', after_goto)
    crawler_strategy.set_hook('on_execution_started', on_execution_started)
    crawler_strategy.set_hook('before_return_html', before_return_html)
    
    async with AsyncWebCrawler(verbose=True, crawler_strategy=crawler_strategy) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            js_code="window.scrollTo(0, document.body.scrollHeight);",
            wait_for="footer"
        )

    print("📦 Crawler Hooks result:")
    print(result)

asyncio.run(main())
```

### Explanation

- `on_browser_created`: This hook is called when the Playwright browser is created. It sets up the browser context, logs in to a website, and adds a custom cookie.
- `before_goto`: This hook is called right before Playwright navigates to the URL. It adds custom HTTP headers.
- `after_goto`: This hook is called after Playwright navigates to the URL. It logs the current URL.
- `on_execution_started`: This hook is called after any custom JavaScript is executed. It performs additional JavaScript actions.
- `before_return_html`: This hook is called before returning the HTML content. It logs the length of the HTML content.

### Additional Ideas

- **Handling authentication**: Use the `on_browser_created` hook to handle login processes or set authentication tokens.
- **Dynamic header modification**: Modify headers based on the target URL or other conditions in the `before_goto` hook.
- **Content verification**: Use the `after_goto` hook to verify that the expected content is present on the page.
- **Custom JavaScript injection**: Inject and execute custom JavaScript using the `on_execution_started` hook.
- **Content preprocessing**: Modify or analyze the HTML content in the `before_return_html` hook before it's returned.

By using these hooks, you can customize the behavior of the AsyncWebCrawler to suit your specific needs, including handling authentication, modifying requests, and preprocessing content.