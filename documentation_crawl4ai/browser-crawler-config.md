[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/core/browser-crawler-config/)


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
    * Browser, Crawler & LLM Config
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
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [Browser, Crawler & LLM Configuration (Quick Overview)](https://docs.crawl4ai.com/core/browser-crawler-config/#browser-crawler-llm-configuration-quick-overview)
  * [1. BrowserConfig Essentials](https://docs.crawl4ai.com/core/browser-crawler-config/#1-browserconfig-essentials)
  * [2. CrawlerRunConfig Essentials](https://docs.crawl4ai.com/core/browser-crawler-config/#2-crawlerrunconfig-essentials)
  * [3. LLMConfig Essentials](https://docs.crawl4ai.com/core/browser-crawler-config/#3-llmconfig-essentials)
  * [4. Putting It All Together](https://docs.crawl4ai.com/core/browser-crawler-config/#4-putting-it-all-together)
  * [5. Next Steps](https://docs.crawl4ai.com/core/browser-crawler-config/#5-next-steps)
  * [6. Conclusion](https://docs.crawl4ai.com/core/browser-crawler-config/#6-conclusion)


# Browser, Crawler & LLM Configuration (Quick Overview)
Crawl4AI's flexibility stems from two key classes:
  1. **`BrowserConfig`**– Dictates**how** the browser is launched and behaves (e.g., headless or visible, proxy, user agent).
  2. **`CrawlerRunConfig`**– Dictates**how** each **crawl** operates (e.g., caching, extraction, timeouts, JavaScript code to run, etc.).
  3. **`LLMConfig`**- Dictates**how** LLM providers are configured. (model, api token, base url, temperature etc.)


In most examples, you create **one** `BrowserConfig` for the entire crawler session, then pass a **fresh** or re-used `CrawlerRunConfig` whenever you call `arun()`. This tutorial shows the most commonly used parameters. If you need advanced or rarely used fields, see the [Configuration Parameters](https://docs.crawl4ai.com/api/parameters/).
* * *
## 1. BrowserConfig Essentials
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
Copy
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
Copy
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
Copy
```

**Minimal Example** :
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
Copy
```

* * *
## 2. CrawlerRunConfig Essentials
```
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
        capture_mhtml=False,
        # Location and Identity Parameters
        locale=None,            # e.g. "en-US", "fr-FR"
        timezone_id=None,       # e.g. "America/New_York"
        geolocation=None,       # GeolocationConfig object
        # Resource Management
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
Copy
```

### Key Fields to Note
  1. **`word_count_threshold`**:
  2. The minimum word count before a block is considered.
  3. If your site has lots of short paragraphs or items, you can lower it.
  4. **`extraction_strategy`**:
  5. Where you plug in JSON-based extraction (CSS, LLM, etc.).
  6. If `None`, no structured extraction is done (only raw/cleaned HTML + markdown).
  7. **`markdown_generator`**:
  8. E.g., `DefaultMarkdownGenerator(...)`, controlling how HTML→Markdown conversion is done.
  9. If `None`, a default approach is used.
  10. **`cache_mode`**:
  11. Controls caching behavior (`ENABLED`, `BYPASS`, `DISABLED`, etc.).
  12. If `None`, defaults to some level of caching or you can specify `CacheMode.ENABLED`.
  13. **`js_code`**:
  14. A string or list of JS strings to execute.
  15. Great for "Load More" buttons or user interactions.
  16. **`wait_for`**:
  17. A CSS or JS expression to wait for before extracting content.
  18. Common usage: `wait_for="css:.main-loaded"` or `wait_for="js:() => window.loaded === true"`.
  19. **`screenshot`**,**`pdf`**, & **`capture_mhtml`**:
  20. If `True`, captures a screenshot, PDF, or MHTML snapshot after the page is fully loaded.
  21. The results go to `result.screenshot` (base64), `result.pdf` (bytes), or `result.mhtml` (string).
  22. **Location Parameters** :
  23. **`locale`**: Browser's locale (e.g.,`"en-US"` , `"fr-FR"`) for language preferences
  24. **`timezone_id`**: Browser's timezone (e.g.,`"America/New_York"` , `"Europe/Paris"`)
  25. **`geolocation`**: GPS coordinates via`GeolocationConfig(latitude=48.8566, longitude=2.3522)`
  26. See [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/#7-locale-timezone-and-geolocation-control)
  27. **`verbose`**:
  28. Logs additional runtime details.
  29. Overlaps with the browser's verbosity if also set to `True` in `BrowserConfig`.
  30. **`enable_rate_limiting`**:
  31. If `True`, enables rate limiting for batch processing.
  32. Requires `rate_limit_config` to be set.
  33. **`memory_threshold_percent`**:
     * The memory threshold (as a percentage) to monitor.
     * If exceeded, the crawler will pause or slow down.
  34. **`check_interval`**:
     * The interval (in seconds) to check system resources.
     * Affects how often memory and CPU usage are monitored.
  35. **`max_session_permit`**:
     * The maximum number of concurrent crawl sessions.
     * Helps prevent overwhelming the system.
  36. **`url_matcher`** & **`match_mode`**:
     * Enable URL-specific configurations when used with `arun_many()`.
     * Set `url_matcher` to patterns (glob, function, or list) to match specific URLs.
     * Use `match_mode` (OR/AND) to control how multiple patterns combine.
     * See [URL-Specific Configurations](https://docs.crawl4ai.com/api/arun_many/#url-specific-configurations) for examples.
  37. **`display_mode`**:
     * The display mode for progress information (`DETAILED`, `BRIEF`, etc.).
     * Affects how much information is printed during the crawl.


### Helper Methods
The `clone()` method is particularly useful for creating variations of your crawler configuration:
```
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
Copy
```

The `clone()` method: - Creates a new instance with all the same settings - Updates only the specified parameters - Leaves the original configuration unchanged - Perfect for creating variations without repeating all parameters
* * *
## 3. LLMConfig Essentials
### Key fields to note
  1. **`provider`**:
  2. Which LLM provider to use.
  3. Possible values are `"ollama/llama3","groq/llama3-70b-8192","groq/llama3-8b-8192", "openai/gpt-4o-mini" ,"openai/gpt-4o","openai/o1-mini","openai/o1-preview","openai/o3-mini","openai/o3-mini-high","anthropic/claude-3-haiku-20240307","anthropic/claude-3-opus-20240229","anthropic/claude-3-sonnet-20240229","anthropic/claude-3-5-sonnet-20240620","gemini/gemini-pro","gemini/gemini-1.5-pro","gemini/gemini-2.0-flash","gemini/gemini-2.0-flash-exp","gemini/gemini-2.0-flash-lite-preview-02-05","deepseek/deepseek-chat"`
_(default:`"openai/gpt-4o-mini"`)_
  4. **`api_token`**:
     * Optional. When not provided explicitly, api_token will be read from environment variables based on provider. For example: If a gemini model is passed as provider then,`"GEMINI_API_KEY"` will be read from environment variables
     * API token of LLM provider
eg: `api_token = "gsk_1ClHGGJ7Lpn4WGybR7vNWGdyb3FY7zXEw3SCiy0BAVM9lL8CQv"`
     * Environment variable - use with prefix "env:"
eg:`api_token = "env: GROQ_API_KEY"`
  5. **`base_url`**:
  6. If your provider has a custom endpoint


```
llm_config = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))
Copy
```

## 4. Putting It All Together
In a typical scenario, you define **one** `BrowserConfig` for your crawler session, then create **one or more** `CrawlerRunConfig` & `LLMConfig` depending on each call's needs:
```
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
Copy
```

* * *
## 5. Next Steps
For a **detailed list** of available parameters (including advanced ones), see:
  * [BrowserConfig, CrawlerRunConfig & LLMConfig Reference](https://docs.crawl4ai.com/api/parameters/)


You can explore topics like:
  * **Custom Hooks & Auth** (Inject JavaScript or handle login forms).
  * **Session Management** (Re-use pages, preserve state across multiple calls).
  * **Magic Mode** or **Identity-based Crawling** (Fight bot detection by simulating user behavior).
  * **Advanced Caching** (Fine-tune read/write cache modes).


* * *
## 6. Conclusion
**BrowserConfig** , **CrawlerRunConfig** and **LLMConfig** give you straightforward ways to define:
  * **Which** browser to launch, how it should run, and any proxy or user agent needs.
  * **How** each crawl should behave—caching, timeouts, JavaScript code, extraction strategies, etc.
  * **Which** LLM provider to use, api token, temperature and base url for custom endpoints


Use them together for **clear, maintainable** code, and when you need more specialized behavior, check out the advanced parameters in the [reference docs](https://docs.crawl4ai.com/api/parameters/). Happy crawling!
#### On this page
  * [1. BrowserConfig Essentials](https://docs.crawl4ai.com/core/browser-crawler-config/#1-browserconfig-essentials)
  * [Key Fields to Note](https://docs.crawl4ai.com/core/browser-crawler-config/#key-fields-to-note)
  * [Helper Methods](https://docs.crawl4ai.com/core/browser-crawler-config/#helper-methods)
  * [2. CrawlerRunConfig Essentials](https://docs.crawl4ai.com/core/browser-crawler-config/#2-crawlerrunconfig-essentials)
  * [Key Fields to Note](https://docs.crawl4ai.com/core/browser-crawler-config/#key-fields-to-note_1)
  * [Helper Methods](https://docs.crawl4ai.com/core/browser-crawler-config/#helper-methods_1)
  * [3. LLMConfig Essentials](https://docs.crawl4ai.com/core/browser-crawler-config/#3-llmconfig-essentials)
  * [Key fields to note](https://docs.crawl4ai.com/core/browser-crawler-config/#key-fields-to-note_2)
  * [4. Putting It All Together](https://docs.crawl4ai.com/core/browser-crawler-config/#4-putting-it-all-together)
  * [5. Next Steps](https://docs.crawl4ai.com/core/browser-crawler-config/#5-next-steps)
  * [6. Conclusion](https://docs.crawl4ai.com/core/browser-crawler-config/#6-conclusion)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
