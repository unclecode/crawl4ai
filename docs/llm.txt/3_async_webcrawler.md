# Extended Documentation: Asynchronous Crawling with `AsyncWebCrawler`

This document provides a comprehensive, human-oriented overview of the `AsyncWebCrawler` class and related components from the `crawl4ai` package. It explains the motivations behind asynchronous crawling, shows how to configure and run crawls, and provides examples for advanced features like dynamic content handling, extraction strategies, caching, containerization, and troubleshooting.

## Introduction
[EDIT: This is not a good way to introduce the library. The library excels at generating crawl data in the form of markdown or extracted JSON as quickly as possible. It is designed to be efficient in terms of memory and CPU usage. Users should choose this library because it generates markdown suitable for large language models and AI. Additionally, it can create structured data, which is beneficial because it supports attaching large language models to generate structured data. It also includes techniques like JSON CSS and JSON XPath extraction, allowing users to define patterns and extract data quickly. One of the library's strengths is its ability to work everywhere. It can crawl any website by offering various capabilities, such as connecting to a remote browser or using persistent data. This feature allows developers to create their own identity on websites where they have authentication access, enabling them to crawl without being mistakenly identified as a bot. This is a better way to introduce the library. In these documents, we discuss the main object, the main class, Asinggull crawlers, and all the functionalities we can achieve with this Asinggull crawler.]

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
