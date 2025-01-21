# `arun()` Parameter Guide (New Approach)

In Crawl4AI’s **latest** configuration model, nearly all parameters that once went directly to `arun()` are now part of **`CrawlerRunConfig`**. When calling `arun()`, you provide:

```python
await crawler.arun(
    url="https://example.com",  
    config=my_run_config
)
```

Below is an organized look at the parameters that can go inside `CrawlerRunConfig`, divided by their functional areas. For **Browser** settings (e.g., `headless`, `browser_type`), see [BrowserConfig](./parameters.md).

---

## 1. Core Usage

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    run_config = CrawlerRunConfig(
        verbose=True,            # Detailed logging
        cache_mode=CacheMode.ENABLED,  # Use normal read/write cache
        check_robots_txt=True,   # Respect robots.txt rules
        # ... other parameters
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )
        
        # Check if blocked by robots.txt
        if not result.success and result.status_code == 403:
            print(f"Error: {result.error_message}")
```

**Key Fields**:
- `verbose=True` logs each crawl step.  
- `cache_mode` decides how to read/write the local crawl cache.

---

## 2. Cache Control

**`cache_mode`** (default: `CacheMode.ENABLED`)  
Use a built-in enum from `CacheMode`:
- `ENABLED`: Normal caching—reads if available, writes if missing.
- `DISABLED`: No caching—always refetch pages.
- `READ_ONLY`: Reads from cache only; no new writes.
- `WRITE_ONLY`: Writes to cache but doesn’t read existing data.
- `BYPASS`: Skips reading cache for this crawl (though it might still write if set up that way).

```python
run_config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS
)
```

**Additional flags**:
- `bypass_cache=True` acts like `CacheMode.BYPASS`.
- `disable_cache=True` acts like `CacheMode.DISABLED`.
- `no_cache_read=True` acts like `CacheMode.WRITE_ONLY`.
- `no_cache_write=True` acts like `CacheMode.READ_ONLY`.

---

## 3. Content Processing & Selection

### 3.1 Text Processing

```python
run_config = CrawlerRunConfig(
    word_count_threshold=10,   # Ignore text blocks <10 words
    only_text=False,           # If True, tries to remove non-text elements
    keep_data_attributes=False # Keep or discard data-* attributes
)
```

### 3.2 Content Selection

```python
run_config = CrawlerRunConfig(
    css_selector=".main-content",  # Focus on .main-content region only
    excluded_tags=["form", "nav"], # Remove entire tag blocks
    remove_forms=True,             # Specifically strip <form> elements
    remove_overlay_elements=True,  # Attempt to remove modals/popups
)
```

### 3.3 Link Handling

```python
run_config = CrawlerRunConfig(
    exclude_external_links=True,         # Remove external links from final content
    exclude_social_media_links=True,     # Remove links to known social sites
    exclude_domains=["ads.example.com"], # Exclude links to these domains
    exclude_social_media_domains=["facebook.com","twitter.com"], # Extend the default list
)
```

### 3.4 Media Filtering

```python
run_config = CrawlerRunConfig(
    exclude_external_images=True  # Strip images from other domains
)
```

---

## 4. Page Navigation & Timing

### 4.1 Basic Browser Flow

```python
run_config = CrawlerRunConfig(
    wait_for="css:.dynamic-content", # Wait for .dynamic-content
    delay_before_return_html=2.0,    # Wait 2s before capturing final HTML
    page_timeout=60000,             # Navigation & script timeout (ms)
)
```

**Key Fields**:
- `wait_for`:  
  - `"css:selector"` or  
  - `"js:() => boolean"`  
  e.g. `js:() => document.querySelectorAll('.item').length > 10`.

- `mean_delay` & `max_range`: define random delays for `arun_many()` calls.  
- `semaphore_count`: concurrency limit when crawling multiple URLs.

### 4.2 JavaScript Execution

```python
run_config = CrawlerRunConfig(
    js_code=[
        "window.scrollTo(0, document.body.scrollHeight);",
        "document.querySelector('.load-more')?.click();"
    ],
    js_only=False
)
```

- `js_code` can be a single string or a list of strings.  
- `js_only=True` means “I’m continuing in the same session with new JS steps, no new full navigation.”

### 4.3 Anti-Bot

```python
run_config = CrawlerRunConfig(
    magic=True,
    simulate_user=True,
    override_navigator=True
)
```
- `magic=True` tries multiple stealth features.  
- `simulate_user=True` mimics mouse movements or random delays.  
- `override_navigator=True` fakes some navigator properties (like user agent checks).

---

## 5. Session Management

**`session_id`**: 
```python
run_config = CrawlerRunConfig(
    session_id="my_session123"
)
```
If re-used in subsequent `arun()` calls, the same tab/page context is continued (helpful for multi-step tasks or stateful browsing).

---

## 6. Screenshot, PDF & Media Options

```python
run_config = CrawlerRunConfig(
    screenshot=True,             # Grab a screenshot as base64
    screenshot_wait_for=1.0,     # Wait 1s before capturing
    pdf=True,                    # Also produce a PDF
    image_description_min_word_threshold=5,  # If analyzing alt text
    image_score_threshold=3,                # Filter out low-score images
)
```
**Where they appear**:
- `result.screenshot` → Base64 screenshot string.
- `result.pdf` → Byte array with PDF data.

---

## 7. Extraction Strategy

**For advanced data extraction** (CSS/LLM-based), set `extraction_strategy`:

```python
run_config = CrawlerRunConfig(
    extraction_strategy=my_css_or_llm_strategy
)
```

The extracted data will appear in `result.extracted_content`.

---

## 8. Comprehensive Example

Below is a snippet combining many parameters:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

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
```

**What we covered**:
1. **Crawling** the main content region, ignoring external links.  
2. Running **JavaScript** to click “.show-more”.  
3. **Waiting** for “.loaded-block” to appear.  
4. Generating a **screenshot** & **PDF** of the final page.  
5. Extracting repeated “article.post” elements with a **CSS-based** extraction strategy.

---

## 9. Best Practices

1. **Use `BrowserConfig` for global browser** settings (headless, user agent).  
2. **Use `CrawlerRunConfig`** to handle the **specific** crawl needs: content filtering, caching, JS, screenshot, extraction, etc.  
3. Keep your **parameters consistent** in run configs—especially if you’re part of a large codebase with multiple crawls.  
4. **Limit** large concurrency (`semaphore_count`) if the site or your system can’t handle it.  
5. For dynamic pages, set `js_code` or `scan_full_page` so you load all content.

---

## 10. Conclusion

All parameters that used to be direct arguments to `arun()` now belong in **`CrawlerRunConfig`**. This approach:

- Makes code **clearer** and **more maintainable**.  
- Minimizes confusion about which arguments affect global vs. per-crawl behavior.  
- Allows you to create **reusable** config objects for different pages or tasks.

For a **full** reference, check out the [CrawlerRunConfig Docs](./parameters.md). 

Happy crawling with your **structured, flexible** config approach!