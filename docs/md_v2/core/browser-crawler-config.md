# Browser, Crawler & LLM Configuration (Quick Overview)

Crawl4AI's flexibility stems from two key classes:

1. **`BrowserConfig`** – Dictates **how** the browser is launched and behaves (e.g., headless or visible, proxy, user agent).  
2. **`CrawlerRunConfig`** – Dictates **how** each **crawl** operates (e.g., caching, extraction, timeouts, JavaScript code to run, etc.).  
3. **`LLMConfig`** - Dictates **how** LLM providers are configured. (model, api token, base url, temperature etc.)

In most examples, you create **one** `BrowserConfig` for the entire crawler session, then pass a **fresh** or re-used `CrawlerRunConfig` whenever you call `arun()`. This tutorial shows the most commonly used parameters. If you need advanced or rarely used fields, see the [Configuration Parameters](../api/parameters.md).

---

## 1. BrowserConfig Essentials

```python
class BrowserConfig:
    def __init__(
        browser_type="chromium",
        headless=True,
        browser_mode="dedicated",
        use_managed_browser=False,
        cdp_url=None,
        debugging_port=9222,
        host="localhost",
        proxy_config=None,
        viewport_width=1080,
        viewport_height=600,
        verbose=True,
        use_persistent_context=False,
        user_data_dir=None,
        cookies=None,
        headers=None,
        user_agent=(
            # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) AppleWebKit/537.36 "
            # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            # "(KHTML, like Gecko) Chrome/116.0.5845.187 Safari/604.1 Edg/117.0.2045.47"
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36"
        ),
        user_agent_mode="",
        text_mode=False,
        light_mode=False,
        extra_args=None,
        enable_stealth=False,
        # ... other advanced parameters omitted here
    ):
        ...
```

### Key Fields to Note

1.⠀**`browser_type`**  
   - Options: `"chromium"`, `"firefox"`, or `"webkit"`.  
   - Defaults to `"chromium"`.  
   - If you need a different engine, specify it here.

2.⠀**`headless`**  
   - `True`: Runs the browser in headless mode (invisible browser).  
   - `False`: Runs the browser in visible mode, which helps with debugging.

3.⠀**`browser_mode`**  
   - Determines how the browser should be initialized:
     - `"dedicated"` (default): Creates a new browser instance each time
     - `"builtin"`: Uses the builtin CDP browser running in background
     - `"custom"`: Uses explicit CDP settings provided in `cdp_url`
     - `"docker"`: Runs browser in Docker container with isolation

4.⠀**`use_managed_browser`** & **`cdp_url`**  
   - `use_managed_browser=True`: Launch browser using Chrome DevTools Protocol (CDP) for advanced control
   - `cdp_url`: URL for CDP endpoint (e.g., `"ws://localhost:9222/devtools/browser/"`)
   - Automatically set based on `browser_mode`

5.⠀**`debugging_port`** & **`host`**  
   - `debugging_port`: Port for browser debugging protocol (default: 9222)
   - `host`: Host for browser connection (default: "localhost")

6.⠀**`proxy_config`**  
   - A `ProxyConfig` object or dictionary with fields like:  
```json
{
    "server": "http://proxy.example.com:8080", 
    "username": "...", 
    "password": "..."
}
```
   - Leave as `None` if a proxy is not required.

7.⠀**`viewport_width` & `viewport_height`**  
   - The initial window size.  
   - Some sites behave differently with smaller or bigger viewports.

8.⠀**`verbose`**  
   - If `True`, prints extra logs.  
   - Handy for debugging.

9.⠀**`use_persistent_context`**  
   - If `True`, uses a **persistent** browser profile, storing cookies/local storage across runs.  
   - Typically also set `user_data_dir` to point to a folder.

10.⠀**`cookies`** & **`headers`**  
    - If you want to start with specific cookies or add universal HTTP headers to the browser context, set them here.  
    - E.g. `cookies=[{"name": "session", "value": "abc123", "domain": "example.com"}]`.

11.⠀**`user_agent`** & **`user_agent_mode`**  
    - `user_agent`: Custom User-Agent string. If `None`, a default is used.  
    - `user_agent_mode`: Set to `"random"` for randomization (helps fight bot detection).

12.⠀**`text_mode`** & **`light_mode`**  
    - `text_mode=True` disables images, possibly speeding up text-only crawls.  
    - `light_mode=True` turns off certain background features for performance.  

13.⠀**`extra_args`**  
    - Additional flags for the underlying browser.  
    - E.g. `["--disable-extensions"]`.

14.⠀**`enable_stealth`**  
    - If `True`, enables stealth mode using playwright-stealth.  
    - Modifies browser fingerprints to avoid basic bot detection.  
    - Default is `False`. Recommended for sites with bot protection.

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
        chunking_strategy=RegexChunking(),
        markdown_generator=None,
        cache_mode=CacheMode.BYPASS,
        js_code=None,
        c4a_script=None,
        wait_for=None,
        screenshot=False,
        pdf=False,
        capture_mhtml=False,
        # Location and Identity Parameters
        locale=None,            # e.g. "en-US", "fr-FR"
        timezone_id=None,       # e.g. "America/New_York"
        geolocation=None,       # GeolocationConfig object
        # Proxy Configuration
        proxy_config=None,
        proxy_rotation_strategy=None,
        # Page Interaction Parameters
        scan_full_page=False,
        scroll_delay=0.2,
        wait_until="domcontentloaded",
        page_timeout=60000,
        delay_before_return_html=0.1,
        # URL Matching Parameters
        url_matcher=None,       # For URL-specific configurations
        match_mode=MatchMode.OR,
        verbose=True,
        stream=False,  # Enable streaming for arun_many()
        # ... other advanced parameters omitted
    ):
        ...
```

### Key Fields to Note

1.⠀**`word_count_threshold`**:  
   - The minimum word count before a block is considered.  
   - If your site has lots of short paragraphs or items, you can lower it.

2.⠀**`extraction_strategy`**:  
   - Where you plug in JSON-based extraction (CSS, LLM, etc.).  
   - If `None`, no structured extraction is done (only raw/cleaned HTML + markdown).

3.⠀**`chunking_strategy`**:  
   - Strategy to chunk content before extraction.  
   - Defaults to `RegexChunking()`. Can be customized for different chunking approaches.

4.⠀**`markdown_generator`**:  
   - E.g., `DefaultMarkdownGenerator(...)`, controlling how HTML→Markdown conversion is done.  
   - If `None`, a default approach is used.

5.⠀**`cache_mode`**:  
   - Controls caching behavior (`ENABLED`, `BYPASS`, `DISABLED`, etc.).  
   - Defaults to `CacheMode.BYPASS`.

6.⠀**`js_code`** & **`c4a_script`**:  
   - `js_code`: A string or list of JavaScript strings to execute.  
   - `c4a_script`: C4A script that compiles to JavaScript.
   - Great for "Load More" buttons or user interactions.  

7.⠀**`wait_for`**:  
   - A CSS or JS expression to wait for before extracting content.  
   - Common usage: `wait_for="css:.main-loaded"` or `wait_for="js:() => window.loaded === true"`.

8.⠀**`screenshot`**, **`pdf`**, & **`capture_mhtml`**:  
   - If `True`, captures a screenshot, PDF, or MHTML snapshot after the page is fully loaded.  
   - The results go to `result.screenshot` (base64), `result.pdf` (bytes), or `result.mhtml` (string).

9.⠀**Location Parameters**:  
   - **`locale`**: Browser's locale (e.g., `"en-US"`, `"fr-FR"`) for language preferences
   - **`timezone_id`**: Browser's timezone (e.g., `"America/New_York"`, `"Europe/Paris"`)
   - **`geolocation`**: GPS coordinates via `GeolocationConfig(latitude=48.8566, longitude=2.3522)`
   - See [Identity Based Crawling](../advanced/identity-based-crawling.md#7-locale-timezone-and-geolocation-control)

10.⠀**Proxy Configuration**:  
    - **`proxy_config`**: Proxy server configuration (ProxyConfig object or dict) e.g. {"server": "...", "username": "...", "password"}
    - **`proxy_rotation_strategy`**: Strategy for rotating proxies during crawls

11.⠀**Page Interaction Parameters**:  
    - **`scan_full_page`**: If `True`, scroll through the entire page to load all content
    - **`wait_until`**: Condition to wait for when navigating (e.g., "domcontentloaded", "networkidle")
    - **`page_timeout`**: Timeout in milliseconds for page operations (default: 60000)
    - **`delay_before_return_html`**: Delay in seconds before retrieving final HTML.

12.⠀**`url_matcher`** & **`match_mode`**:  
    - Enable URL-specific configurations when used with `arun_many()`.
    - Set `url_matcher` to patterns (glob, function, or list) to match specific URLs.
    - Use `match_mode` (OR/AND) to control how multiple patterns combine.
    - See [URL-Specific Configurations](../api/arun_many.md#url-specific-configurations) for examples.

13.⠀**`verbose`**:  
    - Logs additional runtime details.  
    - Overlaps with the browser's verbosity if also set to `True` in `BrowserConfig`.

14.⠀**`stream`**:  
    - If `True`, enables streaming mode for `arun_many()` to process URLs as they complete.
    - Allows handling results incrementally instead of waiting for all URLs to finish.


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

---


## 3. LLMConfig Essentials

### Key fields to note

1.⠀**`provider`**:  
- Which LLM provider to use. 
- Possible values are `"ollama/llama3","groq/llama3-70b-8192","groq/llama3-8b-8192", "openai/gpt-4o-mini" ,"openai/gpt-4o","openai/o1-mini","openai/o1-preview","openai/o3-mini","openai/o3-mini-high","anthropic/claude-3-haiku-20240307","anthropic/claude-3-opus-20240229","anthropic/claude-3-sonnet-20240229","anthropic/claude-3-5-sonnet-20240620","gemini/gemini-pro","gemini/gemini-1.5-pro","gemini/gemini-2.0-flash","gemini/gemini-2.0-flash-exp","gemini/gemini-2.0-flash-lite-preview-02-05","deepseek/deepseek-chat"`<br/>*(default: `"openai/gpt-4o-mini"`)*

2.⠀**`api_token`**:  
    - Optional. When not provided explicitly, api_token will be read from environment variables based on provider. For example: If a gemini model is passed as provider then,`"GEMINI_API_KEY"` will be read from environment variables  
    - API token of LLM provider <br/> eg: `api_token = "gsk_1ClHGGJ7Lpn4WGybR7vNWGdyb3FY7zXEw3SCiy0BAVM9lL8CQv"`
    - Environment variable - use with prefix "env:" <br/> eg:`api_token = "env: GROQ_API_KEY"`            

3.⠀**`base_url`**:  
   - If your provider has a custom endpoint

4.⠀**Retry/backoff controls** *(optional)*:  
   - `backoff_base_delay` *(default `2` seconds)* – base delay inserted before the first retry when the provider returns a rate-limit response.  
   - `backoff_max_attempts` *(default `3`)* – total number of attempts (initial call plus retries) before the request is surfaced as an error.  
   - `backoff_exponential_factor` *(default `2`)* – growth rate for the retry delay (`delay = base_delay * factor^attempt`).  
   - These values are forwarded to the shared `perform_completion_with_backoff` helper, ensuring every strategy that consumes your `LLMConfig` honors the same throttling policy.

```python
llm_config = LLMConfig(
    provider="openai/gpt-4o-mini",
    api_token=os.getenv("OPENAI_API_KEY"),
    backoff_base_delay=1, # optional
    backoff_max_attempts=5, # optional
    backoff_exponential_factor=3, #optional
)
```

## 4. Putting It All Together

In a typical scenario, you define **one** `BrowserConfig` for your crawler session, then create **one or more** `CrawlerRunConfig` & `LLMConfig` depending on each call's needs:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig, LLMContentFilter, DefaultMarkdownGenerator
from crawl4ai import JsonCssExtractionStrategy

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

    # 3) Example LLM content filtering

    gemini_config = LLMConfig(
        provider="gemini/gemini-1.5-pro", 
        api_token = "env:GEMINI_API_TOKEN"
    )

    # Initialize LLM filter with specific instruction
    filter = LLMContentFilter(
        llm_config=gemini_config,  # or your preferred provider
        instruction="""
        Focus on extracting the core educational content.
        Include:
        - Key concepts and explanations
        - Important code examples
        - Essential technical details
        Exclude:
        - Navigation elements
        - Sidebars
        - Footer content
        Format the output as clean markdown with proper code blocks and headers.
        """,
        chunk_token_threshold=500,  # Adjust based on your needs
        verbose=True
    )

    md_generator = DefaultMarkdownGenerator(
        content_filter=filter,
        options={"ignore_links": True}
    )

    # 4) Crawler run config: skip cache, use extraction
    run_conf = CrawlerRunConfig(
        markdown_generator=md_generator,
        extraction_strategy=extraction,
        cache_mode=CacheMode.BYPASS,
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

## 5. Next Steps

For a **detailed list** of available parameters (including advanced ones), see:

- [BrowserConfig, CrawlerRunConfig & LLMConfig Reference](../api/parameters.md)  

You can explore topics like:

- **Custom Hooks & Auth** (Inject JavaScript or handle login forms).  
- **Session Management** (Re-use pages, preserve state across multiple calls).  
- **Magic Mode** or **Identity-based Crawling** (Fight bot detection by simulating user behavior).  
- **Advanced Caching** (Fine-tune read/write cache modes).  

---

## 6. Conclusion

**BrowserConfig**, **CrawlerRunConfig** and **LLMConfig** give you straightforward ways to define:

- **Which** browser to launch, how it should run, and any proxy or user agent needs.  
- **How** each crawl should behave—caching, timeouts, JavaScript code, extraction strategies, etc.
- **Which** LLM provider to use, api token, temperature and base url for custom endpoints

Use them together for **clear, maintainable** code, and when you need more specialized behavior, check out the advanced parameters in the [reference docs](../api/parameters.md). Happy crawling!