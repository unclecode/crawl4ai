# 1. **BrowserConfig** – Controlling the Browser

`BrowserConfig` focuses on **how** the browser is launched and behaves. This includes headless mode, proxies, user agents, and other environment tweaks.

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_cfg = BrowserConfig(
    browser_type="chromium",
    headless=True,
    viewport_width=1280,
    viewport_height=720,
    proxy="http://user:pass@proxy:8080",
    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36",
)
```

## 1.1 Parameter Highlights

| **Parameter**         | **Type / Default**                     | **What It Does**                                                                                                                     |
|-----------------------|----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| **`browser_type`**    | `"chromium"`, `"firefox"`, `"webkit"`<br/>*(default: `"chromium"`)* | Which browser engine to use. `"chromium"` is typical for many sites, `"firefox"` or `"webkit"` for specialized tests.                 |
| **`headless`**        | `bool` (default: `True`)               | Headless means no visible UI. `False` is handy for debugging.                                                                         |
| **`viewport_width`**  | `int` (default: `1080`)                | Initial page width (in px). Useful for testing responsive layouts.                                                                    |
| **`viewport_height`** | `int` (default: `600`)                 | Initial page height (in px).                                                                                                          |
| **`proxy`**           | `str` (default: `None`)                | Single-proxy URL if you want all traffic to go through it, e.g. `"http://user:pass@proxy:8080"`.                                      |
| **`proxy_config`**    | `dict` (default: `None`)               | For advanced or multi-proxy needs, specify details like `{"server": "...", "username": "...", ...}`.                                  |
| **`use_persistent_context`** | `bool` (default: `False`)       | If `True`, uses a **persistent** browser context (keep cookies, sessions across runs). Also sets `use_managed_browser=True`.          |
| **`user_data_dir`**   | `str or None` (default: `None`)        | Directory to store user data (profiles, cookies). Must be set if you want permanent sessions.                                         |
| **`ignore_https_errors`** | `bool` (default: `True`)           | If `True`, continues despite invalid certificates (common in dev/staging).                                                            |
| **`java_script_enabled`** | `bool` (default: `True`)           | Disable if you want no JS overhead, or if only static content is needed.                                                              |
| **`cookies`**         | `list` (default: `[]`)                 | Pre-set cookies, each a dict like `{"name": "session", "value": "...", "url": "..."}`.                                                |
| **`headers`**         | `dict` (default: `{}`)                 | Extra HTTP headers for every request, e.g. `{"Accept-Language": "en-US"}`.                                                            |
| **`user_agent`**      | `str` (default: Chrome-based UA)       | Your custom or random user agent. `user_agent_mode="random"` can shuffle it.                                                          |
| **`light_mode`**      | `bool` (default: `False`)              | Disables some background features for performance gains.                                                                              |
| **`text_mode`**       | `bool` (default: `False`)              | If `True`, tries to disable images/other heavy content for speed.                                                                     |
| **`use_managed_browser`** | `bool` (default: `False`)          | For advanced "managed" interactions (debugging, CDP usage). Typically set automatically if persistent context is on.                  |
| **`extra_args`**      | `list` (default: `[]`)                 | Additional flags for the underlying browser process, e.g. `["--disable-extensions"]`.                                                |

**Tips**:
- Set `headless=False` to visually **debug** how pages load or how interactions proceed.  
- If you need **authentication** storage or repeated sessions, consider `use_persistent_context=True` and specify `user_data_dir`.  
- For large pages, you might need a bigger `viewport_width` and `viewport_height` to handle dynamic content.

---

# 2. **CrawlerRunConfig** – Controlling Each Crawl

While `BrowserConfig` sets up the **environment**, `CrawlerRunConfig` details **how** each **crawl operation** should behave: caching, content filtering, link or domain blocking, timeouts, JavaScript code, etc.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

run_cfg = CrawlerRunConfig(
    wait_for="css:.main-content",
    word_count_threshold=15,
    excluded_tags=["nav", "footer"],
    exclude_external_links=True,
    stream=True,  # Enable streaming for arun_many()
)
```

## 2.1 Parameter Highlights

We group them by category. 

### A) **Content Processing**

| **Parameter**                | **Type / Default**                   | **What It Does**                                                                                |
|------------------------------|--------------------------------------|-------------------------------------------------------------------------------------------------|
| **`word_count_threshold`**   | `int` (default: ~200)                | Skips text blocks below X words. Helps ignore trivial sections.                                 |
| **`extraction_strategy`**    | `ExtractionStrategy` (default: None) | If set, extracts structured data (CSS-based, LLM-based, etc.).                                  |
| **`markdown_generator`**     | `MarkdownGenerationStrategy` (None)  | If you want specialized markdown output (citations, filtering, chunking, etc.). Can be customized with options such as `content_source` parameter to select the HTML input source ('cleaned_html', 'raw_html', or 'fit_html').                 |
| **`css_selector`**           | `str` (None)                         | Retains only the part of the page matching this selector. Affects the entire extraction process. |
| **`target_elements`**        | `List[str]` (None)                   | List of CSS selectors for elements to focus on for markdown generation and data extraction, while still processing the entire page for links, media, etc. Provides more flexibility than `css_selector`. |
| **`excluded_tags`**          | `list` (None)                        | Removes entire tags (e.g. `["script", "style"]`).                                               |
| **`excluded_selector`**      | `str` (None)                         | Like `css_selector` but to exclude. E.g. `"#ads, .tracker"`.                                    |
| **`only_text`**              | `bool` (False)                       | If `True`, tries to extract text-only content.                                                  |
| **`prettiify`**              | `bool` (False)                       | If `True`, beautifies final HTML (slower, purely cosmetic).                                      |
| **`keep_data_attributes`**   | `bool` (False)                       | If `True`, preserve `data-*` attributes in cleaned HTML.                                         |
| **`remove_forms`**           | `bool` (False)                       | If `True`, remove all `<form>` elements.                                                        |

---

### B) **Caching & Session**

| **Parameter**           | **Type / Default**     | **What It Does**                                                                                                              |
|-------------------------|------------------------|------------------------------------------------------------------------------------------------------------------------------|
| **`cache_mode`**        | `CacheMode or None`    | Controls how caching is handled (`ENABLED`, `BYPASS`, `DISABLED`, etc.). If `None`, typically defaults to `ENABLED`.          |
| **`session_id`**        | `str or None`          | Assign a unique ID to reuse a single browser session across multiple `arun()` calls.                                          |
| **`bypass_cache`**      | `bool` (False)         | If `True`, acts like `CacheMode.BYPASS`.                                                                                     |
| **`disable_cache`**     | `bool` (False)         | If `True`, acts like `CacheMode.DISABLED`.                                                                                   |
| **`no_cache_read`**     | `bool` (False)         | If `True`, acts like `CacheMode.WRITE_ONLY` (writes cache but never reads).                                                  |
| **`no_cache_write`**    | `bool` (False)         | If `True`, acts like `CacheMode.READ_ONLY` (reads cache but never writes).                                                   |

Use these for controlling whether you read or write from a local content cache. Handy for large batch crawls or repeated site visits.

---

### C) **Page Navigation & Timing**

| **Parameter**              | **Type / Default**      | **What It Does**                                                                                                    |
|----------------------------|-------------------------|----------------------------------------------------------------------------------------------------------------------|
| **`wait_until`**           | `str` (domcontentloaded)| Condition for navigation to "complete". Often `"networkidle"` or `"domcontentloaded"`.                               |
| **`page_timeout`**         | `int` (60000 ms)        | Timeout for page navigation or JS steps. Increase for slow sites.                                                    |
| **`wait_for`**             | `str or None`           | Wait for a CSS (`"css:selector"`) or JS (`"js:() => bool"`) condition before content extraction.                     |
| **`wait_for_images`**      | `bool` (False)          | Wait for images to load before finishing. Slows down if you only want text.                                          |
| **`delay_before_return_html`** | `float` (0.1)       | Additional pause (seconds) before final HTML is captured. Good for last-second updates.                               |
| **`check_robots_txt`**     | `bool` (False)          | Whether to check and respect robots.txt rules before crawling. If True, caches robots.txt for efficiency.            |
| **`mean_delay`** and **`max_range`** | `float` (0.1, 0.3) | If you call `arun_many()`, these define random delay intervals between crawls, helping avoid detection or rate limits. |
| **`semaphore_count`**      | `int` (5)               | Max concurrency for `arun_many()`. Increase if you have resources for parallel crawls.                                |

---

### D) **Page Interaction**

| **Parameter**              | **Type / Default**            | **What It Does**                                                                                                                       |
|----------------------------|--------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| **`js_code`**              | `str or list[str]` (None)      | JavaScript to run after load. E.g. `"document.querySelector('button')?.click();"`.                                                     |
| **`js_only`**              | `bool` (False)                 | If `True`, indicates we're reusing an existing session and only applying JS. No full reload.                                           |
| **`ignore_body_visibility`** | `bool` (True)                | Skip checking if `<body>` is visible. Usually best to keep `True`.                                                                     |
| **`scan_full_page`**       | `bool` (False)                 | If `True`, auto-scroll the page to load dynamic content (infinite scroll).                                                              |
| **`scroll_delay`**         | `float` (0.2)                  | Delay between scroll steps if `scan_full_page=True`.                                                                                   |
| **`process_iframes`**      | `bool` (False)                 | Inlines iframe content for single-page extraction.                                                                                     |
| **`remove_overlay_elements`** | `bool` (False)              | Removes potential modals/popups blocking the main content.                                                                              |
| **`simulate_user`**        | `bool` (False)                 | Simulate user interactions (mouse movements) to avoid bot detection.                                                                    |
| **`override_navigator`**   | `bool` (False)                 | Override `navigator` properties in JS for stealth.                                                                                      |
| **`magic`**                | `bool` (False)                 | Automatic handling of popups/consent banners. Experimental.                                                                             |
| **`adjust_viewport_to_content`** | `bool` (False)           | Resizes viewport to match page content height.                                                                                          |

If your page is a single-page app with repeated JS updates, set `js_only=True` in subsequent calls, plus a `session_id` for reusing the same tab.

---

### E) **Media Handling**

| **Parameter**                              | **Type / Default**  | **What It Does**                                                                                         |
|--------------------------------------------|---------------------|-----------------------------------------------------------------------------------------------------------|
| **`screenshot`**                           | `bool` (False)      | Capture a screenshot (base64) in `result.screenshot`.                                                     |
| **`screenshot_wait_for`**                  | `float or None`     | Extra wait time before the screenshot.                                                                    |
| **`screenshot_height_threshold`**          | `int` (~20000)      | If the page is taller than this, alternate screenshot strategies are used.                                |
| **`pdf`**                                  | `bool` (False)      | If `True`, returns a PDF in `result.pdf`.                                                                 |
| **`capture_mhtml`**                        | `bool` (False)      | If `True`, captures an MHTML snapshot of the page in `result.mhtml`. MHTML includes all page resources (CSS, images, etc.) in a single file. |
| **`image_description_min_word_threshold`** | `int` (~50)         | Minimum words for an image's alt text or description to be considered valid.                              |
| **`image_score_threshold`**                | `int` (~3)          | Filter out low-scoring images. The crawler scores images by relevance (size, context, etc.).              |
| **`exclude_external_images`**              | `bool` (False)      | Exclude images from other domains.                                                                        |

---

### F) **Link/Domain Handling**

| **Parameter**                | **Type / Default**      | **What It Does**                                                                                                             |
|------------------------------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| **`exclude_social_media_domains`** | `list` (e.g. Facebook/Twitter) | A default list can be extended. Any link to these domains is removed from final output.                                      |
| **`exclude_external_links`** | `bool` (False)          | Removes all links pointing outside the current domain.                                                                      |
| **`exclude_social_media_links`** | `bool` (False)      | Strips links specifically to social sites (like Facebook or Twitter).                                                      |
| **`exclude_domains`**        | `list` ([])             | Provide a custom list of domains to exclude (like `["ads.com", "trackers.io"]`).                                            |

Use these for link-level content filtering (often to keep crawls "internal" or to remove spammy domains).

---

### G) **Debug & Logging**

| **Parameter**  | **Type / Default** | **What It Does**                                                         |
|----------------|--------------------|---------------------------------------------------------------------------|
| **`verbose`**  | `bool` (True)     | Prints logs detailing each step of crawling, interactions, or errors.    |
| **`log_console`** | `bool` (False) | Logs the page's JavaScript console output if you want deeper JS debugging.|

---

## 2.2 Helper Methods

Both `BrowserConfig` and `CrawlerRunConfig` provide a `clone()` method to create modified copies:

```python
# Create a base configuration
base_config = CrawlerRunConfig(
    cache_mode=CacheMode.ENABLED,
    word_count_threshold=200
)

# Create variations using clone()
stream_config = base_config.clone(stream=True)
no_cache_config = base_config.clone(
    cache_mode=CacheMode.BYPASS,
    stream=True
)
```

The `clone()` method is particularly useful when you need slightly different configurations for different use cases, without modifying the original config.

## 2.3 Example Usage

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    # Configure the browser
    browser_cfg = BrowserConfig(
        headless=False,
        viewport_width=1280,
        viewport_height=720,
        proxy="http://user:pass@myproxy:8080",
        text_mode=True
    )

    # Configure the run
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        session_id="my_session",
        css_selector="main.article",
        excluded_tags=["script", "style"],
        exclude_external_links=True,
        wait_for="css:.article-loaded",
        screenshot=True,
        stream=True
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://example.com/news",
            config=run_cfg
        )
        if result.success:
            print("Final cleaned_html length:", len(result.cleaned_html))
            if result.screenshot:
                print("Screenshot captured (base64, length):", len(result.screenshot))
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

## 2.4 Compliance & Ethics

| **Parameter**          | **Type / Default**      | **What It Does**                                                                                                    |
|-----------------------|-------------------------|----------------------------------------------------------------------------------------------------------------------|
| **`check_robots_txt`**| `bool` (False)          | When True, checks and respects robots.txt rules before crawling. Uses efficient caching with SQLite backend.          |
| **`user_agent`**      | `str` (None)            | User agent string to identify your crawler. Used for robots.txt checking when enabled.                                |

```python
run_config = CrawlerRunConfig(
    check_robots_txt=True,  # Enable robots.txt compliance
    user_agent="MyBot/1.0"  # Identify your crawler
)
```

# 3. **LLMConfig** - Setting up LLM providers
LLMConfig is useful to pass LLM provider config to strategies and functions that rely on LLMs to do extraction, filtering, schema generation etc. Currently it can be used in the following -

1. LLMExtractionStrategy
2. LLMContentFilter
3. JsonCssExtractionStrategy.generate_schema
4. JsonXPathExtractionStrategy.generate_schema

## 3.1 Parameters
| **Parameter**         | **Type / Default**                     | **What It Does**                                                                                                                     |
|-----------------------|----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| **`provider`**    | `"ollama/llama3","groq/llama-3.3-70b-versatile","groq/meta-llama/llama-4-scout-17b-16e-instruct", "openai/gpt-4o-mini" ,"openai/gpt-4o","openai/o1-mini","openai/o1-preview","openai/o3-mini","openai/o3-mini-high","anthropic/claude-3-haiku-20240307","anthropic/claude-3-opus-20240229","anthropic/claude-3-sonnet-20240229","anthropic/claude-3-5-sonnet-20240620","gemini/gemini-pro","gemini/gemini-1.5-pro","gemini/gemini-2.0-flash","gemini/gemini-2.0-flash-exp","gemini/gemini-2.0-flash-lite-preview-02-05","deepseek/deepseek-chat"`<br/>*(default: `"openai/gpt-4o-mini"`)* | Which LLM provoder to use. 
| **`api_token`**         |1.Optional. When not provided explicitly, api_token will be read from environment variables based on provider. For example: If a gemini model is passed as provider then,`"GEMINI_API_KEY"` will be read from environment variables  <br/> 2. API token of LLM provider <br/> eg: `api_token = "gsk_1ClHGGJ7Lpn4WGybR7vNWGdyb3FY7zXEw3SCiy0BAVM9lL8CQv"` <br/> 3. Environment variable - use with prefix "env:" <br/> eg:`api_token = "env: GROQ_API_KEY"`              | API token to use for the given provider 
| **`base_url`**         |Optional. Custom API endpoint | If your provider has a custom endpoint

## 3.2 Example Usage
```python
llm_config = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))
```

## 4. Putting It All Together

- **Use** `BrowserConfig` for **global** browser settings: engine, headless, proxy, user agent.  
- **Use** `CrawlerRunConfig` for each crawl's **context**: how to filter content, handle caching, wait for dynamic elements, or run JS.  
- **Pass** both configs to `AsyncWebCrawler` (the `BrowserConfig`) and then to `arun()` (the `CrawlerRunConfig`).  
- **Use** `LLMConfig` for LLM provider configurations that can be used across all extraction, filtering, schema generation tasks. Can be used in - `LLMExtractionStrategy`, `LLMContentFilter`, `JsonCssExtractionStrategy.generate_schema` & `JsonXPathExtractionStrategy.generate_schema`

```python
# Create a modified copy with the clone() method
stream_cfg = run_cfg.clone(
    stream=True,
    cache_mode=CacheMode.BYPASS
)
```
