Below is a sample Markdown file (`tutorials/async-webcrawler-basics.md`) illustrating how you might teach new users the fundamentals of `AsyncWebCrawler`. This tutorial builds on the **Getting Started** section by introducing key configuration parameters and the structure of the crawl result. Feel free to adjust the code snippets, wording, or format to match your style.

---

# AsyncWebCrawler Basics

In this tutorial, you’ll learn how to:

1. Create and configure an `AsyncWebCrawler` instance  
2. Understand the `CrawlResult` object returned by `arun()`  
3. Use basic `BrowserConfig` and `CrawlerRunConfig` options to tailor your crawl

> **Prerequisites**  
> - You’ve already completed the [Getting Started](./getting-started.md) tutorial (or have equivalent knowledge).  
> - You have **Crawl4AI** installed and configured with Playwright.

---

## 1. What is `AsyncWebCrawler`?

`AsyncWebCrawler` is the central class for running asynchronous crawling operations in Crawl4AI. It manages browser sessions, handles dynamic pages (if needed), and provides you with a structured result object for each crawl. Essentially, it’s your high-level interface for collecting page data.

```python
from crawl4ai import AsyncWebCrawler

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com")
    print(result)
```

---

## 2. Creating a Basic `AsyncWebCrawler` Instance

Below is a simple code snippet showing how to create and use `AsyncWebCrawler`. This goes one step beyond the minimal example you saw in [Getting Started](./getting-started.md).

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai import BrowserConfig, CrawlerRunConfig

async def main():
    # 1. Set up configuration objects (optional if you want defaults)
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=True
    )
    crawler_config = CrawlerRunConfig(
        page_timeout=30000,     # 30 seconds
        wait_for_images=True,
        verbose=True
    )

    # 2. Initialize AsyncWebCrawler with your chosen browser config
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 3. Run a single crawl
        url_to_crawl = "https://example.com"
        result = await crawler.arun(url=url_to_crawl, config=crawler_config)
        
        # 4. Inspect the result
        if result.success:
            print(f"Successfully crawled: {result.url}")
            print(f"HTML length: {len(result.html)}")
            print(f"Markdown snippet: {result.markdown[:200]}...")
        else:
            print(f"Failed to crawl {result.url}. Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Key Points

1. **`BrowserConfig`** is optional, but it’s the place to specify browser-related settings (e.g., `headless`, `browser_type`).
2. **`CrawlerRunConfig`** deals with how you want the crawler to behave for this particular run (timeouts, waiting for images, etc.).
3. **`arun()`** is the main method to crawl a single URL. We’ll see how `arun_many()` works in later tutorials.

---

## 3. Understanding `CrawlResult`

When you call `arun()`, you get back a `CrawlResult` object containing all the relevant data from that crawl attempt. Some common fields include:

```python
class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: Optional[str] = None
    media: Dict[str, List[Dict]] = {}
    links: Dict[str, List[Dict]] = {}
    screenshot: Optional[str] = None  # base64-encoded screenshot if requested
    pdf: Optional[bytes] = None       # binary PDF data if requested
    markdown: Optional[Union[str, MarkdownGenerationResult]] = None
    markdown_v2: Optional[MarkdownGenerationResult] = None
    error_message: Optional[str] = None
    # ... plus other fields like status_code, ssl_certificate, extracted_content, etc.
```

### Commonly Used Fields

- **`success`**: `True` if the crawl succeeded, `False` otherwise.  
- **`html`**: The raw HTML (or final rendered state if JavaScript was executed).  
- **`markdown` / `markdown_v2`**: Contains the automatically generated Markdown representation of the page.  
- **`media`**: A dictionary with lists of extracted images, videos, or audio elements.  
- **`links`**: A dictionary with lists of “internal” and “external” link objects.  
- **`error_message`**: If `success` is `False`, this often contains a description of the error.

**Example**:

```python
if result.success:
    print("Page Title or snippet of HTML:", result.html[:200])
    if result.markdown:
        print("Markdown snippet:", result.markdown[:200])
    print("Links found:", len(result.links.get("internal", [])), "internal links")
else:
    print("Error crawling:", result.error_message)
```

---

## 4. Relevant Basic Parameters

Below are a few `BrowserConfig` and `CrawlerRunConfig` parameters you might tweak early on. We’ll cover more advanced ones (like proxies, PDF, or screenshots) in later tutorials.

### 4.1 `BrowserConfig` Essentials

| Parameter          | Description                                               | Default        |
|--------------------|-----------------------------------------------------------|----------------|
| `browser_type`     | Which browser engine to use: `"chromium"`, `"firefox"`, `"webkit"` | `"chromium"`   |
| `headless`         | Run the browser with no UI window. If `False`, you see the browser. | `True`         |
| `verbose`          | Print extra logs for debugging.                          | `True`         |
| `java_script_enabled` | Toggle JavaScript. When `False`, you might speed up loads but lose dynamic content. | `True`         |

### 4.2 `CrawlerRunConfig` Essentials

| Parameter             | Description                                                  | Default            |
|-----------------------|--------------------------------------------------------------|--------------------|
| `page_timeout`        | Maximum time in ms to wait for the page to load or scripts. | `30000` (30s)      |
| `wait_for_images`     | Wait for images to fully load. Good for accurate rendering.  | `True`             |
| `css_selector`        | Target only certain elements for extraction.                | `None`             |
| `excluded_tags`       | Skip certain HTML tags (like `nav`, `footer`, etc.)          | `None`             |
| `verbose`             | Print logs for debugging.                                    | `True`             |

> **Tip**: Don’t worry if you see lots of parameters. You’ll learn them gradually in later tutorials.

---

## 5. Windows-Specific Configuration

When using AsyncWebCrawler on Windows, you might encounter a `NotImplementedError` related to `asyncio.create_subprocess_exec`. This is a known Windows-specific issue that occurs because Windows' default event loop doesn't support subprocess operations.

To resolve this, Crawl4AI provides a utility function to configure Windows to use the ProactorEventLoop. Call this function before running any async operations:

```python
from crawl4ai.utils import configure_windows_event_loop

# Call this before any async operations if you're on Windows
configure_windows_event_loop()

# Your AsyncWebCrawler code here
```

---

## 6. Putting It All Together

Here’s a slightly more in-depth example that shows off a few key config parameters at once:

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai import BrowserConfig, CrawlerRunConfig

async def main():
    browser_cfg = BrowserConfig(
        browser_type="chromium",
        headless=True,
        java_script_enabled=True,
        verbose=False
    )

    crawler_cfg = CrawlerRunConfig(
        page_timeout=30000,  # wait up to 30 seconds
        wait_for_images=True,
        css_selector=".article-body",  # only extract content under this CSS selector
        verbose=True
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun("https://news.example.com", config=crawler_cfg)

        if result.success:
            print("[OK] Crawled:", result.url)
            print("HTML length:", len(result.html))
            print("Extracted Markdown:", result.markdown_v2.raw_markdown[:300])
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Observations**:
- `css_selector=".article-body"` ensures we only focus on the main content region.  
- `page_timeout=30000` helps if the site is slow.  
- We turned off `verbose` logs for the browser but kept them on for the crawler config.  

---

## 7. Next Steps

- **Smart Crawling Techniques**: Learn to handle iframes, advanced caching, and selective extraction in the [next tutorial](./smart-crawling.md).
- **Hooks & Custom Code**: See how to inject custom logic before and after navigation in a dedicated [Hooks Tutorial](./hooks-custom.md).
- **Reference**: For a complete list of every parameter in `BrowserConfig` and `CrawlerRunConfig`, check out the [Reference section](../../reference/configuration.md).

---

## Summary

You now know the basics of **AsyncWebCrawler**:
- How to create it with optional browser/crawler configs
- How `arun()` works for single-page crawls
- Where to find your crawled data in `CrawlResult`
- A handful of frequently used configuration parameters

From here, you can refine your crawler to handle more advanced scenarios, like focusing on specific content or dealing with dynamic elements. Let’s move on to **[Smart Crawling Techniques](./smart-crawling.md)** to learn how to handle iframes, advanced caching, and more.

---

**Last updated**: 2024-XX-XX

Keep exploring! If you get stuck, remember to check out the [How-To Guides](../../how-to/) for targeted solutions or the [Explanations](../../explanations/) for deeper conceptual background.