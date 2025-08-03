# `arun_many(...)` Reference

> **Note**: This function is very similar to [`arun()`](./arun.md) but focused on **concurrent** or **batch** crawling. If you’re unfamiliar with `arun()` usage, please read that doc first, then review this for differences.

## Function Signature

```python
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
```

## Differences from `arun()`

1. **Multiple URLs**:  
   
   - Instead of crawling a single URL, you pass a list of them (strings or tasks).  
   - The function returns either a **list** of `CrawlResult` or an **async generator** if streaming is enabled.

2. **Concurrency & Dispatchers**:  

   - **`dispatcher`** param allows advanced concurrency control.  
   - If omitted, a default dispatcher (like `MemoryAdaptiveDispatcher`) is used internally.  
   - Dispatchers handle concurrency, rate limiting, and memory-based adaptive throttling (see [Multi-URL Crawling](../advanced/multi-url-crawling.md)).

3. **Streaming Support**:  

   - Enable streaming by setting `stream=True` in your `CrawlerRunConfig`.
   - When streaming, use `async for` to process results as they become available.
   - Ideal for processing large numbers of URLs without waiting for all to complete.

4. **Parallel** Execution**:  

   - `arun_many()` can run multiple requests concurrently under the hood.  
   - Each `CrawlResult` might also include a **`dispatch_result`** with concurrency details (like memory usage, start/end times).

### Basic Example (Batch Mode)

```python
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
```

### Streaming Example

```python
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
```

### With a Custom Dispatcher

```python
dispatcher = MemoryAdaptiveDispatcher(
    memory_threshold_percent=70.0,
    max_session_permit=10
)
results = await crawler.arun_many(
    urls=["https://site1.com", "https://site2.com", "https://site3.com"],
    config=my_run_config,
    dispatcher=dispatcher
)
```

### URL-Specific Configurations

Instead of using one config for all URLs, provide a list of configs with `url_matcher` patterns:

```python
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
```

**URL Matching Features**:
- **String patterns**: `"*.pdf"`, `"*/blog/*"`, `"*python.org*"`
- **Function matchers**: `lambda url: 'api' in url`
- **Mixed patterns**: Combine strings and functions with `MatchMode.OR` or `MatchMode.AND`
- **First match wins**: Configs are evaluated in order

**Key Points**:
- Each URL is processed by the same or separate sessions, depending on the dispatcher’s strategy.
- `dispatch_result` in each `CrawlResult` (if using concurrency) can hold memory and timing info.  
- If you need to handle authentication or session IDs, pass them in each individual task or within your run config.
- **Important**: Always include a default config (without `url_matcher`) as the last item if you want to handle all URLs. Otherwise, unmatched URLs will fail.

### Return Value

Either a **list** of [`CrawlResult`](./crawl-result.md) objects, or an **async generator** if streaming is enabled. You can iterate to check `result.success` or read each item’s `extracted_content`, `markdown`, or `dispatch_result`.

---

## Dispatcher Reference

- **`MemoryAdaptiveDispatcher`**: Dynamically manages concurrency based on system memory usage.  
- **`SemaphoreDispatcher`**: Fixed concurrency limit, simpler but less adaptive.  

For advanced usage or custom settings, see [Multi-URL Crawling with Dispatchers](../advanced/multi-url-crawling.md).

---

## Common Pitfalls

1. **Large Lists**: If you pass thousands of URLs, be mindful of memory or rate-limits. A dispatcher can help.  

2. **Session Reuse**: If you need specialized logins or persistent contexts, ensure your dispatcher or tasks handle sessions accordingly.  

3. **Error Handling**: Each `CrawlResult` might fail for different reasons—always check `result.success` or the `error_message` before proceeding.

---

## Conclusion

Use `arun_many()` when you want to **crawl multiple URLs** simultaneously or in controlled parallel tasks. If you need advanced concurrency features (like memory-based adaptive throttling or complex rate-limiting), provide a **dispatcher**. Each result is a standard `CrawlResult`, possibly augmented with concurrency stats (`dispatch_result`) for deeper inspection. For more details on concurrency logic and dispatchers, see the [Advanced Multi-URL Crawling](../advanced/multi-url-crawling.md) docs.