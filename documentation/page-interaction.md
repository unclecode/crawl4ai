Page Interaction
================

Crawl4AI provides powerful features for interacting with **dynamic** webpages, handling JavaScript execution, waiting for conditions, and managing multi-step flows. By combining **js\_code**, **wait\_for**, and certain **CrawlerRunConfig** parameters, you can:

1. Click “Load More” buttons
2. Fill forms and submit them
3. Wait for elements or data to appear
4. Reuse sessions across multiple steps

Below is a quick overview of how to do it.

---

1. JavaScript Execution
-----------------------

### Basic Execution

**`js_code`** in **`CrawlerRunConfig`** accepts either a single JS string or a list of JS snippets.
**Example**: We’ll scroll to the bottom of the page, then optionally click a “Load More” button.

```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Single JS command
    config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",  # Example site
            config=config
        )
        print("Crawled length:", len(result.cleaned_html))

    # Multiple commands
    js_commands = [
        "window.scrollTo(0, document.body.scrollHeight);",
        # 'More' link on Hacker News
        "document.querySelector('a.morelink')?.click();",
    ]
    config = CrawlerRunConfig(js_code=js_commands)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",  # Another pass
            config=config
        )
        print("After scroll+click, length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
```

**Relevant `CrawlerRunConfig` params**:
- **`js_code`**: A string or list of strings with JavaScript to run after the page loads.
- **`js_only`**: If set to `True` on subsequent calls, indicates we’re continuing an existing session without a new full navigation.
- **`session_id`**: If you want to keep the same page across multiple calls, specify an ID.

---