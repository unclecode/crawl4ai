AsyncWebCrawler
===============

The **`AsyncWebCrawler`** is the core class for asynchronous web crawling in Crawl4AI. You typically create it **once**, optionally customize it with a **`BrowserConfig`** (e.g., headless, user agent), then **run** multiple **`arun()`** calls with different **`CrawlerRunConfig`** objects.

**Recommended usage**:

1. **Create** a `BrowserConfig` for global browser settings.

2. **Instantiate** `AsyncWebCrawler(config=browser_config)`.

3. **Use** the crawler in an async context manager (`async with`) or manage start/close manually.

4. **Call** `arun(url, config=crawler_run_config)` for each page you want.

---

1. Constructor Overview
-----------------------

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
```

**Notes**:

* **Legacy** parameters like `always_bypass_cache` remain for backward compatibility, but prefer to set **caching** in `CrawlerRunConfig`.

---