[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/api/arun/)


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
    * arun()
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [arun() Parameter Guide (New Approach)](https://docs.crawl4ai.com/api/arun/#arun-parameter-guide-new-approach)
  * [1. Core Usage](https://docs.crawl4ai.com/api/arun/#1-core-usage)
  * [2. Cache Control](https://docs.crawl4ai.com/api/arun/#2-cache-control)
  * [3. Content Processing & Selection](https://docs.crawl4ai.com/api/arun/#3-content-processing-selection)
  * [4. Page Navigation & Timing](https://docs.crawl4ai.com/api/arun/#4-page-navigation-timing)
  * [5. Session Management](https://docs.crawl4ai.com/api/arun/#5-session-management)
  * [6. Screenshot, PDF & Media Options](https://docs.crawl4ai.com/api/arun/#6-screenshot-pdf-media-options)
  * [7. Extraction Strategy](https://docs.crawl4ai.com/api/arun/#7-extraction-strategy)
  * [8. Comprehensive Example](https://docs.crawl4ai.com/api/arun/#8-comprehensive-example)
  * [9. Best Practices](https://docs.crawl4ai.com/api/arun/#9-best-practices)
  * [10. Conclusion](https://docs.crawl4ai.com/api/arun/#10-conclusion)


#  `arun()` Parameter Guide (New Approach)
In Crawl4AI’s **latest** configuration model, nearly all parameters that once went directly to `arun()` are now part of **`CrawlerRunConfig`**. When calling`arun()` , you provide:
```
await crawler.arun(
    url="https://example.com",
    config=my_run_config
)
Copy
```

Below is an organized look at the parameters that can go inside `CrawlerRunConfig`, divided by their functional areas. For **Browser** settings (e.g., `headless`, `browser_type`), see [BrowserConfig](https://docs.crawl4ai.com/api/parameters/).
* * *
## 1. Core Usage
```
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    run_config = CrawlerRunConfig(
        verbose=True,            # Detailed logging
        cache_mode=CacheMode.ENABLED,  # Use normal read/write cache
        check_robots_txt=True,   # Respect robots.txt rules
        # ... other parameters
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )

        # Check if blocked by robots.txt
        if not result.success and result.status_code == 403:
            print(f"Error: {result.error_message}")
Copy
```

**Key Fields** : - `verbose=True` logs each crawl step. - `cache_mode` decides how to read/write the local crawl cache.
* * *
## 2. Cache Control
**`cache_mode`**(default:`CacheMode.ENABLED`)
Use a built-in enum from `CacheMode`:
  * `ENABLED`: Normal caching—reads if available, writes if missing.
  * `DISABLED`: No caching—always refetch pages.
  * `READ_ONLY`: Reads from cache only; no new writes.
  * `WRITE_ONLY`: Writes to cache but doesn’t read existing data.
  * `BYPASS`: Skips reading cache for this crawl (though it might still write if set up that way).


```
run_config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS
)
Copy
```

**Additional flags** :
  * `bypass_cache=True` acts like `CacheMode.BYPASS`.
  * `disable_cache=True` acts like `CacheMode.DISABLED`.
  * `no_cache_read=True` acts like `CacheMode.WRITE_ONLY`.
  * `no_cache_write=True` acts like `CacheMode.READ_ONLY`.


* * *
## 3. Content Processing & Selection
### 3.1 Text Processing
```
run_config = CrawlerRunConfig(
    word_count_threshold=10,   # Ignore text blocks <10 words
    only_text=False,           # If True, tries to remove non-text elements
    keep_data_attributes=False # Keep or discard data-* attributes
)
Copy
```

### 3.2 Content Selection
```
run_config = CrawlerRunConfig(
    css_selector=".main-content",  # Focus on .main-content region only
    excluded_tags=["form", "nav"], # Remove entire tag blocks
    remove_forms=True,             # Specifically strip <form> elements
    remove_overlay_elements=True,  # Attempt to remove modals/popups
)
Copy
```

### 3.3 Link Handling
```
run_config = CrawlerRunConfig(
    exclude_external_links=True,         # Remove external links from final content
    exclude_social_media_links=True,     # Remove links to known social sites
    exclude_domains=["ads.example.com"], # Exclude links to these domains
    exclude_social_media_domains=["facebook.com","twitter.com"], # Extend the default list
)
Copy
```

### 3.4 Media Filtering
```
run_config = CrawlerRunConfig(
    exclude_external_images=True  # Strip images from other domains
)
Copy
```

* * *
## 4. Page Navigation & Timing
### 4.1 Basic Browser Flow
```
run_config = CrawlerRunConfig(
    wait_for="css:.dynamic-content", # Wait for .dynamic-content
    delay_before_return_html=2.0,    # Wait 2s before capturing final HTML
    page_timeout=60000,             # Navigation & script timeout (ms)
)
Copy
```

**Key Fields** :
  * `wait_for`:
  * `"css:selector"` or
  * `"js:() => boolean"`
e.g. `js:() => document.querySelectorAll('.item').length > 10`.
  * `mean_delay` & `max_range`: define random delays for `arun_many()` calls.
  * `semaphore_count`: concurrency limit when crawling multiple URLs.


### 4.2 JavaScript Execution
```
run_config = CrawlerRunConfig(
    js_code=[
        "window.scrollTo(0, document.body.scrollHeight);",
        "document.querySelector('.load-more')?.click();"
    ],
    js_only=False
)
Copy
```

  * `js_code` can be a single string or a list of strings.
  * `js_only=True` means “I’m continuing in the same session with new JS steps, no new full navigation.”


### 4.3 Anti-Bot
```
run_config = CrawlerRunConfig(
    magic=True,
    simulate_user=True,
    override_navigator=True
)
Copy
```

- `magic=True` tries multiple stealth features. - `simulate_user=True` mimics mouse movements or random delays. - `override_navigator=True` fakes some navigator properties (like user agent checks).
* * *
## 5. Session Management
**`session_id`**:
```
run_config = CrawlerRunConfig(
    session_id="my_session123"
)
Copy
```

If re-used in subsequent `arun()` calls, the same tab/page context is continued (helpful for multi-step tasks or stateful browsing).
* * *
## 6. Screenshot, PDF & Media Options
```
run_config = CrawlerRunConfig(
    screenshot=True,             # Grab a screenshot as base64
    screenshot_wait_for=1.0,     # Wait 1s before capturing
    pdf=True,                    # Also produce a PDF
    image_description_min_word_threshold=5,  # If analyzing alt text
    image_score_threshold=3,                # Filter out low-score images
)
Copy
```

**Where they appear** : - `result.screenshot` → Base64 screenshot string. - `result.pdf` → Byte array with PDF data.
* * *
## 7. Extraction Strategy
**For advanced data extraction** (CSS/LLM-based), set `extraction_strategy`:
```
run_config = CrawlerRunConfig(
    extraction_strategy=my_css_or_llm_strategy
)
Copy
```

The extracted data will appear in `result.extracted_content`.
* * *
## 8. Comprehensive Example
Below is a snippet combining many parameters:
```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

async def main():
    # Example schema
    schema = {
        "name": "Articles",
        "baseSelector": "article.post",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "link",  "selector": "a",  "type": "attribute", "attribute": "href"}
        ]
    }

    run_config = CrawlerRunConfig(
        # Core
        verbose=True,
        cache_mode=CacheMode.ENABLED,
        check_robots_txt=True,   # Respect robots.txt rules

        # Content
        word_count_threshold=10,
        css_selector="main.content",
        excluded_tags=["nav", "footer"],
        exclude_external_links=True,

        # Page & JS
        js_code="document.querySelector('.show-more')?.click();",
        wait_for="css:.loaded-block",
        page_timeout=30000,

        # Extraction
        extraction_strategy=JsonCssExtractionStrategy(schema),

        # Session
        session_id="persistent_session",

        # Media
        screenshot=True,
        pdf=True,

        # Anti-bot
        simulate_user=True,
        magic=True,
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com/posts", config=run_config)
        if result.success:
            print("HTML length:", len(result.cleaned_html))
            print("Extraction JSON:", result.extracted_content)
            if result.screenshot:
                print("Screenshot length:", len(result.screenshot))
            if result.pdf:
                print("PDF bytes length:", len(result.pdf))
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

**What we covered** :
1. **Crawling** the main content region, ignoring external links. 2. Running **JavaScript** to click “.show-more”. 3. **Waiting** for “.loaded-block” to appear. 4. Generating a **screenshot** & **PDF** of the final page. 5. Extracting repeated “article.post” elements with a **CSS-based** extraction strategy.
* * *
## 9. Best Practices
1. **Use`BrowserConfig` for global browser** settings (headless, user agent). 2. **Use`CrawlerRunConfig`** to handle the **specific** crawl needs: content filtering, caching, JS, screenshot, extraction, etc. 3. Keep your **parameters consistent** in run configs—especially if you’re part of a large codebase with multiple crawls. 4. **Limit** large concurrency (`semaphore_count`) if the site or your system can’t handle it. 5. For dynamic pages, set `js_code` or `scan_full_page` so you load all content.
* * *
## 10. Conclusion
All parameters that used to be direct arguments to `arun()` now belong in **`CrawlerRunConfig`**. This approach:
  * Makes code **clearer** and **more maintainable**.
  * Minimizes confusion about which arguments affect global vs. per-crawl behavior.
  * Allows you to create **reusable** config objects for different pages or tasks.


For a **full** reference, check out the [CrawlerRunConfig Docs](https://docs.crawl4ai.com/api/parameters/).
Happy crawling with your **structured, flexible** config approach!
#### On this page
  * [1. Core Usage](https://docs.crawl4ai.com/api/arun/#1-core-usage)
  * [2. Cache Control](https://docs.crawl4ai.com/api/arun/#2-cache-control)
  * [3. Content Processing & Selection](https://docs.crawl4ai.com/api/arun/#3-content-processing-selection)
  * [3.1 Text Processing](https://docs.crawl4ai.com/api/arun/#31-text-processing)
  * [3.2 Content Selection](https://docs.crawl4ai.com/api/arun/#32-content-selection)
  * [3.3 Link Handling](https://docs.crawl4ai.com/api/arun/#33-link-handling)
  * [3.4 Media Filtering](https://docs.crawl4ai.com/api/arun/#34-media-filtering)
  * [4. Page Navigation & Timing](https://docs.crawl4ai.com/api/arun/#4-page-navigation-timing)
  * [4.1 Basic Browser Flow](https://docs.crawl4ai.com/api/arun/#41-basic-browser-flow)
  * [4.2 JavaScript Execution](https://docs.crawl4ai.com/api/arun/#42-javascript-execution)
  * [4.3 Anti-Bot](https://docs.crawl4ai.com/api/arun/#43-anti-bot)
  * [5. Session Management](https://docs.crawl4ai.com/api/arun/#5-session-management)
  * [6. Screenshot, PDF & Media Options](https://docs.crawl4ai.com/api/arun/#6-screenshot-pdf-media-options)
  * [7. Extraction Strategy](https://docs.crawl4ai.com/api/arun/#7-extraction-strategy)
  * [8. Comprehensive Example](https://docs.crawl4ai.com/api/arun/#8-comprehensive-example)
  * [9. Best Practices](https://docs.crawl4ai.com/api/arun/#9-best-practices)
  * [10. Conclusion](https://docs.crawl4ai.com/api/arun/#10-conclusion)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
