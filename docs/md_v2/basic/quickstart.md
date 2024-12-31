# Quick Start Guide 🚀

Welcome to the Crawl4AI Quickstart Guide! In this tutorial, we'll walk you through the basic usage of Crawl4AI, covering everything from initial setup to advanced features like chunking and extraction strategies, using asynchronous programming. Let's dive in! 🌟

---

## Getting Started 🛠️

Set up your environment with `BrowserConfig` and create an `AsyncWebCrawler` instance.

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig

async def main():
    browser_config = BrowserConfig(verbose=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Add your crawling logic here
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Basic Usage

Provide a URL and let Crawl4AI do the work!

```python
from crawl4ai.async_configs import CrawlerRunConfig

async def main():
    browser_config = BrowserConfig(verbose=True)
    crawl_config = CrawlerRunConfig(url="https://www.nbcnews.com/business")
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(config=crawl_config)
        print(f"Basic crawl result: {result.markdown[:500]}")  # Print first 500 characters

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Taking Screenshots 📸

Capture and save webpage screenshots with `CrawlerRunConfig`:

```python
from crawl4ai.async_configs import CacheMode

async def capture_and_save_screenshot(url: str, output_path: str):
    browser_config = BrowserConfig(verbose=True)
    crawl_config = CrawlerRunConfig(
        url=url,
        screenshot=True,
        cache_mode=CacheMode.BYPASS
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(config=crawl_config)
        
        if result.success and result.screenshot:
            import base64
            screenshot_data = base64.b64decode(result.screenshot)
            with open(output_path, 'wb') as f:
                f.write(screenshot_data)
            print(f"Screenshot saved successfully to {output_path}")
        else:
            print("Failed to capture screenshot")
```

---

### Browser Selection 🌐

Choose from multiple browser engines using `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig

# Use Firefox
firefox_config = BrowserConfig(browser_type="firefox", verbose=True, headless=True)
async with AsyncWebCrawler(config=firefox_config) as crawler:
    result = await crawler.arun(config=CrawlerRunConfig(url="https://www.example.com"))

# Use WebKit
webkit_config = BrowserConfig(browser_type="webkit", verbose=True, headless=True)
async with AsyncWebCrawler(config=webkit_config) as crawler:
    result = await crawler.arun(config=CrawlerRunConfig(url="https://www.example.com"))

# Use Chromium (default)
chromium_config = BrowserConfig(verbose=True, headless=True)
async with AsyncWebCrawler(config=chromium_config) as crawler:
    result = await crawler.arun(config=CrawlerRunConfig(url="https://www.example.com"))
```

---

### User Simulation 🎭

Simulate real user behavior to bypass detection:

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(verbose=True, headless=True)
crawl_config = CrawlerRunConfig(
    url="YOUR-URL-HERE",
    cache_mode=CacheMode.BYPASS,
    simulate_user=True,          # Random mouse movements and clicks
    override_navigator=True      # Makes the browser appear like a real user
)
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(config=crawl_config)
```

---

### Understanding Parameters 🧠

Explore caching and forcing fresh crawls:

```python
async def main():
    browser_config = BrowserConfig(verbose=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First crawl (uses cache)
        result1 = await crawler.arun(config=CrawlerRunConfig(url="https://www.nbcnews.com/business"))
        print(f"First crawl result: {result1.markdown[:100]}...")

        # Force fresh crawl
        result2 = await crawler.arun(
            config=CrawlerRunConfig(url="https://www.nbcnews.com/business", cache_mode=CacheMode.BYPASS)
        )
        print(f"Second crawl result: {result2.markdown[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Adding a Chunking Strategy 🧩

Split content into chunks using `RegexChunking`:

```python
from crawl4ai.chunking_strategy import RegexChunking

async def main():
    browser_config = BrowserConfig(verbose=True)
    crawl_config = CrawlerRunConfig(
        url="https://www.nbcnews.com/business",
        chunking_strategy=RegexChunking(patterns=["\n\n"])
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(config=crawl_config)
        print(f"RegexChunking result: {result.extracted_content[:200]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Advanced Features and Configurations

For advanced examples (LLM strategies, knowledge graphs, pagination handling), ensure all code aligns with the `BrowserConfig` and `CrawlerRunConfig` pattern shown above.
