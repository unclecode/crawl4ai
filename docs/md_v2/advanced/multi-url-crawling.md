# Advanced Multi-URL Crawling with Dispatchers

> **Heads Up**: Crawl4AI supports advanced dispatchers for **parallel** or **throttled** crawling, providing dynamic rate limiting and memory usage checks. The built-in `arun_many()` function uses these dispatchers to handle concurrency efficiently.

## 1. Introduction

When crawling many URLs:

- **Basic**: Use `arun()` in a loop (simple but less efficient)
- **Better**: Use `arun_many()`, which efficiently handles multiple URLs with proper concurrency control
- **Best**: Customize dispatcher behavior for your specific needs (memory management, rate limits, etc.)

**Why Dispatchers?**  

- **Adaptive**: Memory-based dispatchers can pause or slow down based on system resources
- **Rate-limiting**: Built-in rate limiting with exponential backoff for 429/503 responses
- **Real-time Monitoring**: Live dashboard of ongoing tasks, memory usage, and performance
- **Flexibility**: Choose between memory-adaptive or semaphore-based concurrency

---

## 2. Core Components

### 2.1 Rate Limiter

```python
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
```

Here’s the revised and simplified explanation of the **RateLimiter**, focusing on constructor parameters and adhering to your markdown style and mkDocs guidelines.

#### RateLimiter Constructor Parameters

The **RateLimiter** is a utility that helps manage the pace of requests to avoid overloading servers or getting blocked due to rate limits. It operates internally to delay requests and handle retries but can be configured using its constructor parameters.

**Parameters of the `RateLimiter` constructor:**

1. **`base_delay`** (`Tuple[float, float]`, default: `(1.0, 3.0)`)  
  The range for a random delay (in seconds) between consecutive requests to the same domain.

- A random delay is chosen between `base_delay[0]` and `base_delay[1]` for each request.  
- This prevents sending requests at a predictable frequency, reducing the chances of triggering rate limits.

**Example:**  
If `base_delay = (2.0, 5.0)`, delays could be randomly chosen as `2.3s`, `4.1s`, etc.

---

2. **`max_delay`** (`float`, default: `60.0`)  
  The maximum allowable delay when rate-limiting errors occur.

- When servers return rate-limit responses (e.g., 429 or 503), the delay increases exponentially with jitter.  
- The `max_delay` ensures the delay doesn’t grow unreasonably high, capping it at this value.

**Example:**  
For a `max_delay = 30.0`, even if backoff calculations suggest a delay of `45s`, it will cap at `30s`.

---

3. **`max_retries`** (`int`, default: `3`)  
  The maximum number of retries for a request if rate-limiting errors occur.

- After encountering a rate-limit response, the `RateLimiter` retries the request up to this number of times.  
- If all retries fail, the request is marked as failed, and the process continues.

**Example:**  
If `max_retries = 3`, the system retries a failed request three times before giving up.

---

4. **`rate_limit_codes`** (`List[int]`, default: `[429, 503]`)  
  A list of HTTP status codes that trigger the rate-limiting logic.

- These status codes indicate the server is overwhelmed or actively limiting requests.  
- You can customize this list to include other codes based on specific server behavior.

**Example:**  
If `rate_limit_codes = [429, 503, 504]`, the crawler will back off on these three error codes.

---

**How to Use the `RateLimiter`:**

Here’s an example of initializing and using a `RateLimiter` in your project:

```python
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
```

The `RateLimiter` integrates seamlessly with dispatchers like `MemoryAdaptiveDispatcher` and `SemaphoreDispatcher`, ensuring requests are paced correctly without user intervention. Its internal mechanisms manage delays and retries to avoid overwhelming servers while maximizing efficiency.


### 2.2 Crawler Monitor

The CrawlerMonitor provides real-time visibility into crawling operations:

```python
from crawl4ai import CrawlerMonitor, DisplayMode
monitor = CrawlerMonitor(
    # Maximum rows in live display
    max_visible_rows=15,          

    # DETAILED or AGGREGATED view
    display_mode=DisplayMode.DETAILED  
)
```

**Display Modes**:

1. **DETAILED**: Shows individual task status, memory usage, and timing
2. **AGGREGATED**: Displays summary statistics and overall progress

---

## 3. Available Dispatchers

### 3.1 MemoryAdaptiveDispatcher (Default)

Automatically manages concurrency based on system memory usage:

```python
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
```

**Constructor Parameters:**

1. **`memory_threshold_percent`** (`float`, default: `90.0`)  
  Specifies the memory usage threshold (as a percentage). If system memory usage exceeds this value, the dispatcher pauses crawling to prevent system overload.

2. **`check_interval`** (`float`, default: `1.0`)  
  The interval (in seconds) at which the dispatcher checks system memory usage.

3. **`max_session_permit`** (`int`, default: `10`)  
  The maximum number of concurrent crawling tasks allowed. This ensures resource limits are respected while maintaining concurrency.

4. **`memory_wait_timeout`** (`float`, default: `300.0`)  
  Optional timeout (in seconds). If memory usage exceeds `memory_threshold_percent` for longer than this duration, a `MemoryError` is raised.

5. **`rate_limiter`** (`RateLimiter`, default: `None`)  
  Optional rate-limiting logic to avoid server-side blocking (e.g., for handling 429 or 503 errors). See **RateLimiter** for details.

6. **`monitor`** (`CrawlerMonitor`, default: `None`)  
  Optional monitoring for real-time task tracking and performance insights. See **CrawlerMonitor** for details.

---

### 3.2 SemaphoreDispatcher

Provides simple concurrency control with a fixed limit:

```python
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
```

**Constructor Parameters:**

1. **`max_session_permit`** (`int`, default: `20`)  
  The maximum number of concurrent crawling tasks allowed, irrespective of semaphore slots.

2. **`rate_limiter`** (`RateLimiter`, default: `None`)  
  Optional rate-limiting logic to avoid overwhelming servers. See **RateLimiter** for details.

3. **`monitor`** (`CrawlerMonitor`, default: `None`)  
  Optional monitoring for tracking task progress and resource usage. See **CrawlerMonitor** for details.

---

## 4. Usage Examples

### 4.1 Batch Processing (Default)

```python
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
```

**Review:**  
- **Purpose:** Executes a batch crawl with all URLs processed together after crawling is complete.  
- **Dispatcher:** Uses `MemoryAdaptiveDispatcher` to manage concurrency and system memory.  
- **Stream:** Disabled (`stream=False`), so all results are collected at once for post-processing.  
- **Best Use Case:** When you need to analyze results in bulk rather than individually during the crawl.

---

### 4.2 Streaming Mode

```python
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
```

**Review:**  
- **Purpose:** Enables streaming to process results as soon as they’re available.  
- **Dispatcher:** Uses `MemoryAdaptiveDispatcher` for concurrency and memory management.  
- **Stream:** Enabled (`stream=True`), allowing real-time processing during crawling.  
- **Best Use Case:** When you need to act on results immediately, such as for real-time analytics or progressive data storage.

---

### 4.3 Semaphore-based Crawling

```python
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
```

**Review:**  
- **Purpose:** Uses `SemaphoreDispatcher` to limit concurrency with a fixed number of slots.  
- **Dispatcher:** Configured with a semaphore to control parallel crawling tasks.  
- **Rate Limiter:** Prevents servers from being overwhelmed by pacing requests.  
- **Best Use Case:** When you want precise control over the number of concurrent requests, independent of system memory.

---

### 4.4 Robots.txt Consideration

```python
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
```

**Review:**  
- **Purpose:** Ensures compliance with `robots.txt` rules for ethical and legal web crawling.  
- **Configuration:** Set `check_robots_txt=True` to validate each URL against `robots.txt` before crawling.  
- **Dispatcher:** Handles requests with concurrency limits (`semaphore_count=3`).  
- **Best Use Case:** When crawling websites that strictly enforce robots.txt policies or for responsible crawling practices.

---

## 5. Dispatch Results

Each crawl result includes dispatch information:

```python
@dataclass
class DispatchResult:
    task_id: str
    memory_usage: float
    peak_memory: float
    start_time: datetime
    end_time: datetime
    error_message: str = ""
```

Access via `result.dispatch_result`:

```python
for result in results:
    if result.success:
        dr = result.dispatch_result
        print(f"URL: {result.url}")
        print(f"Memory: {dr.memory_usage:.1f}MB")
        print(f"Duration: {dr.end_time - dr.start_time}")
```

## 6. Summary

1. **Two Dispatcher Types**:

   - MemoryAdaptiveDispatcher (default): Dynamic concurrency based on memory
   - SemaphoreDispatcher: Fixed concurrency limit

2. **Optional Components**:

   - RateLimiter: Smart request pacing and backoff
   - CrawlerMonitor: Real-time progress visualization

3. **Key Benefits**:

   - Automatic memory management
   - Built-in rate limiting
   - Live progress monitoring
   - Flexible concurrency control

Choose the dispatcher that best fits your needs:

- **MemoryAdaptiveDispatcher**: For large crawls or limited resources
- **SemaphoreDispatcher**: For simple, fixed-concurrency scenarios
