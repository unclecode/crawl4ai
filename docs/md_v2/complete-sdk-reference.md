# Crawl4AI Complete SDK Documentation

**Generated:** 2025-10-19 12:56
**Format:** Ultra-Dense Reference (Optimized for AI Assistants)
**Crawl4AI Version:** 0.7.4

---

## Navigation


- [Installation & Setup](#installation--setup)
- [Quick Start](#quick-start)
- [Core API](#core-api)
- [Configuration](#configuration)
- [Crawling Patterns](#crawling-patterns)
- [Content Processing](#content-processing)
- [Extraction Strategies](#extraction-strategies)
- [Advanced Features](#advanced-features)

---


# Installation & Setup

# Installation & Setup (2023 Edition)
## 1. Basic Installation
```bash
pip install crawl4ai
```
## 2. Initial Setup & Diagnostics
### 2.1 Run the Setup Command
```bash
crawl4ai-setup
```
- Performs OS-level checks (e.g., missing libs on Linux)
- Confirms your environment is ready to crawl
### 2.2 Diagnostics
```bash
crawl4ai-doctor
```
- Check Python version compatibility
- Verify Playwright installation
- Inspect environment variables or library conflicts
If any issues arise, follow its suggestions (e.g., installing additional system packages) and re-run `crawl4ai-setup`.
## 3. Verifying Installation: A Simple Crawl (Skip this step if you already run `crawl4ai-doctor`)
Below is a minimal Python script demonstrating a **basic** crawl. It uses our new **`BrowserConfig`** and **`CrawlerRunConfig`** for clarity, though no custom settings are passed in this example:
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.example.com",
        )
        print(result.markdown[:300])  # Show the first 300 characters of extracted text

if __name__ == "__main__":
    asyncio.run(main())
```
- A headless browser session loads `example.com`
- Crawl4AI returns ~300 characters of markdown.  
If errors occur, rerun `crawl4ai-doctor` or manually ensure Playwright is installed correctly.
## 4. Advanced Installation (Optional)
### 4.1 Torch, Transformers, or All
- **Text Clustering (Torch)**  
  ```bash
  pip install crawl4ai[torch]
  crawl4ai-setup
  ```
- **Transformers**  
  ```bash
  pip install crawl4ai[transformer]
  crawl4ai-setup
  ```
- **All Features**  
  ```bash
  pip install crawl4ai[all]
  crawl4ai-setup
  ```
```bash
crawl4ai-download-models
```
## 5. Docker (Experimental)
```bash
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
```
You can then make POST requests to `http://localhost:11235/crawl` to perform crawls. **Production usage** is discouraged until our new Docker approach is ready (planned in Jan or Feb 2025).
## 6. Local Server Mode (Legacy)
## Summary
1. **Install** with `pip install crawl4ai` and run `crawl4ai-setup`.
2. **Diagnose** with `crawl4ai-doctor` if you see errors.
3. **Verify** by crawling `example.com` with minimal `BrowserConfig` + `CrawlerRunConfig`.



# Quick Start

# Getting Started with Crawl4AI
1. Run your **first crawl** using minimal configuration.  
3. Experiment with a simple **CSS-based extraction** strategy.  
5. Crawl a **dynamic** page that loads content via JavaScript.
## 1. Introduction
- An asynchronous crawler, **`AsyncWebCrawler`**.  
- Configurable browser and run settings via **`BrowserConfig`** and **`CrawlerRunConfig`**.  
- Automatic HTML-to-Markdown conversion via **`DefaultMarkdownGenerator`** (supports optional filters).  
- Multiple extraction strategies (LLM-based or “traditional” CSS/XPath-based).
## 2. Your First Crawl
Here’s a minimal Python script that creates an **`AsyncWebCrawler`**, fetches a webpage, and prints the first 300 characters of its Markdown output:
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown[:300])  # Print first 300 chars

if __name__ == "__main__":
    asyncio.run(main())
```
- **`AsyncWebCrawler`** launches a headless browser (Chromium by default).
- It fetches `https://example.com`.
- Crawl4AI automatically converts the HTML into Markdown.
## 3. Basic Configuration (Light Introduction)
1. **`BrowserConfig`**: Controls browser behavior (headless or full UI, user agent, JavaScript toggles, etc.).  
2. **`CrawlerRunConfig`**: Controls how each crawl runs (caching, extraction, timeouts, hooking, etc.).
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    browser_conf = BrowserConfig(headless=True)  # or False to see the browser
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_conf
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```
> IMPORTANT: By default cache mode is set to `CacheMode.BYPASS` to have fresh content. Set `CacheMode.ENABLED` to enable caching.
## 4. Generating Markdown Output
- **`result.markdown`**:  
- **`result.markdown.fit_markdown`**:  
  The same content after applying any configured **content filter** (e.g., `PruningContentFilter`).
### Example: Using a Filter with `DefaultMarkdownGenerator`
```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

md_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
)

config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://news.ycombinator.com", config=config)
    print("Raw Markdown length:", len(result.markdown.raw_markdown))
    print("Fit Markdown length:", len(result.markdown.fit_markdown))
```
**Note**: If you do **not** specify a content filter or markdown generator, you’ll typically see only the raw Markdown. `PruningContentFilter` may adds around `50ms` in processing time. We’ll dive deeper into these strategies in a dedicated **Markdown Generation** tutorial.
## 5. Simple Data Extraction (CSS-based)
```python
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai import LLMConfig

# Generate a schema (one-time cost)
html = "<div class='product'><h2>Gaming Laptop</h2><span class='price'>$999.99</span></div>"

# Using OpenAI (requires API token)
schema = JsonCssExtractionStrategy.generate_schema(
    html,
    llm_config = LLMConfig(provider="openai/gpt-4o",api_token="your-openai-token")  # Required for OpenAI
)

# Or using Ollama (open source, no token needed)
schema = JsonCssExtractionStrategy.generate_schema(
    html,
    llm_config = LLMConfig(provider="ollama/llama3.3", api_token=None)  # Not needed for Ollama
)

# Use the schema for fast, repeated extractions
strategy = JsonCssExtractionStrategy(schema)
```
```python
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

async def main():
    schema = {
        "name": "Example Items",
        "baseSelector": "div.item",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }

    raw_html = "<div class='item'><h2>Item 1</h2><a href='https://example.com/item1'>Link 1</a></div>"

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="raw://" + raw_html,
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=JsonCssExtractionStrategy(schema)
            )
        )
        # The JSON output is stored in 'extracted_content'
        data = json.loads(result.extracted_content)
        print(data)

if __name__ == "__main__":
    asyncio.run(main())
```
- Great for repetitive page structures (e.g., item listings, articles).
- No AI usage or costs.
- The crawler returns a JSON string you can parse or store.
> Tips: You can pass raw HTML to the crawler instead of a URL. To do so, prefix the HTML with `raw://`.
## 6. Simple Data Extraction (LLM-based)
- **Open-Source Models** (e.g., `ollama/llama3.3`, `no_token`)  
- **OpenAI Models** (e.g., `openai/gpt-4`, requires `api_token`)  
- Or any provider supported by the underlying library
```python
import os
import json
import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig
from crawl4ai import LLMExtractionStrategy

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(
        ..., description="Fee for output token for the OpenAI model."
    )

async def extract_structured_data_using_llm(
    provider: str, api_token: str = None, extra_headers: Dict[str, str] = None
):
    print(f"\n--- Extracting Structured Data with {provider} ---")

    if api_token is None and provider != "ollama":
        print(f"API token is required for {provider}. Skipping this example.")
        return

    browser_config = BrowserConfig(headless=True)

    extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 2000}
    if extra_headers:
        extra_args["extra_headers"] = extra_headers

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=1,
        page_timeout=80000,
        extraction_strategy=LLMExtractionStrategy(
            llm_config = LLMConfig(provider=provider,api_token=api_token),
            schema=OpenAIModelFee.model_json_schema(),
            extraction_type="schema",
            instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
            Do not miss any models in the entire content.""",
            extra_args=extra_args,
        ),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://openai.com/api/pricing/", config=crawler_config
        )
        print(result.extracted_content)

if __name__ == "__main__":

    asyncio.run(
        extract_structured_data_using_llm(
            provider="openai/gpt-4o", api_token=os.getenv("OPENAI_API_KEY")
        )
    )
```
- We define a Pydantic schema (`PricingInfo`) describing the fields we want.
## 7. Adaptive Crawling (New!)
```python
import asyncio
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler

async def adaptive_example():
    async with AsyncWebCrawler() as crawler:
        adaptive = AdaptiveCrawler(crawler)

        # Start adaptive crawling
        result = await adaptive.digest(
            start_url="https://docs.python.org/3/",
            query="async context managers"
        )

        # View results
        adaptive.print_stats()
        print(f"Crawled {len(result.crawled_urls)} pages")
        print(f"Achieved {adaptive.confidence:.0%} confidence")

if __name__ == "__main__":
    asyncio.run(adaptive_example())
```
- **Automatic stopping**: Stops when sufficient information is gathered
- **Intelligent link selection**: Follows only relevant links
- **Confidence scoring**: Know how complete your information is
## 8. Multi-URL Concurrency (Preview)
If you need to crawl multiple URLs in **parallel**, you can use `arun_many()`. By default, Crawl4AI employs a **MemoryAdaptiveDispatcher**, automatically adjusting concurrency based on system resources. Here’s a quick glimpse:
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def quick_parallel_example():
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ]

    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=True  # Enable streaming mode
    )

    async with AsyncWebCrawler() as crawler:
        # Stream results as they complete
        async for result in await crawler.arun_many(urls, config=run_conf):
            if result.success:
                print(f"[OK] {result.url}, length: {len(result.markdown.raw_markdown)}")
            else:
                print(f"[ERROR] {result.url} => {result.error_message}")

        # Or get all results at once (default behavior)
        run_conf = run_conf.clone(stream=False)
        results = await crawler.arun_many(urls, config=run_conf)
        for res in results:
            if res.success:
                print(f"[OK] {res.url}, length: {len(res.markdown.raw_markdown)}")
            else:
                print(f"[ERROR] {res.url} => {res.error_message}")

if __name__ == "__main__":
    asyncio.run(quick_parallel_example())
```
1. **Streaming mode** (`stream=True`): Process results as they become available using `async for`
2. **Batch mode** (`stream=False`): Wait for all results to complete
## 8. Dynamic Content Example
Some sites require multiple “page clicks” or dynamic JavaScript updates. Below is an example showing how to **click** a “Next Page” button and wait for new commits to load on GitHub, using **`BrowserConfig`** and **`CrawlerRunConfig`**:
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

async def extract_structured_data_using_css_extractor():
    print("\n--- Using JsonCssExtractionStrategy for Fast Structured Output ---")
    schema = {
        "name": "KidoCode Courses",
        "baseSelector": "section.charge-methodology .w-tab-content > div",
        "fields": [
            {
                "name": "section_title",
                "selector": "h3.heading-50",
                "type": "text",
            },
            {
                "name": "section_description",
                "selector": ".charge-content",
                "type": "text",
            },
            {
                "name": "course_name",
                "selector": ".text-block-93",
                "type": "text",
            },
            {
                "name": "course_description",
                "selector": ".course-content-text",
                "type": "text",
            },
            {
                "name": "course_icon",
                "selector": ".image-92",
                "type": "attribute",
                "attribute": "src",
            },
        ],
    }

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)

    js_click_tabs = """
    (async () => {
        const tabs = document.querySelectorAll("section.charge-methodology .tabs-menu-3 > div");
        for(let tab of tabs) {
            tab.scrollIntoView();
            tab.click();
            await new Promise(r => setTimeout(r, 500));
        }
    })();
    """

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        js_code=[js_click_tabs],
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.kidocode.com/degrees/technology", config=crawler_config
        )

        companies = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(companies)} companies")
        print(json.dumps(companies[0], indent=2))

async def main():
    await extract_structured_data_using_css_extractor()

if __name__ == "__main__":
    asyncio.run(main())
```
- **`BrowserConfig(headless=False)`**: We want to watch it click “Next Page.”  
- **`CrawlerRunConfig(...)`**: We specify the extraction strategy, pass `session_id` to reuse the same page.  
- **`js_code`** and **`wait_for`** are used for subsequent pages (`page > 0`) to click the “Next” button and wait for new commits to load.  
- **`js_only=True`** indicates we’re not re-navigating but continuing the existing session.  
- Finally, we call `kill_session()` to clean up the page and browser session.
## 9. Next Steps
1. Performed a basic crawl and printed Markdown.  
2. Used **content filters** with a markdown generator.  
3. Extracted JSON via **CSS** or **LLM** strategies.  
4. Handled **dynamic** pages with JavaScript triggers.



# Core API

# AsyncWebCrawler
The **`AsyncWebCrawler`** is the core class for asynchronous web crawling in Crawl4AI. You typically create it **once**, optionally customize it with a **`BrowserConfig`** (e.g., headless, user agent), then **run** multiple **`arun()`** calls with different **`CrawlerRunConfig`** objects.
1. **Create** a `BrowserConfig` for global browser settings.  
2. **Instantiate** `AsyncWebCrawler(config=browser_config)`.  
3. **Use** the crawler in an async context manager (`async with`) or manage start/close manually.  
4. **Call** `arun(url, config=crawler_run_config)` for each page you want.
## 1. Constructor Overview
```python
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
crawler = AsyncWebCrawler(config=browser_cfg)
```

**Notes**:

- **Legacy** parameters like `always_bypass_cache` remain for backward compatibility, but prefer to set **caching** in `CrawlerRunConfig`.

---

## 2. Lifecycle: Start/Close or Context Manager

### 2.1 Context Manager (Recommended)

```python
async with AsyncWebCrawler(config=browser_cfg) as crawler:
    result = await crawler.arun("https://example.com")
    # The crawler automatically starts/closes resources
```

When the `async with` block ends, the crawler cleans up (closes the browser, etc.).

### 2.2 Manual Start & Close

```python
crawler = AsyncWebCrawler(config=browser_cfg)
await crawler.start()
result1 = await crawler.arun("https://example.com")
result2 = await crawler.arun("https://another.com")
await crawler.close()
```

Use this style if you have a **long-running** application or need full control of the crawler’s lifecycle.

---

## 3. Primary Method: `arun()`

```python
async def arun(
    url: str,
    config: Optional[CrawlerRunConfig] = None,
    # Legacy parameters for backward compatibility...
```

### 3.1 New Approach

You pass a `CrawlerRunConfig` object that sets up everything about a crawl—content filtering, caching, session reuse, JS code, screenshots, etc.

```python
import asyncio
from crawl4ai import CrawlerRunConfig, CacheMode
run_cfg = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    css_selector="main.article",
    word_count_threshold=10,
    screenshot=True
async with AsyncWebCrawler(config=browser_cfg) as crawler:
    result = await crawler.arun("https://example.com/news", config=run_cfg)
```

### 3.2 Legacy Parameters Still Accepted

For **backward** compatibility, `arun()` can still accept direct arguments like `css_selector=...`, `word_count_threshold=...`, etc., but we strongly advise migrating them into a **`CrawlerRunConfig`**.

---

## 4. Batch Processing: `arun_many()`

```python
async def arun_many(
    urls: List[str],
    config: Optional[CrawlerRunConfig] = None,
    # Legacy parameters maintained for backwards compatibility...
```

### 4.1 Resource-Aware Crawling

The `arun_many()` method now uses an intelligent dispatcher that:

- Monitors system memory usage
- Implements adaptive rate limiting
- Provides detailed progress monitoring
- Manages concurrent crawls efficiently

### 4.2 Example Usage

Check page [Multi-url Crawling](../advanced/multi-url-crawling.md) for a detailed example of how to use `arun_many()`.

```python
### 4.3 Key Features
1. **Rate Limiting**
   - Automatic delay between requests
   - Exponential backoff on rate limit detection
   - Domain-specific rate limiting
   - Configurable retry strategy
2. **Resource Monitoring**
   - Memory usage tracking
   - Adaptive concurrency based on system load
   - Automatic pausing when resources are constrained
3. **Progress Monitoring**
   - Detailed or aggregated progress display
   - Real-time status updates
   - Memory usage statistics
4. **Error Handling**
   - Graceful handling of rate limits
   - Automatic retries with backoff
   - Detailed error reporting
## 5. `CrawlResult` Output
Each `arun()` returns a **`CrawlResult`** containing:
- `url`: Final URL (if redirected).
- `html`: Original HTML.
- `cleaned_html`: Sanitized HTML.
- `markdown_v2`: Deprecated. Instead just use regular `markdown`
- `extracted_content`: If an extraction strategy was used (JSON for CSS/LLM strategies).
- `screenshot`, `pdf`: If screenshots/PDF requested.
- `media`, `links`: Information about discovered images/links.
- `success`, `error_message`: Status info.
## 6. Quick Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy
import json

async def main():
    # 1. Browser config
    browser_cfg = BrowserConfig(
        browser_type="firefox",
        headless=False,
        verbose=True
    )

    # 2. Run config
    schema = {
        "name": "Articles",
        "baseSelector": "article.post",
        "fields": [
            {
                "name": "title", 
                "selector": "h2", 
                "type": "text"
            },
            {
                "name": "url", 
                "selector": "a", 
                "type": "attribute", 
                "attribute": "href"
            }
        ]
    }

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        word_count_threshold=15,
        remove_overlay_elements=True,
        wait_for="css:.post"  # Wait for posts to appear
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://example.com/blog",
            config=run_cfg
        )

        if result.success:
            print("Cleaned HTML length:", len(result.cleaned_html))
            if result.extracted_content:
                articles = json.loads(result.extracted_content)
                print("Extracted articles:", articles[:2])
        else:
            print("Error:", result.error_message)

asyncio.run(main())
```
- We define a **`BrowserConfig`** with Firefox, no headless, and `verbose=True`.  
- We define a **`CrawlerRunConfig`** that **bypasses cache**, uses a **CSS** extraction schema, has a `word_count_threshold=15`, etc.  
- We pass them to `AsyncWebCrawler(config=...)` and `arun(url=..., config=...)`.
## 7. Best Practices & Migration Notes
1. **Use** `BrowserConfig` for **global** settings about the browser’s environment.  
2. **Use** `CrawlerRunConfig` for **per-crawl** logic (caching, content filtering, extraction strategies, wait conditions).  
3. **Avoid** legacy parameters like `css_selector` or `word_count_threshold` directly in `arun()`. Instead:
   ```python
   run_cfg = CrawlerRunConfig(css_selector=".main-content", word_count_threshold=20)
   result = await crawler.arun(url="...", config=run_cfg)
   ```
## 8. Summary
- **Constructor** accepts **`BrowserConfig`** (or defaults).  
- **`arun(url, config=CrawlerRunConfig)`** is the main method for single-page crawls.  
- **`arun_many(urls, config=CrawlerRunConfig)`** handles concurrency across multiple URLs.  
- For advanced lifecycle control, use `start()` and `close()` explicitly.  
- If you used `AsyncWebCrawler(browser_type="chromium", css_selector="...")`, move browser settings to `BrowserConfig(...)` and content/crawl logic to `CrawlerRunConfig(...)`.


# `arun()` Parameter Guide (New Approach)
In Crawl4AI’s **latest** configuration model, nearly all parameters that once went directly to `arun()` are now part of **`CrawlerRunConfig`**. When calling `arun()`, you provide:
```python
await crawler.arun(
    url="https://example.com",  
    config=my_run_config
)
```
Below is an organized look at the parameters that can go inside `CrawlerRunConfig`, divided by their functional areas. For **Browser** settings (e.g., `headless`, `browser_type`), see [BrowserConfig](./parameters.md).
## 1. Core Usage
```python
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
```
- `verbose=True` logs each crawl step.  
- `cache_mode` decides how to read/write the local crawl cache.
## 2. Cache Control
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
- `bypass_cache=True` acts like `CacheMode.BYPASS`.
- `disable_cache=True` acts like `CacheMode.DISABLED`.
- `no_cache_read=True` acts like `CacheMode.WRITE_ONLY`.
- `no_cache_write=True` acts like `CacheMode.READ_ONLY`.
## 3. Content Processing & Selection
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
## 4. Page Navigation & Timing
### 4.1 Basic Browser Flow
```python
run_config = CrawlerRunConfig(
    wait_for="css:.dynamic-content", # Wait for .dynamic-content
    delay_before_return_html=2.0,    # Wait 2s before capturing final HTML
    page_timeout=60000,             # Navigation & script timeout (ms)
)
```
- `wait_for`:  
  - `"css:selector"` or  
  - `"js:() => boolean"`  
  e.g. `js:() => document.querySelectorAll('.item').length > 10`.
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
## 5. Session Management
**`session_id`**: 
```python
run_config = CrawlerRunConfig(
    session_id="my_session123"
)
```
If re-used in subsequent `arun()` calls, the same tab/page context is continued (helpful for multi-step tasks or stateful browsing).
## 6. Screenshot, PDF & Media Options
```python
run_config = CrawlerRunConfig(
    screenshot=True,             # Grab a screenshot as base64
    screenshot_wait_for=1.0,     # Wait 1s before capturing
    pdf=True,                    # Also produce a PDF
    image_description_min_word_threshold=5,  # If analyzing alt text
    image_score_threshold=3,                # Filter out low-score images
)
```
- `result.screenshot` → Base64 screenshot string.
- `result.pdf` → Byte array with PDF data.
## 7. Extraction Strategy
**For advanced data extraction** (CSS/LLM-based), set `extraction_strategy`:
```python
run_config = CrawlerRunConfig(
    extraction_strategy=my_css_or_llm_strategy
)
```
The extracted data will appear in `result.extracted_content`.
## 8. Comprehensive Example
Below is a snippet combining many parameters:
```python
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
```
1. **Crawling** the main content region, ignoring external links.  
2. Running **JavaScript** to click “.show-more”.  
3. **Waiting** for “.loaded-block” to appear.  
4. Generating a **screenshot** & **PDF** of the final page.  
## 9. Best Practices
1. **Use `BrowserConfig` for global browser** settings (headless, user agent).  
2. **Use `CrawlerRunConfig`** to handle the **specific** crawl needs: content filtering, caching, JS, screenshot, extraction, etc.  
4. **Limit** large concurrency (`semaphore_count`) if the site or your system can’t handle it.  
5. For dynamic pages, set `js_code` or `scan_full_page` so you load all content.
## 10. Conclusion
All parameters that used to be direct arguments to `arun()` now belong in **`CrawlerRunConfig`**. This approach:
- Makes code **clearer** and **more maintainable**.  


# `arun_many(...)` Reference
> **Note**: This function is very similar to [`arun()`](./arun.md) but focused on **concurrent** or **batch** crawling. If you’re unfamiliar with `arun()` usage, please read that doc first, then review this for differences.
## Function Signature
```python
async def arun_many(
    urls: Union[List[str], List[Any]],
    config: Optional[Union[CrawlerRunConfig, List[CrawlerRunConfig]]] = None,
    dispatcher: Optional[BaseDispatcher] = None,
    ...
) -> Union[List[CrawlResult], AsyncGenerator[CrawlResult, None]]:
    """
    Crawl multiple URLs concurrently or in batches.

    :param urls: A list of URLs (or tasks) to crawl.
    :param config: (Optional) Either:
        - A single `CrawlerRunConfig` applying to all URLs
        - A list of `CrawlerRunConfig` objects with url_matcher patterns
    :param dispatcher: (Optional) A concurrency controller (e.g. MemoryAdaptiveDispatcher).
    ...
    :return: Either a list of `CrawlResult` objects, or an async generator if streaming is enabled.
    """
```
## Differences from `arun()`
1. **Multiple URLs**:  
   - Instead of crawling a single URL, you pass a list of them (strings or tasks).  
   - The function returns either a **list** of `CrawlResult` or an **async generator** if streaming is enabled.
2. **Concurrency & Dispatchers**:  
   - **`dispatcher`** param allows advanced concurrency control.  
   - If omitted, a default dispatcher (like `MemoryAdaptiveDispatcher`) is used internally.  
3. **Streaming Support**:  
   - Enable streaming by setting `stream=True` in your `CrawlerRunConfig`.
   - When streaming, use `async for` to process results as they become available.
4. **Parallel** Execution**:  
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
### URL-Specific Configurations
Instead of using one config for all URLs, provide a list of configs with `url_matcher` patterns:
```python
from crawl4ai import CrawlerRunConfig, MatchMode
from crawl4ai.processors.pdf import PDFContentScrapingStrategy
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# PDF files - specialized extraction
pdf_config = CrawlerRunConfig(
    url_matcher="*.pdf",
    scraping_strategy=PDFContentScrapingStrategy()
)

# Blog/article pages - content filtering
blog_config = CrawlerRunConfig(
    url_matcher=["*/blog/*", "*/article/*", "*python.org*"],
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48)
    )
)

# Dynamic pages - JavaScript execution
github_config = CrawlerRunConfig(
    url_matcher=lambda url: 'github.com' in url,
    js_code="window.scrollTo(0, 500);"
)

# API endpoints - JSON extraction
api_config = CrawlerRunConfig(
    url_matcher=lambda url: 'api' in url or url.endswith('.json'),
    # Custome settings for JSON extraction
)

# Default fallback config
default_config = CrawlerRunConfig()  # No url_matcher means it never matches except as fallback

# Pass the list of configs - first match wins!
results = await crawler.arun_many(
    urls=[
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",  # → pdf_config
        "https://blog.python.org/",  # → blog_config
        "https://github.com/microsoft/playwright",  # → github_config
        "https://httpbin.org/json",  # → api_config
        "https://example.com/"  # → default_config
    ],
    config=[pdf_config, blog_config, github_config, api_config, default_config]
)
```
- **String patterns**: `"*.pdf"`, `"*/blog/*"`, `"*python.org*"`
- **Function matchers**: `lambda url: 'api' in url`
- **Mixed patterns**: Combine strings and functions with `MatchMode.OR` or `MatchMode.AND`
- **First match wins**: Configs are evaluated in order
- `dispatch_result` in each `CrawlResult` (if using concurrency) can hold memory and timing info.  
- **Important**: Always include a default config (without `url_matcher`) as the last item if you want to handle all URLs. Otherwise, unmatched URLs will fail.
### Return Value
Either a **list** of [`CrawlResult`](./crawl-result.md) objects, or an **async generator** if streaming is enabled. You can iterate to check `result.success` or read each item’s `extracted_content`, `markdown`, or `dispatch_result`.
## Dispatcher Reference
- **`MemoryAdaptiveDispatcher`**: Dynamically manages concurrency based on system memory usage.  
- **`SemaphoreDispatcher`**: Fixed concurrency limit, simpler but less adaptive.  
## Common Pitfalls
3. **Error Handling**: Each `CrawlResult` might fail for different reasons—always check `result.success` or the `error_message` before proceeding.
## Conclusion
Use `arun_many()` when you want to **crawl multiple URLs** simultaneously or in controlled parallel tasks. If you need advanced concurrency features (like memory-based adaptive throttling or complex rate-limiting), provide a **dispatcher**. Each result is a standard `CrawlResult`, possibly augmented with concurrency stats (`dispatch_result`) for deeper inspection. For more details on concurrency logic and dispatchers, see the [Advanced Multi-URL Crawling](../advanced/multi-url-crawling.md) docs.


# `CrawlResult` Reference
The **`CrawlResult`** class encapsulates everything returned after a single crawl operation. It provides the **raw or processed content**, details on links and media, plus optional metadata (like screenshots, PDFs, or extracted JSON).
**Location**: `crawl4ai/crawler/models.py` (for reference)
```python
class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: Optional[str] = None
    fit_html: Optional[str] = None  # Preprocessed HTML optimized for extraction
    media: Dict[str, List[Dict]] = {}
    links: Dict[str, List[Dict]] = {}
    downloaded_files: Optional[List[str]] = None
    screenshot: Optional[str] = None
    pdf : Optional[bytes] = None
    mhtml: Optional[str] = None
    markdown: Optional[Union[str, MarkdownGenerationResult]] = None
    extracted_content: Optional[str] = None
    metadata: Optional[dict] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    response_headers: Optional[dict] = None
    status_code: Optional[int] = None
    ssl_certificate: Optional[SSLCertificate] = None
    dispatch_result: Optional[DispatchResult] = None
    ...
```
## 1. Basic Crawl Info
### 1.1 **`url`** *(str)*  
```python
print(result.url)  # e.g., "https://example.com/"
```
### 1.2 **`success`** *(bool)*  
**What**: `True` if the crawl pipeline ended without major errors; `False` otherwise.  
```python
if not result.success:
    print(f"Crawl failed: {result.error_message}")
```
### 1.3 **`status_code`** *(Optional[int])*  
```python
if result.status_code == 404:
    print("Page not found!")
```
### 1.4 **`error_message`** *(Optional[str])*  
**What**: If `success=False`, a textual description of the failure.  
```python
if not result.success:
    print("Error:", result.error_message)
```
### 1.5 **`session_id`** *(Optional[str])*  
```python
# If you used session_id="login_session" in CrawlerRunConfig, see it here:
print("Session:", result.session_id)
```
### 1.6 **`response_headers`** *(Optional[dict])*  
```python
if result.response_headers:
    print("Server:", result.response_headers.get("Server", "Unknown"))
```
### 1.7 **`ssl_certificate`** *(Optional[SSLCertificate])*  
**What**: If `fetch_ssl_certificate=True` in your CrawlerRunConfig, **`result.ssl_certificate`** contains a  [**`SSLCertificate`**](../advanced/ssl-certificate.md) object describing the site's certificate. You can export the cert in multiple formats (PEM/DER/JSON) or access its properties like `issuer`, 
 `subject`, `valid_from`, `valid_until`, etc. 
```python
if result.ssl_certificate:
    print("Issuer:", result.ssl_certificate.issuer)
```
## 2. Raw / Cleaned Content
### 2.1 **`html`** *(str)*  
```python
# Possibly large
print(len(result.html))
```
### 2.2 **`cleaned_html`** *(Optional[str])*  
**What**: A sanitized HTML version—scripts, styles, or excluded tags are removed based on your `CrawlerRunConfig`.  
```python
print(result.cleaned_html[:500])  # Show a snippet
```
## 3. Markdown Fields
### 3.1 The Markdown Generation Approach
- **Raw** markdown  
- **Links as citations** (with a references section)  
- **Fit** markdown if a **content filter** is used (like Pruning or BM25)
**`MarkdownGenerationResult`** includes:
- **`raw_markdown`** *(str)*: The full HTML→Markdown conversion.  
- **`markdown_with_citations`** *(str)*: Same markdown, but with link references as academic-style citations.  
- **`references_markdown`** *(str)*: The reference list or footnotes at the end.  
- **`fit_markdown`** *(Optional[str])*: If content filtering (Pruning/BM25) was applied, the filtered "fit" text.  
- **`fit_html`** *(Optional[str])*: The HTML that led to `fit_markdown`.
```python
if result.markdown:
    md_res = result.markdown
    print("Raw MD:", md_res.raw_markdown[:300])
    print("Citations MD:", md_res.markdown_with_citations[:300])
    print("References:", md_res.references_markdown)
    if md_res.fit_markdown:
        print("Pruned text:", md_res.fit_markdown[:300])
```
### 3.2 **`markdown`** *(Optional[Union[str, MarkdownGenerationResult]])*  
**What**: Holds the `MarkdownGenerationResult`.  
```python
print(result.markdown.raw_markdown[:200])
print(result.markdown.fit_markdown)
print(result.markdown.fit_html)
```
**Important**: "Fit" content (in `fit_markdown`/`fit_html`) exists in result.markdown, only if you used a **filter** (like **PruningContentFilter** or **BM25ContentFilter**) within a `MarkdownGenerationStrategy`.
## 4. Media & Links
### 4.1 **`media`** *(Dict[str, List[Dict]])*  
**What**: Contains info about discovered images, videos, or audio. Typically keys: `"images"`, `"videos"`, `"audios"`.  
- `src` *(str)*: Media URL  
- `alt` or `title` *(str)*: Descriptive text  
- `score` *(float)*: Relevance score if the crawler's heuristic found it "important"  
- `desc` or `description` *(Optional[str])*: Additional context extracted from surrounding text  
```python
images = result.media.get("images", [])
for img in images:
    if img.get("score", 0) > 5:
        print("High-value image:", img["src"])
```
### 4.2 **`links`** *(Dict[str, List[Dict]])*  
**What**: Holds internal and external link data. Usually two keys: `"internal"` and `"external"`.  
- `href` *(str)*: The link target  
- `text` *(str)*: Link text  
- `title` *(str)*: Title attribute  
- `context` *(str)*: Surrounding text snippet  
- `domain` *(str)*: If external, the domain
```python
for link in result.links["internal"]:
    print(f"Internal link to {link['href']} with text {link['text']}")
```
## 5. Additional Fields
### 5.1 **`extracted_content`** *(Optional[str])*  
**What**: If you used **`extraction_strategy`** (CSS, LLM, etc.), the structured output (JSON).  
```python
if result.extracted_content:
    data = json.loads(result.extracted_content)
    print(data)
```
### 5.2 **`downloaded_files`** *(Optional[List[str]])*  
**What**: If `accept_downloads=True` in your `BrowserConfig` + `downloads_path`, lists local file paths for downloaded items.  
```python
if result.downloaded_files:
    for file_path in result.downloaded_files:
        print("Downloaded:", file_path)
```
### 5.3 **`screenshot`** *(Optional[str])*  
**What**: Base64-encoded screenshot if `screenshot=True` in `CrawlerRunConfig`.  
```python
import base64
if result.screenshot:
    with open("page.png", "wb") as f:
        f.write(base64.b64decode(result.screenshot))
```
### 5.4 **`pdf`** *(Optional[bytes])*  
**What**: Raw PDF bytes if `pdf=True` in `CrawlerRunConfig`.  
```python
if result.pdf:
    with open("page.pdf", "wb") as f:
        f.write(result.pdf)
```
### 5.5 **`mhtml`** *(Optional[str])*  
**What**: MHTML snapshot of the page if `capture_mhtml=True` in `CrawlerRunConfig`. MHTML (MIME HTML) format preserves the entire web page with all its resources (CSS, images, scripts, etc.) in a single file.  
```python
if result.mhtml:
    with open("page.mhtml", "w", encoding="utf-8") as f:
        f.write(result.mhtml)
```
### 5.6 **`metadata`** *(Optional[dict])*  
```python
if result.metadata:
    print("Title:", result.metadata.get("title"))
    print("Author:", result.metadata.get("author"))
```
## 6. `dispatch_result` (optional)
A `DispatchResult` object providing additional concurrency and resource usage information when crawling URLs in parallel (e.g., via `arun_many()` with custom dispatchers). It contains:
- **`task_id`**: A unique identifier for the parallel task.
- **`memory_usage`** (float): The memory (in MB) used at the time of completion.
- **`peak_memory`** (float): The peak memory usage (in MB) recorded during the task's execution.
- **`start_time`** / **`end_time`** (datetime): Time range for this crawling task.
- **`error_message`** (str): Any dispatcher- or concurrency-related error encountered.
```python
# Example usage:
for result in results:
    if result.success and result.dispatch_result:
        dr = result.dispatch_result
        print(f"URL: {result.url}, Task ID: {dr.task_id}")
        print(f"Memory: {dr.memory_usage:.1f} MB (Peak: {dr.peak_memory:.1f} MB)")
        print(f"Duration: {dr.end_time - dr.start_time}")
```
> **Note**: This field is typically populated when using `arun_many(...)` alongside a **dispatcher** (e.g., `MemoryAdaptiveDispatcher` or `SemaphoreDispatcher`). If no concurrency or dispatcher is used, `dispatch_result` may remain `None`. 
## 7. Network Requests & Console Messages
When you enable network and console message capturing in `CrawlerRunConfig` using `capture_network_requests=True` and `capture_console_messages=True`, the `CrawlResult` will include these fields:
### 7.1 **`network_requests`** *(Optional[List[Dict[str, Any]]])*
- Each item has an `event_type` field that can be `"request"`, `"response"`, or `"request_failed"`.
- Request events include `url`, `method`, `headers`, `post_data`, `resource_type`, and `is_navigation_request`.
- Response events include `url`, `status`, `status_text`, `headers`, and `request_timing`.
- Failed request events include `url`, `method`, `resource_type`, and `failure_text`.
- All events include a `timestamp` field.
```python
if result.network_requests:
    # Count different types of events
    requests = [r for r in result.network_requests if r.get("event_type") == "request"]
    responses = [r for r in result.network_requests if r.get("event_type") == "response"]
    failures = [r for r in result.network_requests if r.get("event_type") == "request_failed"]

    print(f"Captured {len(requests)} requests, {len(responses)} responses, and {len(failures)} failures")

    # Analyze API calls
    api_calls = [r for r in requests if "api" in r.get("url", "")]

    # Identify failed resources
    for failure in failures:
        print(f"Failed to load: {failure.get('url')} - {failure.get('failure_text')}")
```
### 7.2 **`console_messages`** *(Optional[List[Dict[str, Any]]])*
- Each item has a `type` field indicating the message type (e.g., `"log"`, `"error"`, `"warning"`, etc.).
- The `text` field contains the actual message text.
- Some messages include `location` information (URL, line, column).
- All messages include a `timestamp` field.
```python
if result.console_messages:
    # Count messages by type
    message_types = {}
    for msg in result.console_messages:
        msg_type = msg.get("type", "unknown")
        message_types[msg_type] = message_types.get(msg_type, 0) + 1

    print(f"Message type counts: {message_types}")

    # Display errors (which are usually most important)
    for msg in result.console_messages:
        if msg.get("type") == "error":
            print(f"Error: {msg.get('text')}")
```
## 8. Example: Accessing Everything
```python
async def handle_result(result: CrawlResult):
    if not result.success:
        print("Crawl error:", result.error_message)
        return

    # Basic info
    print("Crawled URL:", result.url)
    print("Status code:", result.status_code)

    # HTML
    print("Original HTML size:", len(result.html))
    print("Cleaned HTML size:", len(result.cleaned_html or ""))

    # Markdown output
    if result.markdown:
        print("Raw Markdown:", result.markdown.raw_markdown[:300])
        print("Citations Markdown:", result.markdown.markdown_with_citations[:300])
        if result.markdown.fit_markdown:
            print("Fit Markdown:", result.markdown.fit_markdown[:200])

    # Media & Links
    if "images" in result.media:
        print("Image count:", len(result.media["images"]))
    if "internal" in result.links:
        print("Internal link count:", len(result.links["internal"]))

    # Extraction strategy result
    if result.extracted_content:
        print("Structured data:", result.extracted_content)

    # Screenshot/PDF/MHTML
    if result.screenshot:
        print("Screenshot length:", len(result.screenshot))
    if result.pdf:
        print("PDF bytes length:", len(result.pdf))
    if result.mhtml:
        print("MHTML length:", len(result.mhtml))

    # Network and console capturing
    if result.network_requests:
        print(f"Network requests captured: {len(result.network_requests)}")
        # Analyze request types
        req_types = {}
        for req in result.network_requests:
            if "resource_type" in req:
                req_types[req["resource_type"]] = req_types.get(req["resource_type"], 0) + 1
        print(f"Resource types: {req_types}")

    if result.console_messages:
        print(f"Console messages captured: {len(result.console_messages)}")
        # Count by message type
        msg_types = {}
        for msg in result.console_messages:
            msg_types[msg.get("type", "unknown")] = msg_types.get(msg.get("type", "unknown"), 0) + 1
        print(f"Message types: {msg_types}")
```
## 9. Key Points & Future
1. **Deprecated legacy properties of CrawlResult**  
   - `markdown_v2` - Deprecated in v0.5. Just use `markdown`. It holds the `MarkdownGenerationResult` now!
   - `fit_markdown` and `fit_html` - Deprecated in v0.5. They can now be accessed via `MarkdownGenerationResult` in `result.markdown`. eg: `result.markdown.fit_markdown` and `result.markdown.fit_html`
2. **Fit Content**  
   - **`fit_markdown`** and **`fit_html`** appear in MarkdownGenerationResult, only if you used a content filter (like **PruningContentFilter** or **BM25ContentFilter**) inside your **MarkdownGenerationStrategy** or set them directly.  
   - If no filter is used, they remain `None`.
3. **References & Citations**  
   - If you enable link citations in your `DefaultMarkdownGenerator` (`options={"citations": True}`), you’ll see `markdown_with_citations` plus a **`references_markdown`** block. This helps large language models or academic-like referencing.
4. **Links & Media**  
   - `links["internal"]` and `links["external"]` group discovered anchors by domain.  
   - `media["images"]` / `["videos"]` / `["audios"]` store extracted media elements with optional scoring or context.
5. **Error Cases**  
   - If `success=False`, check `error_message` (e.g., timeouts, invalid URLs).  
   - `status_code` might be `None` if we failed before an HTTP response.
Use **`CrawlResult`** to glean all final outputs and feed them into your data pipelines, AI models, or archives. With the synergy of a properly configured **BrowserConfig** and **CrawlerRunConfig**, the crawler can produce robust, structured results here in **`CrawlResult`**.



# Configuration

# Browser, Crawler & LLM Configuration (Quick Overview)
Crawl4AI's flexibility stems from two key classes:
1. **`BrowserConfig`** – Dictates **how** the browser is launched and behaves (e.g., headless or visible, proxy, user agent).  
2. **`CrawlerRunConfig`** – Dictates **how** each **crawl** operates (e.g., caching, extraction, timeouts, JavaScript code to run, etc.).  
3. **`LLMConfig`** - Dictates **how** LLM providers are configured. (model, api token, base url, temperature etc.)
In most examples, you create **one** `BrowserConfig` for the entire crawler session, then pass a **fresh** or re-used `CrawlerRunConfig` whenever you call `arun()`. This tutorial shows the most commonly used parameters. If you need advanced or rarely used fields, see the [Configuration Parameters](../api/parameters.md).
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
        enable_stealth=False,
        # ... other advanced parameters omitted here
    ):
        ...
```
### Key Fields to Note
1. **`browser_type`**  
- Options: `"chromium"`, `"firefox"`, or `"webkit"`.  
- Defaults to `"chromium"`.  
- If you need a different engine, specify it here.
2. **`headless`**  
   - `True`: Runs the browser in headless mode (invisible browser).  
   - `False`: Runs the browser in visible mode, which helps with debugging.
3. **`proxy_config`**  
   - A dictionary with fields like:  
```json
{
    "server": "http://proxy.example.com:8080", 
    "username": "...", 
    "password": "..."
}
```
   - Leave as `None` if a proxy is not required.
4. **`viewport_width` & `viewport_height`**:  
   - The initial window size.  
   - Some sites behave differently with smaller or bigger viewports.
5. **`verbose`**:  
   - If `True`, prints extra logs.  
   - Handy for debugging.
6. **`use_persistent_context`**:  
   - If `True`, uses a **persistent** browser profile, storing cookies/local storage across runs.  
   - Typically also set `user_data_dir` to point to a folder.
7. **`cookies`** & **`headers`**:  
   - E.g. `cookies=[{"name": "session", "value": "abc123", "domain": "example.com"}]`.
8. **`user_agent`**:  
   - Custom User-Agent string. If `None`, a default is used.  
   - You can also set `user_agent_mode="random"` for randomization (if you want to fight bot detection).
9. **`text_mode`** & **`light_mode`**:  
   - `text_mode=True` disables images, possibly speeding up text-only crawls.  
   - `light_mode=True` turns off certain background features for performance.  
10. **`extra_args`**:  
    - Additional flags for the underlying browser.  
    - E.g. `["--disable-extensions"]`.
11. **`enable_stealth`**:  
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
```
### Key Fields to Note
1. **`word_count_threshold`**:  
   - The minimum word count before a block is considered.  
   - If your site has lots of short paragraphs or items, you can lower it.
2. **`extraction_strategy`**:  
   - Where you plug in JSON-based extraction (CSS, LLM, etc.).  
   - If `None`, no structured extraction is done (only raw/cleaned HTML + markdown).
3. **`markdown_generator`**:  
   - E.g., `DefaultMarkdownGenerator(...)`, controlling how HTML→Markdown conversion is done.  
   - If `None`, a default approach is used.
4. **`cache_mode`**:  
   - Controls caching behavior (`ENABLED`, `BYPASS`, `DISABLED`, etc.).  
   - If `None`, defaults to some level of caching or you can specify `CacheMode.ENABLED`.
5. **`js_code`**:  
   - A string or list of JS strings to execute.  
   - Great for "Load More" buttons or user interactions.  
6. **`wait_for`**:  
   - A CSS or JS expression to wait for before extracting content.  
   - Common usage: `wait_for="css:.main-loaded"` or `wait_for="js:() => window.loaded === true"`.
7. **`screenshot`**, **`pdf`**, & **`capture_mhtml`**:  
   - If `True`, captures a screenshot, PDF, or MHTML snapshot after the page is fully loaded.  
   - The results go to `result.screenshot` (base64), `result.pdf` (bytes), or `result.mhtml` (string).
8. **Location Parameters**:  
   - **`locale`**: Browser's locale (e.g., `"en-US"`, `"fr-FR"`) for language preferences
   - **`timezone_id`**: Browser's timezone (e.g., `"America/New_York"`, `"Europe/Paris"`)
   - **`geolocation`**: GPS coordinates via `GeolocationConfig(latitude=48.8566, longitude=2.3522)`
9. **`verbose`**:  
   - Logs additional runtime details.  
   - Overlaps with the browser's verbosity if also set to `True` in `BrowserConfig`.
10. **`enable_rate_limiting`**:  
   - If `True`, enables rate limiting for batch processing.  
   - Requires `rate_limit_config` to be set.
11. **`memory_threshold_percent`**:  
    - The memory threshold (as a percentage) to monitor.  
    - If exceeded, the crawler will pause or slow down.
12. **`check_interval`**:  
    - The interval (in seconds) to check system resources.  
    - Affects how often memory and CPU usage are monitored.
13. **`max_session_permit`**:  
    - The maximum number of concurrent crawl sessions.  
    - Helps prevent overwhelming the system.
14. **`url_matcher`** & **`match_mode`**:  
    - Enable URL-specific configurations when used with `arun_many()`.
    - Set `url_matcher` to patterns (glob, function, or list) to match specific URLs.
    - Use `match_mode` (OR/AND) to control how multiple patterns combine.
15. **`display_mode`**:  
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
## 3. LLMConfig Essentials
### Key fields to note
1. **`provider`**:  
- Which LLM provider to use. 
- Possible values are `"ollama/llama3","groq/llama3-70b-8192","groq/llama3-8b-8192", "openai/gpt-4o-mini" ,"openai/gpt-4o","openai/o1-mini","openai/o1-preview","openai/o3-mini","openai/o3-mini-high","anthropic/claude-3-haiku-20240307","anthropic/claude-3-opus-20240229","anthropic/claude-3-sonnet-20240229","anthropic/claude-3-5-sonnet-20240620","gemini/gemini-pro","gemini/gemini-1.5-pro","gemini/gemini-2.0-flash","gemini/gemini-2.0-flash-exp","gemini/gemini-2.0-flash-lite-preview-02-05","deepseek/deepseek-chat"`<br/>*(default: `"openai/gpt-4o-mini"`)*
2. **`api_token`**:  
    - Optional. When not provided explicitly, api_token will be read from environment variables based on provider. For example: If a gemini model is passed as provider then,`"GEMINI_API_KEY"` will be read from environment variables  
    - API token of LLM provider <br/> eg: `api_token = "gsk_1ClHGGJ7Lpn4WGybR7vNWGdyb3FY7zXEw3SCiy0BAVM9lL8CQv"`
    - Environment variable - use with prefix "env:" <br/> eg:`api_token = "env: GROQ_API_KEY"`            
3. **`base_url`**:  
   - If your provider has a custom endpoint
```python
llm_config = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))
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
## 5. Next Steps
- [BrowserConfig, CrawlerRunConfig & LLMConfig Reference](../api/parameters.md)  
- **Custom Hooks & Auth** (Inject JavaScript or handle login forms).  
- **Session Management** (Re-use pages, preserve state across multiple calls).  
- **Advanced Caching** (Fine-tune read/write cache modes).  
## 6. Conclusion


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
| **`proxy`**           | `str` (deprecated)                      | Deprecated. Use `proxy_config` instead. If set, it will be auto-converted internally. |
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
| **`use_managed_browser`** | `bool` (default: `False`)          | For advanced “managed” interactions (debugging, CDP usage). Typically set automatically if persistent context is on.                  |
| **`extra_args`**      | `list` (default: `[]`)                 | Additional flags for the underlying browser process, e.g. `["--disable-extensions"]`.                                                |
- Set `headless=False` to visually **debug** how pages load or how interactions proceed.  
- If you need **authentication** storage or repeated sessions, consider `use_persistent_context=True` and specify `user_data_dir`.  
- For large pages, you might need a bigger `viewport_width` and `viewport_height` to handle dynamic content.
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
### B) **Caching & Session**
| **Parameter**           | **Type / Default**     | **What It Does**                                                                                                              |
|-------------------------|------------------------|------------------------------------------------------------------------------------------------------------------------------|
| **`cache_mode`**        | `CacheMode or None`    | Controls how caching is handled (`ENABLED`, `BYPASS`, `DISABLED`, etc.). If `None`, typically defaults to `ENABLED`.          |
| **`session_id`**        | `str or None`          | Assign a unique ID to reuse a single browser session across multiple `arun()` calls.                                          |
| **`bypass_cache`**      | `bool` (False)         | If `True`, acts like `CacheMode.BYPASS`.                                                                                     |
| **`disable_cache`**     | `bool` (False)         | If `True`, acts like `CacheMode.DISABLED`.                                                                                   |
| **`no_cache_read`**     | `bool` (False)         | If `True`, acts like `CacheMode.WRITE_ONLY` (writes cache but never reads).                                                  |
| **`no_cache_write`**    | `bool` (False)         | If `True`, acts like `CacheMode.READ_ONLY` (reads cache but never writes).                                                   |
### C) **Page Navigation & Timing**
| **Parameter**              | **Type / Default**      | **What It Does**                                                                                                    |
|----------------------------|-------------------------|----------------------------------------------------------------------------------------------------------------------|
| **`wait_until`**           | `str` (domcontentloaded)| Condition for navigation to “complete”. Often `"networkidle"` or `"domcontentloaded"`.                               |
| **`page_timeout`**         | `int` (60000 ms)        | Timeout for page navigation or JS steps. Increase for slow sites.                                                    |
| **`wait_for`**             | `str or None`           | Wait for a CSS (`"css:selector"`) or JS (`"js:() => bool"`) condition before content extraction.                     |
| **`wait_for_images`**      | `bool` (False)          | Wait for images to load before finishing. Slows down if you only want text.                                          |
| **`delay_before_return_html`** | `float` (0.1)       | Additional pause (seconds) before final HTML is captured. Good for last-second updates.                               |
| **`check_robots_txt`**     | `bool` (False)          | Whether to check and respect robots.txt rules before crawling. If True, caches robots.txt for efficiency.            |
| **`mean_delay`** and **`max_range`** | `float` (0.1, 0.3) | If you call `arun_many()`, these define random delay intervals between crawls, helping avoid detection or rate limits. |
| **`semaphore_count`**      | `int` (5)               | Max concurrency for `arun_many()`. Increase if you have resources for parallel crawls.                                |
### D) **Page Interaction**
| **Parameter**              | **Type / Default**            | **What It Does**                                                                                                                       |
|----------------------------|--------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| **`js_code`**              | `str or list[str]` (None)      | JavaScript to run after load. E.g. `"document.querySelector('button')?.click();"`.                                                     |
| **`js_only`**              | `bool` (False)                 | If `True`, indicates we’re reusing an existing session and only applying JS. No full reload.                                           |
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
### E) **Media Handling**
| **Parameter**                              | **Type / Default**  | **What It Does**                                                                                         |
|--------------------------------------------|---------------------|-----------------------------------------------------------------------------------------------------------|
| **`screenshot`**                           | `bool` (False)      | Capture a screenshot (base64) in `result.screenshot`.                                                     |
| **`screenshot_wait_for`**                  | `float or None`     | Extra wait time before the screenshot.                                                                    |
| **`screenshot_height_threshold`**          | `int` (~20000)      | If the page is taller than this, alternate screenshot strategies are used.                                |
| **`pdf`**                                  | `bool` (False)      | If `True`, returns a PDF in `result.pdf`.                                                                 |
| **`capture_mhtml`**                        | `bool` (False)      | If `True`, captures an MHTML snapshot of the page in `result.mhtml`. MHTML includes all page resources (CSS, images, etc.) in a single file. |
| **`image_description_min_word_threshold`** | `int` (~50)         | Minimum words for an image’s alt text or description to be considered valid.                              |
| **`image_score_threshold`**                | `int` (~3)          | Filter out low-scoring images. The crawler scores images by relevance (size, context, etc.).              |
| **`exclude_external_images`**              | `bool` (False)      | Exclude images from other domains.                                                                        |
### F) **Link/Domain Handling**
| **Parameter**                | **Type / Default**      | **What It Does**                                                                                                             |
|------------------------------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| **`exclude_social_media_domains`** | `list` (e.g. Facebook/Twitter) | A default list can be extended. Any link to these domains is removed from final output.                                      |
| **`exclude_external_links`** | `bool` (False)          | Removes all links pointing outside the current domain.                                                                      |
| **`exclude_social_media_links`** | `bool` (False)      | Strips links specifically to social sites (like Facebook or Twitter).                                                      |
| **`exclude_domains`**        | `list` ([])             | Provide a custom list of domains to exclude (like `["ads.com", "trackers.io"]`).                                            |
| **`preserve_https_for_internal_links`** | `bool` (False) | If `True`, preserves HTTPS scheme for internal links even when the server redirects to HTTP. Useful for security-conscious crawling. |
### G) **Debug & Logging**
| **Parameter**  | **Type / Default** | **What It Does**                                                         |
|----------------|--------------------|---------------------------------------------------------------------------|
| **`verbose`**  | `bool` (True)     | Prints logs detailing each step of crawling, interactions, or errors.    |
| **`log_console`** | `bool` (False) | Logs the page’s JavaScript console output if you want deeper JS debugging.|
### H) **Virtual Scroll Configuration**
| **Parameter**                | **Type / Default**           | **What It Does**                                                                                                                    |
|------------------------------|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| **`virtual_scroll_config`**  | `VirtualScrollConfig or dict` (None) | Configuration for handling virtualized scrolling on sites like Twitter/Instagram where content is replaced rather than appended. |
When sites use virtual scrolling (content replaced as you scroll), use `VirtualScrollConfig`:
```python
from crawl4ai import VirtualScrollConfig

virtual_config = VirtualScrollConfig(
    container_selector="#timeline",    # CSS selector for scrollable container
    scroll_count=30,                   # Number of times to scroll
    scroll_by="container_height",      # How much to scroll: "container_height", "page_height", or pixels (e.g. 500)
    wait_after_scroll=0.5             # Seconds to wait after each scroll for content to load
)

config = CrawlerRunConfig(
    virtual_scroll_config=virtual_config
)
```
**VirtualScrollConfig Parameters:**
| **Parameter**          | **Type / Default**        | **What It Does**                                                                          |
|------------------------|---------------------------|-------------------------------------------------------------------------------------------|
| **`container_selector`** | `str` (required)        | CSS selector for the scrollable container (e.g., `"#feed"`, `".timeline"`)              |
| **`scroll_count`**     | `int` (10)               | Maximum number of scrolls to perform                                                      |
| **`scroll_by`**        | `str or int` ("container_height") | Scroll amount: `"container_height"`, `"page_height"`, or pixels (e.g., `500`)   |
| **`wait_after_scroll`** | `float` (0.5)           | Time in seconds to wait after each scroll for new content to load                        |
- Use `virtual_scroll_config` when content is **replaced** during scroll (Twitter, Instagram)
- Use `scan_full_page` when content is **appended** during scroll (traditional infinite scroll)
### I) **URL Matching Configuration**
| **Parameter**          | **Type / Default**           | **What It Does**                                                                                                                    |
|------------------------|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| **`url_matcher`**      | `UrlMatcher` (None)          | Pattern(s) to match URLs against. Can be: string (glob), function, or list of mixed types. **None means match ALL URLs**         |
| **`match_mode`**       | `MatchMode` (MatchMode.OR)   | How to combine multiple matchers in a list: `MatchMode.OR` (any match) or `MatchMode.AND` (all must match)                       |
The `url_matcher` parameter enables URL-specific configurations when used with `arun_many()`:
```python
from crawl4ai import CrawlerRunConfig, MatchMode
from crawl4ai.processors.pdf import PDFContentScrapingStrategy
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Simple string pattern (glob-style)
pdf_config = CrawlerRunConfig(
    url_matcher="*.pdf",
    scraping_strategy=PDFContentScrapingStrategy()
)

# Multiple patterns with OR logic (default)
blog_config = CrawlerRunConfig(
    url_matcher=["*/blog/*", "*/article/*", "*/news/*"],
    match_mode=MatchMode.OR  # Any pattern matches
)

# Function matcher
api_config = CrawlerRunConfig(
    url_matcher=lambda url: 'api' in url or url.endswith('.json'),
    # Other settings like extraction_strategy
)

# Mixed: String + Function with AND logic
complex_config = CrawlerRunConfig(
    url_matcher=[
        lambda url: url.startswith('https://'),  # Must be HTTPS
        "*.org/*",                               # Must be .org domain
        lambda url: 'docs' in url                # Must contain 'docs'
    ],
    match_mode=MatchMode.AND  # ALL conditions must match
)

# Combined patterns and functions with AND logic
secure_docs = CrawlerRunConfig(
    url_matcher=["https://*", lambda url: '.doc' in url],
    match_mode=MatchMode.AND  # Must be HTTPS AND contain .doc
)

# Default config - matches ALL URLs
default_config = CrawlerRunConfig()  # No url_matcher = matches everything
```
**UrlMatcher Types:**
- **None (default)**: When `url_matcher` is None or not set, the config matches ALL URLs
- **String patterns**: Glob-style patterns like `"*.pdf"`, `"*/api/*"`, `"https://*.example.com/*"`
- **Functions**: `lambda url: bool` - Custom logic for complex matching
- **Lists**: Mix strings and functions, combined with `MatchMode.OR` or `MatchMode.AND`
**Important Behavior:**
- When passing a list of configs to `arun_many()`, URLs are matched against each config's `url_matcher` in order. First match wins!
- If no config matches a URL and there's no default config (one without `url_matcher`), the URL will fail with "No matching configuration found"
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
1. LLMExtractionStrategy
2. LLMContentFilter
3. JsonCssExtractionStrategy.generate_schema
4. JsonXPathExtractionStrategy.generate_schema
## 3.1 Parameters
| **Parameter**         | **Type / Default**                     | **What It Does**                                                                                                                     |
|-----------------------|----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| **`provider`**    | `"ollama/llama3","groq/llama3-70b-8192","groq/llama3-8b-8192", "openai/gpt-4o-mini" ,"openai/gpt-4o","openai/o1-mini","openai/o1-preview","openai/o3-mini","openai/o3-mini-high","anthropic/claude-3-haiku-20240307","anthropic/claude-3-opus-20240229","anthropic/claude-3-sonnet-20240229","anthropic/claude-3-5-sonnet-20240620","gemini/gemini-pro","gemini/gemini-1.5-pro","gemini/gemini-2.0-flash","gemini/gemini-2.0-flash-exp","gemini/gemini-2.0-flash-lite-preview-02-05","deepseek/deepseek-chat"`<br/>*(default: `"openai/gpt-4o-mini"`)* | Which LLM provider to use. 
| **`api_token`**         |1.Optional. When not provided explicitly, api_token will be read from environment variables based on provider. For example: If a gemini model is passed as provider then,`"GEMINI_API_KEY"` will be read from environment variables  <br/> 2. API token of LLM provider <br/> eg: `api_token = "gsk_1ClHGGJ7Lpn4WGybR7vNWGdyb3FY7zXEw3SCiy0BAVM9lL8CQv"` <br/> 3. Environment variable - use with prefix "env:" <br/> eg:`api_token = "env: GROQ_API_KEY"`              | API token to use for the given provider 
| **`base_url`**         |Optional. Custom API endpoint | If your provider has a custom endpoint
## 3.2 Example Usage
```python
llm_config = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))
```
## 4. Putting It All Together
- **Use** `BrowserConfig` for **global** browser settings: engine, headless, proxy, user agent.  
- **Use** `CrawlerRunConfig` for each crawl’s **context**: how to filter content, handle caching, wait for dynamic elements, or run JS.  
- **Pass** both configs to `AsyncWebCrawler` (the `BrowserConfig`) and then to `arun()` (the `CrawlerRunConfig`).  
- **Use** `LLMConfig` for LLM provider configurations that can be used across all extraction, filtering, schema generation tasks. Can be used in - `LLMExtractionStrategy`, `LLMContentFilter`, `JsonCssExtractionStrategy.generate_schema` & `JsonXPathExtractionStrategy.generate_schema`
```python
# Create a modified copy with the clone() method
stream_cfg = run_cfg.clone(
    stream=True,
    cache_mode=CacheMode.BYPASS
)
```



# Crawling Patterns

# Simple Crawling
## Basic Usage
Set up a simple crawl using `BrowserConfig` and `CrawlerRunConfig`:
```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def main():
    browser_config = BrowserConfig()  # Default browser configuration
    run_config = CrawlerRunConfig()   # Default crawl run configuration

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )
        print(result.markdown)  # Print clean markdown content

if __name__ == "__main__":
    asyncio.run(main())
```
## Understanding the Response
The `arun()` method returns a `CrawlResult` object with several useful properties. Here's a quick overview (see [CrawlResult](../api/crawl-result.md) for complete details):
```python
config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.6),
        options={"ignore_links": True}
    )
)

result = await crawler.arun(
    url="https://example.com",
    config=config
)

# Different content formats
print(result.html)         # Raw HTML
print(result.cleaned_html) # Cleaned HTML
print(result.markdown.raw_markdown) # Raw markdown from cleaned html
print(result.markdown.fit_markdown) # Most relevant content in markdown

# Check success status
print(result.success)      # True if crawl succeeded
print(result.status_code)  # HTTP status code (e.g., 200, 404)

# Access extracted media and links
print(result.media)        # Dictionary of found media (images, videos, audio)
print(result.links)        # Dictionary of internal and external links
```
## Adding Basic Options
Customize your crawl using `CrawlerRunConfig`:
```python
run_config = CrawlerRunConfig(
    word_count_threshold=10,        # Minimum words per content block
    exclude_external_links=True,    # Remove external links
    remove_overlay_elements=True,   # Remove popups/modals
    process_iframes=True           # Process iframe content
)

result = await crawler.arun(
    url="https://example.com",
    config=run_config
)
```
## Handling Errors
```python
run_config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=run_config)

if not result.success:
    print(f"Crawl failed: {result.error_message}")
    print(f"Status code: {result.status_code}")
```
## Logging and Debugging
Enable verbose logging in `BrowserConfig`:
```python
browser_config = BrowserConfig(verbose=True)

async with AsyncWebCrawler(config=browser_config) as crawler:
    run_config = CrawlerRunConfig()
    result = await crawler.arun(url="https://example.com", config=run_config)
```
## Complete Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        # Content filtering
        word_count_threshold=10,
        excluded_tags=['form', 'header'],
        exclude_external_links=True,

        # Content processing
        process_iframes=True,
        remove_overlay_elements=True,

        # Cache control
        cache_mode=CacheMode.ENABLED  # Use cache if available
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )

        if result.success:
            # Print clean content
            print("Content:", result.markdown[:500])  # First 500 chars

            # Process images
            for image in result.media["images"]:
                print(f"Found image: {image['src']}")

            # Process links
            for link in result.links["internal"]:
                print(f"Internal link: {link['href']}")

        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
```



# Content Processing

# Markdown Generation Basics
1. How to configure the **Default Markdown Generator**  
3. The difference between raw markdown (`result.markdown`) and filtered markdown (`fit_markdown`)  
> - You know how to configure `CrawlerRunConfig`.
## 1. Quick Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator()
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)

        if result.success:
            print("Raw Markdown Output:\n")
            print(result.markdown)  # The unfiltered markdown from the page
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```
- `CrawlerRunConfig( markdown_generator = DefaultMarkdownGenerator() )` instructs Crawl4AI to convert the final HTML into markdown at the end of each crawl.  
- The resulting markdown is accessible via `result.markdown`.
## 2. How Markdown Generation Works
### 2.1 HTML-to-Text Conversion (Forked & Modified)
- Preserves headings, code blocks, bullet points, etc.  
- Removes extraneous tags (scripts, styles) that don’t add meaningful content.  
- Can optionally generate references for links or skip them altogether.
### 2.2 Link Citations & References
By default, the generator can convert `<a href="...">` elements into `[text][1]` citations, then place the actual links at the bottom of the document. This is handy for research workflows that demand references in a structured manner.
### 2.3 Optional Content Filters
## 3. Configuring the Default Markdown Generator
You can tweak the output by passing an `options` dict to `DefaultMarkdownGenerator`. For example:
```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Example: ignore all links, don't escape HTML, and wrap text at 80 characters
    md_generator = DefaultMarkdownGenerator(
        options={
            "ignore_links": True,
            "escape_html": False,
            "body_width": 80
        }
    )

    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com/docs", config=config)
        if result.success:
            print("Markdown:\n", result.markdown[:500])  # Just a snippet
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```
Some commonly used `options`:
- **`ignore_links`** (bool): Whether to remove all hyperlinks in the final markdown.  
- **`ignore_images`** (bool): Remove all `![image]()` references.  
- **`escape_html`** (bool): Turn HTML entities into text (default is often `True`).  
- **`body_width`** (int): Wrap text at N characters. `0` or `None` means no wrapping.  
- **`skip_internal_links`** (bool): If `True`, omit `#localAnchors` or internal links referencing the same page.  
- **`include_sup_sub`** (bool): Attempt to handle `<sup>` / `<sub>` in a more readable way.
## 4. Selecting the HTML Source for Markdown Generation
The `content_source` parameter allows you to control which HTML content is used as input for markdown generation. This gives you flexibility in how the HTML is processed before conversion to markdown.
```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Option 1: Use the raw HTML directly from the webpage (before any processing)
    raw_md_generator = DefaultMarkdownGenerator(
        content_source="raw_html",
        options={"ignore_links": True}
    )

    # Option 2: Use the cleaned HTML (after scraping strategy processing - default)
    cleaned_md_generator = DefaultMarkdownGenerator(
        content_source="cleaned_html",  # This is the default
        options={"ignore_links": True}
    )

    # Option 3: Use preprocessed HTML optimized for schema extraction
    fit_md_generator = DefaultMarkdownGenerator(
        content_source="fit_html",
        options={"ignore_links": True}
    )

    # Use one of the generators in your crawler config
    config = CrawlerRunConfig(
        markdown_generator=raw_md_generator  # Try each of the generators
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)
        if result.success:
            print("Markdown:\n", result.markdown.raw_markdown[:500])
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```
### HTML Source Options
- **`"cleaned_html"`** (default): Uses the HTML after it has been processed by the scraping strategy. This HTML is typically cleaner and more focused on content, with some boilerplate removed.
- **`"raw_html"`**: Uses the original HTML directly from the webpage, before any cleaning or processing. This preserves more of the original content, but may include navigation bars, ads, footers, and other elements that might not be relevant to the main content.
- **`"fit_html"`**: Uses HTML preprocessed for schema extraction. This HTML is optimized for structured data extraction and may have certain elements simplified or removed.
### When to Use Each Option
- Use **`"cleaned_html"`** (default) for most cases where you want a balance of content preservation and noise removal.
- Use **`"raw_html"`** when you need to preserve all original content, or when the cleaning process is removing content you actually want to keep.
- Use **`"fit_html"`** when working with structured data or when you need HTML that's optimized for schema extraction.
## 5. Content Filters
### 5.1 BM25ContentFilter
```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai import CrawlerRunConfig

bm25_filter = BM25ContentFilter(
    user_query="machine learning",
    bm25_threshold=1.2,
    language="english"
)

md_generator = DefaultMarkdownGenerator(
    content_filter=bm25_filter,
    options={"ignore_links": True}
)

config = CrawlerRunConfig(markdown_generator=md_generator)
```
- **`user_query`**: The term you want to focus on. BM25 tries to keep only content blocks relevant to that query.  
- **`bm25_threshold`**: Raise it to keep fewer blocks; lower it to keep more.  
- **`use_stemming`** *(default `True`)*: Whether to apply stemming to the query and content.
- **`language (str)`**: Language for stemming (default: 'english').
### 5.2 PruningContentFilter
If you **don’t** have a specific query, or if you just want a robust “junk remover,” use `PruningContentFilter`. It analyzes text density, link density, HTML structure, and known patterns (like “nav,” “footer”) to systematically prune extraneous or repetitive sections.
```python
from crawl4ai.content_filter_strategy import PruningContentFilter

prune_filter = PruningContentFilter(
    threshold=0.5,
    threshold_type="fixed",  # or "dynamic"
    min_word_threshold=50
)
```
- **`threshold`**: Score boundary. Blocks below this score get removed.  
- **`threshold_type`**:  
    - `"fixed"`: Straight comparison (`score >= threshold` keeps the block).  
    - `"dynamic"`: The filter adjusts threshold in a data-driven manner.  
- **`min_word_threshold`**: Discard blocks under N words as likely too short or unhelpful.
- You want a broad cleanup without a user query.  
### 5.3 LLMContentFilter
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMConfig, DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import LLMContentFilter

async def main():
    # Initialize LLM filter with specific instruction
    filter = LLMContentFilter(
        llm_config = LLMConfig(provider="openai/gpt-4o",api_token="your-api-token"), #or use environment variable
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
        chunk_token_threshold=4096,  # Adjust based on your needs
        verbose=True
    )
    md_generator = DefaultMarkdownGenerator(
        content_filter=filter,
        options={"ignore_links": True}
    )
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)
        print(result.markdown.fit_markdown)  # Filtered markdown content
```
- **Chunk Processing**: Handles large documents by processing them in chunks (controlled by `chunk_token_threshold`)
- **Parallel Processing**: For better performance, use smaller `chunk_token_threshold` (e.g., 2048 or 4096) to enable parallel processing of content chunks
1. **Exact Content Preservation**:
```python
filter = LLMContentFilter(
    instruction="""
    Extract the main educational content while preserving its original wording and substance completely.
    1. Maintain the exact language and terminology
    2. Keep all technical explanations and examples intact
    3. Preserve the original flow and structure
    4. Remove only clearly irrelevant elements like navigation menus and ads
    """,
    chunk_token_threshold=4096
)
```
2. **Focused Content Extraction**:
```python
filter = LLMContentFilter(
    instruction="""
    Focus on extracting specific types of content:
    - Technical documentation
    - Code examples
    - API references
    Reformat the content into clear, well-structured markdown
    """,
    chunk_token_threshold=4096
)
```
> **Performance Tip**: Set a smaller `chunk_token_threshold` (e.g., 2048 or 4096) to enable parallel processing of content chunks. The default value is infinity, which processes the entire content as a single chunk.
## 6. Using Fit Markdown
When a content filter is active, the library produces two forms of markdown inside `result.markdown`:
1. **`raw_markdown`**: The full unfiltered markdown.  
2. **`fit_markdown`**: A “fit” version where the filter has removed or trimmed noisy segments.
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

async def main():
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.6),
            options={"ignore_links": True}
        )
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://news.example.com/tech", config=config)
        if result.success:
            print("Raw markdown:\n", result.markdown)

            # If a filter is used, we also have .fit_markdown:
            md_object = result.markdown  # or your equivalent
            print("Filtered markdown:\n", md_object.fit_markdown)
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```
## 7. The `MarkdownGenerationResult` Object
If your library stores detailed markdown output in an object like `MarkdownGenerationResult`, you’ll see fields such as:
- **`raw_markdown`**: The direct HTML-to-markdown transformation (no filtering).  
- **`markdown_with_citations`**: A version that moves links to reference-style footnotes.  
- **`references_markdown`**: A separate string or section containing the gathered references.  
- **`fit_markdown`**: The filtered markdown if you used a content filter.  
- **`fit_html`**: The corresponding HTML snippet used to generate `fit_markdown` (helpful for debugging or advanced usage).
```python
md_obj = result.markdown  # your library’s naming may vary
print("RAW:\n", md_obj.raw_markdown)
print("CITED:\n", md_obj.markdown_with_citations)
print("REFERENCES:\n", md_obj.references_markdown)
print("FIT:\n", md_obj.fit_markdown)
```
- You can supply `raw_markdown` to an LLM if you want the entire text.  
- Or feed `fit_markdown` into a vector database to reduce token usage.  
- `references_markdown` can help you keep track of link provenance.
## 8. Combining Filters (BM25 + Pruning) in Two Passes
You might want to **prune out** noisy boilerplate first (with `PruningContentFilter`), and then **rank what’s left** against a user query (with `BM25ContentFilter`). You don’t have to crawl the page twice. Instead:
1. **First pass**: Apply `PruningContentFilter` directly to the raw HTML from `result.html` (the crawler’s downloaded HTML).  
2. **Second pass**: Take the pruned HTML (or text) from step 1, and feed it into `BM25ContentFilter`, focusing on a user query.
### Two-Pass Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from bs4 import BeautifulSoup

async def main():
    # 1. Crawl with minimal or no markdown generator, just get raw HTML
    config = CrawlerRunConfig(
        # If you only want raw HTML, you can skip passing a markdown_generator
        # or provide one but focus on .html in this example
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com/tech-article", config=config)

        if not result.success or not result.html:
            print("Crawl failed or no HTML content.")
            return

        raw_html = result.html

        # 2. First pass: PruningContentFilter on raw HTML
        pruning_filter = PruningContentFilter(threshold=0.5, min_word_threshold=50)

        # filter_content returns a list of "text chunks" or cleaned HTML sections
        pruned_chunks = pruning_filter.filter_content(raw_html)
        # This list is basically pruned content blocks, presumably in HTML or text form

        # For demonstration, let's combine these chunks back into a single HTML-like string
        # or you could do further processing. It's up to your pipeline design.
        pruned_html = "\n".join(pruned_chunks)

        # 3. Second pass: BM25ContentFilter with a user query
        bm25_filter = BM25ContentFilter(
            user_query="machine learning",
            bm25_threshold=1.2,
            language="english"
        )

        # returns a list of text chunks
        bm25_chunks = bm25_filter.filter_content(pruned_html)  

        if not bm25_chunks:
            print("Nothing matched the BM25 query after pruning.")
            return

        # 4. Combine or display final results
        final_text = "\n---\n".join(bm25_chunks)

        print("==== PRUNED OUTPUT (first pass) ====")
        print(pruned_html[:500], "... (truncated)")  # preview

        print("\n==== BM25 OUTPUT (second pass) ====")
        print(final_text[:500], "... (truncated)")

if __name__ == "__main__":
    asyncio.run(main())
```
### What’s Happening?
1. **Raw HTML**: We crawl once and store the raw HTML in `result.html`.  
4. **BM25ContentFilter**: We feed the pruned string into `BM25ContentFilter` with a user query. This second pass further narrows the content to chunks relevant to “machine learning.”
**No Re-Crawling**: We used `raw_html` from the first pass, so there’s no need to run `arun()` again—**no second network request**.
### Tips & Variations
- **Plain Text vs. HTML**: If your pruned output is mostly text, BM25 can still handle it; just keep in mind it expects a valid string input. If you supply partial HTML (like `"<p>some text</p>"`), it will parse it as HTML.  
- **Adjust Thresholds**: If you see too much or too little text in step one, tweak `threshold=0.5` or `min_word_threshold=50`. Similarly, `bm25_threshold=1.2` can be raised/lowered for more or fewer chunks in step two.
### One-Pass Combination?
## 9. Common Pitfalls & Tips
1. **No Markdown Output?**  
2. **Performance Considerations**  
   - Very large pages with multiple filters can be slower. Consider `cache_mode` to avoid re-downloading.  
3. **Take Advantage of `fit_markdown`**  
4. **Adjusting `html2text` Options**  
   - If you see lots of raw HTML slipping into the text, turn on `escape_html`.  
   - If code blocks look messy, experiment with `mark_code` or `handle_code_in_pre`.
## 10. Summary & Next Steps
- Configure the **DefaultMarkdownGenerator** with HTML-to-text options.  
- Select different HTML sources using the `content_source` parameter.  
- Distinguish between raw and filtered markdown (`fit_markdown`).  
- Leverage the `MarkdownGenerationResult` object to handle different forms of output (citations, references, etc.).


# Fit Markdown with Pruning & BM25
## 1. How “Fit Markdown” Works
### 1.1 The `content_filter`
In **`CrawlerRunConfig`**, you can specify a **`content_filter`** to shape how content is pruned or ranked before final markdown generation. A filter’s logic is applied **before** or **during** the HTML→Markdown process, producing:
- **`result.markdown.raw_markdown`** (unfiltered)
- **`result.markdown.fit_markdown`** (filtered or “fit” version)
- **`result.markdown.fit_html`** (the corresponding HTML snippet that produced `fit_markdown`)
### 1.2 Common Filters
## 2. PruningContentFilter
### 2.1 Usage Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    # Step 1: Create a pruning filter
    prune_filter = PruningContentFilter(
        # Lower → more content retained, higher → more content pruned
        threshold=0.45,           
        # "fixed" or "dynamic"
        threshold_type="dynamic",  
        # Ignore nodes with <5 words
        min_word_threshold=5      
    )

    # Step 2: Insert it into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    # Step 3: Pass it to CrawlerRunConfig
    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com", 
            config=config
        )

        if result.success:
            # 'fit_markdown' is your pruned content, focusing on "denser" text
            print("Raw Markdown length:", len(result.markdown.raw_markdown))
            print("Fit Markdown length:", len(result.markdown.fit_markdown))
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```
### 2.2 Key Parameters
- **`min_word_threshold`** (int): If a block has fewer words than this, it’s pruned.  
- **`threshold_type`** (str):
  - `"fixed"` → each node must exceed `threshold` (0–1).  
  - `"dynamic"` → node scoring adjusts according to tag type, text/link density, etc.  
- **`threshold`** (float, default ~0.48): The base or “anchor” cutoff.  
- **Link density** – Penalizes sections that are mostly links.  
- **Tag importance** – e.g., an `<article>` or `<p>` might be more important than a `<div>`.  
## 3. BM25ContentFilter
### 3.1 Usage Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    # 1) A BM25 filter with a user query
    bm25_filter = BM25ContentFilter(
        user_query="startup fundraising tips",
        # Adjust for stricter or looser results
        bm25_threshold=1.2  
    )

    # 2) Insert into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)

    # 3) Pass to crawler config
    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com", 
            config=config
        )
        if result.success:
            print("Fit Markdown (BM25 query-based):")
            print(result.markdown.fit_markdown)
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```
### 3.2 Parameters
- **`user_query`** (str, optional): E.g. `"machine learning"`. If blank, the filter tries to glean a query from page metadata.  
- **`bm25_threshold`** (float, default 1.0):  
  - Higher → fewer chunks but more relevant.  
  - Lower → more inclusive.  
> In more advanced scenarios, you might see parameters like `language`, `case_sensitive`, or `priority_tags` to refine how text is tokenized or weighted.
## 4. Accessing the “Fit” Output
After the crawl, your “fit” content is found in **`result.markdown.fit_markdown`**. 
```python
fit_md = result.markdown.fit_markdown
fit_html = result.markdown.fit_html
```
If the content filter is **BM25**, you might see additional logic or references in `fit_markdown` that highlight relevant segments. If it’s **Pruning**, the text is typically well-cleaned but not necessarily matched to a query.
## 5. Code Patterns Recap
### 5.1 Pruning
```python
prune_filter = PruningContentFilter(
    threshold=0.5,
    threshold_type="fixed",
    min_word_threshold=10
)
md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
config = CrawlerRunConfig(markdown_generator=md_generator)
```
### 5.2 BM25
```python
bm25_filter = BM25ContentFilter(
    user_query="health benefits fruit",
    bm25_threshold=1.2
)
md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)
config = CrawlerRunConfig(markdown_generator=md_generator)
```
## 6. Combining with “word_count_threshold” & Exclusions
```python
config = CrawlerRunConfig(
    word_count_threshold=10,
    excluded_tags=["nav", "footer", "header"],
    exclude_external_links=True,
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.5)
    )
)
```
1. The crawler’s `excluded_tags` are removed from the HTML first.  
3. The final “fit” content is generated in `result.markdown.fit_markdown`.
## 7. Custom Filters
If you need a different approach (like a specialized ML model or site-specific heuristics), you can create a new class inheriting from `RelevantContentFilter` and implement `filter_content(html)`. Then inject it into your **markdown generator**:
```python
from crawl4ai.content_filter_strategy import RelevantContentFilter

class MyCustomFilter(RelevantContentFilter):
    def filter_content(self, html, min_word_threshold=None):
        # parse HTML, implement custom logic
        return [block for block in ... if ... some condition...]

```
1. Subclass `RelevantContentFilter`.  
2. Implement `filter_content(...)`.  
3. Use it in your `DefaultMarkdownGenerator(content_filter=MyCustomFilter(...))`.
## 8. Final Thoughts
- **Summaries**: Quickly get the important text from a cluttered page.  
- **Search**: Combine with **BM25** to produce content relevant to a query.  
- **BM25ContentFilter**: Perfect for query-based extraction or searching.  
- Combine with **`excluded_tags`, `exclude_external_links`, `word_count_threshold`** to refine your final “fit” text.  
- Fit markdown ends up in **`result.markdown.fit_markdown`**; eventually **`result.markdown.fit_markdown`** in future versions.
- Last Updated: 2025-01-01


# Content Selection
Crawl4AI provides multiple ways to **select**, **filter**, and **refine** the content from your crawls. Whether you need to target a specific CSS region, exclude entire tags, filter out external links, or remove certain domains and images, **`CrawlerRunConfig`** offers a wide range of parameters.
## 1. CSS-Based Selection
There are two ways to select content from a page: using `css_selector` or the more flexible `target_elements`.
### 1.1 Using `css_selector`
A straightforward way to **limit** your crawl results to a certain region of the page is **`css_selector`** in **`CrawlerRunConfig`**:
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        # e.g., first 30 items from Hacker News
        css_selector=".athing:nth-child(-n+30)"  
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com/newest", 
            config=config
        )
        print("Partial HTML length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
```
**Result**: Only elements matching that selector remain in `result.cleaned_html`.
### 1.2 Using `target_elements`
The `target_elements` parameter provides more flexibility by allowing you to target **multiple elements** for content extraction while preserving the entire page context for other features:
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        # Target article body and sidebar, but not other content
        target_elements=["article.main-content", "aside.sidebar"]
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/blog-post", 
            config=config
        )
        print("Markdown focused on target elements")
        print("Links from entire page still available:", len(result.links.get("internal", [])))

if __name__ == "__main__":
    asyncio.run(main())
```
**Key difference**: With `target_elements`, the markdown generation and structural data extraction focus on those elements, but other page elements (like links, images, and tables) are still extracted from the entire page. This gives you fine-grained control over what appears in your markdown content while preserving full page context for link analysis and media collection.
## 2. Content Filtering & Exclusions
### 2.1 Basic Overview
```python
config = CrawlerRunConfig(
    # Content thresholds
    word_count_threshold=10,        # Minimum words per block

    # Tag exclusions
    excluded_tags=['form', 'header', 'footer', 'nav'],

    # Link filtering
    exclude_external_links=True,    
    exclude_social_media_links=True,
    # Block entire domains
    exclude_domains=["adtrackers.com", "spammynews.org"],    
    exclude_social_media_domains=["facebook.com", "twitter.com"],

    # Media filtering
    exclude_external_images=True
)
```
- **`word_count_threshold`**: Ignores text blocks under X words. Helps skip trivial blocks like short nav or disclaimers.  
- **`excluded_tags`**: Removes entire tags (`<form>`, `<header>`, `<footer>`, etc.).  
- **Link Filtering**:  
  - `exclude_external_links`: Strips out external links and may remove them from `result.links`.  
  - `exclude_social_media_links`: Removes links pointing to known social media domains.  
  - `exclude_domains`: A custom list of domains to block if discovered in links.  
  - `exclude_social_media_domains`: A curated list (override or add to it) for social media sites.  
- **Media Filtering**:  
  - `exclude_external_images`: Discards images not hosted on the same domain as the main page (or its subdomains).
By default in case you set `exclude_social_media_links=True`, the following social media domains are excluded:
```python
[
    'facebook.com',
    'twitter.com',
    'x.com',
    'linkedin.com',
    'instagram.com',
    'pinterest.com',
    'tiktok.com',
    'snapchat.com',
    'reddit.com',
]
```
### 2.2 Example Usage
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    config = CrawlerRunConfig(
        css_selector="main.content", 
        word_count_threshold=10,
        excluded_tags=["nav", "footer"],
        exclude_external_links=True,
        exclude_social_media_links=True,
        exclude_domains=["ads.com", "spammytrackers.net"],
        exclude_external_images=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        print("Cleaned HTML length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
```
## 3. Handling Iframes
Some sites embed content in `<iframe>` tags. If you want that inline:
```python
config = CrawlerRunConfig(
    # Merge iframe content into the final output
    process_iframes=True,    
    remove_overlay_elements=True
)
```
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        process_iframes=True,
        remove_overlay_elements=True
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.org/iframe-demo", 
            config=config
        )
        print("Iframe-merged length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
```
## 4. Structured Extraction Examples
### 4.1 Pattern-Based with `JsonCssExtractionStrategy`
```python
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

async def main():
    # Minimal schema for repeated items
    schema = {
        "name": "News Items",
        "baseSelector": "tr.athing",
        "fields": [
            {"name": "title", "selector": "span.titleline a", "type": "text"},
            {
                "name": "link", 
                "selector": "span.titleline a", 
                "type": "attribute", 
                "attribute": "href"
            }
        ]
    }

    config = CrawlerRunConfig(
        # Content filtering
        excluded_tags=["form", "header"],
        exclude_domains=["adsite.com"],

        # CSS selection or entire page
        css_selector="table.itemlist",

        # No caching for demonstration
        cache_mode=CacheMode.BYPASS,

        # Extraction strategy
        extraction_strategy=JsonCssExtractionStrategy(schema)
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com/newest", 
            config=config
        )
        data = json.loads(result.extracted_content)
        print("Sample extracted item:", data[:1])  # Show first item

if __name__ == "__main__":
    asyncio.run(main())
```
### 4.2 LLM-Based Extraction
```python
import asyncio
import json
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig
from crawl4ai import LLMExtractionStrategy

class ArticleData(BaseModel):
    headline: str
    summary: str

async def main():
    llm_strategy = LLMExtractionStrategy(
        llm_config = LLMConfig(provider="openai/gpt-4",api_token="sk-YOUR_API_KEY")
        schema=ArticleData.schema(),
        extraction_type="schema",
        instruction="Extract 'headline' and a short 'summary' from the content."
    )

    config = CrawlerRunConfig(
        exclude_external_links=True,
        word_count_threshold=20,
        extraction_strategy=llm_strategy
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        article = json.loads(result.extracted_content)
        print(article)

if __name__ == "__main__":
    asyncio.run(main())
```
- Filters out external links (`exclude_external_links=True`).  
- Ignores very short text blocks (`word_count_threshold=20`).  
- Passes the final HTML to your LLM strategy for an AI-driven parse.
## 5. Comprehensive Example
```python
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

async def extract_main_articles(url: str):
    schema = {
        "name": "ArticleBlock",
        "baseSelector": "div.article-block",
        "fields": [
            {"name": "headline", "selector": "h2", "type": "text"},
            {"name": "summary", "selector": ".summary", "type": "text"},
            {
                "name": "metadata",
                "type": "nested",
                "fields": [
                    {"name": "author", "selector": ".author", "type": "text"},
                    {"name": "date", "selector": ".date", "type": "text"}
                ]
            }
        ]
    }

    config = CrawlerRunConfig(
        # Keep only #main-content
        css_selector="#main-content",

        # Filtering
        word_count_threshold=10,
        excluded_tags=["nav", "footer"],  
        exclude_external_links=True,
        exclude_domains=["somebadsite.com"],
        exclude_external_images=True,

        # Extraction
        extraction_strategy=JsonCssExtractionStrategy(schema),

        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        if not result.success:
            print(f"Error: {result.error_message}")
            return None
        return json.loads(result.extracted_content)

async def main():
    articles = await extract_main_articles("https://news.ycombinator.com/newest")
    if articles:
        print("Extracted Articles:", articles[:2])  # Show first 2

if __name__ == "__main__":
    asyncio.run(main())
```
- **CSS** scoping with `#main-content`.  
- Multiple **exclude_** parameters to remove domains, external images, etc.  
- A **JsonCssExtractionStrategy** to parse repeated article blocks.
## 6. Scraping Modes
Crawl4AI uses `LXMLWebScrapingStrategy` (LXML-based) as the default scraping strategy for HTML content processing. This strategy offers excellent performance, especially for large HTML documents.
**Note:** For backward compatibility, `WebScrapingStrategy` is still available as an alias for `LXMLWebScrapingStrategy`.
```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LXMLWebScrapingStrategy

async def main():
    # Default configuration already uses LXMLWebScrapingStrategy
    config = CrawlerRunConfig()

    # Or explicitly specify it if desired
    config_explicit = CrawlerRunConfig(
        scraping_strategy=LXMLWebScrapingStrategy()
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com", 
            config=config
        )
```
You can also create your own custom scraping strategy by inheriting from `ContentScrapingStrategy`. The strategy must return a `ScrapingResult` object with the following structure:
```python
from crawl4ai import ContentScrapingStrategy, ScrapingResult, MediaItem, Media, Link, Links

class CustomScrapingStrategy(ContentScrapingStrategy):
    def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        # Implement your custom scraping logic here
        return ScrapingResult(
            cleaned_html="<html>...</html>",  # Cleaned HTML content
            success=True,                     # Whether scraping was successful
            media=Media(
                images=[                      # List of images found
                    MediaItem(
                        src="https://example.com/image.jpg",
                        alt="Image description",
                        desc="Surrounding text",
                        score=1,
                        type="image",
                        group_id=1,
                        format="jpg",
                        width=800
                    )
                ],
                videos=[],                    # List of videos (same structure as images)
                audios=[]                     # List of audio files (same structure as images)
            ),
            links=Links(
                internal=[                    # List of internal links
                    Link(
                        href="https://example.com/page",
                        text="Link text",
                        title="Link title",
                        base_domain="example.com"
                    )
                ],
                external=[]                   # List of external links (same structure)
            ),
            metadata={                        # Additional metadata
                "title": "Page Title",
                "description": "Page description"
            }
        )

    async def ascrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        # For simple cases, you can use the sync version
        return await asyncio.to_thread(self.scrap, url, html, **kwargs)
```
### Performance Considerations
- Fast processing of large HTML documents (especially >100KB)
- Efficient memory usage
- Good handling of well-formed HTML
- Robust table detection and extraction
### Backward Compatibility
For users upgrading from earlier versions:
- `WebScrapingStrategy` is now an alias for `LXMLWebScrapingStrategy`
- Existing code using `WebScrapingStrategy` will continue to work without modification
- No changes are required to your existing code
## 7. Combining CSS Selection Methods
You can combine `css_selector` and `target_elements` in powerful ways to achieve fine-grained control over your output:
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    # Target specific content but preserve page context
    config = CrawlerRunConfig(
        # Focus markdown on main content and sidebar
        target_elements=["#main-content", ".sidebar"],

        # Global filters applied to entire page
        excluded_tags=["nav", "footer", "header"],
        exclude_external_links=True,

        # Use basic content thresholds
        word_count_threshold=15,

        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/article",
            config=config
        )

        print(f"Content focuses on specific elements, but all links still analyzed")
        print(f"Internal links: {len(result.links.get('internal', []))}")
        print(f"External links: {len(result.links.get('external', []))}")

if __name__ == "__main__":
    asyncio.run(main())
```
- Links, images and other page data still give you the full context of the page
- Content filtering still applies globally
## 8. Conclusion
By mixing **target_elements** or **css_selector** scoping, **content filtering** parameters, and advanced **extraction strategies**, you can precisely **choose** which data to keep. Key parameters in **`CrawlerRunConfig`** for content selection include:
1. **`target_elements`** – Array of CSS selectors to focus markdown generation and data extraction, while preserving full page context for links and media.
2. **`css_selector`** – Basic scoping to an element or region for all extraction processes.  
3. **`word_count_threshold`** – Skip short blocks.  
4. **`excluded_tags`** – Remove entire HTML tags.  
5. **`exclude_external_links`**, **`exclude_social_media_links`**, **`exclude_domains`** – Filter out unwanted links or domains.  
6. **`exclude_external_images`** – Remove images from external sources.  
7. **`process_iframes`** – Merge iframe content if needed.  


# Page Interaction
1. Click “Load More” buttons  
2. Fill forms and submit them  
3. Wait for elements or data to appear  
4. Reuse sessions across multiple steps  
## 1. JavaScript Execution
### Basic Execution
**`js_code`** in **`CrawlerRunConfig`** accepts either a single JS string or a list of JS snippets.  
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Single JS command
    config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",  # Example site
            config=config
        )
        print("Crawled length:", len(result.cleaned_html))

    # Multiple commands
    js_commands = [
        "window.scrollTo(0, document.body.scrollHeight);",
        # 'More' link on Hacker News
        "document.querySelector('a.morelink')?.click();",  
    ]
    config = CrawlerRunConfig(js_code=js_commands)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",  # Another pass
            config=config
        )
        print("After scroll+click, length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
```
**Relevant `CrawlerRunConfig` params**:
- **`js_code`**: A string or list of strings with JavaScript to run after the page loads.
- **`js_only`**: If set to `True` on subsequent calls, indicates we’re continuing an existing session without a new full navigation.  
- **`session_id`**: If you want to keep the same page across multiple calls, specify an ID.
## 2. Wait Conditions
### 2.1 CSS-Based Waiting
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        # Wait for at least 30 items on Hacker News
        wait_for="css:.athing:nth-child(30)"  
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=config
        )
        print("We have at least 30 items loaded!")
        # Rough check
        print("Total items in HTML:", result.cleaned_html.count("athing"))  

if __name__ == "__main__":
    asyncio.run(main())
```
- **`wait_for="css:..."`**: Tells the crawler to wait until that CSS selector is present.
### 2.2 JavaScript-Based Waiting
For more complex conditions (e.g., waiting for content length to exceed a threshold), prefix `js:`:
```python
wait_condition = """() => {
    const items = document.querySelectorAll('.athing');
    return items.length > 50;  // Wait for at least 51 items
}"""

config = CrawlerRunConfig(wait_for=f"js:{wait_condition}")
```
**Behind the Scenes**: Crawl4AI keeps polling the JS function until it returns `true` or a timeout occurs.
## 3. Handling Dynamic Content
### 3.1 Load More Example (Hacker News “More” Link)
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Step 1: Load initial Hacker News page
    config = CrawlerRunConfig(
        wait_for="css:.athing:nth-child(30)"  # Wait for 30 items
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=config
        )
        print("Initial items loaded.")

        # Step 2: Let's scroll and click the "More" link
        load_more_js = [
            "window.scrollTo(0, document.body.scrollHeight);",
            # The "More" link at page bottom
            "document.querySelector('a.morelink')?.click();"  
        ]

        next_page_conf = CrawlerRunConfig(
            js_code=load_more_js,
            wait_for="""js:() => {
                return document.querySelectorAll('.athing').length > 30;
            }""",
            # Mark that we do not re-navigate, but run JS in the same session:
            js_only=True,
            session_id="hn_session"
        )

        # Re-use the same crawler session
        result2 = await crawler.arun(
            url="https://news.ycombinator.com",  # same URL but continuing session
            config=next_page_conf
        )
        total_items = result2.cleaned_html.count("athing")
        print("Items after load-more:", total_items)

if __name__ == "__main__":
    asyncio.run(main())
```
- **`session_id="hn_session"`**: Keep the same page across multiple calls to `arun()`.
- **`js_only=True`**: We’re not performing a full reload, just applying JS in the existing page.
- **`wait_for`** with `js:`: Wait for item count to grow beyond 30.
### 3.2 Form Interaction
If the site has a search or login form, you can fill fields and submit them with **`js_code`**. For instance, if GitHub had a local search form:
```python
js_form_interaction = """
document.querySelector('#your-search').value = 'TypeScript commits';
document.querySelector('form').submit();
"""

config = CrawlerRunConfig(
    js_code=js_form_interaction,
    wait_for="css:.commit"
)
result = await crawler.arun(url="https://github.com/search", config=config)
```
## 4. Timing Control
1. **`page_timeout`** (ms): Overall page load or script execution time limit.  
2. **`delay_before_return_html`** (seconds): Wait an extra moment before capturing the final HTML.  
3. **`mean_delay`** & **`max_range`**: If you call `arun_many()` with multiple URLs, these add a random pause between each request.
```python
config = CrawlerRunConfig(
    page_timeout=60000,  # 60s limit
    delay_before_return_html=2.5
)
```
## 5. Multi-Step Interaction Example
Below is a simplified script that does multiple “Load More” clicks on GitHub’s TypeScript commits page. It **re-uses** the same session to accumulate new commits each time. The code includes the relevant **`CrawlerRunConfig`** parameters you’d rely on.
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def multi_page_commits():
    browser_cfg = BrowserConfig(
        headless=False,  # Visible for demonstration
        verbose=True
    )
    session_id = "github_ts_commits"

    base_wait = """js:() => {
        const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
        return commits.length > 0;
    }"""

    # Step 1: Load initial commits
    config1 = CrawlerRunConfig(
        wait_for=base_wait,
        session_id=session_id,
        cache_mode=CacheMode.BYPASS,
        # Not using js_only yet since it's our first load
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://github.com/microsoft/TypeScript/commits/main",
            config=config1
        )
        print("Initial commits loaded. Count:", result.cleaned_html.count("commit"))

        # Step 2: For subsequent pages, we run JS to click 'Next Page' if it exists
        js_next_page = """
        const selector = 'a[data-testid="pagination-next-button"]';
        const button = document.querySelector(selector);
        if (button) button.click();
        """

        # Wait until new commits appear
        wait_for_more = """js:() => {
            const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
            if (!window.firstCommit && commits.length>0) {
                window.firstCommit = commits[0].textContent;
                return false;
            }
            // If top commit changes, we have new commits
            const topNow = commits[0]?.textContent.trim();
            return topNow && topNow !== window.firstCommit;
        }"""

        for page in range(2):  # let's do 2 more "Next" pages
            config_next = CrawlerRunConfig(
                session_id=session_id,
                js_code=js_next_page,
                wait_for=wait_for_more,
                js_only=True,       # We're continuing from the open tab
                cache_mode=CacheMode.BYPASS
            )
            result2 = await crawler.arun(
                url="https://github.com/microsoft/TypeScript/commits/main",
                config=config_next
            )
            print(f"Page {page+2} commits count:", result2.cleaned_html.count("commit"))

        # Optionally kill session
        await crawler.crawler_strategy.kill_session(session_id)

async def main():
    await multi_page_commits()

if __name__ == "__main__":
    asyncio.run(main())
```
- **`session_id`**: Keep the same page open.  
- **`js_code`** + **`wait_for`** + **`js_only=True`**: We do partial refreshes, waiting for new commits to appear.  
- **`cache_mode=CacheMode.BYPASS`** ensures we always see fresh data each step.
## 6. Combine Interaction with Extraction
Once dynamic content is loaded, you can attach an **`extraction_strategy`** (like `JsonCssExtractionStrategy` or `LLMExtractionStrategy`). For example:
```python
from crawl4ai import JsonCssExtractionStrategy

schema = {
    "name": "Commits",
    "baseSelector": "li.Box-sc-g0xbh4-0",
    "fields": [
        {"name": "title", "selector": "h4.markdown-title", "type": "text"}
    ]
}
config = CrawlerRunConfig(
    session_id="ts_commits_session",
    js_code=js_next_page,
    wait_for=wait_for_more,
    extraction_strategy=JsonCssExtractionStrategy(schema)
)
```
When done, check `result.extracted_content` for the JSON.
## 7. Relevant `CrawlerRunConfig` Parameters
Below are the key interaction-related parameters in `CrawlerRunConfig`. For a full list, see [Configuration Parameters](../api/parameters.md).
- **`js_code`**: JavaScript to run after initial load.  
- **`js_only`**: If `True`, no new page navigation—only JS in the existing session.  
- **`wait_for`**: CSS (`"css:..."`) or JS (`"js:..."`) expression to wait for.  
- **`session_id`**: Reuse the same page across calls.  
- **`cache_mode`**: Whether to read/write from the cache or bypass.  
- **`remove_overlay_elements`**: Remove certain popups automatically.  
- **`simulate_user`, `override_navigator`, `magic`**: Anti-bot or “human-like” interactions.
## 8. Conclusion
1. **Execute JavaScript** for scrolling, clicks, or form filling.  
2. **Wait** for CSS or custom JS conditions before capturing data.  
4. Combine with **structured extraction** for dynamic sites.
## 9. Virtual Scrolling
For sites that use **virtual scrolling** (where content is replaced rather than appended as you scroll, like Twitter or Instagram), Crawl4AI provides a dedicated `VirtualScrollConfig`:
```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, VirtualScrollConfig

async def crawl_twitter_timeline():
    # Configure virtual scroll for Twitter-like feeds
    virtual_config = VirtualScrollConfig(
        container_selector="[data-testid='primaryColumn']",  # Twitter's main column
        scroll_count=30,                # Scroll 30 times
        scroll_by="container_height",   # Scroll by container height each time
        wait_after_scroll=1.0          # Wait 1 second after each scroll
    )

    config = CrawlerRunConfig(
        virtual_scroll_config=virtual_config
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://twitter.com/search?q=AI",
            config=config
        )
        # result.html now contains ALL tweets from the virtual scroll
```
### Virtual Scroll vs JavaScript Scrolling
| Feature | Virtual Scroll | JS Code Scrolling |
|---------|---------------|-------------------|
| **Use Case** | Content replaced during scroll | Content appended or simple scroll |
| **Configuration** | `VirtualScrollConfig` object | `js_code` with scroll commands |
| **Automatic Merging** | Yes - merges all unique content | No - captures final state only |
| **Best For** | Twitter, Instagram, virtual tables | Traditional pages, load more buttons |


# Link & Media 
1. Extract links (internal, external) from crawled pages  
2. Filter or exclude specific domains (e.g., social media or custom domains)  
3. Access and ma### 3.2 Excluding Images
```python
crawler_cfg = CrawlerRunConfig(
    exclude_external_images=True
)
```
```python
crawler_cfg = CrawlerRunConfig(
    exclude_all_images=True
)
```
- You don't need image data in your results
- You're crawling image-heavy pages that cause memory issues
- You want to focus only on text content
4. Configure your crawler to exclude or prioritize certain images
Below is a revised version of the **Link Extraction** and **Media Extraction** sections that includes example data structures showing how links and media items are stored in `CrawlResult`. Feel free to adjust any field names or descriptions to match your actual output.
## 1. Link Extraction
### 1.1 `result.links`
When you call `arun()` or `arun_many()` on a URL, Crawl4AI automatically extracts links and stores them in the `links` field of `CrawlResult`. By default, the crawler tries to distinguish **internal** links (same domain) from **external** links (different domains).
```python
from crawl4ai import AsyncWebCrawler

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://www.example.com")
    if result.success:
        internal_links = result.links.get("internal", [])
        external_links = result.links.get("external", [])
        print(f"Found {len(internal_links)} internal links.")
        print(f"Found {len(internal_links)} external links.")
        print(f"Found {len(result.media)} media items.")

        # Each link is typically a dictionary with fields like:
        # { "href": "...", "text": "...", "title": "...", "base_domain": "..." }
        if internal_links:
            print("Sample Internal Link:", internal_links[0])
    else:
        print("Crawl failed:", result.error_message)
```
```python
result.links = {
  "internal": [
    {
      "href": "https://kidocode.com/",
      "text": "",
      "title": "",
      "base_domain": "kidocode.com"
    },
    {
      "href": "https://kidocode.com/degrees/technology",
      "text": "Technology Degree",
      "title": "KidoCode Tech Program",
      "base_domain": "kidocode.com"
    },
    # ...
  ],
  "external": [
    # possibly other links leading to third-party sites
  ]
}
```
- **`href`**: The raw hyperlink URL.  
- **`text`**: The link text (if any) within the `<a>` tag.  
- **`title`**: The `title` attribute of the link (if present).  
- **`base_domain`**: The domain extracted from `href`. Helpful for filtering or grouping by domain.
## 2. Advanced Link Head Extraction & Scoring
Ever wanted to not just extract links, but also get the actual content (title, description, metadata) from those linked pages? And score them for relevance? This is exactly what Link Head Extraction does - it fetches the `<head>` section from each discovered link and scores them using multiple algorithms.
### 2.1 Why Link Head Extraction?
1. **Fetching head content** from each link (title, description, meta tags)
4. **Combining scores intelligently** to give you a final relevance ranking
### 2.2 Complete Working Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import LinkPreviewConfig

async def extract_link_heads_example():
    """
    Complete example showing link head extraction with scoring.
    This will crawl a documentation site and extract head content from internal links.
    """

    # Configure link head extraction
    config = CrawlerRunConfig(
        # Enable link head extraction with detailed configuration
        link_preview_config=LinkPreviewConfig(
            include_internal=True,           # Extract from internal links
            include_external=False,          # Skip external links for this example
            max_links=10,                   # Limit to 10 links for demo
            concurrency=5,                  # Process 5 links simultaneously
            timeout=10,                     # 10 second timeout per link
            query="API documentation guide", # Query for contextual scoring
            score_threshold=0.3,            # Only include links scoring above 0.3
            verbose=True                    # Show detailed progress
        ),
        # Enable intrinsic scoring (URL quality, text relevance)
        score_links=True,
        # Keep output clean
        only_text=True,
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        # Crawl a documentation site (great for testing)
        result = await crawler.arun("https://docs.python.org/3/", config=config)

        if result.success:
            print(f"✅ Successfully crawled: {result.url}")
            print(f"📄 Page title: {result.metadata.get('title', 'No title')}")

            # Access links (now enhanced with head data and scores)
            internal_links = result.links.get("internal", [])
            external_links = result.links.get("external", [])

            print(f"\n🔗 Found {len(internal_links)} internal links")
            print(f"🌍 Found {len(external_links)} external links")

            # Count links with head data
            links_with_head = [link for link in internal_links 
                             if link.get("head_data") is not None]
            print(f"🧠 Links with head data extracted: {len(links_with_head)}")

            # Show the top 3 scoring links
            print(f"\n🏆 Top 3 Links with Full Scoring:")
            for i, link in enumerate(links_with_head[:3]):
                print(f"\n{i+1}. {link['href']}")
                print(f"   Link Text: '{link.get('text', 'No text')[:50]}...'")

                # Show all three score types
                intrinsic = link.get('intrinsic_score')
                contextual = link.get('contextual_score') 
                total = link.get('total_score')

                if intrinsic is not None:
                    print(f"   📊 Intrinsic Score: {intrinsic:.2f}/10.0 (URL quality & context)")
                if contextual is not None:
                    print(f"   🎯 Contextual Score: {contextual:.3f} (BM25 relevance to query)")
                if total is not None:
                    print(f"   ⭐ Total Score: {total:.3f} (combined final score)")

                # Show extracted head data
                head_data = link.get("head_data", {})
                if head_data:
                    title = head_data.get("title", "No title")
                    description = head_data.get("meta", {}).get("description", "No description")

                    print(f"   📰 Title: {title[:60]}...")
                    if description:
                        print(f"   📝 Description: {description[:80]}...")

                    # Show extraction status
                    status = link.get("head_extraction_status", "unknown")
                    print(f"   ✅ Extraction Status: {status}")
        else:
            print(f"❌ Crawl failed: {result.error_message}")

# Run the example
if __name__ == "__main__":
    asyncio.run(extract_link_heads_example())
```
```
✅ Successfully crawled: https://docs.python.org/3/
📄 Page title: 3.13.5 Documentation
🔗 Found 53 internal links
🌍 Found 1 external links
🧠 Links with head data extracted: 10

🏆 Top 3 Links with Full Scoring:

1. https://docs.python.org/3.15/
   Link Text: 'Python 3.15 (in development)...'
   📊 Intrinsic Score: 4.17/10.0 (URL quality & context)
   🎯 Contextual Score: 1.000 (BM25 relevance to query)
   ⭐ Total Score: 5.917 (combined final score)
   📰 Title: 3.15.0a0 Documentation...
   📝 Description: The official Python documentation...
   ✅ Extraction Status: valid
```
### 2.3 Configuration Deep Dive
The `LinkPreviewConfig` class supports these options:
```python
from crawl4ai import LinkPreviewConfig

link_preview_config = LinkPreviewConfig(
    # BASIC SETTINGS
    verbose=True,                    # Show detailed logs (recommended for learning)

    # LINK FILTERING
    include_internal=True,           # Include same-domain links
    include_external=True,           # Include different-domain links
    max_links=50,                   # Maximum links to process (prevents overload)

    # PATTERN FILTERING
    include_patterns=[               # Only process links matching these patterns
        "*/docs/*", 
        "*/api/*", 
        "*/reference/*"
    ],
    exclude_patterns=[               # Skip links matching these patterns
        "*/login*",
        "*/admin*"
    ],

    # PERFORMANCE SETTINGS
    concurrency=10,                  # How many links to process simultaneously
    timeout=5,                      # Seconds to wait per link

    # RELEVANCE SCORING
    query="machine learning API",    # Query for BM25 contextual scoring
    score_threshold=0.3,            # Only include links above this score
)
```
### 2.4 Understanding the Three Score Types
```python
# High intrinsic score indicators:
# ✅ Clean URL structure (docs.python.org/api/reference)
# ✅ Meaningful link text ("API Reference Guide")
# ✅ Relevant to page context
# ✅ Not buried deep in navigation

# Low intrinsic score indicators:
# ❌ Random URLs (site.com/x7f9g2h)
# ❌ No link text or generic text ("Click here")
# ❌ Unrelated to page content
```
Only available when you provide a `query`. Uses BM25 algorithm against head content:
```python
# Example: query = "machine learning tutorial"
# High contextual score: Link to "Complete Machine Learning Guide"
# Low contextual score: Link to "Privacy Policy"
```
```python
# When both scores available: (intrinsic * 0.3) + (contextual * 0.7)
# When only intrinsic: uses intrinsic score
# When only contextual: uses contextual score
# When neither: not calculated
```
### 2.5 Practical Use Cases
```python
async def research_assistant():
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_external=True,
            include_patterns=["*/docs/*", "*/tutorial/*", "*/guide/*"],
            query="machine learning neural networks",
            max_links=20,
            score_threshold=0.5,  # Only high-relevance links
            verbose=True
        ),
        score_links=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://scikit-learn.org/", config=config)

        if result.success:
            # Get high-scoring links
            good_links = [link for link in result.links.get("internal", [])
                         if link.get("total_score", 0) > 0.7]

            print(f"🎯 Found {len(good_links)} highly relevant links:")
            for link in good_links[:5]:
                print(f"⭐ {link['total_score']:.3f} - {link['href']}")
                print(f"   {link.get('head_data', {}).get('title', 'No title')}")
```
```python
async def api_discovery():
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_patterns=["*/api/*", "*/reference/*"],
            exclude_patterns=["*/deprecated/*"],
            max_links=100,
            concurrency=15,
            verbose=False  # Clean output
        ),
        score_links=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://docs.example-api.com/", config=config)

        if result.success:
            api_links = result.links.get("internal", [])

            # Group by endpoint type
            endpoints = {}
            for link in api_links:
                if link.get("head_data"):
                    title = link["head_data"].get("title", "")
                    if "GET" in title:
                        endpoints.setdefault("GET", []).append(link)
                    elif "POST" in title:
                        endpoints.setdefault("POST", []).append(link)

            for method, links in endpoints.items():
                print(f"\n{method} Endpoints ({len(links)}):")
                for link in links[:3]:
                    print(f"  • {link['href']}")
```
```python
async def quality_analysis():
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            max_links=200,
            concurrency=20,
        ),
        score_links=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://your-website.com/", config=config)

        if result.success:
            links = result.links.get("internal", [])

            # Analyze intrinsic scores
            scores = [link.get('intrinsic_score', 0) for link in links]
            avg_score = sum(scores) / len(scores) if scores else 0

            print(f"📊 Link Quality Analysis:")
            print(f"   Average intrinsic score: {avg_score:.2f}/10.0")
            print(f"   High quality links (>7.0): {len([s for s in scores if s > 7.0])}")
            print(f"   Low quality links (<3.0): {len([s for s in scores if s < 3.0])}")

            # Find problematic links
            bad_links = [link for link in links 
                        if link.get('intrinsic_score', 0) < 2.0]

            if bad_links:
                print(f"\n⚠️  Links needing attention:")
                for link in bad_links[:5]:
                    print(f"   {link['href']} (score: {link.get('intrinsic_score', 0):.1f})")
```
### 2.6 Performance Tips
1. **Start Small**: Begin with `max_links: 10` to understand the feature
2. **Use Patterns**: Filter with `include_patterns` to focus on relevant sections
3. **Adjust Concurrency**: Higher concurrency = faster but more resource usage
4. **Set Timeouts**: Use `timeout: 5` to prevent hanging on slow sites
5. **Use Score Thresholds**: Filter out low-quality links with `score_threshold`
### 2.7 Troubleshooting
```python
# Check your configuration:
config = CrawlerRunConfig(
    link_preview_config=LinkPreviewConfig(
        verbose=True   # ← Enable to see what's happening
    )
)
```
```python
# Make sure scoring is enabled:
config = CrawlerRunConfig(
    score_links=True,  # ← Enable intrinsic scoring
    link_preview_config=LinkPreviewConfig(
        query="your search terms"  # ← For contextual scoring
    )
)
```
```python
# Optimize performance:
link_preview_config = LinkPreviewConfig(
    max_links=20,      # ← Reduce number
    concurrency=10,    # ← Increase parallelism
    timeout=3,         # ← Shorter timeout
    include_patterns=["*/important/*"]  # ← Focus on key areas
)
```
## 3. Domain Filtering
Some websites contain hundreds of third-party or affiliate links. You can filter out certain domains at **crawl time** by configuring the crawler. The most relevant parameters in `CrawlerRunConfig` are:
- **`exclude_external_links`**: If `True`, discard any link pointing outside the root domain.  
- **`exclude_social_media_domains`**: Provide a list of social media platforms (e.g., `["facebook.com", "twitter.com"]`) to exclude from your crawl.  
- **`exclude_social_media_links`**: If `True`, automatically skip known social platforms.  
- **`exclude_domains`**: Provide a list of custom domains you want to exclude (e.g., `["spammyads.com", "tracker.net"]`).
### 3.1 Example: Excluding External & Social Media Links
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    crawler_cfg = CrawlerRunConfig(
        exclude_external_links=True,          # No links outside primary domain
        exclude_social_media_links=True       # Skip recognized social media domains
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            "https://www.example.com",
            config=crawler_cfg
        )
        if result.success:
            print("[OK] Crawled:", result.url)
            print("Internal links count:", len(result.links.get("internal", [])))
            print("External links count:", len(result.links.get("external", [])))  
            # Likely zero external links in this scenario
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```
### 3.2 Example: Excluding Specific Domains
If you want to let external links in, but specifically exclude a domain (e.g., `suspiciousads.com`), do this:
```python
crawler_cfg = CrawlerRunConfig(
    exclude_domains=["suspiciousads.com"]
)
```
## 4. Media Extraction
### 4.1 Accessing `result.media`
By default, Crawl4AI collects images, audio and video URLs it finds on the page. These are stored in `result.media`, a dictionary keyed by media type (e.g., `images`, `videos`, `audio`).
**Note: Tables have been moved from `result.media["tables"]` to the new `result.tables` format for better organization and direct access.**
```python
if result.success:
    # Get images
    images_info = result.media.get("images", [])
    print(f"Found {len(images_info)} images in total.")
    for i, img in enumerate(images_info[:3]):  # Inspect just the first 3
        print(f"[Image {i}] URL: {img['src']}")
        print(f"           Alt text: {img.get('alt', '')}")
        print(f"           Score: {img.get('score')}")
        print(f"           Description: {img.get('desc', '')}\n")
```
```python
result.media = {
  "images": [
    {
      "src": "https://cdn.prod.website-files.com/.../Group%2089.svg",
      "alt": "coding school for kids",
      "desc": "Trial Class Degrees degrees All Degrees AI Degree Technology ...",
      "score": 3,
      "type": "image",
      "group_id": 0,
      "format": None,
      "width": None,
      "height": None
    },
    # ...
  ],
  "videos": [
    # Similar structure but with video-specific fields
  ],
  "audio": [
    # Similar structure but with audio-specific fields
  ],
}
```
- **`src`**: The media URL (e.g., image source)  
- **`alt`**: The alt text for images (if present)  
- **`desc`**: A snippet of nearby text or a short description (optional)  
- **`score`**: A heuristic relevance score if you’re using content-scoring features  
- **`width`**, **`height`**: If the crawler detects dimensions for the image/video  
- **`type`**: Usually `"image"`, `"video"`, or `"audio"`  
- **`group_id`**: If you’re grouping related media items, the crawler might assign an ID  
### 4.2 Excluding External Images
```python
crawler_cfg = CrawlerRunConfig(
    exclude_external_images=True
)
```
### 4.3 Additional Media Config
- **`screenshot`**: Set to `True` if you want a full-page screenshot stored as `base64` in `result.screenshot`.  
- **`pdf`**: Set to `True` if you want a PDF version of the page in `result.pdf`.  
- **`capture_mhtml`**: Set to `True` if you want an MHTML snapshot of the page in `result.mhtml`. This format preserves the entire web page with all its resources (CSS, images, scripts) in a single file, making it perfect for archiving or offline viewing.
- **`wait_for_images`**: If `True`, attempts to wait until images are fully loaded before final extraction.
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    crawler_cfg = CrawlerRunConfig(
        capture_mhtml=True  # Enable MHTML capture
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=crawler_cfg)

        if result.success and result.mhtml:
            # Save the MHTML snapshot to a file
            with open("example.mhtml", "w", encoding="utf-8") as f:
                f.write(result.mhtml)
            print("MHTML snapshot saved to example.mhtml")
        else:
            print("Failed to capture MHTML:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```
- It captures the complete page state including all resources
- It can be opened in most modern browsers for offline viewing
- It preserves the page exactly as it appeared during crawling
- It's a single file, making it easy to store and transfer
## 5. Putting It All Together: Link & Media Filtering
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    # Suppose we want to keep only internal links, remove certain domains, 
    # and discard external images from the final crawl data.
    crawler_cfg = CrawlerRunConfig(
        exclude_external_links=True,
        exclude_domains=["spammyads.com"],
        exclude_social_media_links=True,   # skip Twitter, Facebook, etc.
        exclude_external_images=True,      # keep only images from main domain
        wait_for_images=True,             # ensure images are loaded
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://www.example.com", config=crawler_cfg)

        if result.success:
            print("[OK] Crawled:", result.url)

            # 1. Links
            in_links = result.links.get("internal", [])
            ext_links = result.links.get("external", [])
            print("Internal link count:", len(in_links))
            print("External link count:", len(ext_links))  # should be zero with exclude_external_links=True

            # 2. Images
            images = result.media.get("images", [])
            print("Images found:", len(images))

            # Let's see a snippet of these images
            for i, img in enumerate(images[:3]):
                print(f"  - {img['src']} (alt={img.get('alt','')}, score={img.get('score','N/A')})")
        else:
            print("[ERROR] Failed to crawl. Reason:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```
## 6. Common Pitfalls & Tips
1. **Conflicting Flags**:  
   - `exclude_external_links=True` but then also specifying `exclude_social_media_links=True` is typically fine, but understand that the first setting already discards *all* external links. The second becomes somewhat redundant.  
   - `exclude_external_images=True` but want to keep some external images? Currently no partial domain-based setting for images, so you might need a custom approach or hook logic.
2. **Relevancy Scores**:  
   - If your version of Crawl4AI or your scraping strategy includes an `img["score"]`, it’s typically a heuristic based on size, position, or content analysis. Evaluate carefully if you rely on it.
3. **Performance**:  
4. **Social Media Lists**:  
   - `exclude_social_media_links=True` typically references an internal list of known social domains like Facebook, Twitter, LinkedIn, etc. If you need to add or remove from that list, look for library settings or a local config file (depending on your version).



# Extraction Strategies

# Extracting JSON (No LLM)
1. **Schema-based extraction** with CSS or XPath selectors via `JsonCssExtractionStrategy` and `JsonXPathExtractionStrategy`
2. **Regular expression extraction** with `RegexExtractionStrategy` for fast pattern matching
1. **Faster & Cheaper**: No API calls or GPU overhead.  
## 1. Intro to Schema-Based Extraction
3. **Nested** or **list** types for repeated or hierarchical structures.  
## 2. Simple Example: Crypto Prices
Let's begin with a **simple** schema-based extraction using the `JsonCssExtractionStrategy`. Below is a snippet that extracts cryptocurrency prices from a site (similar to the legacy Coinbase example). Notice we **don't** call any LLM:
```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

async def extract_crypto_prices():
    # 1. Define a simple extraction schema
    schema = {
        "name": "Crypto Prices",
        "baseSelector": "div.crypto-row",    # Repeated elements
        "fields": [
            {
                "name": "coin_name",
                "selector": "h2.coin-name",
                "type": "text"
            },
            {
                "name": "price",
                "selector": "span.coin-price",
                "type": "text"
            }
        ]
    }

    # 2. Create the extraction strategy
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    # 3. Set up your crawler config (if needed)
    config = CrawlerRunConfig(
        # e.g., pass js_code or wait_for if the page is dynamic
        # wait_for="css:.crypto-row:nth-child(20)"
        cache_mode = CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        # 4. Run the crawl and extraction
        result = await crawler.arun(
            url="https://example.com/crypto-prices",

            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        # 5. Parse the extracted JSON
        data = json.loads(result.extracted_content)
        print(f"Extracted {len(data)} coin entries")
        print(json.dumps(data[0], indent=2) if data else "No data found")

asyncio.run(extract_crypto_prices())
```
- **`baseSelector`**: Tells us where each "item" (crypto row) is.  
- **`fields`**: Two fields (`coin_name`, `price`) using simple CSS selectors.  
- Each field defines a **`type`** (e.g., `text`, `attribute`, `html`, `regex`, etc.).
### **XPath Example with `raw://` HTML**
Below is a short example demonstrating **XPath** extraction plus the **`raw://`** scheme. We'll pass a **dummy HTML** directly (no network request) and define the extraction strategy in `CrawlerRunConfig`.
```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import JsonXPathExtractionStrategy

async def extract_crypto_prices_xpath():
    # 1. Minimal dummy HTML with some repeating rows
    dummy_html = """
    <html>
      <body>
        <div class='crypto-row'>
          <h2 class='coin-name'>Bitcoin</h2>
          <span class='coin-price'>$28,000</span>
        </div>
        <div class='crypto-row'>
          <h2 class='coin-name'>Ethereum</h2>
          <span class='coin-price'>$1,800</span>
        </div>
      </body>
    </html>
    """

    # 2. Define the JSON schema (XPath version)
    schema = {
        "name": "Crypto Prices via XPath",
        "baseSelector": "//div[@class='crypto-row']",
        "fields": [
            {
                "name": "coin_name",
                "selector": ".//h2[@class='coin-name']",
                "type": "text"
            },
            {
                "name": "price",
                "selector": ".//span[@class='coin-price']",
                "type": "text"
            }
        ]
    }

    # 3. Place the strategy in the CrawlerRunConfig
    config = CrawlerRunConfig(
        extraction_strategy=JsonXPathExtractionStrategy(schema, verbose=True)
    )

    # 4. Use raw:// scheme to pass dummy_html directly
    raw_url = f"raw://{dummy_html}"

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=raw_url,
            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        data = json.loads(result.extracted_content)
        print(f"Extracted {len(data)} coin rows")
        if data:
            print("First item:", data[0])

asyncio.run(extract_crypto_prices_xpath())
```
1. **`JsonXPathExtractionStrategy`** is used instead of `JsonCssExtractionStrategy`.  
2. **`baseSelector`** and each field's `"selector"` use **XPath** instead of CSS.  
3. **`raw://`** lets us pass `dummy_html` with no real network request—handy for local testing.  
4. Everything (including the extraction strategy) is in **`CrawlerRunConfig`**.  
That's how you keep the config self-contained, illustrate **XPath** usage, and demonstrate the **raw** scheme for direct HTML input—all while avoiding the old approach of passing `extraction_strategy` directly to `arun()`.
## 3. Advanced Schema & Nested Structures
### Sample E-Commerce HTML
```
https://gist.githubusercontent.com/githubusercontent/2d7b8ba3cd8ab6cf3c8da771ddb36878/raw/1ae2f90c6861ce7dd84cc50d3df9920dee5e1fd2/sample_ecommerce.html
```
```python
schema = {
    "name": "E-commerce Product Catalog",
    "baseSelector": "div.category",
    # (1) We can define optional baseFields if we want to extract attributes 
    # from the category container
    "baseFields": [
        {"name": "data_cat_id", "type": "attribute", "attribute": "data-cat-id"}, 
    ],
    "fields": [
        {
            "name": "category_name",
            "selector": "h2.category-name",
            "type": "text"
        },
        {
            "name": "products",
            "selector": "div.product",
            "type": "nested_list",    # repeated sub-objects
            "fields": [
                {
                    "name": "name",
                    "selector": "h3.product-name",
                    "type": "text"
                },
                {
                    "name": "price",
                    "selector": "p.product-price",
                    "type": "text"
                },
                {
                    "name": "details",
                    "selector": "div.product-details",
                    "type": "nested",  # single sub-object
                    "fields": [
                        {
                            "name": "brand",
                            "selector": "span.brand",
                            "type": "text"
                        },
                        {
                            "name": "model",
                            "selector": "span.model",
                            "type": "text"
                        }
                    ]
                },
                {
                    "name": "features",
                    "selector": "ul.product-features li",
                    "type": "list",
                    "fields": [
                        {"name": "feature", "type": "text"} 
                    ]
                },
                {
                    "name": "reviews",
                    "selector": "div.review",
                    "type": "nested_list",
                    "fields": [
                        {
                            "name": "reviewer", 
                            "selector": "span.reviewer", 
                            "type": "text"
                        },
                        {
                            "name": "rating", 
                            "selector": "span.rating", 
                            "type": "text"
                        },
                        {
                            "name": "comment", 
                            "selector": "p.review-text", 
                            "type": "text"
                        }
                    ]
                },
                {
                    "name": "related_products",
                    "selector": "ul.related-products li",
                    "type": "list",
                    "fields": [
                        {
                            "name": "name", 
                            "selector": "span.related-name", 
                            "type": "text"
                        },
                        {
                            "name": "price", 
                            "selector": "span.related-price", 
                            "type": "text"
                        }
                    ]
                }
            ]
        }
    ]
}
```
- **Nested vs. List**:  
  - **`type: "nested"`** means a **single** sub-object (like `details`).  
  - **`type: "list"`** means multiple items that are **simple** dictionaries or single text fields.  
  - **`type: "nested_list"`** means repeated **complex** objects (like `products` or `reviews`).
- **Base Fields**: We can extract **attributes** from the container element via `"baseFields"`. For instance, `"data_cat_id"` might be `data-cat-id="elect123"`.  
- **Transforms**: We can also define a `transform` if we want to lower/upper case, strip whitespace, or even run a custom function.
### Running the Extraction
```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy

ecommerce_schema = {
    # ... the advanced schema from above ...
}

async def extract_ecommerce_data():
    strategy = JsonCssExtractionStrategy(ecommerce_schema, verbose=True)

    config = CrawlerRunConfig()

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://gist.githubusercontent.com/githubusercontent/2d7b8ba3cd8ab6cf3c8da771ddb36878/raw/1ae2f90c6861ce7dd84cc50d3df9920dee5e1fd2/sample_ecommerce.html",
            extraction_strategy=strategy,
            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        # Parse the JSON output
        data = json.loads(result.extracted_content)
        print(json.dumps(data, indent=2) if data else "No data found.")

asyncio.run(extract_ecommerce_data())
```
If all goes well, you get a **structured** JSON array with each "category," containing an array of `products`. Each product includes `details`, `features`, `reviews`, etc. All of that **without** an LLM.
## 4. RegexExtractionStrategy - Fast Pattern-Based Extraction
Crawl4AI now offers a powerful new zero-LLM extraction strategy: `RegexExtractionStrategy`. This strategy provides lightning-fast extraction of common data types like emails, phone numbers, URLs, dates, and more using pre-compiled regular expressions.
### Key Features
- **Zero LLM Dependency**: Extracts data without any AI model calls
- **Blazing Fast**: Uses pre-compiled regex patterns for maximum performance
- **Built-in Patterns**: Includes ready-to-use patterns for common data types
### Simple Example: Extracting Common Entities
```python
import json
import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    RegexExtractionStrategy
)

async def extract_with_regex():
    # Create a strategy using built-in patterns for URLs and currencies
    strategy = RegexExtractionStrategy(
        pattern = RegexExtractionStrategy.Url | RegexExtractionStrategy.Currency
    )

    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=config
        )

        if result.success:
            data = json.loads(result.extracted_content)
            for item in data[:5]:  # Show first 5 matches
                print(f"{item['label']}: {item['value']}")
            print(f"Total matches: {len(data)}")

asyncio.run(extract_with_regex())
```
### Available Built-in Patterns
`RegexExtractionStrategy` provides these common patterns as IntFlag attributes for easy combining:
```python
# Use individual patterns
strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.Email)

# Combine multiple patterns
strategy = RegexExtractionStrategy(
    pattern = (
        RegexExtractionStrategy.Email | 
        RegexExtractionStrategy.PhoneUS | 
        RegexExtractionStrategy.Url
    )
)

# Use all available patterns
strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.All)
```
- `Email` - Email addresses
- `PhoneIntl` - International phone numbers
- `PhoneUS` - US-format phone numbers
- `Url` - HTTP/HTTPS URLs
- `IPv4` - IPv4 addresses
- `IPv6` - IPv6 addresses
- `Uuid` - UUIDs
- `Currency` - Currency values (USD, EUR, etc.)
- `Percentage` - Percentage values
- `Number` - Numeric values
- `DateIso` - ISO format dates
- `DateUS` - US format dates
- `Time24h` - 24-hour format times
- `PostalUS` - US postal codes
- `PostalUK` - UK postal codes
- `HexColor` - HTML hex color codes
- `TwitterHandle` - Twitter handles
- `Hashtag` - Hashtags
- `MacAddr` - MAC addresses
- `Iban` - International bank account numbers
- `CreditCard` - Credit card numbers
### Custom Pattern Example
```python
import json
import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    RegexExtractionStrategy
)

async def extract_prices():
    # Define a custom pattern for US Dollar prices
    price_pattern = {"usd_price": r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?"}

    # Create strategy with custom pattern
    strategy = RegexExtractionStrategy(custom=price_pattern)
    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.example.com/products",
            config=config
        )

        if result.success:
            data = json.loads(result.extracted_content)
            for item in data:
                print(f"Found price: {item['value']}")

asyncio.run(extract_prices())
```
### LLM-Assisted Pattern Generation
```python
import json
import asyncio
from pathlib import Path
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    RegexExtractionStrategy,
    LLMConfig
)

async def extract_with_generated_pattern():
    cache_dir = Path("./pattern_cache")
    cache_dir.mkdir(exist_ok=True)
    pattern_file = cache_dir / "price_pattern.json"

    # 1. Generate or load pattern
    if pattern_file.exists():
        pattern = json.load(pattern_file.open())
        print(f"Using cached pattern: {pattern}")
    else:
        print("Generating pattern via LLM...")

        # Configure LLM
        llm_config = LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token="env:OPENAI_API_KEY",
        )

        # Get sample HTML for context
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://example.com/products")
            html = result.fit_html

        # Generate pattern (one-time LLM usage)
        pattern = RegexExtractionStrategy.generate_pattern(
            label="price",
            html=html,
            query="Product prices in USD format",
            llm_config=llm_config,
        )

        # Cache pattern for future use
        json.dump(pattern, pattern_file.open("w"), indent=2)

    # 2. Use pattern for extraction (no LLM calls)
    strategy = RegexExtractionStrategy(custom=pattern)
    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/products",
            config=config
        )

        if result.success:
            data = json.loads(result.extracted_content)
            for item in data[:10]:
                print(f"Extracted: {item['value']}")
            print(f"Total matches: {len(data)}")

asyncio.run(extract_with_generated_pattern())
```
1. Use an LLM once to generate a highly optimized regex for your specific site
2. Save the pattern to disk for reuse 
3. Extract data using only regex (no further LLM calls) in production
### Extraction Results Format
The `RegexExtractionStrategy` returns results in a consistent format:
```json
[
  {
    "url": "https://example.com",
    "label": "email",
    "value": "contact@example.com",
    "span": [145, 163]
  },
  {
    "url": "https://example.com",
    "label": "url",
    "value": "https://support.example.com",
    "span": [210, 235]
  }
]
```
- `url`: The source URL
- `label`: The pattern name that matched (e.g., "email", "phone_us")
- `value`: The extracted text
- `span`: The start and end positions in the source content
## 5. Why "No LLM" Is Often Better
## 6. Base Element Attributes & Additional Fields
It's easy to **extract attributes** (like `href`, `src`, or `data-xxx`) from your base or nested elements using:
```json
{
  "name": "href",
  "type": "attribute",
  "attribute": "href",
  "default": null
}
```
You can define them in **`baseFields`** (extracted from the main container element) or in each field's sub-lists. This is especially helpful if you need an item's link or ID stored in the parent `<div>`.
## 7. Putting It All Together: Larger Example
Consider a blog site. We have a schema that extracts the **URL** from each post card (via `baseFields` with an `"attribute": "href"`), plus the title, date, summary, and author:
```python
schema = {
  "name": "Blog Posts",
  "baseSelector": "a.blog-post-card",
  "baseFields": [
    {"name": "post_url", "type": "attribute", "attribute": "href"}
  ],
  "fields": [
    {"name": "title", "selector": "h2.post-title", "type": "text", "default": "No Title"},
    {"name": "date", "selector": "time.post-date", "type": "text", "default": ""},
    {"name": "summary", "selector": "p.post-summary", "type": "text", "default": ""},
    {"name": "author", "selector": "span.post-author", "type": "text", "default": ""}
  ]
}
```
Then run with `JsonCssExtractionStrategy(schema)` to get an array of blog post objects, each with `"post_url"`, `"title"`, `"date"`, `"summary"`, `"author"`.
## 8. Tips & Best Practices
3. **Test** your schema on partial HTML or a test page before a big crawl.  
4. **Combine with JS Execution** if the site loads content dynamically. You can pass `js_code` or `wait_for` in `CrawlerRunConfig`.  
5. **Look at Logs** when `verbose=True`: if your selectors are off or your schema is malformed, it'll often show warnings.  
6. **Use baseFields** if you need attributes from the container element (e.g., `href`, `data-id`), especially for the "parent" item.  
8. **Consider Using Regex First**: For simple data types like emails, URLs, and dates, `RegexExtractionStrategy` is often the fastest approach.
## 9. Schema Generation Utility
1. You're dealing with a new website structure and want a quick starting point
2. You need to extract complex nested data structures
3. You want to avoid the learning curve of CSS/XPath selector syntax
### Using the Schema Generator
The schema generator is available as a static method on both `JsonCssExtractionStrategy` and `JsonXPathExtractionStrategy`. You can choose between OpenAI's GPT-4 or the open-source Ollama for schema generation:
```python
from crawl4ai import JsonCssExtractionStrategy, JsonXPathExtractionStrategy
from crawl4ai import LLMConfig

# Sample HTML with product information
html = """
<div class="product-card">
    <h2 class="title">Gaming Laptop</h2>
    <div class="price">$999.99</div>
    <div class="specs">
        <ul>
            <li>16GB RAM</li>
            <li>1TB SSD</li>
        </ul>
    </div>
</div>
"""

# Option 1: Using OpenAI (requires API token)
css_schema = JsonCssExtractionStrategy.generate_schema(
    html,
    schema_type="css", 
    llm_config = LLMConfig(provider="openai/gpt-4o",api_token="your-openai-token")
)

# Option 2: Using Ollama (open source, no token needed)
xpath_schema = JsonXPathExtractionStrategy.generate_schema(
    html,
    schema_type="xpath",
    llm_config = LLMConfig(provider="ollama/llama3.3", api_token=None)  # Not needed for Ollama
)

# Use the generated schema for fast, repeated extractions
strategy = JsonCssExtractionStrategy(css_schema)
```
### LLM Provider Options
1. **OpenAI GPT-4 (`openai/gpt4o`)**
   - Default provider
   - Requires an API token
   - Generally provides more accurate schemas
   - Set via environment variable: `OPENAI_API_KEY`
2. **Ollama (`ollama/llama3.3`)**
   - Open source alternative
   - No API token required
   - Self-hosted option
   - Good for development and testing
### Benefits of Schema Generation
### Best Practices
6. **Choose Provider Wisely**: 
   - Use OpenAI for production-quality schemas
   - Use Ollama for development, testing, or when you need a self-hosted solution
## 10. Conclusion
With Crawl4AI's LLM-free extraction strategies - `JsonCssExtractionStrategy`, `JsonXPathExtractionStrategy`, and now `RegexExtractionStrategy` - you can build powerful pipelines that:
- Scrape any consistent site for structured data.  
- Support nested objects, repeating lists, or pattern-based extraction.  
- Scale to thousands of pages quickly and reliably.
- Use **`RegexExtractionStrategy`** for fast extraction of common data types like emails, phones, URLs, dates, etc.
- Use **`JsonCssExtractionStrategy`** or **`JsonXPathExtractionStrategy`** for structured data with clear HTML patterns


# Extracting JSON (LLM)
**Important**: LLM-based extraction can be slower and costlier than schema-based approaches. If your page data is highly structured, consider using [`JsonCssExtractionStrategy`](./no-llm-strategies.md) or [`JsonXPathExtractionStrategy`](./no-llm-strategies.md) first. But if you need AI to interpret or reorganize content, read on!
## 1. Why Use an LLM?
## 2. Provider-Agnostic via LiteLLM
```python
llmConfig = LlmConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))
```
Crawl4AI uses a “provider string” (e.g., `"openai/gpt-4o"`, `"ollama/llama2.0"`, `"aws/titan"`) to identify your LLM. **Any** model that LiteLLM supports is fair game. You just provide:
- **`provider`**: The `<provider>/<model_name>` identifier (e.g., `"openai/gpt-4"`, `"ollama/llama2"`, `"huggingface/google-flan"`, etc.).  
- **`api_token`**: If needed (for OpenAI, HuggingFace, etc.); local models or Ollama might not require it.  
- **`base_url`** (optional): If your provider has a custom endpoint.  
## 3. How LLM Extraction Works
### 3.1 Flow
1. **Chunking** (optional): The HTML or markdown is split into smaller segments if it’s very long (based on `chunk_token_threshold`, overlap, etc.).  
2. **Prompt Construction**: For each chunk, the library forms a prompt that includes your **`instruction`** (and possibly schema or examples).  
4. **Combining**: The results from each chunk are merged and parsed into JSON.
### 3.2 `extraction_type`
- **`"schema"`**: The model tries to return JSON conforming to your Pydantic-based schema.  
- **`"block"`**: The model returns freeform text, or smaller JSON structures, which the library collects.  
For structured data, `"schema"` is recommended. You provide `schema=YourPydanticModel.model_json_schema()`.
## 4. Key Parameters
Below is an overview of important LLM extraction parameters. All are typically set inside `LLMExtractionStrategy(...)`. You then put that strategy in your `CrawlerRunConfig(..., extraction_strategy=...)`.
1. **`llmConfig`** (LlmConfig): e.g., `"openai/gpt-4"`, `"ollama/llama2"`.    
2. **`schema`** (dict): A JSON schema describing the fields you want. Usually generated by `YourModel.model_json_schema()`.  
3. **`extraction_type`** (str): `"schema"` or `"block"`.  
4. **`instruction`** (str): Prompt text telling the LLM what you want extracted. E.g., “Extract these fields as a JSON array.”  
5. **`chunk_token_threshold`** (int): Maximum tokens per chunk. If your content is huge, you can break it up for the LLM.  
6. **`overlap_rate`** (float): Overlap ratio between adjacent chunks. E.g., `0.1` means 10% of each chunk is repeated to preserve context continuity.  
7. **`apply_chunking`** (bool): Set `True` to chunk automatically. If you want a single pass, set `False`.  
8. **`input_format`** (str): Determines **which** crawler result is passed to the LLM. Options include:  
   - `"markdown"`: The raw markdown (default).  
   - `"fit_markdown"`: The filtered “fit” markdown if you used a content filter.  
   - `"html"`: The cleaned or raw HTML.  
9. **`extra_args`** (dict): Additional LLM parameters like `temperature`, `max_tokens`, `top_p`, etc.  
10. **`show_usage()`**: A method you can call to print out usage info (token usage per chunk, total cost if known).  
```python
extraction_strategy = LLMExtractionStrategy(
    llm_config = LLMConfig(provider="openai/gpt-4", api_token="YOUR_OPENAI_KEY"),
    schema=MyModel.model_json_schema(),
    extraction_type="schema",
    instruction="Extract a list of items from the text with 'name' and 'price' fields.",
    chunk_token_threshold=1200,
    overlap_rate=0.1,
    apply_chunking=True,
    input_format="html",
    extra_args={"temperature": 0.1, "max_tokens": 1000},
    verbose=True
)
```
## 5. Putting It in `CrawlerRunConfig`
**Important**: In Crawl4AI, all strategy definitions should go inside the `CrawlerRunConfig`, not directly as a param in `arun()`. Here’s a full example:
```python
import os
import asyncio
import json
from pydantic import BaseModel, Field
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai import LLMExtractionStrategy

class Product(BaseModel):
    name: str
    price: str

async def main():
    # 1. Define the LLM extraction strategy
    llm_strategy = LLMExtractionStrategy(
        llm_config = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv('OPENAI_API_KEY')),
        schema=Product.schema_json(), # Or use model_json_schema()
        extraction_type="schema",
        instruction="Extract all product objects with 'name' and 'price' from the content.",
        chunk_token_threshold=1000,
        overlap_rate=0.0,
        apply_chunking=True,
        input_format="markdown",   # or "html", "fit_markdown"
        extra_args={"temperature": 0.0, "max_tokens": 800}
    )

    # 2. Build the crawler config
    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS
    )

    # 3. Create a browser config if needed
    browser_cfg = BrowserConfig(headless=True)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # 4. Let's say we want to crawl a single page
        result = await crawler.arun(
            url="https://example.com/products",
            config=crawl_config
        )

        if result.success:
            # 5. The extracted content is presumably JSON
            data = json.loads(result.extracted_content)
            print("Extracted items:", data)

            # 6. Show usage stats
            llm_strategy.show_usage()  # prints token usage
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```
## 6. Chunking Details
### 6.1 `chunk_token_threshold`
If your page is large, you might exceed your LLM’s context window. **`chunk_token_threshold`** sets the approximate max tokens per chunk. The library calculates word→token ratio using `word_token_rate` (often ~0.75 by default). If chunking is enabled (`apply_chunking=True`), the text is split into segments.
### 6.2 `overlap_rate`
To keep context continuous across chunks, we can overlap them. E.g., `overlap_rate=0.1` means each subsequent chunk includes 10% of the previous chunk’s text. This is helpful if your needed info might straddle chunk boundaries.
### 6.3 Performance & Parallelism
## 7. Input Format
By default, **LLMExtractionStrategy** uses `input_format="markdown"`, meaning the **crawler’s final markdown** is fed to the LLM. You can change to:
- **`html`**: The cleaned HTML or raw HTML (depending on your crawler config) goes into the LLM.  
- **`fit_markdown`**: If you used, for instance, `PruningContentFilter`, the “fit” version of the markdown is used. This can drastically reduce tokens if you trust the filter.  
- **`markdown`**: Standard markdown output from the crawler’s `markdown_generator`.
This setting is crucial: if the LLM instructions rely on HTML tags, pick `"html"`. If you prefer a text-based approach, pick `"markdown"`.
```python
LLMExtractionStrategy(
    # ...
    input_format="html",  # Instead of "markdown" or "fit_markdown"
)
```
## 8. Token Usage & Show Usage
- **`usages`** (list): token usage per chunk or call.  
- **`total_usage`**: sum of all chunk calls.  
- **`show_usage()`**: prints a usage report (if the provider returns usage data).
```python
llm_strategy = LLMExtractionStrategy(...)
# ...
llm_strategy.show_usage()
# e.g. “Total usage: 1241 tokens across 2 chunk calls”
```
## 9. Example: Building a Knowledge Graph
Below is a snippet combining **`LLMExtractionStrategy`** with a Pydantic schema for a knowledge graph. Notice how we pass an **`instruction`** telling the model what to parse.
```python
import os
import json
import asyncio
from typing import List
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai import LLMExtractionStrategy

class Entity(BaseModel):
    name: str
    description: str

class Relationship(BaseModel):
    entity1: Entity
    entity2: Entity
    description: str
    relation_type: str

class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]

async def main():
    # LLM extraction strategy
    llm_strat = LLMExtractionStrategy(
        llmConfig = LLMConfig(provider="openai/gpt-4", api_token=os.getenv('OPENAI_API_KEY')),
        schema=KnowledgeGraph.model_json_schema(),
        extraction_type="schema",
        instruction="Extract entities and relationships from the content. Return valid JSON.",
        chunk_token_threshold=1400,
        apply_chunking=True,
        input_format="html",
        extra_args={"temperature": 0.1, "max_tokens": 1500}
    )

    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strat,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        # Example page
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, config=crawl_config)

        print("--- LLM RAW RESPONSE ---")
        print(result.extracted_content)
        print("--- END LLM RAW RESPONSE ---")

        if result.success:
            with open("kb_result.json", "w", encoding="utf-8") as f:
                f.write(result.extracted_content)
            llm_strat.show_usage()
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```
- **`extraction_type="schema"`** ensures we get JSON fitting our `KnowledgeGraph`.  
- **`input_format="html"`** means we feed HTML to the model.  
- **`instruction`** guides the model to output a structured knowledge graph.  
## 10. Best Practices & Caveats
4. **Schema Strictness**: `"schema"` extraction tries to parse the model output as JSON. If the model returns invalid JSON, partial extraction might happen, or you might get an error.  
## 11. Conclusion
- Put your LLM strategy **in `CrawlerRunConfig`**.  
- Use **`input_format`** to pick which form (markdown, HTML, fit_markdown) the LLM sees.  
- Tweak **`chunk_token_threshold`**, **`overlap_rate`**, and **`apply_chunking`** to handle large content efficiently.  
- Monitor token usage with `show_usage()`.
If your site’s data is consistent or repetitive, consider [`JsonCssExtractionStrategy`](./no-llm-strategies.md) first for speed and simplicity. But if you need an **AI-driven** approach, `LLMExtractionStrategy` offers a flexible, multi-provider solution for extracting structured JSON from any website.
1. **Experiment with Different Providers**  
   - Try switching the `provider` (e.g., `"ollama/llama2"`, `"openai/gpt-4o"`, etc.) to see differences in speed, accuracy, or cost.  
   - Pass different `extra_args` like `temperature`, `top_p`, and `max_tokens` to fine-tune your results.
2. **Performance Tuning**  
   - If pages are large, tweak `chunk_token_threshold`, `overlap_rate`, or `apply_chunking` to optimize throughput.  
   - Check the usage logs with `show_usage()` to keep an eye on token consumption and identify potential bottlenecks.
3. **Validate Outputs**  
   - If using `extraction_type="schema"`, parse the LLM’s JSON with a Pydantic model for a final validation step.  
4. **Explore Hooks & Automation**  



# Advanced Features

# Session Management
- **Performing JavaScript actions before and after crawling.**
Use `BrowserConfig` and `CrawlerRunConfig` to maintain state with a `session_id`:
```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async with AsyncWebCrawler() as crawler:
    session_id = "my_session"

    # Define configurations
    config1 = CrawlerRunConfig(
        url="https://example.com/page1", session_id=session_id
    )
    config2 = CrawlerRunConfig(
        url="https://example.com/page2", session_id=session_id
    )

    # First request
    result1 = await crawler.arun(config=config1)

    # Subsequent request using the same session
    result2 = await crawler.arun(config=config2)

    # Clean up when done
    await crawler.crawler_strategy.kill_session(session_id)
```
```python
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.cache_context import CacheMode

async def crawl_dynamic_content():
    url = "https://github.com/microsoft/TypeScript/commits/main"
    session_id = "wait_for_session"
    all_commits = []

    js_next_page = """
    const commits = document.querySelectorAll('li[data-testid="commit-row-item"] h4');
    if (commits.length > 0) {
        window.lastCommit = commits[0].textContent.trim();
    }
    const button = document.querySelector('a[data-testid="pagination-next-button"]');
    if (button) {button.click(); console.log('button clicked') }
    """

    wait_for = """() => {
        const commits = document.querySelectorAll('li[data-testid="commit-row-item"] h4');
        if (commits.length === 0) return false;
        const firstCommit = commits[0].textContent.trim();
        return firstCommit !== window.lastCommit;
    }"""

    schema = {
        "name": "Commit Extractor",
        "baseSelector": "li[data-testid='commit-row-item']",
        "fields": [
            {
                "name": "title",
                "selector": "h4 a",
                "type": "text",
                "transform": "strip",
            },
        ],
    }
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    browser_config = BrowserConfig(
        verbose=True,
        headless=False,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(3):
            crawler_config = CrawlerRunConfig(
                session_id=session_id,
                css_selector="li[data-testid='commit-row-item']",
                extraction_strategy=extraction_strategy,
                js_code=js_next_page if page > 0 else None,
                wait_for=wait_for if page > 0 else None,
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS,
                capture_console_messages=True,
            )

            result = await crawler.arun(url=url, config=crawler_config)

            if result.console_messages:
                print(f"Page {page + 1} console messages:", result.console_messages)

            if result.extracted_content:
                # print(f"Page {page + 1} result:", result.extracted_content)
                commits = json.loads(result.extracted_content)
                all_commits.extend(commits)
                print(f"Page {page + 1}: Found {len(commits)} commits")
            else:
                print(f"Page {page + 1}: No content extracted")

        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")
        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
```
## Example 1: Basic Session-Based Crawling
```python
import asyncio
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.cache_context import CacheMode

async def basic_session_crawl():
    async with AsyncWebCrawler() as crawler:
        session_id = "dynamic_content_session"
        url = "https://example.com/dynamic-content"

        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                js_code="document.querySelector('.load-more-button').click();" if page > 0 else None,
                css_selector=".content-item",
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            print(f"Page {page + 1}: Found {result.extracted_content.count('.content-item')} items")

        await crawler.crawler_strategy.kill_session(session_id)

asyncio.run(basic_session_crawl())
```
1. Reusing the same `session_id` across multiple requests.
2. Executing JavaScript to load more content dynamically.
3. Properly closing the session to free resources.
## Advanced Technique 1: Custom Execution Hooks
```python
async def advanced_session_crawl_with_hooks():
    first_commit = ""

    async def on_execution_started(page):
        nonlocal first_commit
        try:
            while True:
                await page.wait_for_selector("li.commit-item h4")
                commit = await page.query_selector("li.commit-item h4")
                commit = await commit.evaluate("(element) => element.textContent").strip()
                if commit and commit != first_commit:
                    first_commit = commit
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Warning: New content didn't appear: {e}")

    async with AsyncWebCrawler() as crawler:
        session_id = "commit_session"
        url = "https://github.com/example/repo/commits/main"
        crawler.crawler_strategy.set_hook("on_execution_started", on_execution_started)

        js_next_page = """document.querySelector('a.pagination-next').click();"""

        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                js_code=js_next_page if page > 0 else None,
                css_selector="li.commit-item",
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            print(f"Page {page + 1}: Found {len(result.extracted_content)} commits")

        await crawler.crawler_strategy.kill_session(session_id)

asyncio.run(advanced_session_crawl_with_hooks())
```
## Advanced Technique 2: Integrated JavaScript Execution and Waiting
```python
async def integrated_js_and_wait_crawl():
    async with AsyncWebCrawler() as crawler:
        session_id = "integrated_session"
        url = "https://github.com/example/repo/commits/main"

        js_next_page_and_wait = """
        (async () => {
            const getCurrentCommit = () => document.querySelector('li.commit-item h4').textContent.trim();
            const initialCommit = getCurrentCommit();
            document.querySelector('a.pagination-next').click();
            while (getCurrentCommit() === initialCommit) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        })();
        """

        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                js_code=js_next_page_and_wait if page > 0 else None,
                css_selector="li.commit-item",
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            print(f"Page {page + 1}: Found {len(result.extracted_content)} commits")

        await crawler.crawler_strategy.kill_session(session_id)

asyncio.run(integrated_js_and_wait_crawl())
```
1. **Authentication Flows**: Login and interact with secured pages.
2. **Pagination Handling**: Navigate through multiple pages.
3. **Form Submissions**: Fill forms, submit, and process results.
4. **Multi-step Processes**: Complete workflows that span multiple actions.


# Hooks & Auth in AsyncWebCrawler
1. **`on_browser_created`** – After browser creation.  
2. **`on_page_context_created`** – After a new context & page are created.  
3. **`before_goto`** – Just before navigating to a page.  
4. **`after_goto`** – Right after navigation completes.  
5. **`on_user_agent_updated`** – Whenever the user agent changes.  
6. **`on_execution_started`** – Once custom JavaScript execution begins.  
7. **`before_retrieve_html`** – Just before the crawler retrieves final HTML.  
8. **`before_return_html`** – Right before returning the HTML content.
**Important**: Avoid heavy tasks in `on_browser_created` since you don’t yet have a page context. If you need to *log in*, do so in **`on_page_context_created`**.
> note "Important Hook Usage Warning"
    **Avoid Misusing Hooks**: Do not manipulate page objects in the wrong hook or at the wrong time, as it can crash the pipeline or produce incorrect results. A common mistake is attempting to handle authentication prematurely—such as creating or closing pages in `on_browser_created`. 
>   **Use the Right Hook for Auth**: If you need to log in or set tokens, use `on_page_context_created`. This ensures you have a valid page/context to work with, without disrupting the main crawling flow.
## Example: Using Hooks in AsyncWebCrawler
```python
import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext

async def main():
    print("🔗 Hooks Example: Demonstrating recommended usage")

    # 1) Configure the browser
    browser_config = BrowserConfig(
        headless=True,
        verbose=True
    )

    # 2) Configure the crawler run
    crawler_run_config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        wait_for="body",
        cache_mode=CacheMode.BYPASS
    )

    # 3) Create the crawler instance
    crawler = AsyncWebCrawler(config=browser_config)

    #
    # Define Hook Functions
    #

    async def on_browser_created(browser, **kwargs):
        # Called once the browser instance is created (but no pages or contexts yet)
        print("[HOOK] on_browser_created - Browser created successfully!")
        # Typically, do minimal setup here if needed
        return browser

    async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
        # Called right after a new page + context are created (ideal for auth or route config).
        print("[HOOK] on_page_context_created - Setting up page & context.")

        # Example 1: Route filtering (e.g., block images)
        async def route_filter(route):
            if route.request.resource_type == "image":
                print(f"[HOOK] Blocking image request: {route.request.url}")
                await route.abort()
            else:
                await route.continue_()

        await context.route("**", route_filter)

        # Example 2: (Optional) Simulate a login scenario
        # (We do NOT create or close pages here, just do quick steps if needed)
        # e.g., await page.goto("https://example.com/login")
        # e.g., await page.fill("input[name='username']", "testuser")
        # e.g., await page.fill("input[name='password']", "password123")
        # e.g., await page.click("button[type='submit']")
        # e.g., await page.wait_for_selector("#welcome")
        # e.g., await context.add_cookies([...])
        # Then continue

        # Example 3: Adjust the viewport
        await page.set_viewport_size({"width": 1080, "height": 600})
        return page

    async def before_goto(
        page: Page, context: BrowserContext, url: str, **kwargs
    ):
        # Called before navigating to each URL.
        print(f"[HOOK] before_goto - About to navigate: {url}")
        # e.g., inject custom headers
        await page.set_extra_http_headers({
            "Custom-Header": "my-value"
        })
        return page

    async def after_goto(
        page: Page, context: BrowserContext, 
        url: str, response, **kwargs
    ):
        # Called after navigation completes.
        print(f"[HOOK] after_goto - Successfully loaded: {url}")
        # e.g., wait for a certain element if we want to verify
        try:
            await page.wait_for_selector('.content', timeout=1000)
            print("[HOOK] Found .content element!")
        except:
            print("[HOOK] .content not found, continuing anyway.")
        return page

    async def on_user_agent_updated(
        page: Page, context: BrowserContext, 
        user_agent: str, **kwargs
    ):
        # Called whenever the user agent updates.
        print(f"[HOOK] on_user_agent_updated - New user agent: {user_agent}")
        return page

    async def on_execution_started(page: Page, context: BrowserContext, **kwargs):
        # Called after custom JavaScript execution begins.
        print("[HOOK] on_execution_started - JS code is running!")
        return page

    async def before_retrieve_html(page: Page, context: BrowserContext, **kwargs):
        # Called before final HTML retrieval.
        print("[HOOK] before_retrieve_html - We can do final actions")
        # Example: Scroll again
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        return page

    async def before_return_html(
        page: Page, context: BrowserContext, html: str, **kwargs
    ):
        # Called just before returning the HTML in the result.
        print(f"[HOOK] before_return_html - HTML length: {len(html)}")
        return page

    #
    # Attach Hooks
    #

    crawler.crawler_strategy.set_hook("on_browser_created", on_browser_created)
    crawler.crawler_strategy.set_hook(
        "on_page_context_created", on_page_context_created
    )
    crawler.crawler_strategy.set_hook("before_goto", before_goto)
    crawler.crawler_strategy.set_hook("after_goto", after_goto)
    crawler.crawler_strategy.set_hook(
        "on_user_agent_updated", on_user_agent_updated
    )
    crawler.crawler_strategy.set_hook(
        "on_execution_started", on_execution_started
    )
    crawler.crawler_strategy.set_hook(
        "before_retrieve_html", before_retrieve_html
    )
    crawler.crawler_strategy.set_hook(
        "before_return_html", before_return_html
    )

    await crawler.start()

    # 4) Run the crawler on an example page
    url = "https://example.com"
    result = await crawler.arun(url, config=crawler_run_config)

    if result.success:
        print("\nCrawled URL:", result.url)
        print("HTML length:", len(result.html))
    else:
        print("Error:", result.error_message)

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())
```
## Hook Lifecycle Summary
1. **`on_browser_created`**:  
   - Browser is up, but **no** pages or contexts yet.  
   - Light setup only—don’t try to open or close pages here (that belongs in `on_page_context_created`).
2. **`on_page_context_created`**:  
   - Perfect for advanced **auth** or route blocking.  
3. **`before_goto`**:  
4. **`after_goto`**:  
5. **`on_user_agent_updated`**:  
   - Whenever the user agent changes (for stealth or different UA modes).
6. **`on_execution_started`**:  
   - If you set `js_code` or run custom scripts, this runs once your JS is about to start.
7. **`before_retrieve_html`**:  
8. **`before_return_html`**:  
   - The last hook before returning HTML to the `CrawlResult`. Good for logging HTML length or minor modifications.
## When to Handle Authentication
**Recommended**: Use **`on_page_context_created`** if you need to:
- Navigate to a login page or fill forms
- Set cookies or localStorage tokens
- Block resource routes to avoid ads
This ensures the newly created context is under your control **before** `arun()` navigates to the main URL.
## Additional Considerations
- **Session Management**: If you want multiple `arun()` calls to reuse a single session, pass `session_id=` in your `CrawlerRunConfig`. Hooks remain the same.  
- **Concurrency**: If you run `arun_many()`, each URL triggers these hooks in parallel. Ensure your hooks are thread/async-safe.
## Conclusion
- **Browser** creation (light tasks only)
- **Page** and **context** creation (auth, route blocking)
- **Navigation** phases
- **Final HTML** retrieval
- **Login** or advanced tasks in `on_page_context_created`  
- **Custom headers** or logs in `before_goto` / `after_goto`  
- **Scrolling** or final checks in `before_retrieve_html` / `before_return_html`



---

# Quick Reference

## Core Imports
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy, CosineStrategy
```

## Basic Pattern
```python
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
    print(result.markdown)
```

## Advanced Pattern
```python
browser_config = BrowserConfig(headless=True, viewport_width=1920)
crawler_config = CrawlerConfig(
    cache_mode=CacheMode.BYPASS,
    wait_for="css:.content",
    screenshot=True,
    pdf=True
)
strategy = LLMExtractionStrategy(
    provider="openai/gpt-4",
    instruction="Extract products with name and price"
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        config=crawler_config,
        extraction_strategy=strategy
    )
```

## Multi-URL Pattern
```python
urls = ["https://example.com/1", "https://example.com/2"]
results = await crawler.arun_many(urls, config=crawler_config)
```

---

**End of Crawl4AI SDK Documentation**
