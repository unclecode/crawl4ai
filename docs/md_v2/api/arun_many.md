# `arun_many(...)` Reference

> **Note**: This function is very similar to [`arun()`](./arun.md) but focused on **concurrent** or **batch** crawling. If you’re unfamiliar with `arun()` usage, please read that doc first, then review this for differences.

## Function Signature

```python
async def arun_many(
    urls: Union[List[str], List[Any]],
    config: Optional[CrawlerRunConfig] = None,
    dispatcher: Optional[BaseDispatcher] = None,
    ...
) -> Union[List[CrawlResult], AsyncGenerator[CrawlResult, None]]:
    """
    Crawl multiple URLs concurrently or in batches.

    :param urls: A list of URLs (or tasks) to crawl.
    :param config: (Optional) A default `CrawlerRunConfig` applying to each crawl.
    :param dispatcher: (Optional) A concurrency controller (e.g. MemoryAdaptiveDispatcher).
    ...
    :return: Either a list of `CrawlResult` objects, or an async generator if streaming is enabled.
    """
```

## Differences from `arun()`

1. **Multiple URLs**:  
   - Instead of crawling a single URL, you pass a list of them (strings or tasks).  
   - The function returns either a **list** of `CrawlResult` or an **async generator** if streaming is enabled.

2. **Concurrency & Dispatchers**:  
   - **`dispatcher`** param allows advanced concurrency control.  
   - If omitted, a default dispatcher (like `MemoryAdaptiveDispatcher`) is used internally.  
   - Dispatchers handle concurrency, rate limiting, and memory-based adaptive throttling (see [Multi-URL Crawling](../advanced/multi-url-crawling.md)).

3. **Streaming Support**:  
   - Enable streaming by setting `stream=True` in your `CrawlerRunConfig`.
   - When streaming, use `async for` to process results as they become available.
   - Ideal for processing large numbers of URLs without waiting for all to complete.

4. **Parallel** Execution**:  
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

**Key Points**:
- Each URL is processed by the same or separate sessions, depending on the dispatcher’s strategy.
- `dispatch_result` in each `CrawlResult` (if using concurrency) can hold memory and timing info.  
- If you need to handle authentication or session IDs, pass them in each individual task or within your run config.

### Return Value

Either a **list** of [`CrawlResult`](./crawl-result.md) objects, or an **async generator** if streaming is enabled. You can iterate to check `result.success` or read each item’s `extracted_content`, `markdown`, or `dispatch_result`.

---

## Dispatcher Reference

- **`MemoryAdaptiveDispatcher`**: Dynamically manages concurrency based on system memory usage.  
- **`SemaphoreDispatcher`**: Fixed concurrency limit, simpler but less adaptive.  

For advanced usage or custom settings, see [Multi-URL Crawling with Dispatchers](../advanced/multi-url-crawling.md).

---

## Common Pitfalls

1. **Large Lists**: If you pass thousands of URLs, be mindful of memory or rate-limits. A dispatcher can help.  
2. **Session Reuse**: If you need specialized logins or persistent contexts, ensure your dispatcher or tasks handle sessions accordingly.  
3. **Error Handling**: Each `CrawlResult` might fail for different reasons—always check `result.success` or the `error_message` before proceeding.

---

## Conclusion

Use `arun_many()` when you want to **crawl multiple URLs** simultaneously or in controlled parallel tasks. If you need advanced concurrency features (like memory-based adaptive throttling or complex rate-limiting), provide a **dispatcher**. Each result is a standard `CrawlResult`, possibly augmented with concurrency stats (`dispatch_result`) for deeper inspection. For more details on concurrency logic and dispatchers, see the [Advanced Multi-URL Crawling](../advanced/multi-url-crawling.md) docs.