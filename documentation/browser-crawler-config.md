Browser, Crawler & LLM Configuration (Quick Overview)
=====================================================

Crawl4AI's flexibility stems from two key classes:

1. **`BrowserConfig`** – Dictates **how** the browser is launched and behaves (e.g., headless or visible, proxy, user agent).
2. **`CrawlerRunConfig`** – Dictates **how** each **crawl** operates (e.g., caching, extraction, timeouts, JavaScript code to run, etc.).
3. **`LLMConfig`** - Dictates **how** LLM providers are configured. (model, api token, base url, temperature etc.)

In most examples, you create **one** `BrowserConfig` for the entire crawler session, then pass a **fresh** or re-used `CrawlerRunConfig` whenever you call `arun()`. This tutorial shows the most commonly used parameters. If you need advanced or rarely used fields, see the [Configuration Parameters](../../api/parameters/).

---

1. BrowserConfig Essentials
---------------------------

```
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
        enable_stealth=False,
        # ... other advanced parameters omitted here
    ):
        ...
```

### Key Fields to Note

1. **`browser_type`**
2. Options: `"chromium"`, `"firefox"`, or `"webkit"`.
3. Defaults to `"chromium"`.
4. If you need a different engine, specify it here.
5. **`headless`**
6. `True`: Runs the browser in headless mode (invisible browser).
7. `False`: Runs the browser in visible mode, which helps with debugging.
8. **`proxy_config`**
9. A dictionary with fields like:

   ```
   {
       "server": "http://proxy.example.com:8080",
       "username": "...",
       "password": "..."
   }
   ```
10. Leave as `None` if a proxy is not required.
11. **`viewport_width` & `viewport_height`**:
12. The initial window size.
13. Some sites behave differently with smaller or bigger viewports.
14. **`verbose`**:
15. If `True`, prints extra logs.
16. Handy for debugging.
17. **`use_persistent_context`**:
18. If `True`, uses a **persistent** browser profile, storing cookies/local storage across runs.
19. Typically also set `user_data_dir` to point to a folder.
20. **`cookies`** & **`headers`**:
21. If you want to start with specific cookies or add universal HTTP headers, set them here.
22. E.g. `cookies=[{"name": "session", "value": "abc123", "domain": "example.com"}]`.
23. **`user_agent`**:
24. Custom User-Agent string. If `None`, a default is used.
25. You can also set `user_agent_mode="random"` for randomization (if you want to fight bot detection).
26. **`text_mode`** & **`light_mode`**:
27. `text_mode=True` disables images, possibly speeding up text-only crawls.
28. `light_mode=True` turns off certain background features for performance.
29. **`extra_args`**:

    * Additional flags for the underlying browser.
    * E.g. `["--disable-extensions"]`.
30. **`enable_stealth`**:

    * If `True`, enables stealth mode using playwright-stealth.
    * Modifies browser fingerprints to avoid basic bot detection.
    * Default is `False`. Recommended for sites with bot protection.

### Helper Methods

Both configuration classes provide a `clone()` method to create modified copies:

```
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

```
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