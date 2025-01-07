# Optimized Multi-URL Crawling

> **Note**: We’re developing a new **executor module** that uses a sophisticated algorithm to dynamically manage multi-URL crawling, optimizing for speed and memory usage. The approaches in this document remain fully valid, but keep an eye on **Crawl4AI**’s upcoming releases for this powerful feature! Follow [@unclecode](https://twitter.com/unclecode) on X and check the changelogs to stay updated.


Crawl4AI’s **AsyncWebCrawler** can handle multiple URLs in a single run, which can greatly reduce overhead and speed up crawling. This guide shows how to:

1. **Sequentially** crawl a list of URLs using the **same** session, avoiding repeated browser creation.  
2. **Parallel**-crawl subsets of URLs in batches, again reusing the same browser.  

When the entire process finishes, you close the browser once—**minimizing** memory and resource usage.

---

## 1. Why Avoid Simple Loops per URL?

If you naively do:

```python
for url in urls:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
```

You end up:

1. Spinning up a **new** browser for each URL  
2. Closing it immediately after the single crawl  
3. Potentially using a lot of CPU/memory for short-living browsers  
4. Missing out on session reusability if you have login or ongoing states

**Better** approaches ensure you **create** the browser once, then crawl multiple URLs with minimal overhead.

---

## 2. Sequential Crawling with Session Reuse

### 2.1 Overview

1. **One** `AsyncWebCrawler` instance for **all** URLs.  
2. **One** session (via `session_id`) so we can preserve local storage or cookies across URLs if needed.  
3. The crawler is only closed at the **end**.

**This** is the simplest pattern if your workload is moderate (dozens to a few hundred URLs).

### 2.2 Example Code

```python
import asyncio
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def crawl_sequential(urls: List[str]):
    print("\n=== Sequential Crawling with Session Reuse ===")

    browser_config = BrowserConfig(
        headless=True,
        # For better performance in Docker or low-memory environments:
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )

    crawl_config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator()
    )

    # Create the crawler (opens the browser)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        session_id = "session1"  # Reuse the same session across all URLs
        for url in urls:
            result = await crawler.arun(
                url=url,
                config=crawl_config,
                session_id=session_id
            )
            if result.success:
                print(f"Successfully crawled: {url}")
                # E.g. check markdown length
                print(f"Markdown length: {len(result.markdown_v2.raw_markdown)}")
            else:
                print(f"Failed: {url} - Error: {result.error_message}")
    finally:
        # After all URLs are done, close the crawler (and the browser)
        await crawler.close()

async def main():
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ]
    await crawl_sequential(urls)

if __name__ == "__main__":
    asyncio.run(main())
```

**Why It’s Good**:

- **One** browser launch.  
- Minimal memory usage.  
- If the site requires login, you can log in once in `session_id` context and preserve auth across all URLs.

---

## 3. Parallel Crawling with Browser Reuse

### 3.1 Overview

To speed up crawling further, you can crawl multiple URLs in **parallel** (batches or a concurrency limit). The crawler still uses **one** browser, but spawns different sessions (or the same, depending on your logic) for each task.

### 3.2 Example Code

For this example make sure to install the [psutil](https://pypi.org/project/psutil/) package.

```bash
pip install psutil
```

Then you can run the following code:

```python
import os
import sys
import psutil
import asyncio

__location__ = os.path.dirname(os.path.abspath(__file__))
__output__ = os.path.join(__location__, "output")

# Append parent directory to system path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def crawl_parallel(urls: List[str], max_concurrent: int = 3):
    print("\n=== Parallel Crawling with Browser Reuse + Memory Check ===")

    # We'll keep track of peak memory usage across all tasks
    peak_memory = 0
    process = psutil.Process(os.getpid())

    def log_memory(prefix: str = ""):
        nonlocal peak_memory
        current_mem = process.memory_info().rss  # in bytes
        if current_mem > peak_memory:
            peak_memory = current_mem
        print(f"{prefix} Current Memory: {current_mem // (1024 * 1024)} MB, Peak: {peak_memory // (1024 * 1024)} MB")

    # Minimal browser config
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,   # corrected from 'verbos=False'
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    # Create the crawler instance
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        # We'll chunk the URLs in batches of 'max_concurrent'
        success_count = 0
        fail_count = 0
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = []

            for j, url in enumerate(batch):
                # Unique session_id per concurrent sub-task
                session_id = f"parallel_session_{i + j}"
                task = crawler.arun(url=url, config=crawl_config, session_id=session_id)
                tasks.append(task)

            # Check memory usage prior to launching tasks
            log_memory(prefix=f"Before batch {i//max_concurrent + 1}: ")

            # Gather results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check memory usage after tasks complete
            log_memory(prefix=f"After batch {i//max_concurrent + 1}: ")

            # Evaluate results
            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Error crawling {url}: {result}")
                    fail_count += 1
                elif result.success:
                    success_count += 1
                else:
                    fail_count += 1

        print(f"\nSummary:")
        print(f"  - Successfully crawled: {success_count}")
        print(f"  - Failed: {fail_count}")

    finally:
        print("\nClosing crawler...")
        await crawler.close()
        # Final memory log
        log_memory(prefix="Final: ")
        print(f"\nPeak memory usage (MB): {peak_memory // (1024 * 1024)}")

async def main():
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
        "https://example.com/page4"
    ]
    await crawl_parallel(urls, max_concurrent=2)

if __name__ == "__main__":
    asyncio.run(main())

```

**Notes**:

- We **reuse** the same `AsyncWebCrawler` instance for all parallel tasks, launching **one** browser.  
- Each parallel sub-task might get its own `session_id` so they don’t share cookies/localStorage (unless that’s desired).  
- We limit concurrency to `max_concurrent=2` or 3 to avoid saturating CPU/memory.

---

## 4. Performance Tips

1. **Extra Browser Args**  
   - `--disable-gpu`, `--no-sandbox` can help in Docker or restricted environments.  
   - `--disable-dev-shm-usage` avoids using `/dev/shm` which can be small on some systems.

2. **Session Reuse**  
   - If your site requires a login or you want to maintain local data across URLs, share the **same** `session_id`.  
   - If you want isolation (each URL fresh), create unique sessions.

3. **Batching**  
   - If you have **many** URLs (like thousands), you can do parallel crawling in chunks (like `max_concurrent=5`).  
   - Use `arun_many()` for a built-in approach if you prefer, but the example above is often more flexible.

4. **Cache**  
   - If your pages share many resources or you’re re-crawling the same domain repeatedly, consider setting `cache_mode=CacheMode.ENABLED` in `CrawlerRunConfig`.  
   - If you need fresh data each time, keep `cache_mode=CacheMode.BYPASS`.

5. **Hooks**  
   - You can set up global hooks for each crawler (like to block images) or per-run if you want.  
   - Keep them consistent if you’re reusing sessions.

---

## 5. Summary

- **One** `AsyncWebCrawler` + multiple calls to `.arun()` is far more efficient than launching a new crawler per URL.  
- **Sequential** approach with a shared session is simple and memory-friendly for moderate sets of URLs.  
- **Parallel** approach can speed up large crawls by concurrency, but keep concurrency balanced to avoid overhead.  
- Close the crawler once at the end, ensuring the browser is only opened/closed once.

For even more advanced memory optimizations or dynamic concurrency patterns, see future sections on hooking or distributed crawling. The patterns above suffice for the majority of multi-URL scenarios—**giving you speed, simplicity, and minimal resource usage**. Enjoy your optimized crawling!