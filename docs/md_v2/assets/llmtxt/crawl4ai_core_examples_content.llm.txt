```markdown
# Examples Outline for crawl4ai - core Component

**Target Document Type:** Examples Collection
**Target Output Filename Suggestion:** `llm_examples_core.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2024-05-24 10:00:00
---

This document provides a collection of runnable code examples for the `core` component of the `crawl4ai` library. Each example is designed to showcase a specific feature or configuration.

## 1. Basic `AsyncWebCrawler` Usage

### 1.1. Example: Simplest crawl of a single URL with default `BrowserConfig` and `CrawlerRunConfig`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def simplest_crawl():
    # Uses default BrowserConfig and CrawlerRunConfig
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        if result.success:
            print("Crawl successful!")
            print(f"Markdown (first 300 chars):\n{result.markdown.raw_markdown[:300]}...")
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(simplest_crawl())
```

---
### 1.2. Example: Using `AsyncWebCrawler` as an asynchronous context manager (`async with`).

This is the recommended way to manage the crawler's lifecycle.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def context_manager_crawl():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        if result.success:
            print("Crawl successful using context manager!")
            print(f"Page title from metadata: {result.metadata.get('title')}")
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(context_manager_crawl())
```

---
### 1.3. Example: Explicitly starting and closing the `AsyncWebCrawler` using `start()` and `close()`.

Useful for scenarios where the crawler's lifecycle needs more manual control.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def explicit_lifecycle_crawl():
    crawler = AsyncWebCrawler()
    await crawler.start()  # Explicitly start the crawler and browser
    try:
        result = await crawler.arun(url="https://example.com")
        if result.success:
            print("Crawl successful with explicit start/close!")
            print(f"Cleaned HTML (first 300 chars):\n{result.cleaned_html[:300]}...")
        else:
            print(f"Crawl failed: {result.error_message}")
    finally:
        await crawler.close()  # Ensure the crawler is closed

if __name__ == "__main__":
    asyncio.run(explicit_lifecycle_crawl())
```

---
### 1.4. Example: Handling a failed crawl (e.g., non-existent URL, network error) and checking `CrawlResult.success` and `CrawlResult.error_message`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def failed_crawl_handling():
    async with AsyncWebCrawler() as crawler:
        # Using a deliberately non-existent URL
        result = await crawler.arun(url="https://thissitedoesnotexist.crawl4ai")
        if not result.success:
            print(f"Crawl failed as expected for URL: {result.url}")
            print(f"Status Code: {result.status_code}")
            print(f"Error Message: {result.error_message}")
        else:
            print("Crawl unexpectedly succeeded!")

if __name__ == "__main__":
    asyncio.run(failed_crawl_handling())
```

---
### 1.5. Example: Processing raw HTML content directly using `crawler.aprocess_html()`.

This is useful if you already have HTML content and want to use Crawl4ai's processing capabilities.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def process_raw_html_directly():
    raw_html_content = """
    <html>
        <head><title>My Test Page</title></head>
        <body>
            <h1>Welcome!</h1>
            <p>This is a paragraph with a <a href="https://example.com">link</a>.</p>
            <script>console.log("This should be removed");</script>
        </body>
    </html>
    """
    # No need for BrowserConfig as we are not navigating
    async with AsyncWebCrawler() as crawler:
        # Use CrawlerRunConfig if you need specific processing options
        config = CrawlerRunConfig()
        result = await crawler.aprocess_html(
            url="raw://my_virtual_page", # Provide a conceptual URL
            html=raw_html_content,
            config=config
        )
        if result.success:
            print("Raw HTML processed successfully!")
            print(f"Markdown:\n{result.markdown.raw_markdown}")
            print(f"Cleaned HTML:\n{result.cleaned_html}")
        else:
            print(f"HTML processing failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(process_raw_html_directly())
```

---
### 1.6. Example: Crawling a local HTML file using the `file:///` prefix.

First, create a dummy HTML file named `local_test.html` in the same directory as your script.

```python
# local_test.html
# <!DOCTYPE html>
# <html>
# <head>
#     <title>Local Test File</title>
# </head>
# <body>
#     <h1>Hello from a local file!</h1>
#     <p>This content is loaded from the local filesystem.</p>
# </body>
# </html>
```

```python
import asyncio
import os
from pathlib import Path
from crawl4ai import AsyncWebCrawler

async def crawl_local_file():
    # Create a dummy local HTML file for the example
    script_dir = Path(__file__).parent
    local_file_path = script_dir / "local_test_for_crawl.html"
    with open(local_file_path, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html><head><title>Local Test</title></head><body><h1>Local Content</h1></body></html>")

    file_url = f"file:///{local_file_path.resolve()}"
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=file_url)
        if result.success:
            print(f"Successfully crawled local file: {file_url}")
            print(f"Markdown (first 100 chars): {result.markdown.raw_markdown[:100]}...")
        else:
            print(f"Failed to crawl local file: {result.error_message}")
    
    # Clean up the dummy file
    if os.path.exists(local_file_path):
        os.remove(local_file_path)

if __name__ == "__main__":
    asyncio.run(crawl_local_file())
```

---
### 1.7. Example: Accessing basic fields from `CrawlResult` (e.g., `url`, `html`, `markdown.raw_markdown`, `status_code`, `response_headers`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def access_crawl_result_fields():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        if result.success:
            print(f"URL Crawled: {result.url}")
            print(f"Status Code: {result.status_code}")
            
            print("\n--- Response Headers (sample) ---")
            if result.response_headers:
                for key, value in list(result.response_headers.items())[:3]: # Print first 3 headers
                    print(f"{key}: {value}")
            
            print(f"\n--- Raw HTML (first 100 chars) ---\n{result.html[:100]}...")
            print(f"\n--- Cleaned HTML (first 100 chars) ---\n{result.cleaned_html[:100]}...")
            
            if result.markdown:
                 print(f"\n--- Raw Markdown (first 100 chars) ---\n{result.markdown.raw_markdown[:100]}...")
            
            print(f"\n--- Metadata (sample) ---")
            if result.metadata:
                 for key, value in list(result.metadata.items())[:3]: # Print first 3 metadata items
                    print(f"{key}: {value}")
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(access_crawl_result_fields())
```

---
## 2. Configuring the Browser (`BrowserConfig`)

### 2.1. Example: Initializing `AsyncWebCrawler` with a custom `BrowserConfig` object.

This example sets the browser to run in non-headless mode and uses Firefox.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def custom_browser_config_init():
    # Configure browser to be Firefox and visible
    browser_config = BrowserConfig(
        browser_type="firefox",
        headless=False  # Set to True to run without UI
    )
    
    # Pass the custom config to the crawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com")
        if result.success:
            print(f"Crawl successful with custom BrowserConfig (Firefox, visible)!")
            print(f"Page title: {result.metadata.get('title')}")
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    # This example might open a visible browser window.
    # Ensure Firefox is installed if you run this.
    # asyncio.run(custom_browser_config_init()) 
    print("Skipping custom_browser_config_init example in automated run to avoid GUI interaction.")
```

---
### 2.2. Browser Type and Headless Mode

#### 2.2.1. Example: Using Chromium browser (default).

This shows the default behavior if no `browser_type` is specified.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def chromium_default_crawl():
    # Chromium is the default, but we can explicitly set it
    browser_config = BrowserConfig(browser_type="chromium", headless=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com")
        if result.success:
            print("Crawl successful with Chromium (default)!")
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(chromium_default_crawl())
```

---
#### 2.2.2. Example: Using Firefox browser (`browser_type="firefox"`).

Ensure Firefox is installed on your system for this example to run.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def firefox_crawl():
    browser_config = BrowserConfig(browser_type="firefox", headless=True)
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url="https://example.com")
            if result.success:
                print("Crawl successful with Firefox!")
            else:
                print(f"Crawl failed with Firefox: {result.error_message}")
    except Exception as e:
        print(f"Error running Firefox example: {e}. Ensure Firefox is installed and Playwright browsers are set up (`crawl4ai-setup`).")


if __name__ == "__main__":
    # asyncio.run(firefox_crawl())
    print("Skipping Firefox example in automated run. Uncomment to run if Firefox is installed.")
```

---
#### 2.2.3. Example: Using WebKit browser (`browser_type="webkit"`).

Ensure WebKit (Safari's engine) is installed via Playwright.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def webkit_crawl():
    browser_config = BrowserConfig(browser_type="webkit", headless=True)
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url="https://example.com")
            if result.success:
                print("Crawl successful with WebKit!")
            else:
                print(f"Crawl failed with WebKit: {result.error_message}")
    except Exception as e:
         print(f"Error running WebKit example: {e}. Ensure WebKit is installed and Playwright browsers are set up (`crawl4ai-setup`).")


if __name__ == "__main__":
    # asyncio.run(webkit_crawl())
    print("Skipping WebKit example in automated run. Uncomment to run if WebKit is installed.")
```

---
#### 2.2.4. Example: Running the browser in non-headless mode (`headless=False`) for visual debugging.

This will open a visible browser window.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def non_headless_crawl():
    browser_config = BrowserConfig(headless=False)  # Browser window will be visible
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https
```