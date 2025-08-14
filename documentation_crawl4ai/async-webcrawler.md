[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/api/async-webcrawler/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * [URL Seeding](https://docs.crawl4ai.com/core/url-seeding/)
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * [Fit Markdown](https://docs.crawl4ai.com/core/fit-markdown/)
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * [SSL Certificate](https://docs.crawl4ai.com/advanced/ssl-certificate/)
    * [Network & Console Capture](https://docs.crawl4ai.com/advanced/network-console-capture/)
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * AsyncWebCrawler
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/#asyncwebcrawler)
  * [1. Constructor Overview](https://docs.crawl4ai.com/api/async-webcrawler/#1-constructor-overview)
  * [2. Lifecycle: Start/Close or Context Manager](https://docs.crawl4ai.com/api/async-webcrawler/#2-lifecycle-startclose-or-context-manager)
  * [3. Primary Method: arun()](https://docs.crawl4ai.com/api/async-webcrawler/#3-primary-method-arun)
  * [4. Batch Processing: arun_many()](https://docs.crawl4ai.com/api/async-webcrawler/#4-batch-processing-arun_many)
  * [7. Best Practices & Migration Notes](https://docs.crawl4ai.com/api/async-webcrawler/#7-best-practices-migration-notes)
  * [8. Summary](https://docs.crawl4ai.com/api/async-webcrawler/#8-summary)


# AsyncWebCrawler
The **`AsyncWebCrawler`**is the core class for asynchronous web crawling in Crawl4AI. You typically create it**once** , optionally customize it with a **`BrowserConfig`**(e.g., headless, user agent), then**run** multiple **`arun()`**calls with different**`CrawlerRunConfig`**objects.
**Recommended usage** :
1. **Create** a `BrowserConfig` for global browser settings.
2. **Instantiate** `AsyncWebCrawler(config=browser_config)`.
3. **Use** the crawler in an async context manager (`async with`) or manage start/close manually.
4. **Call** `arun(url, config=crawler_run_config)` for each page you want.
* * *
## 1. Constructor Overview
```
class AsyncWebCrawler:
    def __init__(
        self,
        crawler_strategy: Optional[AsyncCrawlerStrategy] = None,
        config: Optional[BrowserConfig] = None,
        always_bypass_cache: bool = False,           # deprecated
        always_by_pass_cache: Optional[bool] = None, # also deprecated
        base_directory: str = ...,
        thread_safe: bool = False,
        **kwargs,
    ):
        """
        Create an AsyncWebCrawler instance.

        Args:
            crawler_strategy:
                (Advanced) Provide a custom crawler strategy if needed.
            config:
                A BrowserConfig object specifying how the browser is set up.
            always_bypass_cache:
                (Deprecated) Use CrawlerRunConfig.cache_mode instead.
            base_directory:
                Folder for storing caches/logs (if relevant).
            thread_safe:
                If True, attempts some concurrency safeguards. Usually False.
            **kwargs:
                Additional legacy or debugging parameters.
        """
    )

### Typical Initialization

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_cfg = BrowserConfig(
    browser_type="chromium",
    headless=True,
    verbose=True
)

crawler = AsyncWebCrawler(config=browser_cfg)
Copy
```

**Notes** :
  * **Legacy** parameters like `always_bypass_cache` remain for backward compatibility, but prefer to set **caching** in `CrawlerRunConfig`.


* * *
## 2. Lifecycle: Start/Close or Context Manager
### 2.1 Context Manager (Recommended)
```
async with AsyncWebCrawler(config=browser_cfg) as crawler:
    result = await crawler.arun("https://example.com")
    # The crawler automatically starts/closes resources
Copy
```

When the `async with` block ends, the crawler cleans up (closes the browser, etc.).
### 2.2 Manual Start & Close
```
crawler = AsyncWebCrawler(config=browser_cfg)
await crawler.start()

result1 = await crawler.arun("https://example.com")
result2 = await crawler.arun("https://another.com")

await crawler.close()
Copy
```

Use this style if you have a **long-running** application or need full control of the crawler’s lifecycle.
* * *
## 3. Primary Method: `arun()`
```
async def arun(
    self,
    url: str,
    config: Optional[CrawlerRunConfig] = None,
    # Legacy parameters for backward compatibility...
) -> CrawlResult:
    ...
Copy
```

### 3.1 New Approach
You pass a `CrawlerRunConfig` object that sets up everything about a crawl—content filtering, caching, session reuse, JS code, screenshots, etc.
```
import asyncio
from crawl4ai import CrawlerRunConfig, CacheMode

run_cfg = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    css_selector="main.article",
    word_count_threshold=10,
    screenshot=True
)

async with AsyncWebCrawler(config=browser_cfg) as crawler:
    result = await crawler.arun("https://example.com/news", config=run_cfg)
    print("Crawled HTML length:", len(result.cleaned_html))
    if result.screenshot:
        print("Screenshot base64 length:", len(result.screenshot))
Copy
```

### 3.2 Legacy Parameters Still Accepted
For **backward** compatibility, `arun()` can still accept direct arguments like `css_selector=...`, `word_count_threshold=...`, etc., but we strongly advise migrating them into a **`CrawlerRunConfig`**.
* * *
## 4. Batch Processing: `arun_many()`
```
async def arun_many(
    self,
    urls: List[str],
    config: Optional[CrawlerRunConfig] = None,
    # Legacy parameters maintained for backwards compatibility...
) -> List[CrawlResult]:
    """
    Process multiple URLs with intelligent rate limiting and resource monitoring.
    """
Copy
```

### 4.1 Resource-Aware Crawling
The `arun_many()` method now uses an intelligent dispatcher that:
  * Monitors system memory usage
  * Implements adaptive rate limiting
  * Provides detailed progress monitoring
  * Manages concurrent crawls efficiently


### 4.2 Example Usage
Check page [Multi-url Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/) for a detailed example of how to use `arun_many()`.
```
### 4.3 Key Features

1. **Rate Limiting**

   - Automatic delay between requests
   - Exponential backoff on rate limit detection
   - Domain-specific rate limiting
   - Configurable retry strategy

2. **Resource Monitoring**

   - Memory usage tracking
   - Adaptive concurrency based on system load
   - Automatic pausing when resources are constrained

3. **Progress Monitoring**

   - Detailed or aggregated progress display
   - Real-time status updates
   - Memory usage statistics

4. **Error Handling**

   - Graceful handling of rate limits
   - Automatic retries with backoff
   - Detailed error reporting

---

## 5. `CrawlResult` Output

Each `arun()` returns a **`CrawlResult`** containing:

- `url`: Final URL (if redirected).
- `html`: Original HTML.
- `cleaned_html`: Sanitized HTML.
- `markdown_v2`: Deprecated. Instead just use regular `markdown`
- `extracted_content`: If an extraction strategy was used (JSON for CSS/LLM strategies).
- `screenshot`, `pdf`: If screenshots/PDF requested.
- `media`, `links`: Information about discovered images/links.
- `success`, `error_message`: Status info.

For details, see [CrawlResult doc](./crawl-result.md).

---

## 6. Quick Example

Below is an example hooking it all together:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy
import json

async def main():
    # 1. Browser config
    browser_cfg = BrowserConfig(
        browser_type="firefox",
        headless=False,
        verbose=True
    )

    # 2. Run config
    schema = {
        "name": "Articles",
        "baseSelector": "article.post",
        "fields": [
            {
                "name": "title",
                "selector": "h2",
                "type": "text"
            },
            {
                "name": "url",
                "selector": "a",
                "type": "attribute",
                "attribute": "href"
            }
        ]
    }

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        word_count_threshold=15,
        remove_overlay_elements=True,
        wait_for="css:.post"  # Wait for posts to appear
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://example.com/blog",
            config=run_cfg
        )

        if result.success:
            print("Cleaned HTML length:", len(result.cleaned_html))
            if result.extracted_content:
                articles = json.loads(result.extracted_content)
                print("Extracted articles:", articles[:2])
        else:
            print("Error:", result.error_message)

asyncio.run(main())
Copy
```

**Explanation** :
  * We define a **`BrowserConfig`**with Firefox, no headless, and`verbose=True`.
  * We define a **`CrawlerRunConfig`**that**bypasses cache** , uses a **CSS** extraction schema, has a `word_count_threshold=15`, etc.
  * We pass them to `AsyncWebCrawler(config=...)` and `arun(url=..., config=...)`.


* * *
## 7. Best Practices & Migration Notes
1. **Use** `BrowserConfig` for **global** settings about the browser’s environment. 2. **Use** `CrawlerRunConfig` for **per-crawl** logic (caching, content filtering, extraction strategies, wait conditions). 3. **Avoid** legacy parameters like `css_selector` or `word_count_threshold` directly in `arun()`. Instead:
```
run_cfg = CrawlerRunConfig(css_selector=".main-content", word_count_threshold=20)
result = await crawler.arun(url="...", config=run_cfg)
Copy
```

4. **Context Manager** usage is simplest unless you want a persistent crawler across many calls.
* * *
## 8. Summary
**AsyncWebCrawler** is your entry point to asynchronous crawling:
  * **Constructor** accepts **`BrowserConfig`**(or defaults).
  * **`arun(url, config=CrawlerRunConfig)`**is the main method for single-page crawls.
  * **`arun_many(urls, config=CrawlerRunConfig)`**handles concurrency across multiple URLs.
  * For advanced lifecycle control, use `start()` and `close()` explicitly.


**Migration** :
  * If you used `AsyncWebCrawler(browser_type="chromium", css_selector="...")`, move browser settings to `BrowserConfig(...)` and content/crawl logic to `CrawlerRunConfig(...)`.


This modular approach ensures your code is **clean** , **scalable** , and **easy to maintain**. For any advanced or rarely used parameters, see the [BrowserConfig docs](https://docs.crawl4ai.com/api/parameters/).
#### On this page
  * [1. Constructor Overview](https://docs.crawl4ai.com/api/async-webcrawler/#1-constructor-overview)
  * [2. Lifecycle: Start/Close or Context Manager](https://docs.crawl4ai.com/api/async-webcrawler/#2-lifecycle-startclose-or-context-manager)
  * [2.1 Context Manager (Recommended)](https://docs.crawl4ai.com/api/async-webcrawler/#21-context-manager-recommended)
  * [2.2 Manual Start & Close](https://docs.crawl4ai.com/api/async-webcrawler/#22-manual-start-close)
  * [3. Primary Method: arun()](https://docs.crawl4ai.com/api/async-webcrawler/#3-primary-method-arun)
  * [3.1 New Approach](https://docs.crawl4ai.com/api/async-webcrawler/#31-new-approach)
  * [3.2 Legacy Parameters Still Accepted](https://docs.crawl4ai.com/api/async-webcrawler/#32-legacy-parameters-still-accepted)
  * [4. Batch Processing: arun_many()](https://docs.crawl4ai.com/api/async-webcrawler/#4-batch-processing-arun_many)
  * [4.1 Resource-Aware Crawling](https://docs.crawl4ai.com/api/async-webcrawler/#41-resource-aware-crawling)
  * [4.2 Example Usage](https://docs.crawl4ai.com/api/async-webcrawler/#42-example-usage)
  * [7. Best Practices & Migration Notes](https://docs.crawl4ai.com/api/async-webcrawler/#7-best-practices-migration-notes)
  * [8. Summary](https://docs.crawl4ai.com/api/async-webcrawler/#8-summary)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
