[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/advanced/multi-url-crawling/)


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
    * Multi-URL Crawling
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
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [Advanced Multi-URL Crawling with Dispatchers](https://docs.crawl4ai.com/advanced/multi-url-crawling/#advanced-multi-url-crawling-with-dispatchers)
  * [1. Introduction](https://docs.crawl4ai.com/advanced/multi-url-crawling/#1-introduction)
  * [2. Core Components](https://docs.crawl4ai.com/advanced/multi-url-crawling/#2-core-components)
  * [3. Available Dispatchers](https://docs.crawl4ai.com/advanced/multi-url-crawling/#3-available-dispatchers)
  * [4. Usage Examples](https://docs.crawl4ai.com/advanced/multi-url-crawling/#4-usage-examples)
  * [5. Dispatch Results](https://docs.crawl4ai.com/advanced/multi-url-crawling/#5-dispatch-results)
  * [6. URL-Specific Configurations](https://docs.crawl4ai.com/advanced/multi-url-crawling/#6-url-specific-configurations)
  * [7. Summary](https://docs.crawl4ai.com/advanced/multi-url-crawling/#7-summary)


# Advanced Multi-URL Crawling with Dispatchers
> **Heads Up** : Crawl4AI supports advanced dispatchers for **parallel** or **throttled** crawling, providing dynamic rate limiting and memory usage checks. The built-in `arun_many()` function uses these dispatchers to handle concurrency efficiently.
## 1. Introduction
When crawling many URLs:
  * **Basic** : Use `arun()` in a loop (simple but less efficient)
  * **Better** : Use `arun_many()`, which efficiently handles multiple URLs with proper concurrency control
  * **Best** : Customize dispatcher behavior for your specific needs (memory management, rate limits, etc.)


**Why Dispatchers?**
  * **Adaptive** : Memory-based dispatchers can pause or slow down based on system resources
  * **Rate-limiting** : Built-in rate limiting with exponential backoff for 429/503 responses
  * **Real-time Monitoring** : Live dashboard of ongoing tasks, memory usage, and performance
  * **Flexibility** : Choose between memory-adaptive or semaphore-based concurrency


* * *
## 2. Core Components
### 2.1 Rate Limiter
```
class RateLimiter:
    def __init__(
        # Random delay range between requests
        base_delay: Tuple[float, float] = (1.0, 3.0),

        # Maximum backoff delay
        max_delay: float = 60.0,

        # Retries before giving up
        max_retries: int = 3,

        # Status codes triggering backoff
        rate_limit_codes: List[int] = [429, 503]
    )
Copy
```

Here’s the revised and simplified explanation of the **RateLimiter** , focusing on constructor parameters and adhering to your markdown style and mkDocs guidelines.
#### RateLimiter Constructor Parameters
The **RateLimiter** is a utility that helps manage the pace of requests to avoid overloading servers or getting blocked due to rate limits. It operates internally to delay requests and handle retries but can be configured using its constructor parameters.
**Parameters of the`RateLimiter` constructor:**
1. **`base_delay`**(`Tuple[float, float]` , default: `(1.0, 3.0)`)
The range for a random delay (in seconds) between consecutive requests to the same domain.
  * A random delay is chosen between `base_delay[0]` and `base_delay[1]` for each request.
  * This prevents sending requests at a predictable frequency, reducing the chances of triggering rate limits.


**Example:**
If `base_delay = (2.0, 5.0)`, delays could be randomly chosen as `2.3s`, `4.1s`, etc.
* * *
2. **`max_delay`**(`float` , default: `60.0`)
The maximum allowable delay when rate-limiting errors occur.
  * When servers return rate-limit responses (e.g., 429 or 503), the delay increases exponentially with jitter.
  * The `max_delay` ensures the delay doesn’t grow unreasonably high, capping it at this value.


**Example:**
For a `max_delay = 30.0`, even if backoff calculations suggest a delay of `45s`, it will cap at `30s`.
* * *
3. **`max_retries`**(`int` , default: `3`)
The maximum number of retries for a request if rate-limiting errors occur.
  * After encountering a rate-limit response, the `RateLimiter` retries the request up to this number of times.
  * If all retries fail, the request is marked as failed, and the process continues.


**Example:**
If `max_retries = 3`, the system retries a failed request three times before giving up.
* * *
4. **`rate_limit_codes`**(`List[int]` , default: `[429, 503]`)
A list of HTTP status codes that trigger the rate-limiting logic.
  * These status codes indicate the server is overwhelmed or actively limiting requests.
  * You can customize this list to include other codes based on specific server behavior.


**Example:**
If `rate_limit_codes = [429, 503, 504]`, the crawler will back off on these three error codes.
* * *
**How to Use the`RateLimiter` :**
Here’s an example of initializing and using a `RateLimiter` in your project:
```
from crawl4ai import RateLimiter

# Create a RateLimiter with custom settings
rate_limiter = RateLimiter(
    base_delay=(2.0, 4.0),  # Random delay between 2-4 seconds
    max_delay=30.0,         # Cap delay at 30 seconds
    max_retries=5,          # Retry up to 5 times on rate-limiting errors
    rate_limit_codes=[429, 503]  # Handle these HTTP status codes
)

# RateLimiter will handle delays and retries internally
# No additional setup is required for its operation
Copy
```

The `RateLimiter` integrates seamlessly with dispatchers like `MemoryAdaptiveDispatcher` and `SemaphoreDispatcher`, ensuring requests are paced correctly without user intervention. Its internal mechanisms manage delays and retries to avoid overwhelming servers while maximizing efficiency.
### 2.2 Crawler Monitor
The CrawlerMonitor provides real-time visibility into crawling operations:
```
from crawl4ai import CrawlerMonitor, DisplayMode
monitor = CrawlerMonitor(
    # Maximum rows in live display
    max_visible_rows=15,

    # DETAILED or AGGREGATED view
    display_mode=DisplayMode.DETAILED
)
Copy
```

**Display Modes** :
  1. **DETAILED** : Shows individual task status, memory usage, and timing
  2. **AGGREGATED** : Displays summary statistics and overall progress


* * *
## 3. Available Dispatchers
### 3.1 MemoryAdaptiveDispatcher (Default)
Automatically manages concurrency based on system memory usage:
```
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher

dispatcher = MemoryAdaptiveDispatcher(
    memory_threshold_percent=90.0,  # Pause if memory exceeds this
    check_interval=1.0,             # How often to check memory
    max_session_permit=10,          # Maximum concurrent tasks
    rate_limiter=RateLimiter(       # Optional rate limiting
        base_delay=(1.0, 2.0),
        max_delay=30.0,
        max_retries=2
    ),
    monitor=CrawlerMonitor(         # Optional monitoring
        max_visible_rows=15,
        display_mode=DisplayMode.DETAILED
    )
)
Copy
```

**Constructor Parameters:**
1. **`memory_threshold_percent`**(`float` , default: `90.0`)
Specifies the memory usage threshold (as a percentage). If system memory usage exceeds this value, the dispatcher pauses crawling to prevent system overload.
2. **`check_interval`**(`float` , default: `1.0`)
The interval (in seconds) at which the dispatcher checks system memory usage.
3. **`max_session_permit`**(`int` , default: `10`)
The maximum number of concurrent crawling tasks allowed. This ensures resource limits are respected while maintaining concurrency.
4. **`memory_wait_timeout`**(`float` , default: `600.0`) Optional timeout (in seconds). If memory usage exceeds `memory_threshold_percent` for longer than this duration, a `MemoryError` is raised.
5. **`rate_limiter`**(`RateLimiter` , default: `None`)
Optional rate-limiting logic to avoid server-side blocking (e.g., for handling 429 or 503 errors). See **RateLimiter** for details.
6. **`monitor`**(`CrawlerMonitor` , default: `None`)
Optional monitoring for real-time task tracking and performance insights. See **CrawlerMonitor** for details.
* * *
### 3.2 SemaphoreDispatcher
Provides simple concurrency control with a fixed limit:
```
from crawl4ai.async_dispatcher import SemaphoreDispatcher

dispatcher = SemaphoreDispatcher(
    max_session_permit=20,         # Maximum concurrent tasks
    rate_limiter=RateLimiter(      # Optional rate limiting
        base_delay=(0.5, 1.0),
        max_delay=10.0
    ),
    monitor=CrawlerMonitor(        # Optional monitoring
        max_visible_rows=15,
        display_mode=DisplayMode.DETAILED
    )
)
Copy
```

**Constructor Parameters:**
1. **`max_session_permit`**(`int` , default: `20`)
The maximum number of concurrent crawling tasks allowed, irrespective of semaphore slots.
2. **`rate_limiter`**(`RateLimiter` , default: `None`)
Optional rate-limiting logic to avoid overwhelming servers. See **RateLimiter** for details.
3. **`monitor`**(`CrawlerMonitor` , default: `None`)
Optional monitoring for tracking task progress and resource usage. See **CrawlerMonitor** for details.
* * *
## 4. Usage Examples
### 4.1 Batch Processing (Default)
```
async def crawl_batch():
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=False  # Default: get all results at once
    )

    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=10,
        monitor=CrawlerMonitor(
            display_mode=DisplayMode.DETAILED
        )
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Get all results at once
        results = await crawler.arun_many(
            urls=urls,
            config=run_config,
            dispatcher=dispatcher
        )

        # Process all results after completion
        for result in results:
            if result.success:
                await process_result(result)
            else:
                print(f"Failed to crawl {result.url}: {result.error_message}")
Copy
```

**Review:**
- **Purpose:** Executes a batch crawl with all URLs processed together after crawling is complete.
- **Dispatcher:** Uses `MemoryAdaptiveDispatcher` to manage concurrency and system memory.
- **Stream:** Disabled (`stream=False`), so all results are collected at once for post-processing.
- **Best Use Case:** When you need to analyze results in bulk rather than individually during the crawl.
* * *
### 4.2 Streaming Mode
```
async def crawl_streaming():
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=True  # Enable streaming mode
    )

    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=10,
        monitor=CrawlerMonitor(
            display_mode=DisplayMode.DETAILED
        )
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Process results as they become available
        async for result in await crawler.arun_many(
            urls=urls,
            config=run_config,
            dispatcher=dispatcher
        ):
            if result.success:
                # Process each result immediately
                await process_result(result)
            else:
                print(f"Failed to crawl {result.url}: {result.error_message}")
Copy
```

**Review:**
- **Purpose:** Enables streaming to process results as soon as they’re available.
- **Dispatcher:** Uses `MemoryAdaptiveDispatcher` for concurrency and memory management.
- **Stream:** Enabled (`stream=True`), allowing real-time processing during crawling.
- **Best Use Case:** When you need to act on results immediately, such as for real-time analytics or progressive data storage.
* * *
### 4.3 Semaphore-based Crawling
```
async def crawl_with_semaphore(urls):
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    dispatcher = SemaphoreDispatcher(
        semaphore_count=5,
        rate_limiter=RateLimiter(
            base_delay=(0.5, 1.0),
            max_delay=10.0
        ),
        monitor=CrawlerMonitor(
            max_visible_rows=15,
            display_mode=DisplayMode.DETAILED
        )
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(
            urls,
            config=run_config,
            dispatcher=dispatcher
        )
        return results
Copy
```

**Review:**
- **Purpose:** Uses `SemaphoreDispatcher` to limit concurrency with a fixed number of slots.
- **Dispatcher:** Configured with a semaphore to control parallel crawling tasks.
- **Rate Limiter:** Prevents servers from being overwhelmed by pacing requests.
- **Best Use Case:** When you want precise control over the number of concurrent requests, independent of system memory.
* * *
### 4.4 Robots.txt Consideration
```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    urls = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]

    config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        check_robots_txt=True,  # Will respect robots.txt for each URL
        semaphore_count=3      # Max concurrent requests
    )

    async with AsyncWebCrawler() as crawler:
        async for result in crawler.arun_many(urls, config=config):
            if result.success:
                print(f"Successfully crawled {result.url}")
            elif result.status_code == 403 and "robots.txt" in result.error_message:
                print(f"Skipped {result.url} - blocked by robots.txt")
            else:
                print(f"Failed to crawl {result.url}: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

**Review:**
- **Purpose:** Ensures compliance with `robots.txt` rules for ethical and legal web crawling.
- **Configuration:** Set `check_robots_txt=True` to validate each URL against `robots.txt` before crawling.
- **Dispatcher:** Handles requests with concurrency limits (`semaphore_count=3`).
- **Best Use Case:** When crawling websites that strictly enforce robots.txt policies or for responsible crawling practices.
* * *
## 5. Dispatch Results
Each crawl result includes dispatch information:
```
@dataclass
class DispatchResult:
    task_id: str
    memory_usage: float
    peak_memory: float
    start_time: datetime
    end_time: datetime
    error_message: str = ""
Copy
```

Access via `result.dispatch_result`:
```
for result in results:
    if result.success:
        dr = result.dispatch_result
        print(f"URL: {result.url}")
        print(f"Memory: {dr.memory_usage:.1f}MB")
        print(f"Duration: {dr.end_time - dr.start_time}")
Copy
```

## 6. URL-Specific Configurations
When crawling diverse content types, you often need different configurations for different URLs. For example: - PDFs need specialized extraction - Blog pages benefit from content filtering - Dynamic sites need JavaScript execution - API endpoints need JSON parsing
### 6.1 Basic URL Pattern Matching
```
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, MatchMode
from crawl4ai.processors.pdf import PDFContentScrapingStrategy
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def crawl_mixed_content():
    # Configure different strategies for different content
    configs = [
        # PDF files - specialized extraction
        CrawlerRunConfig(
            url_matcher="*.pdf",
            scraping_strategy=PDFContentScrapingStrategy()
        ),

        # Blog/article pages - content filtering
        CrawlerRunConfig(
            url_matcher=["*/blog/*", "*/article/*"],
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.48)
            )
        ),

        # Dynamic pages - JavaScript execution
        CrawlerRunConfig(
            url_matcher=lambda url: 'github.com' in url,
            js_code="window.scrollTo(0, 500);"
        ),

        # API endpoints - JSON extraction
        CrawlerRunConfig(
            url_matcher=lambda url: 'api' in url or url.endswith('.json'),
            # Custome settings for JSON extraction
        ),

        # Default config for everything else
        CrawlerRunConfig()  # No url_matcher means it matches ALL URLs (fallback)
    ]

    # Mixed URLs
    urls = [
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "https://blog.python.org/",
        "https://github.com/microsoft/playwright",
        "https://httpbin.org/json",
        "https://example.com/"
    ]

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=configs  # Pass list of configs
        )

        for result in results:
            print(f"{result.url}: {len(result.markdown)} chars")
Copy
```

### 6.2 Advanced Pattern Matching
**Important** : A `CrawlerRunConfig` without `url_matcher` (or with `url_matcher=None`) matches ALL URLs. This makes it perfect as a default/fallback configuration.
The `url_matcher` parameter supports three types of patterns:
#### Glob Patterns (Strings)
```
# Simple patterns
"*.pdf"                    # Any PDF file
"*/api/*"                  # Any URL with /api/ in path
"https://*.example.com/*"  # Subdomain matching
"*://example.com/blog/*"   # Any protocol
Copy
```

#### Custom Functions
```
# Complex logic with lambdas
lambda url: url.startswith('https://') and 'secure' in url
lambda url: len(url) > 50 and url.count('/') > 5
lambda url: any(domain in url for domain in ['api.', 'data.', 'feed.'])
Copy
```

#### Mixed Lists with AND/OR Logic
```
# Combine multiple conditions
CrawlerRunConfig(
    url_matcher=[
        "https://*",                        # Must be HTTPS
        lambda url: 'internal' in url,      # Must contain 'internal'
        lambda url: not url.endswith('.pdf') # Must not be PDF
    ],
    match_mode=MatchMode.AND  # ALL conditions must match
)
Copy
```

### 6.3 Practical Example: News Site Crawler
```
async def crawl_news_site():
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        rate_limiter=RateLimiter(base_delay=(1.0, 2.0))
    )

    configs = [
        # Homepage - light extraction
        CrawlerRunConfig(
            url_matcher=lambda url: url.rstrip('/') == 'https://news.ycombinator.com',
            css_selector="nav, .headline",
            extraction_strategy=None
        ),

        # Article pages - full extraction
        CrawlerRunConfig(
            url_matcher="*/article/*",
            extraction_strategy=CosineStrategy(
                semantic_filter="article content",
                word_count_threshold=100
            ),
            screenshot=True,
            excluded_tags=["nav", "aside", "footer"]
        ),

        # Author pages - metadata focus
        CrawlerRunConfig(
            url_matcher="*/author/*",
            extraction_strategy=JsonCssExtractionStrategy({
                "name": "h1.author-name",
                "bio": ".author-bio",
                "articles": "article.post-card h2"
            })
        ),

        # Everything else
        CrawlerRunConfig()
    ]

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=news_urls,
            config=configs,
            dispatcher=dispatcher
        )
Copy
```

### 6.4 Best Practices
  1. **Order Matters** : Configs are evaluated in order - put specific patterns before general ones
  2. **Default Config Behavior** :
  3. A config without `url_matcher` matches ALL URLs
  4. Always include a default config as the last item if you want to handle all URLs
  5. Without a default config, unmatched URLs will fail with "No matching configuration found"
  6. **Test Your Patterns** : Use the config's `is_match()` method to test patterns:
```
config = CrawlerRunConfig(url_matcher="*.pdf")
print(config.is_match("https://example.com/doc.pdf"))  # True

default_config = CrawlerRunConfig()  # No url_matcher
print(default_config.is_match("https://any-url.com"))  # True - matches everything!
Copy
```

  7. **Optimize for Performance** :
  8. Disable JS for static content
  9. Skip screenshots for data APIs
  10. Use appropriate extraction strategies


## 7. Summary
1. **Two Dispatcher Types** :
  * MemoryAdaptiveDispatcher (default): Dynamic concurrency based on memory
  * SemaphoreDispatcher: Fixed concurrency limit


2. **Optional Components** :
  * RateLimiter: Smart request pacing and backoff
  * CrawlerMonitor: Real-time progress visualization


3. **Key Benefits** :
  * Automatic memory management
  * Built-in rate limiting
  * Live progress monitoring
  * Flexible concurrency control


Choose the dispatcher that best fits your needs:
  * **MemoryAdaptiveDispatcher** : For large crawls or limited resources
  * **SemaphoreDispatcher** : For simple, fixed-concurrency scenarios


#### On this page
  * [1. Introduction](https://docs.crawl4ai.com/advanced/multi-url-crawling/#1-introduction)
  * [2. Core Components](https://docs.crawl4ai.com/advanced/multi-url-crawling/#2-core-components)
  * [2.1 Rate Limiter](https://docs.crawl4ai.com/advanced/multi-url-crawling/#21-rate-limiter)
  * [RateLimiter Constructor Parameters](https://docs.crawl4ai.com/advanced/multi-url-crawling/#ratelimiter-constructor-parameters)
  * [2.2 Crawler Monitor](https://docs.crawl4ai.com/advanced/multi-url-crawling/#22-crawler-monitor)
  * [3. Available Dispatchers](https://docs.crawl4ai.com/advanced/multi-url-crawling/#3-available-dispatchers)
  * [3.1 MemoryAdaptiveDispatcher (Default)](https://docs.crawl4ai.com/advanced/multi-url-crawling/#31-memoryadaptivedispatcher-default)
  * [3.2 SemaphoreDispatcher](https://docs.crawl4ai.com/advanced/multi-url-crawling/#32-semaphoredispatcher)
  * [4. Usage Examples](https://docs.crawl4ai.com/advanced/multi-url-crawling/#4-usage-examples)
  * [4.1 Batch Processing (Default)](https://docs.crawl4ai.com/advanced/multi-url-crawling/#41-batch-processing-default)
  * [4.2 Streaming Mode](https://docs.crawl4ai.com/advanced/multi-url-crawling/#42-streaming-mode)
  * [4.3 Semaphore-based Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/#43-semaphore-based-crawling)
  * [4.4 Robots.txt Consideration](https://docs.crawl4ai.com/advanced/multi-url-crawling/#44-robotstxt-consideration)
  * [5. Dispatch Results](https://docs.crawl4ai.com/advanced/multi-url-crawling/#5-dispatch-results)
  * [6. URL-Specific Configurations](https://docs.crawl4ai.com/advanced/multi-url-crawling/#6-url-specific-configurations)
  * [6.1 Basic URL Pattern Matching](https://docs.crawl4ai.com/advanced/multi-url-crawling/#61-basic-url-pattern-matching)
  * [6.2 Advanced Pattern Matching](https://docs.crawl4ai.com/advanced/multi-url-crawling/#62-advanced-pattern-matching)
  * [Glob Patterns (Strings)](https://docs.crawl4ai.com/advanced/multi-url-crawling/#glob-patterns-strings)
  * [Custom Functions](https://docs.crawl4ai.com/advanced/multi-url-crawling/#custom-functions)
  * [Mixed Lists with AND/OR Logic](https://docs.crawl4ai.com/advanced/multi-url-crawling/#mixed-lists-with-andor-logic)
  * [6.3 Practical Example: News Site Crawler](https://docs.crawl4ai.com/advanced/multi-url-crawling/#63-practical-example-news-site-crawler)
  * [6.4 Best Practices](https://docs.crawl4ai.com/advanced/multi-url-crawling/#64-best-practices)
  * [7. Summary](https://docs.crawl4ai.com/advanced/multi-url-crawling/#7-summary)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
