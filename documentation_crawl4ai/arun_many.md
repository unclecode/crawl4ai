[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/api/arun_many/)


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
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * arun_many()
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [arun_many(...) Reference](https://docs.crawl4ai.com/api/arun_many/#arun_many-reference)
  * [Function Signature](https://docs.crawl4ai.com/api/arun_many/#function-signature)
  * [Differences from arun()](https://docs.crawl4ai.com/api/arun_many/#differences-from-arun)
  * [Dispatcher Reference](https://docs.crawl4ai.com/api/arun_many/#dispatcher-reference)
  * [Common Pitfalls](https://docs.crawl4ai.com/api/arun_many/#common-pitfalls)
  * [Conclusion](https://docs.crawl4ai.com/api/arun_many/#conclusion)


#  `arun_many(...)` Reference
> **Note** : This function is very similar to [`arun()`](https://docs.crawl4ai.com/api/arun/) but focused on **concurrent** or **batch** crawling. If you’re unfamiliar with `arun()` usage, please read that doc first, then review this for differences.
## Function Signature
```
async def arun_many(
    urls: Union[List[str], List[Any]],
    config: Optional[Union[CrawlerRunConfig, List[CrawlerRunConfig]]] = None,
    dispatcher: Optional[BaseDispatcher] = None,
    ...
) -> Union[List[CrawlResult], AsyncGenerator[CrawlResult, None]]:
    """
    Crawl multiple URLs concurrently or in batches.

    :param urls: A list of URLs (or tasks) to crawl.
    :param config: (Optional) Either:
        - A single `CrawlerRunConfig` applying to all URLs
        - A list of `CrawlerRunConfig` objects with url_matcher patterns
    :param dispatcher: (Optional) A concurrency controller (e.g. MemoryAdaptiveDispatcher).
    ...
    :return: Either a list of `CrawlResult` objects, or an async generator if streaming is enabled.
    """
Copy
```

## Differences from `arun()`
1. **Multiple URLs** :
  * Instead of crawling a single URL, you pass a list of them (strings or tasks).
  * The function returns either a **list** of `CrawlResult` or an **async generator** if streaming is enabled.


2. **Concurrency & Dispatchers**:
  * **`dispatcher`**param allows advanced concurrency control.
  * If omitted, a default dispatcher (like `MemoryAdaptiveDispatcher`) is used internally.
  * Dispatchers handle concurrency, rate limiting, and memory-based adaptive throttling (see [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)).


3. **Streaming Support** :
  * Enable streaming by setting `stream=True` in your `CrawlerRunConfig`.
  * When streaming, use `async for` to process results as they become available.
  * Ideal for processing large numbers of URLs without waiting for all to complete.


4. **Parallel** Execution**:
  * `arun_many()` can run multiple requests concurrently under the hood.
  * Each `CrawlResult` might also include a **`dispatch_result`**with concurrency details (like memory usage, start/end times).


### Basic Example (Batch Mode)
```
# Minimal usage: The default dispatcher will be used
results = await crawler.arun_many(
    urls=["https://site1.com", "https://site2.com"],
    config=CrawlerRunConfig(stream=False)  # Default behavior
)

for res in results:
    if res.success:
        print(res.url, "crawled OK!")
    else:
        print("Failed:", res.url, "-", res.error_message)
Copy
```

### Streaming Example
```
config = CrawlerRunConfig(
    stream=True,  # Enable streaming mode
    cache_mode=CacheMode.BYPASS
)

# Process results as they complete
async for result in await crawler.arun_many(
    urls=["https://site1.com", "https://site2.com", "https://site3.com"],
    config=config
):
    if result.success:
        print(f"Just completed: {result.url}")
        # Process each result immediately
        process_result(result)
Copy
```

### With a Custom Dispatcher
```
dispatcher = MemoryAdaptiveDispatcher(
    memory_threshold_percent=70.0,
    max_session_permit=10
)
results = await crawler.arun_many(
    urls=["https://site1.com", "https://site2.com", "https://site3.com"],
    config=my_run_config,
    dispatcher=dispatcher
)
Copy
```

### URL-Specific Configurations
Instead of using one config for all URLs, provide a list of configs with `url_matcher` patterns:
```
from crawl4ai import CrawlerRunConfig, MatchMode
from crawl4ai.processors.pdf import PDFContentScrapingStrategy
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# PDF files - specialized extraction
pdf_config = CrawlerRunConfig(
    url_matcher="*.pdf",
    scraping_strategy=PDFContentScrapingStrategy()
)

# Blog/article pages - content filtering
blog_config = CrawlerRunConfig(
    url_matcher=["*/blog/*", "*/article/*", "*python.org*"],
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48)
    )
)

# Dynamic pages - JavaScript execution
github_config = CrawlerRunConfig(
    url_matcher=lambda url: 'github.com' in url,
    js_code="window.scrollTo(0, 500);"
)

# API endpoints - JSON extraction
api_config = CrawlerRunConfig(
    url_matcher=lambda url: 'api' in url or url.endswith('.json'),
    # Custome settings for JSON extraction
)

# Default fallback config
default_config = CrawlerRunConfig()  # No url_matcher means it never matches except as fallback

# Pass the list of configs - first match wins!
results = await crawler.arun_many(
    urls=[
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",  # → pdf_config
        "https://blog.python.org/",  # → blog_config
        "https://github.com/microsoft/playwright",  # → github_config
        "https://httpbin.org/json",  # → api_config
        "https://example.com/"  # → default_config
    ],
    config=[pdf_config, blog_config, github_config, api_config, default_config]
)
Copy
```

**URL Matching Features** : - **String patterns** : `"*.pdf"`, `"*/blog/*"`, `"*python.org*"` - **Function matchers** : `lambda url: 'api' in url` - **Mixed patterns** : Combine strings and functions with `MatchMode.OR` or `MatchMode.AND` - **First match wins** : Configs are evaluated in order
**Key Points** : - Each URL is processed by the same or separate sessions, depending on the dispatcher’s strategy. - `dispatch_result` in each `CrawlResult` (if using concurrency) can hold memory and timing info. - If you need to handle authentication or session IDs, pass them in each individual task or within your run config. - **Important** : Always include a default config (without `url_matcher`) as the last item if you want to handle all URLs. Otherwise, unmatched URLs will fail.
### Return Value
Either a **list** of [`CrawlResult`](https://docs.crawl4ai.com/api/crawl-result/) objects, or an **async generator** if streaming is enabled. You can iterate to check `result.success` or read each item’s `extracted_content`, `markdown`, or `dispatch_result`.
* * *
## Dispatcher Reference
  * **`MemoryAdaptiveDispatcher`**: Dynamically manages concurrency based on system memory usage.
  * **`SemaphoreDispatcher`**: Fixed concurrency limit, simpler but less adaptive.


For advanced usage or custom settings, see [Multi-URL Crawling with Dispatchers](https://docs.crawl4ai.com/advanced/multi-url-crawling/).
* * *
## Common Pitfalls
1. **Large Lists** : If you pass thousands of URLs, be mindful of memory or rate-limits. A dispatcher can help.
2. **Session Reuse** : If you need specialized logins or persistent contexts, ensure your dispatcher or tasks handle sessions accordingly.
3. **Error Handling** : Each `CrawlResult` might fail for different reasons—always check `result.success` or the `error_message` before proceeding.
* * *
## Conclusion
Use `arun_many()` when you want to **crawl multiple URLs** simultaneously or in controlled parallel tasks. If you need advanced concurrency features (like memory-based adaptive throttling or complex rate-limiting), provide a **dispatcher**. Each result is a standard `CrawlResult`, possibly augmented with concurrency stats (`dispatch_result`) for deeper inspection. For more details on concurrency logic and dispatchers, see the [Advanced Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/) docs.
#### On this page
  * [Function Signature](https://docs.crawl4ai.com/api/arun_many/#function-signature)
  * [Differences from arun()](https://docs.crawl4ai.com/api/arun_many/#differences-from-arun)
  * [Basic Example (Batch Mode)](https://docs.crawl4ai.com/api/arun_many/#basic-example-batch-mode)
  * [Streaming Example](https://docs.crawl4ai.com/api/arun_many/#streaming-example)
  * [With a Custom Dispatcher](https://docs.crawl4ai.com/api/arun_many/#with-a-custom-dispatcher)
  * [URL-Specific Configurations](https://docs.crawl4ai.com/api/arun_many/#url-specific-configurations)
  * [Return Value](https://docs.crawl4ai.com/api/arun_many/#return-value)
  * [Dispatcher Reference](https://docs.crawl4ai.com/api/arun_many/#dispatcher-reference)
  * [Common Pitfalls](https://docs.crawl4ai.com/api/arun_many/#common-pitfalls)
  * [Conclusion](https://docs.crawl4ai.com/api/arun_many/#conclusion)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
