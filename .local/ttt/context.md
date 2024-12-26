File: 10_file_download.md
================================================================================
# Download Handling in Crawl4AI

This guide explains how to use Crawl4AI to handle file downloads during crawling. You'll learn how to trigger downloads, specify download locations, and access downloaded files.

## Enabling Downloads

To enable downloads, set the `accept_downloads` parameter in the `BrowserConfig` object and pass it to the crawler.

```python
from crawl4ai.async_configs import BrowserConfig, AsyncWebCrawler

async def main():
    config = BrowserConfig(accept_downloads=True)  # Enable downloads globally
    async with AsyncWebCrawler(config=config) as crawler:
        # ... your crawling logic ...

asyncio.run(main())
```

Or, enable it for a specific crawl by using `CrawlerRunConfig`:

```python
from crawl4ai.async_configs import CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(accept_downloads=True)
        result = await crawler.arun(url="https://example.com", config=config)
        # ...
```

## Specifying Download Location

Specify the download directory using the `downloads_path` attribute in the `BrowserConfig` object. If not provided, Crawl4AI defaults to creating a "downloads" directory inside the `.crawl4ai` folder in your home directory.

```python
from crawl4ai.async_configs import BrowserConfig
import os

downloads_path = os.path.join(os.getcwd(), "my_downloads")  # Custom download path
os.makedirs(downloads_path, exist_ok=True)

config = BrowserConfig(accept_downloads=True, downloads_path=downloads_path)

async def main():
    async with AsyncWebCrawler(config=config) as crawler:
        result = await crawler.arun(url="https://example.com")
        # ...
```

## Triggering Downloads

Downloads are typically triggered by user interactions on a web page, such as clicking a download button. Use `js_code` in `CrawlerRunConfig` to simulate these actions and `wait_for` to allow sufficient time for downloads to start.

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig(
    js_code="""
        const downloadLink = document.querySelector('a[href$=".exe"]');
        if (downloadLink) {
            downloadLink.click();
        }
    """,
    wait_for=5  # Wait 5 seconds for the download to start
)

result = await crawler.arun(url="https://www.python.org/downloads/", config=config)
```

## Accessing Downloaded Files

The `downloaded_files` attribute of the `CrawlResult` object contains paths to downloaded files.

```python
if result.downloaded_files:
    print("Downloaded files:")
    for file_path in result.downloaded_files:
        print(f"- {file_path}")
        file_size = os.path.getsize(file_path)
        print(f"- File size: {file_size} bytes")
else:
    print("No files downloaded.")
```

## Example: Downloading Multiple Files

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os
from pathlib import Path

async def download_multiple_files(url: str, download_path: str):
    config = BrowserConfig(accept_downloads=True, downloads_path=download_path)
    async with AsyncWebCrawler(config=config) as crawler:
        run_config = CrawlerRunConfig(
            js_code="""
                const downloadLinks = document.querySelectorAll('a[download]');
                for (const link of downloadLinks) {
                    link.click();
                    await new Promise(r => setTimeout(r, 2000));  // Delay between clicks
                }
            """,
            wait_for=10  # Wait for all downloads to start
        )
        result = await crawler.arun(url=url, config=run_config)

        if result.downloaded_files:
            print("Downloaded files:")
            for file in result.downloaded_files:
                print(f"- {file}")
        else:
            print("No files downloaded.")

# Usage
download_path = os.path.join(Path.home(), ".crawl4ai", "downloads")
os.makedirs(download_path, exist_ok=True)

asyncio.run(download_multiple_files("https://www.python.org/downloads/windows/", download_path))
```

## Important Considerations

- **Browser Context:** Downloads are managed within the browser context. Ensure `js_code` correctly targets the download triggers on the webpage.
- **Timing:** Use `wait_for` in `CrawlerRunConfig` to manage download timing.
- **Error Handling:** Handle errors to manage failed downloads or incorrect paths gracefully.
- **Security:** Scan downloaded files for potential security threats before use.

This revised guide ensures consistency with the `Crawl4AI` codebase by using `BrowserConfig` and `CrawlerRunConfig` for all download-related configurations. Let me know if further adjustments are needed!
File: 11_page_interaction.md
================================================================================
# Page Interaction

Crawl4AI provides powerful features for interacting with dynamic webpages, handling JavaScript execution, and managing page events.

## JavaScript Execution

### Basic Execution

```python
from crawl4ai.async_configs import CrawlerRunConfig

# Single JavaScript command
config = CrawlerRunConfig(
    js_code="window.scrollTo(0, document.body.scrollHeight);"
)
result = await crawler.arun(url="https://example.com", config=config)

# Multiple commands
js_commands = [
    "window.scrollTo(0, document.body.scrollHeight);",
    "document.querySelector('.load-more').click();",
    "document.querySelector('#consent-button').click();"
]
config = CrawlerRunConfig(js_code=js_commands)
result = await crawler.arun(url="https://example.com", config=config)
```

### Wait Conditions

### CSS-Based Waiting

Wait for elements to appear:

```python
config = CrawlerRunConfig(wait_for="css:.dynamic-content")  # Wait for element with class 'dynamic-content'
result = await crawler.arun(url="https://example.com", config=config)
```

### JavaScript-Based Waiting

Wait for custom conditions:

```python
# Wait for number of elements
wait_condition = """() => {
    return document.querySelectorAll('.item').length > 10;
}"""

config = CrawlerRunConfig(wait_for=f"js:{wait_condition}")
result = await crawler.arun(url="https://example.com", config=config)

# Wait for dynamic content to load
wait_for_content = """() => {
    const content = document.querySelector('.content');
    return content && content.innerText.length > 100;
}"""

config = CrawlerRunConfig(wait_for=f"js:{wait_for_content}")
result = await crawler.arun(url="https://example.com", config=config)
```

### Handling Dynamic Content

### Load More Content

Handle infinite scroll or load more buttons:

```python
config = CrawlerRunConfig(
    js_code=[
        "window.scrollTo(0, document.body.scrollHeight);",  # Scroll to bottom
        "const loadMore = document.querySelector('.load-more'); if(loadMore) loadMore.click();"  # Click load more
    ],
    wait_for="js:() => document.querySelectorAll('.item').length > previousCount"  # Wait for new content
)
result = await crawler.arun(url="https://example.com", config=config)
```

### Form Interaction

Handle forms and inputs:

```python
js_form_interaction = """
    document.querySelector('#search').value = 'search term';  // Fill form fields
    document.querySelector('form').submit();                 // Submit form
"""

config = CrawlerRunConfig(
    js_code=js_form_interaction,
    wait_for="css:.results"  # Wait for results to load
)
result = await crawler.arun(url="https://example.com", config=config)
```

### Timing Control

### Delays and Timeouts

Control timing of interactions:

```python
config = CrawlerRunConfig(
    page_timeout=60000,              # Page load timeout (ms)
    delay_before_return_html=2.0     # Wait before capturing content
)
result = await crawler.arun(url="https://example.com", config=config)
```

### Complex Interactions Example

Here's an example of handling a dynamic page with multiple interactions:

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def crawl_dynamic_content():
    async with AsyncWebCrawler() as crawler:
        # Initial page load
        config = CrawlerRunConfig(
            js_code="document.querySelector('.cookie-accept')?.click();",  # Handle cookie consent
            wait_for="css:.main-content"
        )
        result = await crawler.arun(url="https://example.com", config=config)

        # Load more content
        session_id = "dynamic_session"  # Keep session for multiple interactions
        
        for page in range(3):  # Load 3 pages of content
            config = CrawlerRunConfig(
                session_id=session_id,
                js_code=[
                    "window.scrollTo(0, document.body.scrollHeight);",  # Scroll to bottom
                    "window.previousCount = document.querySelectorAll('.item').length;",  # Store item count
                    "document.querySelector('.load-more')?.click();"   # Click load more
                ],
                wait_for="""() => {
                    const currentCount = document.querySelectorAll('.item').length;
                    return currentCount > window.previousCount;
                }""",
                js_only=(page > 0)  # Execute JS without reloading page for subsequent interactions
            )
            result = await crawler.arun(url="https://example.com", config=config)
            print(f"Page {page + 1} items:", len(result.cleaned_html))

        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
```

### Using with Extraction Strategies

Combine page interaction with structured extraction:

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig

# Pattern-based extraction after interaction
schema = {
    "name": "Dynamic Items",
    "baseSelector": ".item",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "description", "selector": ".desc", "type": "text"}
    ]
}

config = CrawlerRunConfig(
    js_code="window.scrollTo(0, document.body.scrollHeight);",
    wait_for="css:.item:nth-child(10)",  # Wait for 10 items
    extraction_strategy=JsonCssExtractionStrategy(schema)
)
result = await crawler.arun(url="https://example.com", config=config)

# Or use LLM to analyze dynamic content
class ContentAnalysis(BaseModel):
    topics: List[str]
    summary: str

config = CrawlerRunConfig(
    js_code="document.querySelector('.show-more').click();",
    wait_for="css:.full-content",
    extraction_strategy=LLMExtractionStrategy(
        provider="ollama/nemotron",
        schema=ContentAnalysis.schema(),
        instruction="Analyze the full content"
    )
)
result = await crawler.arun(url="https://example.com", config=config)
```

File: 12_prefix_based_input.md
================================================================================
# Prefix-Based Input Handling in Crawl4AI

This guide will walk you through using the Crawl4AI library to crawl web pages, local HTML files, and raw HTML strings. We'll demonstrate these capabilities using a Wikipedia page as an example.

## Crawling a Web URL

To crawl a live web page, provide the URL starting with `http://` or `https://`, using a `CrawlerRunConfig` object:

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def crawl_web():
    config = CrawlerRunConfig(bypass_cache=True)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://en.wikipedia.org/wiki/apple", config=config)
        if result.success:
            print("Markdown Content:")
            print(result.markdown)
        else:
            print(f"Failed to crawl: {result.error_message}")

asyncio.run(crawl_web())
```

## Crawling a Local HTML File

To crawl a local HTML file, prefix the file path with `file://`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def crawl_local_file():
    local_file_path = "/path/to/apple.html"  # Replace with your file path
    file_url = f"file://{local_file_path}"
    config = CrawlerRunConfig(bypass_cache=True)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=file_url, config=config)
        if result.success:
            print("Markdown Content from Local File:")
            print(result.markdown)
        else:
            print(f"Failed to crawl local file: {result.error_message}")

asyncio.run(crawl_local_file())
```

## Crawling Raw HTML Content

To crawl raw HTML content, prefix the HTML string with `raw:`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def crawl_raw_html():
    raw_html = "<html><body><h1>Hello, World!</h1></body></html>"
    raw_html_url = f"raw:{raw_html}"
    config = CrawlerRunConfig(bypass_cache=True)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=raw_html_url, config=config)
        if result.success:
            print("Markdown Content from Raw HTML:")
            print(result.markdown)
        else:
            print(f"Failed to crawl raw HTML: {result.error_message}")

asyncio.run(crawl_raw_html())
```

---

## Complete Example

Below is a comprehensive script that:

1. Crawls the Wikipedia page for "Apple."
2. Saves the HTML content to a local file (`apple.html`).
3. Crawls the local HTML file and verifies the markdown length matches the original crawl.
4. Crawls the raw HTML content from the saved file and verifies consistency.

```python
import os
import sys
import asyncio
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def main():
    wikipedia_url = "https://en.wikipedia.org/wiki/apple"
    script_dir = Path(__file__).parent
    html_file_path = script_dir / "apple.html"

    async with AsyncWebCrawler() as crawler:
        # Step 1: Crawl the Web URL
        print("\n=== Step 1: Crawling the Wikipedia URL ===")
        web_config = CrawlerRunConfig(bypass_cache=True)
        result = await crawler.arun(url=wikipedia_url, config=web_config)

        if not result.success:
            print(f"Failed to crawl {wikipedia_url}: {result.error_message}")
            return

        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(result.html)
        web_crawl_length = len(result.markdown)
        print(f"Length of markdown from web crawl: {web_crawl_length}\n")

        # Step 2: Crawl from the Local HTML File
        print("=== Step 2: Crawling from the Local HTML File ===")
        file_url = f"file://{html_file_path.resolve()}"
        file_config = CrawlerRunConfig(bypass_cache=True)
        local_result = await crawler.arun(url=file_url, config=file_config)

        if not local_result.success:
            print(f"Failed to crawl local file {file_url}: {local_result.error_message}")
            return

        local_crawl_length = len(local_result.markdown)
        assert web_crawl_length == local_crawl_length, "Markdown length mismatch"
        print("✅ Markdown length matches between web and local file crawl.\n")

        # Step 3: Crawl Using Raw HTML Content
        print("=== Step 3: Crawling Using Raw HTML Content ===")
        with open(html_file_path, 'r', encoding='utf-8') as f:
            raw_html_content = f.read()
        raw_html_url = f"raw:{raw_html_content}"
        raw_config = CrawlerRunConfig(bypass_cache=True)
        raw_result = await crawler.arun(url=raw_html_url, config=raw_config)

        if not raw_result.success:
            print(f"Failed to crawl raw HTML content: {raw_result.error_message}")
            return

        raw_crawl_length = len(raw_result.markdown)
        assert web_crawl_length == raw_crawl_length, "Markdown length mismatch"
        print("✅ Markdown length matches between web and raw HTML crawl.\n")

        print("All tests passed successfully!")
    if html_file_path.exists():
        os.remove(html_file_path)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Conclusion

With the unified `url` parameter and prefix-based handling in **Crawl4AI**, you can seamlessly handle web URLs, local HTML files, and raw HTML content. Use `CrawlerRunConfig` for flexible and consistent configuration in all scenarios.
File: 13_hooks_auth.md
================================================================================
# Hooks & Auth for AsyncWebCrawler

Crawl4AI's `AsyncWebCrawler` allows you to customize the behavior of the web crawler using hooks. Hooks are asynchronous functions called at specific points in the crawling process, allowing you to modify the crawler's behavior or perform additional actions. This updated documentation demonstrates how to use hooks, including the new `on_page_context_created` hook, and ensures compatibility with `BrowserConfig` and `CrawlerRunConfig`.

In this example, we'll:

1. Configure the browser and set up authentication when it's created.
2. Apply custom routing and initial actions when the page context is created.
3. Add custom headers before navigating to the URL.
4. Log the current URL after navigation.
5. Perform actions after JavaScript execution.
6. Log the length of the HTML before returning it.

## Hook Definitions

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

## Using the Hooks with AsyncWebCrawler

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

## Explanation of Hooks

- **`on_browser_created`**: Called when the browser is created. Use this to configure the browser or handle authentication (e.g., logging in and setting cookies).
- **`on_page_context_created`**: Called when a new page context is created. Use this to apply routing, block resources, or inject custom logic before navigating to the URL.
- **`before_goto`**: Called before navigating to the URL. Use this to add custom headers or perform other pre-navigation actions.
- **`after_goto`**: Called after navigation. Use this to verify content or log the URL.
- **`on_execution_started`**: Called after executing custom JavaScript. Use this to perform additional actions.
- **`before_return_html`**: Called before returning the HTML content. Use this to log details or preprocess the content.

## Additional Customizations

- **Resource Management**: Use `on_page_context_created` to block or modify requests (e.g., block images, fonts, or third-party scripts).
- **Dynamic Headers**: Use `before_goto` to add or modify headers dynamically based on the URL.
- **Authentication**: Use `on_browser_created` to handle login processes and set authentication cookies or tokens.
- **Content Analysis**: Use `before_return_html` to analyze or modify the extracted HTML content.

These hooks provide powerful customization options for tailoring the crawling process to your needs.


File: 14_proxy_security.md
================================================================================
# Proxy & Security

Configure proxy settings and enhance security features in Crawl4AI for reliable data extraction.

## Basic Proxy Setup

Simple proxy configuration with `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig

# Using proxy URL
browser_config = BrowserConfig(proxy="http://proxy.example.com:8080")
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")

# Using SOCKS proxy
browser_config = BrowserConfig(proxy="socks5://proxy.example.com:1080")
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Authenticated Proxy

Use an authenticated proxy with `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig

proxy_config = {
    "server": "http://proxy.example.com:8080",
    "username": "user",
    "password": "pass"
}

browser_config = BrowserConfig(proxy_config=proxy_config)
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Rotating Proxies

Example using a proxy rotation service and updating `BrowserConfig` dynamically:

```python
from crawl4ai.async_configs import BrowserConfig

async def get_next_proxy():
    # Your proxy rotation logic here
    return {"server": "http://next.proxy.com:8080"}

browser_config = BrowserConfig()
async with AsyncWebCrawler(config=browser_config) as crawler:
    # Update proxy for each request
    for url in urls:
        proxy = await get_next_proxy()
        browser_config.proxy_config = proxy
        result = await crawler.arun(url=url, config=browser_config)
```

## Custom Headers

Add security-related headers via `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig

headers = {
    "X-Forwarded-For": "203.0.113.195",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

browser_config = BrowserConfig(headers=headers)
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Combining with Magic Mode

For maximum protection, combine proxy with Magic Mode via `CrawlerRunConfig` and `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(
    proxy="http://proxy.example.com:8080",
    headers={"Accept-Language": "en-US"}
)
crawler_config = CrawlerRunConfig(magic=True)  # Enable all anti-detection features

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com", config=crawler_config)
```

File: 15_screenshot_and_pdf_export.md
================================================================================
# Capturing Full-Page Screenshots and PDFs from Massive Webpages with Crawl4AI

When dealing with very long web pages, traditional full-page screenshots can be slow or fail entirely. For large pages (like extensive Wikipedia articles), generating a single massive screenshot often leads to delays, memory issues, or style differences.

## **The New Approach:**
We’ve introduced a new feature that effortlessly handles even the biggest pages by first exporting them as a PDF, then converting that PDF into a high-quality image. This approach leverages the browser’s built-in PDF rendering, making it both stable and efficient for very long content. You also have the option to directly save the PDF for your own usage—no need for multiple passes or complex stitching logic.

## **Key Benefits:**
- **Reliability:** The PDF export never times out and works regardless of page length.
- **Versatility:** Get both the PDF and a screenshot in one crawl, without reloading or reprocessing.
- **Performance:** Skips manual scrolling and stitching images, reducing complexity and runtime.

## **Simple Example:**
```python
import os, sys
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode

# Adjust paths as needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

async def main():
    async with AsyncWebCrawler() as crawler:
        # Request both PDF and screenshot
        result = await crawler.arun(
            url='https://en.wikipedia.org/wiki/List_of_common_misconceptions',
            cache_mode=CacheMode.BYPASS,
            pdf=True,
            screenshot=True
        )
        
        if result.success:
            # Save screenshot
            if result.screenshot:
                from base64 import b64decode
                with open(os.path.join(__location__, "screenshot.png"), "wb") as f:
                    f.write(b64decode(result.screenshot))
            
            # Save PDF
            if result.pdf:
                pdf_bytes = b64decode(result.pdf)
                with open(os.path.join(__location__, "page.pdf"), "wb") as f:
                    f.write(pdf_bytes)

if __name__ == "__main__":
    asyncio.run(main())
```

## **What Happens Under the Hood:**
- Crawl4AI navigates to the target page.
- If `pdf=True`, it exports the current page as a full PDF, capturing all of its content no matter the length.
- If `screenshot=True`, and a PDF is already available, it directly converts the first page of that PDF to an image for you—no repeated loading or scrolling.
- Finally, you get your PDF and/or screenshot ready to use.

## **Conclusion:**
With this feature, Crawl4AI becomes even more robust and versatile for large-scale content extraction. Whether you need a PDF snapshot or a quick screenshot, you now have a reliable solution for even the most extensive webpages.
File: 16_storage_state.md
================================================================================
# Using `storage_state` to Pre-Load Cookies and LocalStorage

Crawl4ai’s `AsyncWebCrawler` lets you preserve and reuse session data, including cookies and localStorage, across multiple runs. By providing a `storage_state`, you can start your crawls already “logged in” or with any other necessary session data—no need to repeat the login flow every time.

## What is `storage_state`?

`storage_state` can be:

- A dictionary containing cookies and localStorage data.
- A path to a JSON file that holds this information.

When you pass `storage_state` to the crawler, it applies these cookies and localStorage entries before loading any pages. This means your crawler effectively starts in a known authenticated or pre-configured state.

## Example Structure

Here’s an example storage state:

```json
{
  "cookies": [
    {
      "name": "session",
      "value": "abcd1234",
      "domain": "example.com",
      "path": "/",
      "expires": 1675363572.037711,
      "httpOnly": false,
      "secure": false,
      "sameSite": "None"
    }
  ],
  "origins": [
    {
      "origin": "https://example.com",
      "localStorage": [
        { "name": "token", "value": "my_auth_token" },
        { "name": "refreshToken", "value": "my_refresh_token" }
      ]
    }
  ]
}
```

This JSON sets a `session` cookie and two localStorage entries (`token` and `refreshToken`) for `https://example.com`.

---

## Passing `storage_state` as a Dictionary

You can directly provide the data as a dictionary:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    storage_dict = {
        "cookies": [
            {
                "name": "session",
                "value": "abcd1234",
                "domain": "example.com",
                "path": "/",
                "expires": 1675363572.037711,
                "httpOnly": False,
                "secure": False,
                "sameSite": "None"
            }
        ],
        "origins": [
            {
                "origin": "https://example.com",
                "localStorage": [
                    {"name": "token", "value": "my_auth_token"},
                    {"name": "refreshToken", "value": "my_refresh_token"}
                ]
            }
        ]
    }

    async with AsyncWebCrawler(
        headless=True,
        storage_state=storage_dict
    ) as crawler:
        result = await crawler.arun(url='https://example.com/protected')
        if result.success:
            print("Crawl succeeded with pre-loaded session data!")
            print("Page HTML length:", len(result.html))

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Passing `storage_state` as a File

If you prefer a file-based approach, save the JSON above to `mystate.json` and reference it:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(
        headless=True,
        storage_state="mystate.json"  # Uses a JSON file instead of a dictionary
    ) as crawler:
        result = await crawler.arun(url='https://example.com/protected')
        if result.success:
            print("Crawl succeeded with pre-loaded session data!")
            print("Page HTML length:", len(result.html))

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Using `storage_state` to Avoid Repeated Logins (Sign In Once, Use Later)

A common scenario is when you need to log in to a site (entering username/password, etc.) to access protected pages. Doing so every crawl is cumbersome. Instead, you can:

1. Perform the login once in a hook.
2. After login completes, export the resulting `storage_state` to a file.
3. On subsequent runs, provide that `storage_state` to skip the login step.

**Step-by-Step Example:**

**First Run (Perform Login and Save State):**

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def on_browser_created_hook(browser):
    # Access the default context and create a page
    context = browser.contexts[0]
    page = await context.new_page()
    
    # Navigate to the login page
    await page.goto("https://example.com/login", wait_until="domcontentloaded")
    
    # Fill in credentials and submit
    await page.fill("input[name='username']", "myuser")
    await page.fill("input[name='password']", "mypassword")
    await page.click("button[type='submit']")
    await page.wait_for_load_state("networkidle")
    
    # Now the site sets tokens in localStorage and cookies
    # Export this state to a file so we can reuse it
    await context.storage_state(path="my_storage_state.json")
    await page.close()

async def main():
    # First run: perform login and export the storage_state
    async with AsyncWebCrawler(
        headless=True,
        verbose=True,
        hooks={"on_browser_created": on_browser_created_hook},
        use_persistent_context=True,
        user_data_dir="./my_user_data"
    ) as crawler:
        
        # After on_browser_created_hook runs, we have storage_state saved to my_storage_state.json
        result = await crawler.arun(
            url='https://example.com/protected-page',
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("First run result success:", result.success)
        if result.success:
            print("Protected page HTML length:", len(result.html))

if __name__ == "__main__":
    asyncio.run(main())
```

**Second Run (Reuse Saved State, No Login Needed):**

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    # Second run: no need to hook on_browser_created this time.
    # Just provide the previously saved storage state.
    async with AsyncWebCrawler(
        headless=True,
        verbose=True,
        use_persistent_context=True,
        user_data_dir="./my_user_data",
        storage_state="my_storage_state.json"  # Reuse previously exported state
    ) as crawler:
        
        # Now the crawler starts already logged in
        result = await crawler.arun(
            url='https://example.com/protected-page',
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("Second run result success:", result.success)
        if result.success:
            print("Protected page HTML length:", len(result.html))

if __name__ == "__main__":
    asyncio.run(main())
```

**What’s Happening Here?**

- During the first run, the `on_browser_created_hook` logs into the site.  
- After logging in, the crawler exports the current session (cookies, localStorage, etc.) to `my_storage_state.json`.  
- On subsequent runs, passing `storage_state="my_storage_state.json"` starts the browser context with these tokens already in place, skipping the login steps.

**Sign Out Scenario:**  
If the website allows you to sign out by clearing tokens or by navigating to a sign-out URL, you can also run a script that uses `on_browser_created_hook` or `arun` to simulate signing out, then export the resulting `storage_state` again. That would give you a baseline “logged out” state to start fresh from next time.

---

## Conclusion

By using `storage_state`, you can skip repetitive actions, like logging in, and jump straight into crawling protected content. Whether you provide a file path or a dictionary, this powerful feature helps maintain state between crawls, simplifying your data extraction pipelines.
File: 1_introduction.ex.md
================================================================================
# Introduction

## Quick Start (Minimal Example)
For a fast hands-on start, try crawling a single URL and printing its Markdown output:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

This simple snippet should immediately confirm your environment is set up correctly. If you see the page content in Markdown format, you’re good to go.

---

## Overview of Crawl4AI
Crawl4AI is a state-of-the-art, **asynchronous** web crawling library optimized for large-scale data collection. It’s built to integrate seamlessly into AI workflows such as fine-tuning, retrieval-augmented generation (RAG), and data pipelines. By focusing on generating structured, AI-ready data (like Markdown), it helps you build robust applications quickly.

**Why Asynchronous?**  
Async architecture allows you to concurrently crawl multiple URLs without waiting on slow network operations. This results in drastically improved performance and efficiency, especially when dealing with large-scale data extraction.

### Purpose and Vision
- Offer an open-source alternative to expensive commercial APIs.
- Provide clean, structured, Markdown-based outputs for easy AI integration.
- Democratize large-scale, high-speed, and reliable web crawling solutions.

### Key Features
- **Markdown Generation**: Produces AI-friendly, concise Markdown.
- **High-Performance Crawling**: Asynchronous operations let you crawl numerous URLs concurrently.
- **Browser Control**: Fine-tune browser sessions, user agents, proxies, and viewport.
- **JavaScript Support**: Handle dynamic pages by injecting custom JavaScript snippets.
- **Content Filtering**: Use advanced strategies (e.g., BM25) to focus on what matters.
- **Extensibility**: Define custom extraction strategies for complex data schemas.
- **Deployment Ready**: Easy Docker deployment for production and scalability.

---

## Use Cases
- **LLM Training and Fine-Tuning**: Collect and preprocess large web datasets to train machine learning models.
- **RAG Pipelines**: Generate context documents for retrieval-augmented generation tasks.
- **Content Summarization**: Extract pages and produce summaries directly in Markdown.
- **Structured Data Extraction**: Pull structured JSON data suitable for building knowledge graphs or databases.

**Example: Creating a Fine-Tuning Dataset**
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    urls = ["https://example.com/dataset_page_1", "https://example.com/dataset_page_2"]
    async with AsyncWebCrawler(verbose=True) as crawler:
        results = await asyncio.gather(*[crawler.arun(url=u) for u in urls])
        # Combine Markdown outputs into a single file for model fine-tuning
        with open("fine_tuning_data.md", "w") as f:
            for res in results:
                f.write(res.markdown + "\n")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Installation and Setup

### Environment Setup (Recommended)
Use a virtual environment to keep dependencies isolated:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Basic Installation
```bash
pip install crawl4ai
crawl4ai-setup
```

By default, this installs the asynchronous version and sets up Playwright.

### Verify Installation
Run a quick test:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://crawl4ai.com")
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

If you see the page content printed as Markdown, you’re ready.

### Handling JavaScript-Heavy Pages
For pages that require JavaScript actions (like clicking a “Load More” button), use the `js_code` parameter:

```python
js_code = """
(async () => {
    const loadMoreBtn = document.querySelector('button.load-more');
    if (loadMoreBtn) loadMoreBtn.click();
    await new Promise(r => setTimeout(r, 1000));
})();
"""

async with AsyncWebCrawler(verbose=True) as crawler:
    result = await crawler.arun(
        url="https://example.com/js-page",
        js_code=[js_code]
    )
    print(result.markdown)
```

### Using Cache Modes
`CacheMode` can speed up repeated crawls by reusing previously fetched data. For instance:

```python
from crawl4ai import AsyncWebCrawler, CacheMode

async with AsyncWebCrawler(verbose=True) as crawler:
    result = await crawler.arun(
        url="https://example.com/large-page",
        cache_mode=CacheMode.ENABLED
    )
    print(result.markdown)
```

---

## Quick Start Guide

### Minimal Working Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://crawl4ai.com")
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

### Multiple Concurrent Crawls
Harness async concurrency to run multiple crawls in parallel:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def crawl_url(crawler, url):
    return await crawler.arun(url=url)

async def main():
    urls = ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"]
    async with AsyncWebCrawler(verbose=True) as crawler:
        results = await asyncio.gather(*[crawl_url(crawler, u) for u in urls])
        for r in results:
            print(r.markdown[:200])

if __name__ == "__main__":
    asyncio.run(main())
```

### Dockerized Setup
Run Crawl4AI in Docker for production environments:

```bash
docker pull unclecode/crawl4ai:basic-amd64
docker run -p 11235:11235 unclecode/crawl4ai:basic-amd64
curl http://localhost:11235/health
```

### Proxy and Security Configurations
```python
async with AsyncWebCrawler(
    proxies={"http": "http://proxy.server:port", "https": "https://proxy.server:port"}
) as crawler:
    result = await crawler.arun(url="https://crawl4ai.com")
    print(result.markdown)
```

You can also add basic auth:

```python
async with AsyncWebCrawler(
    proxies={"http": "http://user:password@proxy.server:port"}
) as crawler:
    result = await crawler.arun(url="https://crawl4ai.com")
    print(result.markdown)
```

### Customizing Browser Settings
Customize headers, user agents, and viewport:

```python
async with AsyncWebCrawler(
    verbose=True,
    headers={"User-Agent": "MyCustomBrowser/1.0"},
    viewport={"width": 1280, "height": 800}
) as crawler:
    result = await crawler.arun("https://example.com")
    print(result.markdown)
```

---

## Troubleshooting Installation

### Playwright Errors
If `crawl4ai-setup` fails, install manually:
```bash
playwright install chromium
pip install crawl4ai[all]
```

### SSL or Proxy Issues
- Check certificates or disable SSL verification (for dev only).
- Verify proxy credentials and server details.

Use `verbose=True` for detailed logs:
```python
async with AsyncWebCrawler(verbose=True) as crawler:
    result = await crawler.arun(url="https://crawl4ai.com")
    print(result.markdown)
```

---

## Common Pitfalls

1. **Missing Playwright Installation**: Run `playwright install chromium`.
2. **Time-Out on JavaScript-Heavy Pages**: Increase wait time or use `js_code` for page interactions.
3. **Empty Markdown**: Check if the page is JavaScript-rendered and adjust `js_code` or `wait_for` conditions.
4. **Permission Errors**: Run commands with appropriate permissions or use a virtual environment.

---

## Support and Community
- **GitHub Issues**: Have questions or found a bug? Open an issue on the [GitHub Repo](https://github.com/unclecode/crawl4ai/issues).
- **Contributions**: We welcome pull requests. Check out the [contribution guidelines](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTING.md).
- **Community Discussions**: Join discussions on GitHub to share tips, best practices, and feedback.

---

## Further Exploration
- **Advanced Extraction Strategies**: Dive into specialized extraction strategies like `JsonCssExtractionStrategy` or `LLMExtractionStrategy` for structured data output.
- **Content Filtering**: Explore BM25-based strategies to highlight the most relevant parts of a page.
- **Production Deployment**: Refer to the Docker and environment variable configurations for large-scale, distributed crawling setups.

For more detailed code examples and advanced topics, refer to the accompanying [README](https://github.com/unclecode/crawl4ai) and the `QUICKSTART` Python file included with this distribution.
File: 2_configuration.md
================================================================================
# Core Configurations

## BrowserConfig
`BrowserConfig` centralizes all parameters required to set up and manage a browser instance and its context. This configuration ensures consistent and documented browser behavior for the crawler. Below is a detailed explanation of each parameter and its optimal use cases.

### Parameters and Use Cases

#### `browser_type`
- **Description**: Specifies the type of browser to launch.
  - Supported values: `"chromium"`, `"firefox"`, `"webkit"`
  - Default: `"chromium"`
- **Use Case**:
  - Use `"chromium"` for general-purpose crawling with modern web standards.
  - Use `"firefox"` when testing against Firefox-specific behavior.
  - Use `"webkit"` for testing Safari-like environments.

#### `headless`
- **Description**: Determines whether the browser runs in headless mode (no GUI).
  - Default: `True`
- **Use Case**:
  - Enable for faster, automated operations without UI overhead.
  - Disable (`False`) when debugging or inspecting browser behavior visually.

#### `use_managed_browser`
- **Description**: Enables advanced manipulation via a managed browser approach.
  - Default: `False`
- **Use Case**:
  - Use when fine-grained control is needed over browser sessions, such as debugging network requests or reusing sessions.

#### `debugging_port`
- **Description**: Port for remote debugging.
  - Default: 9222
- **Use Case**:
  - Use for debugging browser sessions with DevTools or external tools.

#### `use_persistent_context`
- **Description**: Uses a persistent browser context (e.g., saved profiles).
  - Automatically enables `use_managed_browser`.
  - Default: `False`
- **Use Case**:
  - Persistent login sessions for authenticated crawling.
  - Retaining cookies or local storage across multiple runs.

#### `user_data_dir`
- **Description**: Path to a directory for storing persistent browser data.
  - Default: `None`
- **Use Case**:
  - Specify a directory to save browser profiles for multi-run crawls or debugging.

#### `chrome_channel`
- **Description**: Specifies the Chrome channel to launch (e.g., `"chrome"`, `"msedge"`).
  - Applies only when `browser_type` is `"chromium"`.
  - Default: `"chrome"`
- **Use Case**:
  - Use `"msedge"` for compatibility testing with Edge browsers.

#### `proxy` and `proxy_config`
- **Description**:
  - `proxy`: Proxy server URL for the browser.
  - `proxy_config`: Detailed proxy configuration.
  - Default: `None`
- **Use Case**:
  - Set `proxy` for single-proxy setups.
  - Use `proxy_config` for advanced configurations, such as authenticated proxies or regional routing.

#### `viewport_width` and `viewport_height`
- **Description**: Sets the default browser viewport dimensions.
  - Default: `1920` (width), `1080` (height)
- **Use Case**:
  - Adjust for crawling responsive layouts or specific device emulations.

#### `accept_downloads` and `downloads_path`
- **Description**:
  - `accept_downloads`: Allows file downloads.
  - `downloads_path`: Directory for storing downloads.
  - Default: `False`, `None`
- **Use Case**:
  - Use when downloading and analyzing files like PDFs or spreadsheets.

#### `storage_state`
- **Description**: Specifies cookies and local storage state.
  - Default: `None`
- **Use Case**:
  - Provide state data for authenticated or preconfigured sessions.

#### `ignore_https_errors`
- **Description**: Ignores HTTPS certificate errors.
  - Default: `True`
- **Use Case**:
  - Enable for crawling sites with invalid certificates (testing environments).

#### `java_script_enabled`
- **Description**: Toggles JavaScript execution in pages.
  - Default: `True`
- **Use Case**:
  - Disable for simpler, faster crawls where JavaScript is unnecessary.

#### `cookies`
- **Description**: List of cookies to add to the browser context.
  - Default: `[]`
- **Use Case**:
  - Use for authenticated or preconfigured crawling scenarios.

#### `headers`
- **Description**: Extra HTTP headers applied to all requests.
  - Default: `{}`
- **Use Case**:
  - Customize headers for API-like crawling or bypassing bot detections.

#### `user_agent` and `user_agent_mode`
- **Description**:
  - `user_agent`: Custom User-Agent string.
  - `user_agent_mode`: Mode for generating User-Agent (e.g., `"random"`).
  - Default: Standard Chromium-based User-Agent.
- **Use Case**:
  - Set static User-Agent for consistent identification.
  - Use `"random"` mode to reduce bot detection likelihood.

#### `text_mode`
- **Description**: Disables images and other rich content for faster load times.
  - Default: `False`
- **Use Case**:
  - Enable for text-only extraction tasks where speed is prioritized.

#### `light_mode`
- **Description**: Disables background features for performance gains.
  - Default: `False`
- **Use Case**:
  - Enable for high-performance crawls on resource-constrained environments.

#### `extra_args`
- **Description**: Additional command-line arguments for browser execution.
  - Default: `[]`
- **Use Case**:
  - Use for advanced browser configurations like WebRTC or GPU tuning.

## CrawlerRunConfig
The `CrawlerRunConfig` class centralizes parameters for controlling crawl operations. This configuration covers content extraction, page interactions, caching, and runtime behaviors. Below is an exhaustive breakdown of parameters and their best-use scenarios.

### Parameters and Use Cases

#### Content Processing Parameters

##### `word_count_threshold`
- **Description**: Minimum word count threshold for processing content.
  - Default: `200`
- **Use Case**:
  - Set a higher threshold for content-heavy pages to skip lightweight or irrelevant content.

##### `extraction_strategy`
- **Description**: Strategy for extracting structured data from crawled pages.
  - Default: `None` (uses `NoExtractionStrategy` by default).
- **Use Case**:
  - Use for schema-driven extraction when working with well-defined data models like JSON.

##### `chunking_strategy`
- **Description**: Strategy to chunk content before extraction.
  - Default: `RegexChunking()`.
- **Use Case**:
  - Use NLP-based chunking for semantic extractions or regex for predictable text blocks.

##### `markdown_generator`
- **Description**: Strategy for generating Markdown output.
  - Default: `None`.
- **Use Case**:
  - Use custom Markdown strategies for AI-ready outputs like RAG pipelines.

##### `content_filter`
- **Description**: Optional filter to prune irrelevant content.
  - Default: `None`.
- **Use Case**:
  - Use relevance-based filters for focused crawls, e.g., keyword-specific searches.

##### `only_text`
- **Description**: Extracts text-only content where applicable.
  - Default: `False`.
- **Use Case**:
  - Enable for extracting clean text without HTML tags or rich content.

##### `css_selector`
- **Description**: CSS selector to extract a specific portion of the page.
  - Default: `None`.
- **Use Case**:
  - Use when targeting specific page elements, like articles or headlines.

##### `excluded_tags`
- **Description**: List of HTML tags to exclude from processing.
  - Default: `None`.
- **Use Case**:
  - Remove elements like `<script>` or `<style>` during text extraction.

##### `keep_data_attributes`
- **Description**: Retain `data-*` attributes in the HTML.
  - Default: `False`.
- **Use Case**:
  - Enable for extracting custom attributes in HTML structures.

##### `remove_forms`
- **Description**: Removes all `<form>` elements from the page.
  - Default: `False`.
- **Use Case**:
  - Use when forms are irrelevant and clutter the extracted content.

##### `prettiify`
- **Description**: Beautifies the HTML output.
  - Default: `False`.
- **Use Case**:
  - Enable for generating readable HTML outputs.

---

#### Caching Parameters

##### `cache_mode`
- **Description**: Controls how caching is handled.
  - Default: `CacheMode.ENABLED`.
- **Use Case**:
  - Use `WRITE_ONLY` mode for crawls where fresh content is critical.

##### `session_id`
- **Description**: Specifies a session ID to persist browser context.
  - Default: `None`.
- **Use Case**:
  - Use for maintaining login states or multi-page workflows.

##### `bypass_cache`, `disable_cache`, `no_cache_read`, `no_cache_write`
- **Description**: Legacy parameters for cache handling.
  - Default: `False`.
- **Use Case**:
  - These options provide finer control when overriding default caching behaviors.

---

#### Page Navigation and Timing Parameters

##### `wait_until`
- **Description**: Defines the navigation wait condition (e.g., `"domcontentloaded"`).
  - Default: `"domcontentloaded"`.
- **Use Case**:
  - Adjust to `"networkidle"` for pages with heavy JavaScript rendering.

##### `page_timeout`
- **Description**: Timeout in milliseconds for page operations.
  - Default: `60000` (60 seconds).
- **Use Case**:
  - Increase for slow-loading pages or complex sites.

##### `wait_for`
- **Description**: CSS selector or JS condition to wait for before extraction.
  - Default: `None`.
- **Use Case**:
  - Use for dynamic content that requires specific elements to load.

##### `wait_for_images`
- **Description**: Waits for images to load before content extraction.
  - Default: `True`.
- **Use Case**:
  - Disable for faster crawls when image data isn’t required.

##### `delay_before_return_html`
- **Description**: Delay in seconds before retrieving HTML.
  - Default: `0.1`.
- **Use Case**:
  - Use for ensuring final DOM updates are captured.

##### `mean_delay` and `max_range`
- **Description**: Configures base and random delays between requests.
  - Default: `0.1` (mean), `0.3` (max).
- **Use Case**:
  - Increase for stealthy crawls to avoid bot detection.

##### `semaphore_count`
- **Description**: Number of concurrent operations allowed.
  - Default: `5`.
- **Use Case**:
  - Adjust based on system resources and network limitations.

---

#### Page Interaction Parameters

##### `js_code`
- **Description**: JavaScript code or snippets to execute on the page.
  - Default: `None`.
- **Use Case**:
  - Use for custom interactions like clicking tabs or dynamically loading content.

##### `js_only`
- **Description**: Indicates subsequent calls rely only on JS updates.
  - Default: `False`.
- **Use Case**:
  - Enable for single-page applications (SPAs) with dynamic content.

##### `scan_full_page`
- **Description**: Simulates scrolling to load all content.
  - Default: `False`.
- **Use Case**:
  - Use for infinite-scroll pages or loading all dynamic elements.

##### `adjust_viewport_to_content`
- **Description**: Adjusts viewport to match content dimensions.
  - Default: `False`.
- **Use Case**:
  - Enable for capturing content-heavy pages fully.

---

#### Media Handling Parameters

##### `screenshot`
- **Description**: Captures a screenshot after crawling.
  - Default: `False`.
- **Use Case**:
  - Enable for visual debugging or reporting purposes.

##### `pdf`
- **Description**: Generates a PDF of the page.
  - Default: `False`.
- **Use Case**:
  - Use for archiving or sharing rendered page outputs.

##### `image_description_min_word_threshold` and `image_score_threshold`
- **Description**: Controls thresholds for image description extraction and processing.
  - Default: `50` (words), `3` (score).
- **Use Case**:
  - Adjust for higher relevance or descriptive quality of image metadata.

---

#### Debugging and Logging Parameters

##### `verbose`
- **Description**: Enables detailed logging.
  - Default: `True`.
- **Use Case**:
  - Use for troubleshooting or analyzing crawler behavior.

##### `log_console`
- **Description**: Logs browser console messages.
  - Default: `False`.
- **Use Case**:
  - Enable when debugging JavaScript errors on pages.


File: 3_async_webcrawler.ex.md
================================================================================
# Extended Documentation: Asynchronous Crawling with `AsyncWebCrawler`

This document provides a comprehensive, human-oriented overview of the `AsyncWebCrawler` class and related components from the `crawl4ai` package. It explains the motivations behind asynchronous crawling, shows how to configure and run crawls, and provides examples for advanced features like dynamic content handling, extraction strategies, caching, containerization, and troubleshooting.

## Introduction

Crawling websites can be slow if done sequentially, especially when handling large numbers of URLs or rendering dynamic pages. Asynchronous crawling helps you run multiple operations concurrently, improving throughput and performance. The `AsyncWebCrawler` class leverages asynchronous I/O and browser automation tools to fetch content efficiently, handle complex DOM interactions, and extract structured data.

### Quick Start

Before diving into advanced features, here is a quick start example that shows how to run a simple asynchronous crawl with a headless Chromium browser, extract basic text, and print the results.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def main():
    # Basic browser configuration
    browser_config = BrowserConfig(browser_type="chromium", headless=True)
    
    # Run the crawler asynchronously
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun("https://example.com")
        print("Extracted Markdown:")
        print(result.markdown)
        
asyncio.run(main())
```

This snippet initializes a headless Chromium browser, crawls the page, processes the HTML, and prints extracted content as Markdown.

## Browser Configuration

The `BrowserConfig` class defines browser-related settings and behaviors. You can customize:

- `browser_type`: Browser to use, such as `chromium` or `firefox`.
- `headless`: Run the browser in headless mode (no visible UI).
- `viewport_width` and `viewport_height`: Control viewport dimensions for rendering.
- `proxy`: Configure proxies to bypass IP restrictions.
- `verbose`: Control logging verbosity.

**Example: Customizing Browser Settings**

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    browser_type="firefox", 
    headless=False, 
    viewport_width=1920, 
    viewport_height=1080,
    verbose=True
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://yourwebsite.com")
    print(result.markdown)
```

### Running in Docker

For scalability and reproducibility, consider running your crawler inside a Docker container. A simple Dockerfile might look like this:

```dockerfile
FROM python:3.10-slim
RUN apt-get update && apt-get install -y wget
RUN pip install crawl4ai playwright
RUN playwright install chromium
COPY your_script.py /app/your_script.py
WORKDIR /app
CMD ["python", "your_script.py"]
```

You can then run:

```bash
docker build -t mycrawler .
docker run mycrawler
```

Within this container, `AsyncWebCrawler` will launch Chromium using Playwright and crawl sites as configured.

## Asynchronous Crawling Strategies

By default, `AsyncWebCrawler` uses `AsyncPlaywrightCrawlerStrategy`, which relies on Playwright for browser automation. This lets you interact with DOM elements, scroll, click buttons, and handle dynamic content. If other strategies are available, you can specify them during initialization.

```python
from crawl4ai import AsyncWebCrawler, AsyncPlaywrightCrawlerStrategy

crawler = AsyncWebCrawler(crawler_strategy=AsyncPlaywrightCrawlerStrategy())
```

## Handling Dynamic Content

Modern websites often load data via JavaScript or require user interactions. You can inject custom JavaScript snippets to manipulate the page, click buttons, or wait for certain elements to appear before extracting content.

**Example: Loading More Content**

```python
js_code = """
(async () => {
    const loadButtons = document.querySelectorAll(".load-more");
    for (const btn of loadButtons) btn.click();
    await new Promise(r => setTimeout(r, 2000)); // Wait for new content
})();
"""

from crawl4ai import CrawlerRunConfig

config = CrawlerRunConfig(js_code=[js_code])
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com/infinite-scroll", config=config)
    print("Extracted Markdown:")
    print(result.markdown)
```

You can also use Playwright selectors to wait for specific elements before extraction.

## Extraction and Filtering

`AsyncWebCrawler` supports various extraction strategies to convert raw HTML into structured data. For example, `JsonCssExtractionStrategy` allows you to specify CSS selectors and get structured JSON from the page. `LLMExtractionStrategy` can feed extracted text into a language model for intelligent data extraction.

You can also apply content filters and chunking strategies to split large documents into smaller pieces before processing.

**Example: Using a JSON CSS Extraction Strategy**

```python
from crawl4ai import JsonCssExtractionStrategy, CrawlerRunConfig, AsyncWebCrawler, RegexChunking

config = CrawlerRunConfig(
    extraction_strategy=JsonCssExtractionStrategy(selectors={"title": "h1"}),
    chunking_strategy=RegexChunking()
)
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com", config=config)
    print("Extracted Content:")
    print(result.extracted_content)
```

**Comparing Chunking Strategies:**

- Regex-based chunking: Splits text by patterns, good for basic splitting.
- NLP-based chunking (if available): Splits text into semantically meaningful units, ideal for LLM-based extraction.

## Caching and Performance

Caching helps avoid repeatedly fetching and rendering the same page. By default, caching is enabled (`CacheMode.ENABLED`), so subsequent crawls of the same URL can skip the network fetch if the data is still fresh. You can control the cache mode, clear the cache, or bypass it when needed.

**Cache Modes:**

- `CacheMode.ENABLED`: Use cache if available, write new results to cache.
- `CacheMode.BYPASS`: Skip cache reading, but still write new results.
- `CacheMode.DISABLED`: Do not use cache at all.

**Clearing and Flushing the Cache:**

```python
async with AsyncWebCrawler() as crawler:
    await crawler.aclear_cache()  # Clear entire cache
    # ... run some crawls ...
    await crawler.aflush_cache()  # Flush partial entries if needed
```

Use caching to speed up development, repeated tests, or partial re-runs of large crawls.

## Batch Crawling and Parallelization

The `arun_many` method lets you process multiple URLs concurrently, improving throughput. You can limit concurrency with `semaphore_count` and apply rate limiting via `CrawlerRunConfig` parameters like `mean_delay` and `max_range`.

**Example: Batch Crawling**

```python
urls = [
    "https://site1.com",
    "https://site2.com",
    "https://site3.com"
]

from crawl4ai import CrawlerRunConfig

config = CrawlerRunConfig(semaphore_count=10, mean_delay=1.0, max_range=0.5)
async with AsyncWebCrawler() as crawler:
    results = await crawler.arun_many(urls, config=config)
    for res in results:
        print(res.url, res.markdown)
```

This allows you to process large URL lists efficiently. Adjust `semaphore_count` to match your resource limits.

## Scaling Crawls

To scale beyond a single machine, consider:

- Distributing URL lists across multiple workers or containers.
- Using a job queue like Celery or Redis Queue to schedule crawls.
- Integrating with cloud-based solutions for browser automation.

Always ensure you respect target site policies and comply with legal and ethical guidelines for web scraping.

## Screenshots and PDFs

If you need visual confirmation, you can enable screenshots or PDFs:

```python
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler

config = CrawlerRunConfig(screenshot=True, pdf=True)
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com", config=config)
    with open("page_screenshot.png", "wb") as f:
        f.write(result.screenshot)
    with open("page.pdf", "wb") as f:
        f.write(result.pdf)
```

This is helpful for debugging rendering issues or retaining visual copies of crawled pages.

## Troubleshooting and Common Issues

**Common Problems and Direct Fixes:**

1. **Browser not launching**:  
   - Check that you have installed Playwright and run `playwright install` for the chosen browser.
   - Ensure all required dependencies are installed.

2. **Timeouts or partial loads**:  
   - Increase timeouts or add delays between requests using `mean_delay` and `max_range`.
   - Wait for specific DOM elements to appear before proceeding.

3. **JavaScript not executing as expected**:  
   - Use `js_code` in `CrawlerRunConfig` to inject scripts.
   - Check browser console for errors or consider headless=False to debug UI interactions.

4. **Content Extraction fails**:  
   - Validate CSS selectors or extraction strategies.
   - Try a different extraction strategy if the current one is not producing results.

5. **Stale Data due to Caching**:  
   - Call `await crawler.aclear_cache()` to remove old entries.
   - Use `cache_mode=CacheMode.BYPASS` to fetch fresh data.

**Direct Code Fixes:**  
If you experience missing content after injecting JS, try waiting longer:
```python
js_code = """
(async () => {
    document.querySelector(".load-more").click();
    await new Promise(r => setTimeout(r, 3000));
})();
"""

config = CrawlerRunConfig(js_code=[js_code])
```

Or run headless=False to visually verify that the UI is changing as expected.

## Best Practices and Tips

- **Structuring your code**: Keep crawl logic modular. Have separate functions for configuring crawls, extracting data, and processing results.
- **Error Handling**: Wrap crawl operations in try/except blocks and log errors with `crawler.logger`.
- **Avoiding Getting Blocked**: Use proxies or rotate user agents if you crawl frequently. Randomize delays between requests.
- **Authentication and Session Management**: If the site requires login, provide the crawler with login steps via `js_code` or Playwright selectors. Consider using cookies or session storage retrieval in `CrawlerRunConfig`.

## Reference and Additional Resources

- **GitHub Repository**: [crawl4ai GitHub](https://github.com/yourusername/crawl4ai)
- **Playwright Docs**: [https://playwright.dev/](https://playwright.dev/)
- **AsyncIO in Python**: [Python Asyncio Docs](https://docs.python.org/3/library/asyncio.html)

## FAQ

**Q**: How do I customize user agents?  
**A**: Pass `user_agent="MyUserAgentString"` to `arun` or `arun_many`, or update `crawler_strategy` directly.

**Q**: Can I crawl local HTML files?  
**A**: Yes, provide a `file://` URL or `raw:` prefix with raw HTML strings.

**Q**: How do I integrate LLM-based extraction?  
**A**: Set `extraction_strategy=LLMExtractionStrategy(...)` and provide a chunking strategy. This allows using large language models for context-aware data extraction.

File: 4_browser_context_page.ex.md
================================================================================
## 4. Creating Browser Instances, Contexts, and Pages

###  Introduction

#### Overview of Browser Management in Crawl4AI
Crawl4AI's browser management system is designed to provide developers with advanced tools for handling complex web crawling tasks. By managing browser instances, contexts, and pages, Crawl4AI ensures optimal performance, identity preservation, and session persistence for high-volume, dynamic web crawling.

#### Key Objectives
- **Identity Preservation**:
  - Implements stealth techniques to maintain authentic digital identity
  - Simulates human-like behavior, such as mouse movements, scrolling, and key presses
  - Supports integration with third-party services to bypass CAPTCHA challenges
- **Persistent Sessions**:
  - Retains session data (cookies, local storage) for workflows requiring user authentication
  - Allows seamless continuation of tasks across multiple runs without re-authentication
- **Scalable Crawling**:
  - Optimized resource utilization for handling thousands of URLs concurrently
  - Flexible configuration options to tailor crawling behavior to specific requirements

---

###  Browser Creation Methods

#### Standard Browser Creation
Standard browser creation initializes a browser instance with default or minimal configurations. It is suitable for tasks that do not require session persistence or heavy customization.

##### Features and Limitations
- **Features**:
  - Quick and straightforward setup for small-scale tasks
  - Supports headless and headful modes
- **Limitations**:
  - Lacks advanced customization options like session reuse
  - May struggle with sites employing strict identity verification

##### Example Usage
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(browser_type="chromium", headless=True)
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://crawl4ai.com")
    print(result.markdown)
```

#### Persistent Contexts
Persistent contexts create browser sessions with stored data, enabling workflows that require maintaining login states or other session-specific information.

##### Benefits of Using `user_data_dir`
- **Session Persistence**:
  - Stores cookies, local storage, and cache between crawling sessions
  - Reduces overhead for repetitive logins or multi-step workflows
- **Enhanced Performance**:
  - Leverages pre-loaded resources for faster page loading
- **Flexibility**:
  - Adapts to complex workflows requiring user-specific configurations

##### Example: Setting Up Persistent Contexts
```python
config = BrowserConfig(user_data_dir="/path/to/user/data")
async with AsyncWebCrawler(config=config) as crawler:
    result = await crawler.arun("https://crawl4ai.com")
    print(result.markdown)
```

#### Managed Browser
The `ManagedBrowser` class offers a high-level abstraction for managing browser instances, emphasizing resource management, debugging capabilities, and identity preservation measures.

##### How It Works
- **Browser Process Management**:
  - Automates initialization and cleanup of browser processes
  - Optimizes resource usage by pooling and reusing browser instances
- **Debugging Support**:
  - Integrates with debugging tools like Chrome Developer Tools for real-time inspection
- **Identity Preservation**:
  - Implements stealth plugins to maintain authentic user identity
  - Preserves browser fingerprints and session data

##### Features
- **Customizable Configurations**:
  - Supports advanced options such as viewport resizing, proxy settings, and header manipulation
- **Debugging and Logging**:
  - Logs detailed browser interactions for debugging and performance analysis
- **Scalability**:
  - Handles multiple browser instances concurrently, scaling dynamically based on workload

##### Example: Using `ManagedBrowser`
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

config = BrowserConfig(headless=False, debug_port=9222)
async with AsyncWebCrawler(config=config) as crawler:
    result = await crawler.arun("https://crawl4ai.com")
    print(result.markdown)
```

---

###  Context and Page Management

#### Creating and Configuring Browser Contexts
Browser contexts act as isolated environments within a single browser instance, enabling independent browsing sessions with their own cookies, cache, and storage.

##### Customizations
- **Headers and Cookies**:
  - Define custom headers to mimic specific devices or browsers
  - Set cookies for authenticated sessions
- **Session Reuse**:
  - Retain and reuse session data across multiple requests
  - Example: Preserve login states for authenticated crawls

##### Example: Context Initialization
```python
from crawl4ai import CrawlerRunConfig

config = CrawlerRunConfig(headers={"User-Agent": "Crawl4AI/1.0"})
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://crawl4ai.com", config=config)
    print(result.markdown)
```

#### Creating Pages
Pages represent individual tabs or views within a browser context. They are responsible for rendering content, executing JavaScript, and handling user interactions.

##### Key Features
- **IFrame Handling**:
  - Extract content from embedded iframes
  - Navigate and interact with nested content
- **Viewport Customization**:
  - Adjust viewport size to match target device dimensions
- **Lazy Loading**:
  - Ensure dynamic elements are fully loaded before extraction

##### Example: Page Initialization
```python
config = CrawlerRunConfig(viewport_width=1920, viewport_height=1080)
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://crawl4ai.com", config=config)
    print(result.markdown)
```

---

# Preserve Your Identity with Crawl4AI

Crawl4AI empowers you to navigate and interact with the web using your authentic digital identity, ensuring that you are recognized as a human and not mistaken for a bot. This section introduces Managed Browsers, the recommended approach for preserving your rights to access the web, and Magic Mode, a simplified solution for specific scenarios.

## Managed Browsers: Your Digital Identity Solution

**Managed Browsers** enable developers to create and use persistent browser profiles. These profiles store local storage, cookies, and other session-related data, allowing you to interact with websites as a recognized user. By leveraging your unique identity, Managed Browsers ensure that your experience reflects your rights as a human browsing the web.

### Why Use Managed Browsers?
1. **Authentic Browsing Experience**: Managed Browsers retain session data and browser fingerprints, mirroring genuine user behavior.
2. **Effortless Configuration**: Once you interact with the site using the browser (e.g., solving a CAPTCHA), the session data is saved and reused, providing seamless access.
3. **Empowered Data Access**: By using your identity, Managed Browsers empower users to access data they can view on their own screens without artificial restrictions.


I'll help create a section about using command-line Chrome with a user data directory, which is indeed a more straightforward approach for identity-based browsing.

```markdown
### Steps to Use Identity-Based Browsing

1. **Launch Chrome with a Custom Profile Directory**

   - **Windows**:
   ```batch
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="C:\ChromeProfiles\CrawlProfile"
   ```

   - **macOS**:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --user-data-dir="/Users/username/ChromeProfiles/CrawlProfile"
   ```

   - **Linux**:
   ```bash
   google-chrome --user-data-dir="/home/username/ChromeProfiles/CrawlProfile"
   ```

2. **Set Up Your Identity**:
   - In the new Chrome window, log into your accounts (Google, social media, etc.)
   - Complete any necessary CAPTCHA challenges
   - Accept cookies and configure site preferences
   - The profile directory will save all settings, cookies, and login states

3. **Use the Profile in Crawl4AI**:
   ```python
   from crawl4ai import AsyncWebCrawler, BrowserConfig
   
   browser_config = BrowserConfig(
       headless=True,
       use_managed_browser=True,
       user_data_dir="/path/to/ChromeProfiles/CrawlProfile"  # Use the same directory from step 1
   )
   
   async with AsyncWebCrawler(config=browser_config) as crawler:
       result = await crawler.arun("https://example.com")
   ```

This approach provides several advantages:
- Complete manual control over profile setup
- Persistent logins across multiple sites
- Pre-solved CAPTCHAs and saved preferences
- Real browser history and cookies for authentic browsing patterns

### Example: Extracting Data Using Managed Browsers

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    # Define schema for structured data extraction
    schema = {
        "name": "Example Data",
        "baseSelector": "div.example",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }

    # Configure crawler
    browser_config = BrowserConfig(
        headless=True,  # Automate subsequent runs
        verbose=True,
        use_managed_browser=True,
        user_data_dir="/path/to/user_profile_data"
    )

    crawl_config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(schema),
        wait_for="css:div.example"  # Wait for the targeted element to load
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=crawl_config
        )

        if result.success:
            print("Extracted Data:", result.extracted_content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Benefits of Managed Browsers Over Other Methods
Managed Browsers eliminate the need for manual detection workarounds by enabling developers to work directly with their identity and user profile data. This approach ensures maximum compatibility with websites and simplifies the crawling process while preserving your right to access data freely.

## Magic Mode: Simplified Automation

While Managed Browsers are the preferred approach, **Magic Mode** provides an alternative for scenarios where persistent user profiles are unnecessary or infeasible. Magic Mode automates user-like behavior and simplifies configuration.

### What Magic Mode Does:
- Simulates human browsing by randomizing interaction patterns and timing
- Masks browser automation signals
- Handles cookie popups and modals
- Modifies navigator properties for enhanced compatibility

### Using Magic Mode

```python
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        magic=True  # Enables all automation features
    )
```

Magic Mode is particularly useful for:
- Quick prototyping when a Managed Browser setup is not available
- Basic sites requiring minimal interaction or configuration

### Example: Combining Magic Mode with Additional Options

```python
async def crawl_with_magic_mode(url: str):
    async with AsyncWebCrawler(headless=True) as crawler:
        result = await crawler.arun(
            url=url,
            magic=True,
            remove_overlay_elements=True,  # Remove popups/modals
            page_timeout=60000            # Increased timeout for complex pages
        )

        return result.markdown if result.success else None
```

## Magic Mode vs. Managed Browsers
While Magic Mode simplifies many tasks, it cannot match the reliability and authenticity of Managed Browsers. By using your identity and persistent profiles, Managed Browsers render Magic Mode largely unnecessary. However, Magic Mode remains a viable fallback for specific situations where user identity is not a factor.

# Session Management

Session management in Crawl4AI is a powerful feature that allows you to maintain state across multiple requests, making it particularly suitable for handling complex multi-step crawling tasks. It enables you to reuse the same browser tab (or page object) across sequential actions and crawls, which is beneficial for:

- **Performing JavaScript actions before and after crawling**
- **Executing multiple sequential crawls faster** without needing to reopen tabs or allocate memory repeatedly
- **Maintaining state for complex workflows**

**Note:** This feature is designed for sequential workflows and is not suitable for parallel operations.

## Basic Session Usage

Use `BrowserConfig` and `CrawlerRunConfig` to maintain state with a `session_id`:

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async with AsyncWebCrawler() as crawler:
    session_id = "my_session"

    # Define configurations
    config1 = CrawlerRunConfig(url="https://example.com/page1", session_id=session_id)
    config2 = CrawlerRunConfig(url="https://example.com/page2", session_id=session_id)

    # First request
    result1 = await crawler.arun(config=config1)

    # Subsequent request using the same session
    result2 = await crawler.arun(config=config2)

    # Clean up when done
    await crawler.crawler_strategy.kill_session(session_id)
```

## Dynamic Content with Sessions

Here's an example of crawling GitHub commits across multiple pages while preserving session state:

```python
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.cache_context import CacheMode

async def crawl_dynamic_content():
    async with AsyncWebCrawler() as crawler:
        session_id = "github_commits_session"
        url = "https://github.com/microsoft/TypeScript/commits/main"
        all_commits = []

        # Define extraction schema
        schema = {
            "name": "Commit Extractor",
            "baseSelector": "li.Box-sc-g0xbh4-0",
            "fields": [{"name": "title", "selector": "h4.markdown-title", "type": "text"}],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema)

        # JavaScript and wait configurations
        js_next_page = """document.querySelector('a[data-testid="pagination-next-button"]').click();"""
        wait_for = """() => document.querySelectorAll('li.Box-sc-g0xbh4-0').length > 0"""

        # Crawl multiple pages
        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                extraction_strategy=extraction_strategy,
                js_code=js_next_page if page > 0 else None,
                wait_for=wait_for if page > 0 else None,
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            if result.success:
                commits = json.loads(result.extracted_content)
                all_commits.extend(commits)
                print(f"Page {page + 1}: Found {len(commits)} commits")

        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
        return all_commits
```

## Session Best Practices

1. **Descriptive Session IDs**:
   Use meaningful names for session IDs to organize workflows:
   ```python
   session_id = "login_flow_session"
   session_id = "product_catalog_session"
   ```

2. **Resource Management**:
   Always ensure sessions are cleaned up to free resources:
   ```python
   try:
       # Your crawling code here
       pass
   finally:
       await crawler.crawler_strategy.kill_session(session_id)
   ```

3. **State Maintenance**:
   Reuse the session for subsequent actions within the same workflow:
   ```python
   # Step 1: Login
   login_config = CrawlerRunConfig(
       url="https://example.com/login",
       session_id=session_id,
       js_code="document.querySelector('form').submit();"
   )
   await crawler.arun(config=login_config)

   # Step 2: Verify login success
   dashboard_config = CrawlerRunConfig(
       url="https://example.com/dashboard",
       session_id=session_id,
       wait_for="css:.user-profile"  # Wait for authenticated content
   )
   result = await crawler.arun(config=dashboard_config)
   ```

4. **Common Use Cases for Sessions**:
   1. **Authentication Flows**: Login and interact with secured pages
   2. **Pagination Handling**: Navigate through multiple pages
   3. **Form Submissions**: Fill forms, submit, and process results
   4. **Multi-step Processes**: Complete workflows that span multiple actions
   5. **Dynamic Content Navigation**: Handle JavaScript-rendered or event-triggered content

# Session-Based Crawling for Dynamic Content

In modern web applications, content is often loaded dynamically without changing the URL. Examples include "Load More" buttons, infinite scrolling, or paginated content that updates via JavaScript. Crawl4AI provides session-based crawling capabilities to handle such scenarios effectively.

## Understanding Session-Based Crawling

Session-based crawling allows you to reuse a persistent browser session across multiple actions. This means the same browser tab (or page object) is used throughout, enabling:

1. **Efficient handling of dynamic content** without reloading the page
2. **JavaScript actions before and after crawling** (e.g., clicking buttons or scrolling)
3. **State maintenance** for authenticated sessions or multi-step workflows
4. **Faster sequential crawling**, as it avoids reopening tabs or reallocating resources

**Note:** Session-based crawling is ideal for sequential operations, not parallel tasks.

## Basic Concepts

Before diving into examples, here are some key concepts:

- **Session ID**: A unique identifier for a browsing session. Use the same `session_id` across multiple requests to maintain state.
- **BrowserConfig & CrawlerRunConfig**: These configuration objects control browser settings and crawling behavior.
- **JavaScript Execution**: Use `js_code` to perform actions like clicking buttons.
- **CSS Selectors**: Target specific elements for interaction or data extraction.
- **Extraction Strategy**: Define rules to extract structured data.
- **Wait Conditions**: Specify conditions to wait for before proceeding.

## Advanced Technique 1: Custom Execution Hooks

Use custom hooks to handle complex scenarios, such as waiting for content to load dynamically:

```python
async def advanced_session_crawl_with_hooks():
    first_commit = ""

    async def on_execution_started(page):
        nonlocal first_commit
        try:
            while True:
                await page.wait_for_selector("li.commit-item h4")
                commit = await page.query_selector("li.commit-item h4")
                commit = await commit.evaluate("(element) => element.textContent").strip()
                if commit and commit != first_commit:
                    first_commit = commit
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Warning: New content didn't appear: {e}")

    async with AsyncWebCrawler() as crawler:
        session_id = "commit_session"
        url = "https://github.com/example/repo/commits/main"
        crawler.crawler_strategy.set_hook("on_execution_started", on_execution_started)

        js_next_page = """document.querySelector('a.pagination-next').click();"""

        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                js_code=js_next_page if page > 0 else None,
                css_selector="li.commit-item",
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            print(f"Page {page + 1}: Found {len(result.extracted_content)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
```

## Advanced Technique 2: Integrated JavaScript Execution and Waiting

Combine JavaScript execution and waiting logic for concise handling of dynamic content:

```python
async def integrated_js_and_wait_crawl():
    async with AsyncWebCrawler() as crawler:
        session_id = "integrated_session"
        url = "https://github.com/example/repo/commits/main"

        js_next_page_and_wait = """
        (async () => {
            const getCurrentCommit = () => document.querySelector('li.commit-item h4').textContent.trim();
            const initialCommit = getCurrentCommit();
            document.querySelector('a.pagination-next').click();
            while (getCurrentCommit() === initialCommit) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        })();
        """

        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                js_code=js_next_page_and_wait if page > 0 else None,
                css_selector="li.commit-item",
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            print(f"Page {page + 1}: Found {len(result.extracted_content)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
```

## Best Practices for Session-Based Crawling

1. **Unique Session IDs**: Assign descriptive and unique `session_id` values
2. **Close Sessions**: Always clean up sessions with `kill_session` after use
3. **Error Handling**: Anticipate and handle errors gracefully
4. **Respect Websites**: Follow terms of service and robots.txt
5. **Delays**: Add delays to avoid overwhelming servers
6. **Optimize JavaScript**: Keep scripts concise for better performance
7. **Monitor Resources**: Track memory and CPU usage for long sessions

## Conclusion

By combining browser management, identity-based crawling through Managed Browsers, and robust session management, Crawl4AI provides a comprehensive solution for modern web crawling needs. These features work together to enable:

1. Authentic identity preservation
2. Efficient session management
3. Reliable handling of dynamic content
4. Scalable and maintainable crawling workflows

Remember to always follow best practices and respect website policies when implementing these features.
File: 5_markdown_generation.ex.md
================================================================================
# 5. Markdown Generation (MEGA Extended Documentation)

## 5.1 Introduction

In modern AI workflows—especially those involving Large Language Models (LLMs)—it’s essential to provide clean, structured, and meaningful textual data. **Crawl4AI** assists with this by extracting web content and converting it into Markdown that is easy to process, fine-tune on, or use for retrieval-augmented generation (RAG).

**What Makes Markdown Outputs Valuable for AI?**  
- **Human-Readable & Machine-Friendly:** Markdown is a simple, text-based format easily parsed by humans and machines alike.  
- **Rich Structure:** Headings, lists, code blocks, and links are preserved and well-organized.  
- **Enhanced Relevance:** Content filtering ensures you focus on the main content while discarding noise, making the data cleaner for LLM training or search.

### Quick Start Example

Here’s a minimal snippet to get started:

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator()
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com", config=config)
    print(result.markdown_v2.raw_markdown)
```

*Within a few lines of code, you can fetch a webpage, run it through the Markdown generator, and get a clean, AI-friendly output.*

---

## 5.2 Markdown Generation

The Markdown generation process transforms raw HTML into a structured format. At its core is the `DefaultMarkdownGenerator` class, which uses configurable parameters and optional filters. Let’s explore its functionality in depth.

### Internal Workings

1. **HTML to Markdown Conversion:**  
   The generator relies on an HTML-to-text conversion process that respects various formatting options. It preserves headings, code blocks, and references while removing extraneous tags like scripts and styles.

2. **Link Citation Handling:**  
   By default, the generator can convert links into citation-style references at the bottom of the document. This feature is particularly useful when you need a clean, reference-rich dataset for an LLM.

3. **Optional Content Filters:**  
   You can provide a content filter (like BM25 or Pruning) to generate a “fit_markdown” output that contains only the most relevant or least noisy parts of the page.

### Key Parameters

- **`base_url` (string):**  
  A base URL used to resolve relative links in the content.

- **`html2text_config` (dict):**  
  Controls how HTML is converted to Markdown. If none is provided, default settings ensure a reasonable output. You can customize a wide array of options. These options mirror standard `html2text` configurations with custom enhancements.  
  **Important Options:**
  - `ignore_links` (bool): If `True`, removes all hyperlinks in the output Markdown. Default: `False`
  - `ignore_images` (bool): If `True`, removes all images. Default: `False`
  - `escape_html` (bool): If `True`, escapes raw HTML entities. Default: `True`
  - `body_width` (int): Sets the text wrapping width. Default: unlimited (0 means no wrapping)
  
  **Advanced html2text-related Options from Source:**
  - `inside_pre`/`inside_code` (internal flags): Track whether we are inside `<pre>` or `<code>` blocks.
  - `preserve_tags` (set): A set of tags to preserve. If not empty, content within these tags is kept verbatim.
  - `current_preserved_tag`/`preserve_depth`: Internally manage nesting levels of preserved tags.
  - `handle_code_in_pre` (bool): If `True`, treats code within `<pre>` blocks distinctly, possibly formatting them as code blocks in Markdown.
  - `skip_internal_links` (bool): If `True`, internal links (like `#section`) are skipped.
  - `single_line_break` (bool): If `True`, uses single line breaks instead of double line breaks.
  - `mark_code` (bool): If `True`, adds special markers around code text.
  - `include_sup_sub` (bool): If `True`, tries to include `<sup>` and `<sub>` text in a readable way.
  - `ignore_mailto_links` (bool): If `True`, ignores `mailto:` links.
  - `escape_backslash`, `escape_dot`, `escape_plus`, `escape_dash`, `escape_snob`: Special escaping options to handle characters that might conflict with Markdown syntax.

**Example Custom `html2text_config`:**

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        options={
            "ignore_links": True,
            "escape_html": False,
            "body_width": 80,
            "skip_internal_links": True,
            "mark_code": True,
            "include_sup_sub": True
        }
    )
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com/docs", config=config)
    print(result.markdown_v2.raw_markdown)
```

In this example, we ignore all hyperlinks, do not escape HTML entities, wrap text at 80 characters wide, skip internal links, mark code regions, and include superscript/subscript formatting.

### Using Content Filters in Markdown Generation

- **`content_filter` (object):**  
  An optional filter (like `BM25ContentFilter` or `PruningContentFilter`) that refines the content before Markdown generation. When applied:
  - `fit_markdown` is generated: a filtered version of the page focusing on main content.
  - `fit_html` is also available: the filtered HTML that was used to generate `fit_markdown`.

### Example Usage

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=BM25ContentFilter(
            user_query="machine learning",
            bm25_threshold=1.5,
            use_stemming=True
        ),
        options={"ignore_links": True, "escape_html": False}
    )
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://crawl4ai.com/ai-research", config=config)
    print(result.markdown_v2.fit_markdown)  # Filtered Markdown focusing on machine learning
```

### Troubleshooting Markdown Generation

- **Empty Markdown Output?**  
  Check if the crawler successfully fetched HTML. Ensure your filters are not overly strict. If no filter is used and you still get no output, verify the HTML content isn’t empty or malformed.

- **Malformed HTML Content?**  
  The internal parser is robust, but if encountering strange characters, consider adjusting `escape_html` to `True` or removing problematic tags using filters.

- **Performance Considerations:**  
  Complex filters or very large HTML documents can slow down processing. Consider caching results or reducing `body_width` if line-wrapping is unnecessary.

---

### 5.2.1 MarkdownGenerationResult

After running the crawler, `result.markdown_v2` returns a `MarkdownGenerationResult` object.

**Attributes:**
- `raw_markdown` (str): Unfiltered Markdown.
- `markdown_with_citations` (str): Markdown with all links converted into references at the end.
- `references_markdown` (str): A list of extracted references.
- `fit_markdown` (Optional[str]): Markdown after applying filters.
- `fit_html` (Optional[str]): Filtered HTML corresponding to `fit_markdown`.

**Integration Example:**

```python
result = await crawler.arun("https://crawl4ai.com")
print("RAW:", result.markdown_v2.raw_markdown)
print("CITED:", result.markdown_v2.markdown_with_citations)
print("FIT:", result.markdown_v2.fit_markdown)
```

**Use Cases:**
- **RAG Pipelines:** Feed `fit_markdown` into a vector database for semantic search.
- **LLM Fine-Tuning:** Use `raw_markdown` or `fit_markdown` as training data for large models.

---

## 5.3 Filtering Strategies

Filters refine raw HTML to produce cleaner Markdown. They can remove boilerplate sections (headers, footers) or focus on content relevant to a specific query.

**Two Major Strategies:**
1. **BM25ContentFilter:**  
   A relevance-based approach using BM25 scoring to rank content sections according to a user query.

2. **PruningContentFilter (Emphasized):**  
   An unsupervised, clustering-like approach that systematically prunes irrelevant or noisy parts of the HTML. Unlike BM25, which relies on a query for relevance, `PruningContentFilter` attempts to cluster and discard noise based on structural and heuristic metrics. This makes it highly useful for general cleanup without predefined queries.

---

### Relevance-Based Filtering: BM25

BM25 ranks content blocks by relevance to a given query. It’s semi-supervised in the sense that it needs a query (`user_query`).

**Key Parameters:**
- `user_query` (string): The query for content relevance.  
- `bm25_threshold` (float): The minimum relevance score. Increase to get less but more focused content.
- `use_stemming` (bool): When `True`, matches variations of words.  
- `case_sensitive` (bool): Controls case sensitivity.

**If omitted `user_query`,** BM25 just scores content but doesn’t have a specific target. Useful if you need general scoring.

**Example:**
```python
from crawl4ai.content_filter_strategy import BM25ContentFilter

config = CrawlerRunConfig(
    content_filter=BM25ContentFilter(
        user_query="artificial intelligence",
        bm25_threshold=2.0,
        use_stemming=True
    )
)
```

**Troubleshooting BM25:**
- If you get too much irrelevant content, raise `bm25_threshold`.
- If you get too little content, lower it or disable `case_sensitive`.

---

### PruningContentFilter: Unsupervised Content Clustering

`PruningContentFilter` is about intelligently stripping away non-essential parts of a page—ads, navigation bars, repetitive links—without relying on a specific user query. Think of it as an unsupervised clustering method that scores content blocks and removes “noise.”

**Key Features:**
- **Unsupervised Nature:** No query needed. Uses heuristics like text density, link density, tag importance, and HTML structure.  
- **Clustering-Like Behavior:** It effectively “clusters” page sections by their structural and textual qualities, and prunes those that don’t meet thresholds.  
- **Threshold Adjustments:** Dynamically adjusts or uses a fixed threshold to remove or keep content blocks.

**Parameters:**
- `threshold` (float): Score threshold for removing content. Higher values prune more aggressively. Default: `0.5`.
- `threshold_type` (str): `"fixed"` or `"dynamic"`.  
   - **Fixed:** Compares each block’s score directly to a set threshold.  
   - **Dynamic:** Adjusts threshold based on content metrics for a more adaptive approach.
- `min_word_threshold` (int): Minimum word count to keep a content block.  
- Internal metrics consider:
  - **Text Density:** Prefers sections rich in text over code or sparse elements.
  - **Link Density:** Penalizes sections with too many links.
  - **Tag Importance:** Some tags (e.g., `<article>`, `<main>`, `<section>`) are considered more important and less likely to be pruned.
  - **Class/ID patterns:** Looks for signals (like `nav`, `footer`) to identify boilerplate.

**Example:**
```python
from crawl4ai.content_filter_strategy import PruningContentFilter

config = CrawlerRunConfig(
    content_filter=PruningContentFilter(
        threshold=0.7,
        threshold_type="dynamic",
        min_word_threshold=100
    )
)
```

In this example, content blocks under a dynamically adjusted threshold are pruned, and any block under 100 words is discarded, ensuring you keep only substantial textual sections.

**When to Use PruningContentFilter:**
- **General Cleanup:** If you want a broad cleanup of the page without a specific target query, pruning is your go-to.
- **Pre-Processing Large Corpora:** Before applying more specific filters, prune to remove boilerplate, then apply BM25 for query-focused refinement.

**Troubleshooting Pruning Filter:**
- **Too Much Content Gone?** Lower the `threshold` or switch from `dynamic` to `fixed` threshold for more predictable behavior.
- **Not Enough Pruning?** Increase `threshold` to be more aggressive.
- **Mixed Results?** Adjust `min_word_threshold` or try the `dynamic` threshold mode to fine-tune results.

---

## 5.4 Fit Markdown: Bringing It All Together

“Fit Markdown” is the output you get when applying filters to the raw HTML before markdown generation. This produces a final, optimized Markdown that’s noise-free and content-focused.

### Advanced Usage Scenario

**Combining BM25 and Pruning:**  
1. First apply `PruningContentFilter` to remove general junk.  
2. Then apply a `BM25ContentFilter` to focus on query relevance.

*Example:*

```python
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler

combined_filter = BM25ContentFilter(
    user_query="technology advancements",
    bm25_threshold=1.2,
    use_stemming=True
)

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.5)  # First prune
    )
)

async with AsyncWebCrawler() as crawler:
    # First run pruning
    result = await crawler.arun("https://crawl4ai.com", config=config)
    pruned_fit_markdown = result.markdown_v2.fit_markdown

    # Re-run the BM25 filter on the pruned output, or integrate BM25 in a pipeline
    # (In practice, you'd integrate both filters within the crawler or run a second pass.)
```

**Performance Note:**  
Fit Markdown reduces token count, making subsequent LLM operations faster and cheaper.

---

## 5.5 Best Practices

- **Iterative Adjustment:** Start with default parameters, then adjust filters, thresholds, and `html2text_config` based on the quality of output you need.
- **Combining Filters:** Use `PruningContentFilter` first to remove boilerplate, then a `BM25ContentFilter` to target relevance.
- **Check Downstream Applications:** If you’re using fit Markdown for training LLMs, inspect the output to ensure no essential references were pruned.
- **Docker Deployment:**  
  Running Crawl4AI in a Docker container ensures a consistent environment. Just include the required packages in your Dockerfile and run the crawler script inside the container.
- **Caching Results:**  
  To save time, cache the raw HTML or intermediate Markdown. If you know you’ll re-run filters or change parameters often, caching avoids redundant crawling.

**Handling Special Cases:**
- **Authentication-Protected Pages:**  
  If you need to crawl gated content, provide appropriate session tokens or use a headless browser approach before feeding HTML to the generator.
- **Proxies and Timeouts:**  
  Configure the crawler with proxies or increased timeouts for sites that are slow or region-restricted.

---

## 5.6 Troubleshooting & FAQ

**Why am I getting empty Markdown?**  
- Ensure that the URL is correct and the crawler fetched content.
- If using filters, relax your thresholds.

**How to handle JavaScript-heavy sites?**  
- Run a headless browser upstream to render the page. Crawl4AI expects server-rendered HTML.
  
**How to improve formatting for code snippets?**  
- Set `handle_code_in_pre = True` in `html2text_config` to preserve code blocks more accurately.

**Links are cluttering my Markdown.**  
- Use `ignore_links=True` or convert them to citations for a cleaner layout.

---

## 5.7 Real-World Use Cases

1. **Summarizing News Articles:**  
   Use `PruningContentFilter` to strip ads and nav bars, then just the raw output to get a neat summary.

2. **Preparing Data for LLM Fine-Tuning:**  
   For a large corpus, first prune all pages to remove boilerplate, then optionally apply BM25 to focus on specific topics. The resulting Markdown is ideal for training because it’s dense with meaningful content.

3. **RAG Pipelines:**  
   Extract `fit_markdown`, store it in a vector database, and use it for retrieval-augmented generation. The references and structured headings enhance search relevance.

---

## 5.8 Appendix (References)

**Source Code Files:**
- [markdown_generation_strategy.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/markdown_generation_strategy.py)
  - **Key Classes:** `MarkdownGenerationStrategy`, `DefaultMarkdownGenerator`
  - **Key Functions:** `convert_links_to_citations()`, `generate_markdown()`
  
- [content_filter_strategy.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/content_filter_strategy.py)
  - **Key Classes:** `RelevantContentFilter`, `BM25ContentFilter`, `PruningContentFilter`
  - **Metrics & Heuristics:** Examine `PruningContentFilter` code for scoring logic and threshold adjustments.

Exploring the source code will provide deeper insights into how tags are parsed, how scores are computed for pruning, and how BM25 relevance is calculated.

---

**In summary**, Markdown generation in Crawl4AI provides a powerful, configurable pipeline to transform raw HTML into AI-ready Markdown. By leveraging `PruningContentFilter` for general cleanup and `BM25ContentFilter` for query-focused extraction, plus fine-tuning `html2text_config`, you can achieve high-quality outputs for a wide range of AI applications.
File: 6_chunking_strategies.md
================================================================================
# Chunking Strategies
Chunking strategies are critical for dividing large texts into manageable parts, enabling effective content processing and extraction. These strategies are foundational in cosine similarity-based extraction techniques, which allow users to retrieve only the most relevant chunks of content for a given query. Additionally, they facilitate direct integration into RAG (Retrieval-Augmented Generation) systems for structured and scalable workflows.

### Why Use Chunking?
1. **Cosine Similarity and Query Relevance**: Prepares chunks for semantic similarity analysis.
2. **RAG System Integration**: Seamlessly processes and stores chunks for retrieval.
3. **Structured Processing**: Allows for diverse segmentation methods, such as sentence-based, topic-based, or windowed approaches.

### Methods of Chunking

#### 1. Regex-Based Chunking
Splits text based on regular expression patterns, useful for coarse segmentation.

**Code Example**:
```python
class RegexChunking:
    def __init__(self, patterns=None):
        self.patterns = patterns or [r'\n\n']  # Default pattern for paragraphs

    def chunk(self, text):
        paragraphs = [text]
        for pattern in self.patterns:
            paragraphs = [seg for p in paragraphs for seg in re.split(pattern, p)]
        return paragraphs

# Example Usage
text = """This is the first paragraph.

This is the second paragraph."""
chunker = RegexChunking()
print(chunker.chunk(text))
```

#### 2. Sentence-Based Chunking
Divides text into sentences using NLP tools, ideal for extracting meaningful statements.

**Code Example**:
```python
from nltk.tokenize import sent_tokenize

class NlpSentenceChunking:
    def chunk(self, text):
        sentences = sent_tokenize(text)
        return [sentence.strip() for sentence in sentences]

# Example Usage
text = "This is sentence one. This is sentence two."
chunker = NlpSentenceChunking()
print(chunker.chunk(text))
```

#### 3. Topic-Based Segmentation
Uses algorithms like TextTiling to create topic-coherent chunks.

**Code Example**:
```python
from nltk.tokenize import TextTilingTokenizer

class TopicSegmentationChunking:
    def __init__(self):
        self.tokenizer = TextTilingTokenizer()

    def chunk(self, text):
        return self.tokenizer.tokenize(text)

# Example Usage
text = """This is an introduction.
This is a detailed discussion on the topic."""
chunker = TopicSegmentationChunking()
print(chunker.chunk(text))
```

#### 4. Fixed-Length Word Chunking
Segments text into chunks of a fixed word count.

**Code Example**:
```python
class FixedLengthWordChunking:
    def __init__(self, chunk_size=100):
        self.chunk_size = chunk_size

    def chunk(self, text):
        words = text.split()
        return [' '.join(words[i:i + self.chunk_size]) for i in range(0, len(words), self.chunk_size)]

# Example Usage
text = "This is a long text with many words to be chunked into fixed sizes."
chunker = FixedLengthWordChunking(chunk_size=5)
print(chunker.chunk(text))
```

#### 5. Sliding Window Chunking
Generates overlapping chunks for better contextual coherence.

**Code Example**:
```python
class SlidingWindowChunking:
    def __init__(self, window_size=100, step=50):
        self.window_size = window_size
        self.step = step

    def chunk(self, text):
        words = text.split()
        chunks = []
        for i in range(0, len(words) - self.window_size + 1, self.step):
            chunks.append(' '.join(words[i:i + self.window_size]))
        return chunks

# Example Usage
text = "This is a long text to demonstrate sliding window chunking."
chunker = SlidingWindowChunking(window_size=5, step=2)
print(chunker.chunk(text))
```

### Combining Chunking with Cosine Similarity
To enhance the relevance of extracted content, chunking strategies can be paired with cosine similarity techniques. Here’s an example workflow:

**Code Example**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CosineSimilarityExtractor:
    def __init__(self, query):
        self.query = query
        self.vectorizer = TfidfVectorizer()

    def find_relevant_chunks(self, chunks):
        vectors = self.vectorizer.fit_transform([self.query] + chunks)
        similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
        return [(chunks[i], similarities[i]) for i in range(len(chunks))]

# Example Workflow
text = """This is a sample document. It has multiple sentences. 
We are testing chunking and similarity."""

chunker = SlidingWindowChunking(window_size=5, step=3)
chunks = chunker.chunk(text)
query = "testing chunking"
extractor = CosineSimilarityExtractor(query)
relevant_chunks = extractor.find_relevant_chunks(chunks)

print(relevant_chunks)
```

File: 7_extraction_strategies.ex.md
================================================================================
# Structured Data Extraction Strategies

## Extraction Strategies
Structured data extraction strategies are designed to convert raw web content into organized, JSON-formatted data. These strategies handle diverse extraction scenarios, including schema-based, language model-driven, and clustering methods. This section covers models using LLMs or without using them to extract data with precision and flexibility.

###  LLM Extraction Strategy
The **LLM Extraction Strategy** employs a large language model (LLM) to process content dynamically. It supports:
- **Schema-Based Extraction**: Using a defined JSON schema to structure output.
- **Instruction-Based Extraction**: Accepting custom prompts to guide the extraction process.
- **Flexible Model Usage**: Supporting open-source or paid LLMs.

#### Key Features
- Accepts customizable schemas for structured outputs.
- Incorporates user prompts for tailored results.
- Handles large inputs with chunking and overlap for efficient processing.

#### Parameters and Configurations
Below is a detailed explanation of key parameters:

- **`provider`** *(str)*: Specifies the LLM provider (e.g., `openai`, `ollama`).
  - Default: `DEFAULT_PROVIDER`

- **`api_token`** *(Optional[str])*: API token for the LLM provider.
  - Required unless using a provider that doesn’t need authentication.

- **`instruction`** *(Optional[str])*: A prompt guiding the model on extraction specifics.
  - Example: "Extract all prices and model names from the page."

- **`schema`** *(Optional[Dict])*: JSON schema defining the structure of extracted data.
  - If provided, extraction switches to schema mode.

- **`extraction_type`** *(str)*: Determines extraction mode (`block` or `schema`).
  - Default: `block`

- **Chunking Settings**:
  - **`chunk_token_threshold`** *(int)*: Maximum token count per chunk. Default: `CHUNK_TOKEN_THRESHOLD`.
  - **`overlap_rate`** *(float)*: Proportion of overlapping tokens between chunks. Default: `OVERLAP_RATE`.

- **`extra_args`** *(Dict)*: Additional arguments passed to the LLM API sucj as `max_length`, `temperature`, etc.

#### Example Usage

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import AsyncWebCrawler
from crawl4ai.config import CrawlerRunConfig, BrowserConfig

class OpenAIModelFee(BaseModel):
    model_name: str
    input_fee: str
    output_fee: str

async def extract_structured_data():
    browser_config = BrowserConfig(headless=True)
    extraction_strategy = LLMExtractionStrategy(
        provider="openai",
        api_token="your_api_token",
        schema=OpenAIModelFee.model_json_schema(),
        instruction="Extract all model fees from the content."
    )

    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://crawl4ai.com/pricing",
            config=crawler_config
        )
        print(result.extracted_content)
```

#### Workflow and Error Handling
- **Chunk Merging**: Content is divided into manageable chunks based on the token threshold.
- **Backoff and Retries**: Handles API rate limits with backoff strategies.
- **Error Logging**: Extracted blocks include error tags when issues occur.
- **Parallel Execution**: Supports multi-threaded execution for efficiency.

#### Benefits of Using LLM Extraction Strategy
- **Dynamic Adaptability**: Easily switch between schema-based and instruction-based modes.
- **Scalable**: Processes large content efficiently using chunking.
- **Versatile**: Works with various LLM providers and configurations.

This strategy is ideal for extracting structured data from complex web pages, ensuring compatibility with LLM training and fine-tuning workflows.

###  Cosine Strategy

The Cosine Strategy in Crawl4AI uses similarity-based clustering to identify and extract relevant content sections from web pages. This strategy is particularly useful when you need to find and extract content based on semantic similarity rather than structural patterns.

#### How It Works

The Cosine Strategy:
1. Breaks down page content into meaningful chunks
2. Converts text into vector representations
3. Calculates similarity between chunks
4. Clusters similar content together
5. Ranks and filters content based on relevance

#### Basic Usage

```python
from crawl4ai.extraction_strategy import CosineStrategy

strategy = CosineStrategy(
    semantic_filter="product reviews",    # Target content type
    word_count_threshold=10,             # Minimum words per cluster
    sim_threshold=0.3                    # Similarity threshold
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://crawl4ai.com/reviews",
        extraction_strategy=strategy
    )
    
    content = result.extracted_content
```

#### Configuration Options

##### Core Parameters

```python
CosineStrategy(
    # Content Filtering
    semantic_filter: str = None,       # Keywords/topic for content filtering
    word_count_threshold: int = 10,    # Minimum words per cluster
    sim_threshold: float = 0.3,        # Similarity threshold (0.0 to 1.0)
    
    # Clustering Parameters
    max_dist: float = 0.2,            # Maximum distance for clustering
    linkage_method: str = 'ward',      # Clustering linkage method
    top_k: int = 3,                   # Number of top categories to extract
    
    # Model Configuration
    model_name: str = 'sentence-transformers/all-MiniLM-L6-v2',  # Embedding model
    
    verbose: bool = False             # Enable logging
)
```

##### Parameter Details

1. **semantic_filter**
   - Sets the target topic or content type
   - Use keywords relevant to your desired content
   - Example: "technical specifications", "user reviews", "pricing information"

2. **sim_threshold**
   - Controls how similar content must be to be grouped together
   - Higher values (e.g., 0.8) mean stricter matching
   - Lower values (e.g., 0.3) allow more variation
   ```python
   # Strict matching
   strategy = CosineStrategy(sim_threshold=0.8)
   
   # Loose matching
   strategy = CosineStrategy(sim_threshold=0.3)
   ```

3. **word_count_threshold**
   - Filters out short content blocks
   - Helps eliminate noise and irrelevant content
   ```python
   # Only consider substantial paragraphs
   strategy = CosineStrategy(word_count_threshold=50)
   ```

4. **top_k**
   - Number of top content clusters to return
   - Higher values return more diverse content
   ```python
   # Get top 5 most relevant content clusters
   strategy = CosineStrategy(top_k=5)
   ```

#### Use Cases

##### 1. Article Content Extraction
```python
strategy = CosineStrategy(
    semantic_filter="main article content",
    word_count_threshold=100,  # Longer blocks for articles
    top_k=1                   # Usually want single main content
)

result = await crawler.arun(
    url="https://crawl4ai.com/blog/post",
    extraction_strategy=strategy
)
```

##### 2. Product Review Analysis
```python
strategy = CosineStrategy(
    semantic_filter="customer reviews and ratings",
    word_count_threshold=20,   # Reviews can be shorter
    top_k=10,                 # Get multiple reviews
    sim_threshold=0.4         # Allow variety in review content
)
```

##### 3. Technical Documentation
```python
strategy = CosineStrategy(
    semantic_filter="technical specifications documentation",
    word_count_threshold=30,
    sim_threshold=0.6,        # Stricter matching for technical content
    max_dist=0.3             # Allow related technical sections
)
```

#### Advanced Features

##### Custom Clustering
```python
strategy = CosineStrategy(
    linkage_method='complete',  # Alternative clustering method
    max_dist=0.4,              # Larger clusters
    model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'  # Multilingual support
)
```

##### Content Filtering Pipeline
```python
strategy = CosineStrategy(
    semantic_filter="pricing plans features",
    word_count_threshold=15,
    sim_threshold=0.5,
    top_k=3
)

async def extract_pricing_features(url: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            extraction_strategy=strategy
        )
        
        if result.success:
            content = json.loads(result.extracted_content)
            return {
                'pricing_features': content,
                'clusters': len(content),
                'similarity_scores': [item['score'] for item in content]
            }
```

#### Best Practices

1. **Adjust Thresholds Iteratively**
   - Start with default values
   - Adjust based on results
   - Monitor clustering quality

2. **Choose Appropriate Word Count Thresholds**
   - Higher for articles (100+)
   - Lower for reviews/comments (20+)
   - Medium for product descriptions (50+)

3. **Optimize Performance**
   ```python
   strategy = CosineStrategy(
       word_count_threshold=10,  # Filter early
       top_k=5,                 # Limit results
       verbose=True             # Monitor performance
   )
   ```

4. **Handle Different Content Types**
   ```python
   # For mixed content pages
   strategy = CosineStrategy(
       semantic_filter="product features",
       sim_threshold=0.4,      # More flexible matching
       max_dist=0.3,          # Larger clusters
       top_k=3                # Multiple relevant sections
   )
   ```

#### Error Handling

```python
try:
    result = await crawler.arun(
        url="https://crawl4ai.com",
        extraction_strategy=strategy
    )
    
    if result.success:
        content = json.loads(result.extracted_content)
        if not content:
            print("No relevant content found")
    else:
        print(f"Extraction failed: {result.error_message}")
        
except Exception as e:
    print(f"Error during extraction: {str(e)}")
```

The Cosine Strategy is particularly effective when:
- Content structure is inconsistent
- You need semantic understanding
- You want to find similar content blocks
- Structure-based extraction (CSS/XPath) isn't reliable

It works well with other strategies and can be used as a pre-processing step for LLM-based extraction.


###  JSON-Based Extraction Strategies with AsyncWebCrawler

In many cases, relying on a Large Language Model (LLM) to parse and structure data from web pages is both unnecessary and wasteful. Instead of incurring additional computational overhead, network latency, and even contributing to unnecessary CO2 emissions, you can employ direct HTML parsing strategies. These approaches are faster, simpler, and more environmentally friendly, running efficiently on any computer or device without costly API calls.

Crawl4AI offers two primary declarative extraction strategies that do not depend on LLMs:
- `JsonCssExtractionStrategy`
- `JsonXPathExtractionStrategy`

Of these two, while CSS selectors are often simpler to use, **XPath selectors are generally more robust and flexible**, particularly for large-scale scraping tasks. Modern websites often generate dynamic or ephemeral class names that are subject to frequent change. XPath, on the other hand, allows you to navigate the DOM structure directly, making your selectors less brittle and less dependent on inconsistent class names.

#### Why Use JSON-Based Extraction Instead of LLMs?

1. **Speed & Efficiency**: Direct HTML parsing bypasses the latency of external API calls.
2. **Lower Resource Usage**: No need for large models, GPU acceleration, or network overhead.
3. **Environmentally Friendly**: Reduced energy consumption and carbon footprint compared to LLM inference.
4. **Offline Capability**: Works anywhere you have the HTML, no network needed.
5. **Scalability & Reliability**: Stable and predictable, without dealing with model “hallucinations” or downtime.

#### Advantages of XPath Over CSS

1. **Stability in Dynamic Environments**: Websites change their classes and IDs constantly. XPath allows you to refer to elements by structure and position instead of relying on fragile class names.
2. **Finer-Grained Control**: XPath supports advanced queries like traversing parent/child relationships, filtering based on attributes, and handling complex nested patterns.
3. **Consistency Across Complex Pages**: Even when the front-end framework changes markup or introduces randomized class names, XPath expressions often remain valid if the structural hierarchy stays intact.
4. **More Powerful Selection Logic**: You can write conditions like `//div[@data-test='price']` or `//tr[3]/td[2]` to accurately pinpoint elements.

#### Example Using XPath

Below is an example that extracts cryptocurrency prices from a hypothetical page using `JsonXPathExtractionStrategy`. Here, we avoid depending on class names entirely, focusing on the consistent structure of the HTML. By adjusting XPath expressions, you can overcome dynamic naming schemes that would break fragile CSS selectors.

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonXPathExtractionStrategy

async def extract_data_using_xpath():
    print("\n--- Using JsonXPathExtractionStrategy for Fast, Reliable Structured Output ---")

    # Define the extraction schema using XPath selectors
    # Example: We know the table rows are always in this structure, regardless of class names
    schema = {
        "name": "Crypto Prices",
        "baseSelector": "//table/tbody/tr",
        "fields": [
            {
                "name": "crypto",
                "selector": ".//td[1]/h2",
                "type": "text",
            },
            {
                "name": "symbol",
                "selector": ".//td[1]/p",
                "type": "text",
            },
            {
                "name": "price",
                "selector": ".//td[2]",
                "type": "text",
            }
        ],
    }

    extraction_strategy = JsonXPathExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(verbose=True) as crawler:
        # Use XPath extraction on a page known for frequently changing its class names
        result = await crawler.arun(
            url="https://www.examplecrypto.com/prices",
            extraction_strategy=extraction_strategy,
            bypass_cache=True,
        )

        assert result.success, "Failed to crawl the page"

        # Parse the extracted content
        crypto_prices = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(crypto_prices)} cryptocurrency prices")
        print(json.dumps(crypto_prices[0], indent=2))

    return crypto_prices

# Run the async function
asyncio.run(extract_data_using_xpath())
```

#### When to Use CSS vs. XPath

- **CSS Selectors**: Good for simpler, stable sites where classes and IDs are fixed and descriptive. Ideal if you’re already familiar with front-end development patterns.
- **XPath Selectors**: Recommended for complex or highly dynamic websites. If classes and IDs are meaningless, random, or prone to frequent changes, XPath provides a more structural and future-proof solution.

#### Handling Dynamic Content

Even on websites that load content asynchronously, you can still rely on XPath extraction. Combine the extraction strategy with JavaScript execution to scroll or wait for certain elements to appear. Using XPath after the page finishes loading ensures you’re targeting elements that are fully rendered and stable.

For example:

```python
async def extract_dynamic_data():
    schema = {
        "name": "Dynamic Crypto Prices",
        "baseSelector": "//tr[contains(@class, 'price-row')]",
        "fields": [
            {"name": "name", "selector": ".//td[1]", "type": "text"},
            {"name": "price", "selector": ".//td[2]", "type": "text"},
        ]
    }

    js_code = """
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(resolve => setTimeout(resolve, 2000));
    """

    extraction_strategy = JsonXPathExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.examplecrypto.com/dynamic-prices",
            extraction_strategy=extraction_strategy,
            js_code=js_code,
            wait_for="//tr[contains(@class, 'price-row')][20]",  # Wait until at least 20 rows load
            bypass_cache=True,
        )

        crypto_data = json.loads(result.extracted_content)
        print(f"Extracted {len(crypto_data)} cryptocurrency entries")
```

#### Best Practices

1. **Avoid LLM-Based Extraction**: If the data is repetitive and structured, direct HTML parsing is faster, cheaper, and more stable.
2. **Start with XPath**: In a constantly changing environment, building XPath selectors from stable structural elements (like table hierarchies, element positions, or unique attributes) ensures you won’t need to frequently rewrite selectors.
3. **Test in Developer Tools**: Use browser consoles or `xmllint` to quickly verify XPath queries before coding.
4. **Focus on Hierarchy, Not Classes**: Avoid relying on class names if they’re dynamic. Instead, use structural approaches like `//table/tbody/tr` or `//div[@data-test='price']`.
5. **Combine with JS Execution**: For dynamic sites, run small snippets of JS to reveal content before extracting with XPath.

By following these guidelines, you can create high-performance, resilient extraction pipelines. You’ll save resources, reduce environmental impact, and enjoy a level of reliability and speed that LLM-based solutions can’t match when parsing repetitive data from complex or ever-changing websites.

### **Automating Schema Generation with a One-Time LLM-Assisted Utility**

While the focus of these extraction strategies is to avoid continuous reliance on LLMs, you can leverage a model once to streamline the creation of complex schemas. Instead of painstakingly determining repetitive patterns, crafting CSS or XPath selectors, and deciding field definitions by hand, you can prompt a language model once with the raw HTML and a brief description of what you need to extract. The result is a ready-to-use schema that you can plug into `JsonCssExtractionStrategy` or `JsonXPathExtractionStrategy` for lightning-fast extraction without further model calls.

**How It Works:**
1. Provide the raw HTML containing your repetitive patterns.
2. Optionally specify a natural language query describing the data you want.
3. Run `generate_schema(html, query)` to let the LLM generate a schema automatically.
4. Take the returned schema and use it directly with `JsonCssExtractionStrategy` or `JsonXPathExtractionStrategy`.
5. After this initial step, no more LLM calls are necessary—you now have a schema that you can reuse as often as you like.

**Code Example:**

Here is a simplified demonstration using the utility function `generate_schema` that you’ve incorporated into your codebase. In this example, we:
- Use a one-time LLM call to derive a schema from the HTML structure of a job board.
- Apply the resulting schema to `JsonXPathExtractionStrategy` (although you can also use `JsonCssExtractionStrategy` if preferred).
- Extract data from the target page at high speed with no subsequent LLM calls.

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonXPathExtractionStrategy

# Assume generate_schema is integrated and available
from my_schema_utils import generate_schema

async def extract_data_with_generated_schema():
    # Raw HTML snippet representing repetitive patterns in the webpage
    test_html = """
    <div class="company-listings">
        <div class="company" data-company-id="123">
            <div class="company-header">
                <img class="company-logo" src="google.png" alt="Google">
                <h1 class="company-name">Google</h1>
                <div class="company-meta">
                    <span class="company-size">10,000+ employees</span>
                    <span class="company-industry">Technology</span>
                    <a href="https://google.careers" class="careers-link">Careers Page</a>
                </div>
            </div>
            
            <div class="departments">
                <div class="department">
                    <h2 class="department-name">Engineering</h2>
                    <div class="positions">
                        <div class="position-card" data-position-id="eng-1">
                            <h3 class="position-title">Senior Software Engineer</h3>
                            <span class="salary-range">$150,000 - $250,000</span>
                            <div class="position-meta">
                                <span class="location">Mountain View, CA</span>
                                <span class="job-type">Full-time</span>
                                <span class="experience">5+ years</span>
                            </div>
                            <div class="skills-required">
                                <span class="skill">Python</span>
                                <span class="skill">Kubernetes</span>
                                <span class="skill">Machine Learning</span>
                            </div>
                            <p class="position-description">Join our core engineering team...</p>
                            <div class="application-info">
                                <span class="posting-date">Posted: 2024-03-15</span>
                                <button class="apply-btn" data-req-id="REQ12345">Apply Now</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """

    # Optional natural language query to guide the schema generation
    query = "Extract company name, position titles, and salaries"

    # One-time call to the LLM to generate a reusable schema
    schema = generate_schema(test_html, query=query)

    # Other exmaples of queries:
    # # Test 1: No query (should extract everything)
    # print("\nTest 1: No Query (Full Schema)")
    # schema1 = generate_schema(test_html)
    # print(json.dumps(schema1, indent=2))
    
    # # Test 2: Query for just basic job info
    # print("\nTest 2: Basic Job Info Query")
    # query2 = "I only need job titles, salaries, and locations"
    # schema2 = generate_schema(test_html, query2)
    # print(json.dumps(schema2, indent=2))
    
    # # Test 3: Query for company and department structure
    # print("\nTest 3: Organizational Structure Query")
    # query3 = "Extract company details and department names, without position details"
    # schema3 = generate_schema(test_html, query3)
    # print(json.dumps(schema3, indent=2))
    
    # # Test 4: Query for specific skills tracking
    # print("\nTest 4: Skills Analysis Query")
    # query4 = "I want to analyze required skills across all positions"
    # schema4 = generate_schema(test_html, query4)
    # print(json.dumps(schema4, indent=2))

    # Now use the generated schema for high-speed extraction without any further LLM calls
    extraction_strategy = JsonXPathExtractionStrategy(schema, verbose=True)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # URL for demonstration purposes (use any URL that contains a similar structure)
        result = await crawler.arun(
            url="https://crawl4ai.com/jobs",
            extraction_strategy=extraction_strategy,
            bypass_cache=True
        )
        
        if not result.success:
            raise Exception("Extraction failed")

        data = json.loads(result.extracted_content)
        print("Extracted data:")
        print(json.dumps(data, indent=2))

# Run the async function
asyncio.run(extract_data_with_generated_schema())
```

**Benefits of the One-Time LLM Approach:**
- **Time-Saving**: Quickly bootstrap your schema creation, especially for complex pages.
- **Once and Done**: Use the LLM once and then rely purely on the ultra-fast, local extraction strategies.
- **Sustainable**: No repeated model calls means less compute, lower cost, and reduced environmental impact.

This approach leverages the strengths of both worlds: a one-time intelligent schema generation step with a language model, followed by a stable, purely local extraction pipeline that runs efficiently on any machine, without further LLM dependencies.

File: 8_content_selection.ex.md
================================================================================
# Content Selection in Crawl4AI

Crawl4AI offers flexible and powerful methods to precisely select and filter content from webpages. Whether you’re extracting articles, filtering unwanted elements, or using LLMs for structured data extraction, this guide will walk you through the essentials and advanced techniques.

**Table of Contents:**  
- [Content Selection in Crawl4AI](#content-selection-in-crawl4ai)
  - [Introduction \& Quick Start](#introduction--quick-start)
  - [CSS Selectors](#css-selectors)
  - [Content Filtering](#content-filtering)
  - [Handling Iframe Content](#handling-iframe-content)
  - [Structured Content Selection Using LLMs](#structured-content-selection-using-llms)
  - [Pattern-Based Selection](#pattern-based-selection)
  - [Comprehensive Example: Combining Techniques](#comprehensive-example-combining-techniques)
  - [Troubleshooting \& Best Practices](#troubleshooting--best-practices)
  - [Additional Resources](#additional-resources)

---

## Introduction & Quick Start

When crawling websites, you often need to isolate specific parts of a page—such as main article text, product listings, or metadata. Crawl4AI’s content selection features help you fine-tune your crawls to grab exactly what you need, while filtering out unnecessary elements.

**Quick Start Example:** Here’s a minimal example that extracts the main article content from a page:

```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler

async def quick_start():
    config = CrawlerRunConfig(css_selector=".main-article")
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://crawl4ai.com", config=config)
        print(result.extracted_content)
```

This snippet sets a simple CSS selector to focus on the main article area of a webpage. You can build from here, adding more advanced strategies as needed.

---

## CSS Selectors

**What are they?**  
CSS selectors let you target specific parts of a webpage’s HTML. If you can identify a unique CSS selector (such as `.main-article`, `article h1`, or `.product-listing > li`), you can precisely control what parts of the page are extracted.

**How to find selectors:**  
1. Open the page in your browser.  
2. Use browser dev tools (e.g., Chrome DevTools: right-click → "Inspect") to locate the elements you want.  
3. Copy the CSS selector for that element.

**Example:**
```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler

async def extract_heading_and_content(url):
    config = CrawlerRunConfig(css_selector="article h1, article .content")
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.extracted_content
```

**Tip:** If your extracted content is empty, verify that your CSS selectors match existing elements on the page. Using overly generic selectors can also lead to too much content being extracted.

---

## Video and Audio Content

The library extracts video and audio elements with their metadata:

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

# Process videos
for video in result.media["videos"]:
    print(f"Video source: {video['src']}")
    print(f"Type: {video['type']}")
    print(f"Duration: {video.get('duration')}")
    print(f"Thumbnail: {video.get('poster')}")

# Process audio
for audio in result.media["audios"]:
    print(f"Audio source: {audio['src']}")
    print(f"Type: {audio['type']}")
    print(f"Duration: {audio.get('duration')}")
```

## Link Analysis

Crawl4AI provides sophisticated link analysis capabilities, helping you understand the relationship between pages and identify important navigation patterns.

### Link Classification

The library automatically categorizes links into:
- Internal links (same domain)
- External links (different domains)
- Social media links
- Navigation links
- Content links

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

# Analyze internal links
for link in result.links["internal"]:
    print(f"Internal: {link['href']}")
    print(f"Link text: {link['text']}")
    print(f"Context: {link['context']}")  # Surrounding text
    print(f"Type: {link['type']}")  # nav, content, etc.

# Analyze external links
for link in result.links["external"]:
    print(f"External: {link['href']}")
    print(f"Domain: {link['domain']}")
    print(f"Type: {link['type']}")
```

### Smart Link Filtering

Control which links are included in the results with `CrawlerRunConfig`:

```python
config = CrawlerRunConfig(
    exclude_external_links=True,          # Remove external links
    exclude_social_media_links=True,      # Remove social media links
    exclude_social_media_domains=[        # Custom social media domains
        "facebook.com", "twitter.com", "instagram.com"
    ],
    exclude_domains=["ads.example.com"]   # Exclude specific domains
)
result = await crawler.arun(url="https://example.com", config=config)
```

## Metadata Extraction

Crawl4AI automatically extracts and processes page metadata, providing valuable information about the content:

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

metadata = result.metadata
print(f"Title: {metadata['title']}")
print(f"Description: {metadata['description']}")
print(f"Keywords: {metadata['keywords']}")
print(f"Author: {metadata['author']}")
print(f"Published Date: {metadata['published_date']}")
print(f"Modified Date: {metadata['modified_date']}")
print(f"Language: {metadata['language']}")
```



## Content Filtering

Crawl4AI provides content filtering parameters to exclude unwanted elements and ensure that you only get meaningful data. For instance, you can remove navigation bars, ads, or other non-essential parts of the page.

**Key Parameters:**
- `word_count_threshold`: Minimum word count per extracted block. Helps skip short or irrelevant snippets.
- `excluded_tags`: List of HTML tags to omit (e.g., `['form', 'header', 'footer', 'nav']`).
- `exclude_external_links`: Strips out links pointing to external domains.
- `exclude_social_media_links`: Removes common social media links or widgets.
- `exclude_external_images`: Filters out images hosted on external domains.

**Example:**
```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler

async def filtered_extraction(url):
    config = CrawlerRunConfig(
        word_count_threshold=10,
        excluded_tags=['form', 'header', 'footer', 'nav'],
        exclude_external_links=True,
        exclude_social_media_links=True,
        exclude_external_images=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.extracted_content
```

**Best Practice:** Start with a minimal set of exclusions and increase them as needed. If you notice no content is extracted, try lowering `word_count_threshold` or removing certain excluded tags.

---

## Handling Iframe Content

If a page embeds content in iframes (such as videos, maps, or third-party widgets), you may need to enable iframe processing. This ensures that Crawl4AI loads and extracts content displayed inside iframes.

**How to enable:**  
- Set `process_iframes=True` in your `CrawlerRunConfig` to process iframe content.
- Use `remove_overlay_elements=True` to discard popups or modals that might block iframe content.

**Example:**
```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler

async def extract_iframe_content(url):
    config = CrawlerRunConfig(
        process_iframes=True,
        remove_overlay_elements=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.extracted_content
```

**Troubleshooting:**  
- If iframe content doesn’t load, ensure the iframe’s origin is allowed and that you have no network-related issues. Check the logs or consider using a browser-based strategy that supports multi-domain requests.

---

## Structured Content Selection Using LLMs

For more complex extraction tasks (e.g., summarizing content, extracting structured data like titles and key points), you can integrate LLMs. LLM-based extraction strategies let you define a schema and provide instructions to an LLM so it returns structured, JSON-formatted results.

**When to use LLM-based strategies:**  
- Extracting complex structures not easily captured by simple CSS selectors.  
- Summarizing or transforming data.  
- Handling varied, unpredictable page layouts.

**Example with an LLMExtractionStrategy:**
```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler
from pydantic import BaseModel
from typing import List
import json

class ArticleContent(BaseModel):
    title: str
    main_points: List[str]
    conclusion: str

async def extract_article_with_llm(url):
    strategy = LLMExtractionStrategy(
        provider="ollama/nemotron",
        schema=ArticleContent.schema(),
        instruction="Extract the main article title, key points, and conclusion"
    )

    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        article = json.loads(result.extracted_content)
        return article
```

**Tips for LLM-based extraction:**  
- Refine your prompt in `instruction` to guide the LLM towards the desired structure.  
- If results are incomplete or incorrect, consider adjusting the schema or adding more context to the instruction.  
- Check for errors and handle edge cases where the LLM might not find certain fields.

---

## Pattern-Based Selection

When dealing with repetitive, structured patterns (like a list of articles or products), you can use `JsonCssExtractionStrategy` to define a JSON schema that maps selectors to specific fields.

**Use Cases:**  
- News article listings, product grids, directory entries.  
- Extract multiple items that follow a similar structure on the same page.

**Example JSON Schema Extraction:**
```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler
import json

schema = {
    "name": "News Articles",
    "baseSelector": "article.news-item",
    "fields": [
        {"name": "headline", "selector": "h2", "type": "text"},
        {"name": "summary", "selector": ".summary", "type": "text"},
        {"name": "category", "selector": ".category", "type": "text"},
        {
            "name": "metadata",
            "type": "nested",
            "fields": [
                {"name": "author", "selector": ".author", "type": "text"},
                {"name": "date", "selector": ".date", "type": "text"}
            ]
        }
    ]
}

async def extract_news_items(url):
    strategy = JsonCssExtractionStrategy(schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        articles = json.loads(result.extracted_content)
        return articles
```

**Maintenance Tip:** If the site’s structure changes, update your schema accordingly. Test small changes to ensure the extracted structure still matches your expectations.

---

## Comprehensive Example: Combining Techniques

Below is a more involved example that demonstrates combining multiple strategies and filtering parameters. Here, we extract structured article content from an `article.main` section, exclude unnecessary elements, and enforce a word count threshold.

```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json

async def extract_article_content(url: str):
    # Schema for structured extraction
    article_schema = {
        "name": "Article",
        "baseSelector": "article.main",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": ".content", "type": "text"}
        ]
    }

    config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(article_schema),
        word_count_threshold=10,
        excluded_tags=['nav', 'footer'],
        exclude_external_links=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        extracted = json.loads(result.extracted_content)
        return extracted
```

**Expanding This Example:**  
- Add pagination logic to handle multi-page extractions.  
- Introduce LLM-based extraction for a summary of the article’s main points.  
- Adjust filtering parameters to refine what content is included or excluded.

---

## Troubleshooting & Best Practices

**Common Issues & Fixes:**
- **Empty extraction result:**  
  - Verify CSS selectors and filtering parameters.  
  - Lower or remove `word_count_threshold` to see if overly strict criteria are filtering everything out.
  - Check network requests or iframe settings if content is loaded dynamically.

- **Unintended content included:**  
  - Add more tags to `excluded_tags`, or refine your CSS selectors.  
  - Use `exclude_external_links` and other filters to clean up results.

- **LLM extraction errors:**  
  - Ensure the schema matches the expected JSON structure.  
  - Refine the `instruction` prompt to guide the LLM more clearly.  
  - Validate LLM provider configuration and error logs.

**Performance Tips:**
- Start with simpler strategies (basic CSS selectors) before moving to advanced LLM-based extraction.  
- Use caching or asynchronous crawling to handle large numbers of pages efficiently.  
- Consider running headless browser extractions in Docker for consistent, reproducible environments.

---

## Additional Resources

- **GitHub Source Files:**  
  - [Async Web Crawler Implementation](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/async_webcrawler.py)  
  - [Async Crawler Strategy Implementation](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/async_crawler_strategy.py)

- **Advanced Topics:**  
  - Dockerized deployments for reproducible scraping environments.  
  - Integration with caching or proxy services for large-scale crawls.  
  - Expanding LLM strategies to perform complex transformations or summarizations.

Use these links and approaches as a starting point to refine your crawling strategies. With Crawl4AI’s flexible configuration and powerful selection methods, you’ll be able to extract exactly the content you need—no more, no less.
File: 9_cache_modes.md
================================================================================
# Crawl4AI Cache System and Migration Guide

## Overview
Starting from version 0.5.0, Crawl4AI introduces a new caching system that replaces the old boolean flags with a more intuitive `CacheMode` enum. This change simplifies cache control and makes the behavior more predictable.

## Old vs New Approach

### Old Way (Deprecated)
The old system used multiple boolean flags:
- `bypass_cache`: Skip cache entirely
- `disable_cache`: Disable all caching
- `no_cache_read`: Don't read from cache
- `no_cache_write`: Don't write to cache

### New Way (Recommended)
The new system uses a single `CacheMode` enum:
- `CacheMode.ENABLED`: Normal caching (read/write)
- `CacheMode.DISABLED`: No caching at all
- `CacheMode.READ_ONLY`: Only read from cache
- `CacheMode.WRITE_ONLY`: Only write to cache
- `CacheMode.BYPASS`: Skip cache for this operation

## Migration Example

### Old Code (Deprecated)
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def use_proxy():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            bypass_cache=True  # Old way
        )
        print(len(result.markdown))

async def main():
    await use_proxy()

if __name__ == "__main__":
    asyncio.run(main())
```

### New Code (Recommended)
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig

async def use_proxy():
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)  # Use CacheMode in CrawlerRunConfig
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            config=config  # Pass the configuration object
        )
        print(len(result.markdown))

async def main():
    await use_proxy()

if __name__ == "__main__":
    asyncio.run(main())
```

## Common Migration Patterns

| Old Flag              | New Mode                       |
|-----------------------|---------------------------------|
| `bypass_cache=True`   | `cache_mode=CacheMode.BYPASS`  |
| `disable_cache=True`  | `cache_mode=CacheMode.DISABLED`|
| `no_cache_read=True`  | `cache_mode=CacheMode.WRITE_ONLY` |
| `no_cache_write=True` | `cache_mode=CacheMode.READ_ONLY` |

## Suppressing Deprecation Warnings
If you need time to migrate, you can temporarily suppress deprecation warnings:
```python
# In your config.py
SHOW_DEPRECATION_WARNINGS = False
```

