# Browser & Crawler Configuration (Quick Overview)

Crawl4AI’s flexibility stems from two key classes:

1. **`BrowserConfig`** – Dictates **how** the browser is launched and behaves (e.g., headless or visible, proxy, user agent).  
2. **`CrawlerRunConfig`** – Dictates **how** each **crawl** operates (e.g., caching, extraction, timeouts, JavaScript code to run, etc.).

In most examples, you create **one** `BrowserConfig` for the entire crawler session, then pass a **fresh** or re-used `CrawlerRunConfig` whenever you call `arun()`. This tutorial shows the most commonly used parameters. If you need advanced or rarely used fields, see the [Configuration Parameters](../api/parameters.md).

---

## 1. BrowserConfig Essentials

```python
class BrowserConfig:
    def __init__(
        browser_type="chromium",
        headless=True,
        proxy_config=None,
        viewport_width=1080,
        viewport_height=600,
        verbose=True,
        use_persistent_context=False,
        user_data_dir=None,
        cookies=None,
        headers=None,
        user_agent=None,
        text_mode=False,
        light_mode=False,
        extra_args=None,
        # ... other advanced parameters omitted here
    ):
        ...
```

### Key Fields to Note



1. **`browser_type`**  
- Options: `"chromium"`, `"firefox"`, or `"webkit"`.  
- Defaults to `"chromium"`.  
- If you need a different engine, specify it here.

2. **`headless`**  
   - `True`: Runs the browser in headless mode (invisible browser).  
   - `False`: Runs the browser in visible mode, which helps with debugging.

3. **`proxy_config`**  
   - A dictionary with fields like:  
```json
{
    "server": "http://proxy.example.com:8080", 
    "username": "...", 
    "password": "..."
}
```
   - Leave as `None` if a proxy is not required.

4. **`viewport_width` & `viewport_height`**:  
   - The initial window size.  
   - Some sites behave differently with smaller or bigger viewports.

5. **`verbose`**:  
   - If `True`, prints extra logs.  
   - Handy for debugging.

6. **`use_persistent_context`**:  
   - If `True`, uses a **persistent** browser profile, storing cookies/local storage across runs.  
   - Typically also set `user_data_dir` to point to a folder.

7. **`cookies`** & **`headers`**:  
   - If you want to start with specific cookies or add universal HTTP headers, set them here.  
   - E.g. `cookies=[{"name": "session", "value": "abc123", "domain": "example.com"}]`.

8. **`user_agent`**:  
   - Custom User-Agent string. If `None`, a default is used.  
   - You can also set `user_agent_mode="random"` for randomization (if you want to fight bot detection).

9. **`text_mode`** & **`light_mode`**:  
   - `text_mode=True` disables images, possibly speeding up text-only crawls.  
   - `light_mode=True` turns off certain background features for performance.  

10. **`extra_args`**:  
    - Additional flags for the underlying browser.  
    - E.g. `["--disable-extensions"]`.

### Helper Methods

Both configuration classes provide a `clone()` method to create modified copies:

```python
# Create a base browser config
base_browser = BrowserConfig(
    browser_type="chromium",
    headless=True,
    text_mode=True
)

# Create a visible browser config for debugging
debug_browser = base_browser.clone(
    headless=False,
    verbose=True
)
```

**Minimal Example**:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_conf = BrowserConfig(
    browser_type="firefox",
    headless=False,
    text_mode=True
)

async with AsyncWebCrawler(config=browser_conf) as crawler:
    result = await crawler.arun("https://example.com")
    print(result.markdown[:300])
```

---

## 2. CrawlerRunConfig Essentials

```python
class CrawlerRunConfig:
    def __init__(
        word_count_threshold=200,
        extraction_strategy=None,
        markdown_generator=None,
        cache_mode=None,
        js_code=None,
        wait_for=None,
        screenshot=False,
        pdf=False,
        enable_rate_limiting=False,
        rate_limit_config=None,
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=20,
        display_mode=None,
        verbose=True,
        stream=False,  # Enable streaming for arun_many()
        # ... other advanced parameters omitted
    ):
        ...
```

### Key Fields to Note

1. **`word_count_threshold`**:  
   - The minimum word count before a block is considered.  
   - If your site has lots of short paragraphs or items, you can lower it.

2. **`extraction_strategy`**:  
   - Where you plug in JSON-based extraction (CSS, LLM, etc.).  
   - If `None`, no structured extraction is done (only raw/cleaned HTML + markdown).

3. **`markdown_generator`**:  
   - E.g., `DefaultMarkdownGenerator(...)`, controlling how HTML→Markdown conversion is done.  
   - If `None`, a default approach is used.

4. **`cache_mode`**:  
   - Controls caching behavior (`ENABLED`, `BYPASS`, `DISABLED`, etc.).  
   - If `None`, defaults to some level of caching or you can specify `CacheMode.ENABLED`.

5. **`js_code`**:  
   - A string or list of JS strings to execute.  
   - Great for “Load More” buttons or user interactions.  

6. **`wait_for`**:  
   - A CSS or JS expression to wait for before extracting content.  
   - Common usage: `wait_for="css:.main-loaded"` or `wait_for="js:() => window.loaded === true"`.

7. **`screenshot`** & **`pdf`**:  
   - If `True`, captures a screenshot or PDF after the page is fully loaded.  
   - The results go to `result.screenshot` (base64) or `result.pdf` (bytes).

8. **`verbose`**:  
   - Logs additional runtime details.  
   - Overlaps with the browser’s verbosity if also set to `True` in `BrowserConfig`.

9. **`enable_rate_limiting`**:  
   - If `True`, enables rate limiting for batch processing.  
   - Requires `rate_limit_config` to be set.

10. **`rate_limit_config`**:  
    - A `RateLimitConfig` object controlling rate limiting behavior.  
    - See below for details.

11. **`memory_threshold_percent`**:  
    - The memory threshold (as a percentage) to monitor.  
    - If exceeded, the crawler will pause or slow down.

12. **`check_interval`**:  
    - The interval (in seconds) to check system resources.  
    - Affects how often memory and CPU usage are monitored.

13. **`max_session_permit`**:  
    - The maximum number of concurrent crawl sessions.  
    - Helps prevent overwhelming the system.

14. **`display_mode`**:  
    - The display mode for progress information (`DETAILED`, `BRIEF`, etc.).  
    - Affects how much information is printed during the crawl.

### Helper Methods

The `clone()` method is particularly useful for creating variations of your crawler configuration:

```python
# Create a base configuration
base_config = CrawlerRunConfig(
    cache_mode=CacheMode.ENABLED,
    word_count_threshold=200,
    wait_until="networkidle"
)

# Create variations for different use cases
stream_config = base_config.clone(
    stream=True,  # Enable streaming mode
    cache_mode=CacheMode.BYPASS
)

debug_config = base_config.clone(
    page_timeout=120000,  # Longer timeout for debugging
    verbose=True
)
```

The `clone()` method:
- Creates a new instance with all the same settings
- Updates only the specified parameters
- Leaves the original configuration unchanged
- Perfect for creating variations without repeating all parameters

### Rate Limiting & Resource Management

For batch processing with `arun_many()`, you can enable intelligent rate limiting:

```python
from crawl4ai import RateLimitConfig
    
config = CrawlerRunConfig(
    enable_rate_limiting=True,
    rate_limit_config=RateLimitConfig(
        base_delay=(1.0, 3.0),    # Random delay range
        max_delay=60.0,           # Max delay after rate limits
        max_retries=3,            # Retries before giving up
        rate_limit_codes=[429, 503]  # Status codes to watch
    ),
    memory_threshold_percent=70.0,  # Memory threshold
    check_interval=1.0,            # Resource check interval
    max_session_permit=20,         # Max concurrent crawls
    display_mode="DETAILED"        # Progress display mode
)
```

This configuration:
- Implements intelligent rate limiting per domain
- Monitors system resources
- Provides detailed progress information
- Manages concurrent crawls efficiently

**Minimal Example**:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

crawl_conf = CrawlerRunConfig(
    js_code="document.querySelector('button#loadMore')?.click()",
    wait_for="css:.loaded-content",
    screenshot=True,
    enable_rate_limiting=True,
    rate_limit_config=RateLimitConfig(
        base_delay=(1.0, 3.0),
        max_delay=60.0,
        max_retries=3,
        rate_limit_codes=[429, 503]
    ),
    stream=True  # Enable streaming
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com", config=crawl_conf)
    print(result.screenshot[:100])  # Base64-encoded PNG snippet
```

---

## 3. Putting It All Together

In a typical scenario, you define **one** `BrowserConfig` for your crawler session, then create **one or more** `CrawlerRunConfig` depending on each call’s needs:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    # 1) Browser config: headless, bigger viewport, no proxy
    browser_conf = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=720
    )

    # 2) Example extraction strategy
    schema = {
        "name": "Articles",
        "baseSelector": "div.article",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }
    extraction = JsonCssExtractionStrategy(schema)

    # 3) Crawler run config: skip cache, use extraction
    run_conf = CrawlerRunConfig(
        extraction_strategy=extraction,
        cache_mode=CacheMode.BYPASS,
        enable_rate_limiting=True,
        rate_limit_config=RateLimitConfig(
            base_delay=(1.0, 3.0),
            max_delay=60.0,
            max_retries=3,
            rate_limit_codes=[429, 503]
        )
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        # 4) Execute the crawl
        result = await crawler.arun(url="https://example.com/news", config=run_conf)

        if result.success:
            print("Extracted content:", result.extracted_content)
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. Next Steps

For a **detailed list** of available parameters (including advanced ones), see:

- [BrowserConfig and CrawlerRunConfig Reference](../api/parameters.md)  

You can explore topics like:

- **Custom Hooks & Auth** (Inject JavaScript or handle login forms).  
- **Session Management** (Re-use pages, preserve state across multiple calls).  
- **Magic Mode** or **Identity-based Crawling** (Fight bot detection by simulating user behavior).  
- **Advanced Caching** (Fine-tune read/write cache modes).  

---

## 5. Conclusion

**BrowserConfig** and **CrawlerRunConfig** give you straightforward ways to define:

- **Which** browser to launch, how it should run, and any proxy or user agent needs.  
- **How** each crawl should behave—caching, timeouts, JavaScript code, extraction strategies, etc.

Use them together for **clear, maintainable** code, and when you need more specialized behavior, check out the advanced parameters in the [reference docs](../api/parameters.md). Happy crawling!