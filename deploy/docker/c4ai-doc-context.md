# Crawl4AI Doc Context

Generated on 2025-04-21

## File: docs/md_v2/core/ask-ai.md

```md
<div class="ask-ai-container">
<iframe id="ask-ai-frame" src="../../ask_ai/index.html" width="100%" style="border:none; display: block;" title="Crawl4AI Assistant"></iframe>
</div>

<script>
// Iframe height adjustment
function resizeAskAiIframe() {
  const iframe = document.getElementById('ask-ai-frame');
  if (iframe) {
    const headerHeight = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-height') || '55');
    // Footer is removed by JS below, so calculate height based on header + small buffer
    const topOffset = headerHeight + 20; // Header + buffer/margin

    const availableHeight = window.innerHeight - topOffset;
    iframe.style.height = Math.max(600, availableHeight) + 'px'; // Min height 600px
  }
}

// Run immediately and on resize/load
resizeAskAiIframe(); // Initial call
let resizeTimer;
window.addEventListener('load', resizeAskAiIframe);
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(resizeAskAiIframe, 150);
});

// Remove Footer & HR from parent page (DOM Ready might be safer)
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => { // Add slight delay just in case elements render slowly
        const footer = window.parent.document.querySelector('footer'); // Target parent document
        if (footer) {
            const hrBeforeFooter = footer.previousElementSibling;
            if (hrBeforeFooter && hrBeforeFooter.tagName === 'HR') {
                hrBeforeFooter.remove();
            }
            footer.remove();
            // Trigger resize again after removing footer
            resizeAskAiIframe();
        } else {
             console.warn("Ask AI Page: Could not find footer in parent document to remove.");
        }
    }, 100); // Shorter delay
});
</script>

<style>
#terminal-mkdocs-main-content {
    padding: 0 !important;
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden; /* Prevent body scrollbars, panels handle scroll */
}

/* Ensure iframe container takes full space */
#terminal-mkdocs-main-content .ask-ai-container {
    /* Remove negative margins if footer removal handles space */
     margin: 0;
    padding: 0;
    max-width: none;
    /* Let the JS set the height */
    /* height: 600px; Initial fallback height */
    overflow: hidden; /* Hide potential overflow before JS resize */
}

/* Hide title/paragraph if they were part of the markdown */
/* Alternatively, just remove them from the .md file directly */
/* #terminal-mkdocs-main-content > h1,
#terminal-mkdocs-main-content > p:first-of-type {
    display: none;
} */

</style>

```


## File: docs/md_v2/core/browser-crawler-config.md

```md
# Browser, Crawler & LLM Configuration (Quick Overview)

Crawl4AI’s flexibility stems from two key classes:

1. **`BrowserConfig`** – Dictates **how** the browser is launched and behaves (e.g., headless or visible, proxy, user agent).  
2. **`CrawlerRunConfig`** – Dictates **how** each **crawl** operates (e.g., caching, extraction, timeouts, JavaScript code to run, etc.).  
3. **`LLMConfig`** - Dictates **how** LLM providers are configured. (model, api token, base url, temperature etc.)

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
        capture_mhtml=False,
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

7. **`screenshot`**, **`pdf`**, & **`capture_mhtml`**:  
   - If `True`, captures a screenshot, PDF, or MHTML snapshot after the page is fully loaded.  
   - The results go to `result.screenshot` (base64), `result.pdf` (bytes), or `result.mhtml` (string).
8. **`verbose`**:  
   - Logs additional runtime details.  
   - Overlaps with the browser’s verbosity if also set to `True` in `BrowserConfig`.

9. **`enable_rate_limiting`**:  
   - If `True`, enables rate limiting for batch processing.  
   - Requires `rate_limit_config` to be set.

10. **`memory_threshold_percent`**:  
    - The memory threshold (as a percentage) to monitor.  
    - If exceeded, the crawler will pause or slow down.

11. **`check_interval`**:  
    - The interval (in seconds) to check system resources.  
    - Affects how often memory and CPU usage are monitored.

12. **`max_session_permit`**:  
    - The maximum number of concurrent crawl sessions.  
    - Helps prevent overwhelming the system.

13. **`display_mode`**:  
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

---





## 3. LLMConfig Essentials

### Key fields to note

1. **`provider`**:  
- Which LLM provider to use. 
- Possible values are `"ollama/llama3","groq/llama3-70b-8192","groq/llama3-8b-8192", "openai/gpt-4o-mini" ,"openai/gpt-4o","openai/o1-mini","openai/o1-preview","openai/o3-mini","openai/o3-mini-high","anthropic/claude-3-haiku-20240307","anthropic/claude-3-opus-20240229","anthropic/claude-3-sonnet-20240229","anthropic/claude-3-5-sonnet-20240620","gemini/gemini-pro","gemini/gemini-1.5-pro","gemini/gemini-2.0-flash","gemini/gemini-2.0-flash-exp","gemini/gemini-2.0-flash-lite-preview-02-05","deepseek/deepseek-chat"`<br/>*(default: `"openai/gpt-4o-mini"`)*

2. **`api_token`**:  
    - Optional. When not provided explicitly, api_token will be read from environment variables based on provider. For example: If a gemini model is passed as provider then,`"GEMINI_API_KEY"` will be read from environment variables  
    - API token of LLM provider <br/> eg: `api_token = "gsk_1ClHGGJ7Lpn4WGybR7vNWGdyb3FY7zXEw3SCiy0BAVM9lL8CQv"`
    - Environment variable - use with prefix "env:" <br/> eg:`api_token = "env: GROQ_API_KEY"`            

3. **`base_url`**:  
   - If your provider has a custom endpoint

```python
llm_config = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))
```

## 4. Putting It All Together

In a typical scenario, you define **one** `BrowserConfig` for your crawler session, then create **one or more** `CrawlerRunConfig` & `LLMConfig` depending on each call’s needs:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
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
        provider="gemini/gemini-1.5-pro" 
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
    options={"ignore_links": True})

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
```


## File: docs/md_v2/core/cache-modes.md

```md
# Crawl4AI Cache System and Migration Guide

## Overview
Starting from version 0.5.0, Crawl4AI introduces a new caching system that replaces the old boolean flags with a more intuitive `CacheMode` enum. This change simplifies cache control and makes the behavior more predictable.

## Old vs New Approach

### Old Way (Deprecated)
The old system used multiple boolean flags:
- `bypass_cache`: Skip cache entirely
- `disable_cache`: Disable all caching
- `no_cache_read`: Don't read from cache
- `no_cache_write`: Don't write to cache

### New Way (Recommended)
The new system uses a single `CacheMode` enum:
- `CacheMode.ENABLED`: Normal caching (read/write)
- `CacheMode.DISABLED`: No caching at all
- `CacheMode.READ_ONLY`: Only read from cache
- `CacheMode.WRITE_ONLY`: Only write to cache
- `CacheMode.BYPASS`: Skip cache for this operation

## Migration Example

### Old Code (Deprecated)
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def use_proxy():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            bypass_cache=True  # Old way
        )
        print(len(result.markdown))

async def main():
    await use_proxy()

if __name__ == "__main__":
    asyncio.run(main())
```

### New Code (Recommended)
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig

async def use_proxy():
    # Use CacheMode in CrawlerRunConfig
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)  
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            config=config  # Pass the configuration object
        )
        print(len(result.markdown))

async def main():
    await use_proxy()

if __name__ == "__main__":
    asyncio.run(main())
```

## Common Migration Patterns

| Old Flag              | New Mode                       |
|-----------------------|---------------------------------|
| `bypass_cache=True`   | `cache_mode=CacheMode.BYPASS`  |
| `disable_cache=True`  | `cache_mode=CacheMode.DISABLED`|
| `no_cache_read=True`  | `cache_mode=CacheMode.WRITE_ONLY` |
| `no_cache_write=True` | `cache_mode=CacheMode.READ_ONLY` |
```


## File: docs/md_v2/core/cli.md

```md
# Crawl4AI CLI Guide

## Table of Contents
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Configuration](#configuration)
  - [Browser Configuration](#browser-configuration)
  - [Crawler Configuration](#crawler-configuration)
  - [Extraction Configuration](#extraction-configuration)
  - [Content Filtering](#content-filtering)
- [Advanced Features](#advanced-features)
  - [LLM Q&A](#llm-qa)
  - [Structured Data Extraction](#structured-data-extraction)
  - [Content Filtering](#content-filtering-1)
- [Output Formats](#output-formats)
- [Examples](#examples)
- [Configuration Reference](#configuration-reference)
- [Best Practices & Tips](#best-practices--tips)

## Basic Usage

The Crawl4AI CLI (`crwl`) provides a simple interface to the Crawl4AI library:

```bash
# Basic crawling
crwl https://example.com

# Get markdown output
crwl https://example.com -o markdown

# Verbose JSON output with cache bypass
crwl https://example.com -o json -v --bypass-cache

# See usage examples
crwl --example
```

## Quick Example of Advanced Usage

If you clone the repository and run the following command, you will receive the content of the page in JSON format according to a JSON-CSS schema:

```bash
crwl "https://www.infoq.com/ai-ml-data-eng/" -e docs/examples/cli/extract_css.yml -s docs/examples/cli/css_schema.json -o json;
```

## Configuration

### Browser Configuration

Browser settings can be configured via YAML file or command line parameters:

```yaml
# browser.yml
headless: true
viewport_width: 1280
user_agent_mode: "random"
verbose: true
ignore_https_errors: true
```

```bash
# Using config file
crwl https://example.com -B browser.yml

# Using direct parameters
crwl https://example.com -b "headless=true,viewport_width=1280,user_agent_mode=random"
```

### Crawler Configuration

Control crawling behavior:

```yaml
# crawler.yml
cache_mode: "bypass"
wait_until: "networkidle"
page_timeout: 30000
delay_before_return_html: 0.5
word_count_threshold: 100
scan_full_page: true
scroll_delay: 0.3
process_iframes: false
remove_overlay_elements: true
magic: true
verbose: true
```

```bash
# Using config file
crwl https://example.com -C crawler.yml

# Using direct parameters
crwl https://example.com -c "css_selector=#main,delay_before_return_html=2,scan_full_page=true"
```

### Extraction Configuration

Two types of extraction are supported:

1. CSS/XPath-based extraction:
```yaml
# extract_css.yml
type: "json-css"
params:
  verbose: true
```

```json
// css_schema.json
{
  "name": "ArticleExtractor",
  "baseSelector": ".article",
  "fields": [
    {
      "name": "title",
      "selector": "h1.title",
      "type": "text"
    },
    {
      "name": "link",
      "selector": "a.read-more",
      "type": "attribute",
      "attribute": "href"
    }
  ]
}
```

2. LLM-based extraction:
```yaml
# extract_llm.yml
type: "llm"
provider: "openai/gpt-4"
instruction: "Extract all articles with their titles and links"
api_token: "your-token"
params:
  temperature: 0.3
  max_tokens: 1000
```

```json
// llm_schema.json
{
  "title": "Article",
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "The title of the article"
    },
    "link": {
      "type": "string",
      "description": "URL to the full article"
    }
  }
}
```

## Advanced Features

### LLM Q&A

Ask questions about crawled content:

```bash
# Simple question
crwl https://example.com -q "What is the main topic discussed?"

# View content then ask questions
crwl https://example.com -o markdown  # See content first
crwl https://example.com -q "Summarize the key points"
crwl https://example.com -q "What are the conclusions?"

# Combined with advanced crawling
crwl https://example.com \
    -B browser.yml \
    -c "css_selector=article,scan_full_page=true" \
    -q "What are the pros and cons mentioned?"
```

First-time setup:
- Prompts for LLM provider and API token
- Saves configuration in `~/.crawl4ai/global.yml`
- Supports various providers (openai/gpt-4, anthropic/claude-3-sonnet, etc.)
- For case of `ollama` you do not need to provide API token.
- See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for full list

### Structured Data Extraction

Extract structured data using CSS selectors:

```bash
crwl https://example.com \
    -e extract_css.yml \
    -s css_schema.json \
    -o json
```

Or using LLM-based extraction:

```bash
crwl https://example.com \
    -e extract_llm.yml \
    -s llm_schema.json \
    -o json
```

### Content Filtering

Filter content for relevance:

```yaml
# filter_bm25.yml
type: "bm25"
query: "target content"
threshold: 1.0

# filter_pruning.yml
type: "pruning"
query: "focus topic"
threshold: 0.48
```

```bash
crwl https://example.com -f filter_bm25.yml -o markdown-fit
```

## Output Formats

- `all` - Full crawl result including metadata
- `json` - Extracted structured data (when using extraction)
- `markdown` / `md` - Raw markdown output
- `markdown-fit` / `md-fit` - Filtered markdown for better readability

## Complete Examples

1. Basic Extraction:
```bash
crwl https://example.com \
    -B browser.yml \
    -C crawler.yml \
    -o json
```

2. Structured Data Extraction:
```bash
crwl https://example.com \
    -e extract_css.yml \
    -s css_schema.json \
    -o json \
    -v
```

3. LLM Extraction with Filtering:
```bash
crwl https://example.com \
    -B browser.yml \
    -e extract_llm.yml \
    -s llm_schema.json \
    -f filter_bm25.yml \
    -o json
```

4. Interactive Q&A:
```bash
# First crawl and view
crwl https://example.com -o markdown

# Then ask questions
crwl https://example.com -q "What are the main points?"
crwl https://example.com -q "Summarize the conclusions"
```

## Best Practices & Tips

1. **Configuration Management**:
   - Keep common configurations in YAML files
   - Use CLI parameters for quick overrides
   - Store sensitive data (API tokens) in `~/.crawl4ai/global.yml`

2. **Performance Optimization**:
   - Use `--bypass-cache` for fresh content
   - Enable `scan_full_page` for infinite scroll pages
   - Adjust `delay_before_return_html` for dynamic content

3. **Content Extraction**:
   - Use CSS extraction for structured content
   - Use LLM extraction for unstructured content
   - Combine with filters for focused results

4. **Q&A Workflow**:
   - View content first with `-o markdown`
   - Ask specific questions
   - Use broader context with appropriate selectors

## Recap

The Crawl4AI CLI provides:
- Flexible configuration via files and parameters
- Multiple extraction strategies (CSS, XPath, LLM)
- Content filtering and optimization
- Interactive Q&A capabilities
- Various output formats


```


## File: docs/md_v2/core/content-selection.md

```md
# Content Selection

Crawl4AI provides multiple ways to **select**, **filter**, and **refine** the content from your crawls. Whether you need to target a specific CSS region, exclude entire tags, filter out external links, or remove certain domains and images, **`CrawlerRunConfig`** offers a wide range of parameters.

Below, we show how to configure these parameters and combine them for precise control.

---

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

---

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

**Explanation**:

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

**Note**: If these parameters remove too much, reduce or disable them accordingly.

---

## 3. Handling Iframes

Some sites embed content in `<iframe>` tags. If you want that inline:
```python
config = CrawlerRunConfig(
    # Merge iframe content into the final output
    process_iframes=True,    
    remove_overlay_elements=True
)
```

**Usage**:
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

---

## 4. Structured Extraction Examples

You can combine content selection with a more advanced extraction strategy. For instance, a **CSS-based** or **LLM-based** extraction strategy can run on the filtered HTML.

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

Here, the crawler:

- Filters out external links (`exclude_external_links=True`).  
- Ignores very short text blocks (`word_count_threshold=20`).  
- Passes the final HTML to your LLM strategy for an AI-driven parse.

---

## 5. Comprehensive Example

Below is a short function that unifies **CSS selection**, **exclusion** logic, and a pattern-based extraction, demonstrating how you can fine-tune your final data:

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

**Why This Works**:
- **CSS** scoping with `#main-content`.  
- Multiple **exclude_** parameters to remove domains, external images, etc.  
- A **JsonCssExtractionStrategy** to parse repeated article blocks.

---

## 6. Scraping Modes

Crawl4AI provides two different scraping strategies for HTML content processing: `WebScrapingStrategy` (BeautifulSoup-based, default) and `LXMLWebScrapingStrategy` (LXML-based). The LXML strategy offers significantly better performance, especially for large HTML documents.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LXMLWebScrapingStrategy

async def main():
    config = CrawlerRunConfig(
        scraping_strategy=LXMLWebScrapingStrategy()  # Faster alternative to default BeautifulSoup
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

The LXML strategy can be up to 10-20x faster than BeautifulSoup strategy, particularly when processing large HTML documents. However, please note:

1. LXML strategy is currently experimental
2. In some edge cases, the parsing results might differ slightly from BeautifulSoup
3. If you encounter any inconsistencies between LXML and BeautifulSoup results, please [raise an issue](https://github.com/codeium/crawl4ai/issues) with a reproducible example

Choose LXML strategy when:
- Processing large HTML documents (recommended for >100KB)
- Performance is critical
- Working with well-formed HTML

Stick to BeautifulSoup strategy (default) when:
- Maximum compatibility is needed
- Working with malformed HTML
- Exact parsing behavior is critical

---

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

This approach gives you the best of both worlds:
- Markdown generation and content extraction focus on the elements you care about
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

Combine these with structured extraction (CSS, LLM-based, or others) to build powerful crawls that yield exactly the content you want, from raw or cleaned HTML up to sophisticated JSON structures. For more detail, see [Configuration Reference](../api/parameters.md). Enjoy curating your data to the max!
```


## File: docs/md_v2/core/crawler-result.md

```md
# Crawl Result and Output

When you call `arun()` on a page, Crawl4AI returns a **`CrawlResult`** object containing everything you might need—raw HTML, a cleaned version, optional screenshots or PDFs, structured extraction results, and more. This document explains those fields and how they map to different output types.  

---

## 1. The `CrawlResult` Model

Below is the core schema. Each field captures a different aspect of the crawl’s result:

```python
class MarkdownGenerationResult(BaseModel):
    raw_markdown: str
    markdown_with_citations: str
    references_markdown: str
    fit_markdown: Optional[str] = None
    fit_html: Optional[str] = None

class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: Optional[str] = None
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
    class Config:
        arbitrary_types_allowed = True
```

### Table: Key Fields in `CrawlResult`

| Field (Name & Type)                       | Description                                                                                         |
|-------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **url (`str`)**                           | The final or actual URL crawled (in case of redirects).                                             |
| **html (`str`)**                          | Original, unmodified page HTML. Good for debugging or custom processing.                            |
| **success (`bool`)**                      | `True` if the crawl completed without major errors, else `False`.                                   |
| **cleaned_html (`Optional[str]`)**        | Sanitized HTML with scripts/styles removed; can exclude tags if configured via `excluded_tags` etc. |
| **media (`Dict[str, List[Dict]]`)**       | Extracted media info (images, audio, etc.), each with attributes like `src`, `alt`, `score`, etc.   |
| **links (`Dict[str, List[Dict]]`)**       | Extracted link data, split by `internal` and `external`. Each link usually has `href`, `text`, etc. |
| **downloaded_files (`Optional[List[str]]`)** | If `accept_downloads=True` in `BrowserConfig`, this lists the filepaths of saved downloads.         |
| **screenshot (`Optional[str]`)**          | Screenshot of the page (base64-encoded) if `screenshot=True`.                                       |
| **pdf (`Optional[bytes]`)**               | PDF of the page if `pdf=True`.                                                                      |
| **mhtml (`Optional[str]`)**               | MHTML snapshot of the page if `capture_mhtml=True`. Contains the full page with all resources.      |
| **markdown (`Optional[str or MarkdownGenerationResult]`)** | It holds a `MarkdownGenerationResult`. Over time, this will be consolidated into `markdown`. The generator can provide raw markdown, citations, references, and optionally `fit_markdown`. |
| **extracted_content (`Optional[str]`)**   | The output of a structured extraction (CSS/LLM-based) stored as JSON string or other text.          |
| **metadata (`Optional[dict]`)**           | Additional info about the crawl or extracted data.                                                  |
| **error_message (`Optional[str]`)**       | If `success=False`, contains a short description of what went wrong.                                |
| **session_id (`Optional[str]`)**          | The ID of the session used for multi-page or persistent crawling.                                   |
| **response_headers (`Optional[dict]`)**   | HTTP response headers, if captured.                                                                 |
| **status_code (`Optional[int]`)**         | HTTP status code (e.g., 200 for OK).                                                                |
| **ssl_certificate (`Optional[SSLCertificate]`)** | SSL certificate info if `fetch_ssl_certificate=True`.                                               |

---

## 2. HTML Variants

### `html`: Raw HTML

Crawl4AI preserves the exact HTML as `result.html`. Useful for:

- Debugging page issues or checking the original content.
- Performing your own specialized parse if needed.

### `cleaned_html`: Sanitized

If you specify any cleanup or exclusion parameters in `CrawlerRunConfig` (like `excluded_tags`, `remove_forms`, etc.), you’ll see the result here:

```python
config = CrawlerRunConfig(
    excluded_tags=["form", "header", "footer"],
    keep_data_attributes=False
)
result = await crawler.arun("https://example.com", config=config)
print(result.cleaned_html)  # Freed of forms, header, footer, data-* attributes
```

---

## 3. Markdown Generation

### 3.1 `markdown`

- **`markdown`**: The current location for detailed markdown output, returning a **`MarkdownGenerationResult`** object.  
- **`markdown_v2`**: Deprecated since v0.5.

**`MarkdownGenerationResult`** Fields:

| Field                   | Description                                                                    |
|-------------------------|--------------------------------------------------------------------------------|
| **raw_markdown**        | The basic HTML→Markdown conversion.                                            |
| **markdown_with_citations** | Markdown including inline citations that reference links at the end.        |
| **references_markdown** | The references/citations themselves (if `citations=True`).                      |
| **fit_markdown**        | The filtered/“fit” markdown if a content filter was used.                       |
| **fit_html**            | The filtered HTML that generated `fit_markdown`.                                |

### 3.2 Basic Example with a Markdown Generator

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        options={"citations": True, "body_width": 80}  # e.g. pass html2text style options
    )
)
result = await crawler.arun(url="https://example.com", config=config)

md_res = result.markdown  # or eventually 'result.markdown'
print(md_res.raw_markdown[:500])
print(md_res.markdown_with_citations)
print(md_res.references_markdown)
```

**Note**: If you use a filter like `PruningContentFilter`, you’ll get `fit_markdown` and `fit_html` as well.

---

## 4. Structured Extraction: `extracted_content`

If you run a JSON-based extraction strategy (CSS, XPath, LLM, etc.), the structured data is **not** stored in `markdown`—it’s placed in **`result.extracted_content`** as a JSON string (or sometimes plain text).

### Example: CSS Extraction with `raw://` HTML

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
        data = json.loads(result.extracted_content)
        print(data)

if __name__ == "__main__":
    asyncio.run(main())
```

Here:
- `url="raw://..."` passes the HTML content directly, no network requests.  
- The **CSS** extraction strategy populates `result.extracted_content` with the JSON array `[{"title": "...", "link": "..."}]`.

---

## 5. More Fields: Links, Media, and More

### 5.1 `links`

A dictionary, typically with `"internal"` and `"external"` lists. Each entry might have `href`, `text`, `title`, etc. This is automatically captured if you haven’t disabled link extraction.

```python
print(result.links["internal"][:3])  # Show first 3 internal links
```

### 5.2 `media`

Similarly, a dictionary with `"images"`, `"audio"`, `"video"`, etc. Each item could include `src`, `alt`, `score`, and more, if your crawler is set to gather them.

```python
images = result.media.get("images", [])
for img in images:
    print("Image URL:", img["src"], "Alt:", img.get("alt"))
```

### 5.3 `screenshot`, `pdf`, and `mhtml`

If you set `screenshot=True`, `pdf=True`, or `capture_mhtml=True` in **`CrawlerRunConfig`**, then:

- `result.screenshot` contains a base64-encoded PNG string.
- `result.pdf` contains raw PDF bytes (you can write them to a file).
- `result.mhtml` contains the MHTML snapshot of the page as a string (you can write it to a .mhtml file).

```python
# Save the PDF
with open("page.pdf", "wb") as f:
    f.write(result.pdf)

# Save the MHTML
if result.mhtml:
    with open("page.mhtml", "w", encoding="utf-8") as f:
        f.write(result.mhtml)
```

The MHTML (MIME HTML) format is particularly useful as it captures the entire web page including all of its resources (CSS, images, scripts, etc.) in a single file, making it perfect for archiving or offline viewing.

### 5.4 `ssl_certificate`

If `fetch_ssl_certificate=True`, `result.ssl_certificate` holds details about the site’s SSL cert, such as issuer, validity dates, etc.

---

## 6. Accessing These Fields

After you run:

```python
result = await crawler.arun(url="https://example.com", config=some_config)
```

Check any field:

```python
if result.success:
    print(result.status_code, result.response_headers)
    print("Links found:", len(result.links.get("internal", [])))
    if result.markdown:
        print("Markdown snippet:", result.markdown.raw_markdown[:200])
    if result.extracted_content:
        print("Structured JSON:", result.extracted_content)
else:
    print("Error:", result.error_message)
```

**Deprecation**: Since v0.5 `result.markdown_v2`, `result.fit_html`,`result.fit_markdown` are deprecated. Use `result.markdown` instead! It holds `MarkdownGenerationResult`, which includes `fit_html` and `fit_markdown`
as it's properties.


---

## 7. Next Steps

- **Markdown Generation**: Dive deeper into how to configure `DefaultMarkdownGenerator` and various filters.  
- **Content Filtering**: Learn how to use `BM25ContentFilter` and `PruningContentFilter`.
- **Session & Hooks**: If you want to manipulate the page or preserve state across multiple `arun()` calls, see the hooking or session docs.  
- **LLM Extraction**: For complex or unstructured content requiring AI-driven parsing, check the LLM-based strategies doc.

**Enjoy** exploring all that `CrawlResult` offers—whether you need raw HTML, sanitized output, markdown, or fully structured data, Crawl4AI has you covered!
```


## File: docs/md_v2/core/deep-crawling.md

```md
# Deep Crawling

One of Crawl4AI's most powerful features is its ability to perform **configurable deep crawling** that can explore websites beyond a single page. With fine-tuned control over crawl depth, domain boundaries, and content filtering, Crawl4AI gives you the tools to extract precisely the content you need.

In this tutorial, you'll learn:

1. How to set up a **Basic Deep Crawler** with BFS strategy  
2. Understanding the difference between **streamed and non-streamed** output  
3. Implementing **filters and scorers** to target specific content  
4. Creating **advanced filtering chains** for sophisticated crawls  
5. Using **BestFirstCrawling** for intelligent exploration prioritization  

> **Prerequisites**  
> - You’ve completed or read [AsyncWebCrawler Basics](../core/simple-crawling.md) to understand how to run a simple crawl.  
> - You know how to configure `CrawlerRunConfig`.

---

## 1. Quick Example

Here's a minimal code snippet that implements a basic deep crawl using the **BFSDeepCrawlStrategy**:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

async def main():
    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2, 
            include_external=False
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun("https://example.com", config=config)
        
        print(f"Crawled {len(results)} pages in total")
        
        # Access individual results
        for result in results[:3]:  # Show first 3 results
            print(f"URL: {result.url}")
            print(f"Depth: {result.metadata.get('depth', 0)}")

if __name__ == "__main__":
    asyncio.run(main())
```

**What's happening?**  
- `BFSDeepCrawlStrategy(max_depth=2, include_external=False)` instructs Crawl4AI to:
  - Crawl the starting page (depth 0) plus 2 more levels
  - Stay within the same domain (don't follow external links)
- Each result contains metadata like the crawl depth
- Results are returned as a list after all crawling is complete

---

## 2. Understanding Deep Crawling Strategy Options

### 2.1 BFSDeepCrawlStrategy (Breadth-First Search)

The **BFSDeepCrawlStrategy** uses a breadth-first approach, exploring all links at one depth before moving deeper:

```python
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

# Basic configuration
strategy = BFSDeepCrawlStrategy(
    max_depth=2,               # Crawl initial page + 2 levels deep
    include_external=False,    # Stay within the same domain
    max_pages=50,              # Maximum number of pages to crawl (optional)
    score_threshold=0.3,       # Minimum score for URLs to be crawled (optional)
)
```

**Key parameters:**
- **`max_depth`**: Number of levels to crawl beyond the starting page
- **`include_external`**: Whether to follow links to other domains
- **`max_pages`**: Maximum number of pages to crawl (default: infinite)
- **`score_threshold`**: Minimum score for URLs to be crawled (default: -inf)
- **`filter_chain`**: FilterChain instance for URL filtering
- **`url_scorer`**: Scorer instance for evaluating URLs

### 2.2 DFSDeepCrawlStrategy (Depth-First Search)

The **DFSDeepCrawlStrategy** uses a depth-first approach, explores as far down a branch as possible before backtracking.

```python
from crawl4ai.deep_crawling import DFSDeepCrawlStrategy

# Basic configuration
strategy = DFSDeepCrawlStrategy(
    max_depth=2,               # Crawl initial page + 2 levels deep
    include_external=False,    # Stay within the same domain
    max_pages=30,              # Maximum number of pages to crawl (optional)
    score_threshold=0.5,       # Minimum score for URLs to be crawled (optional)
)
```

**Key parameters:**
- **`max_depth`**: Number of levels to crawl beyond the starting page
- **`include_external`**: Whether to follow links to other domains
- **`max_pages`**: Maximum number of pages to crawl (default: infinite)
- **`score_threshold`**: Minimum score for URLs to be crawled (default: -inf)
- **`filter_chain`**: FilterChain instance for URL filtering
- **`url_scorer`**: Scorer instance for evaluating URLs

### 2.3 BestFirstCrawlingStrategy (⭐️ - Recommended Deep crawl strategy)

For more intelligent crawling, use **BestFirstCrawlingStrategy** with scorers to prioritize the most relevant pages:

```python
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

# Create a scorer
scorer = KeywordRelevanceScorer(
    keywords=["crawl", "example", "async", "configuration"],
    weight=0.7
)

# Configure the strategy
strategy = BestFirstCrawlingStrategy(
    max_depth=2,
    include_external=False,
    url_scorer=scorer,
    max_pages=25,              # Maximum number of pages to crawl (optional)
)
```

This crawling approach:
- Evaluates each discovered URL based on scorer criteria
- Visits higher-scoring pages first
- Helps focus crawl resources on the most relevant content
- Can limit total pages crawled with `max_pages`
- Does not need `score_threshold` as it naturally prioritizes by score

---

## 3. Streaming vs. Non-Streaming Results

Crawl4AI can return results in two modes:

### 3.1 Non-Streaming Mode (Default)

```python
config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1),
    stream=False  # Default behavior
)

async with AsyncWebCrawler() as crawler:
    # Wait for ALL results to be collected before returning
    results = await crawler.arun("https://example.com", config=config)
    
    for result in results:
        process_result(result)
```

**When to use non-streaming mode:**
- You need the complete dataset before processing
- You're performing batch operations on all results together
- Crawl time isn't a critical factor

### 3.2 Streaming Mode

```python
config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1),
    stream=True  # Enable streaming
)

async with AsyncWebCrawler() as crawler:
    # Returns an async iterator
    async for result in await crawler.arun("https://example.com", config=config):
        # Process each result as it becomes available
        process_result(result)
```

**Benefits of streaming mode:**
- Process results immediately as they're discovered
- Start working with early results while crawling continues
- Better for real-time applications or progressive display
- Reduces memory pressure when handling many pages

---

## 4. Filtering Content with Filter Chains

Filters help you narrow down which pages to crawl. Combine multiple filters using **FilterChain** for powerful targeting.

### 4.1 Basic URL Pattern Filter

```python
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter

# Only follow URLs containing "blog" or "docs"
url_filter = URLPatternFilter(patterns=["*blog*", "*docs*"])

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=FilterChain([url_filter])
    )
)
```

### 4.2 Combining Multiple Filters

```python
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter
)

# Create a chain of filters
filter_chain = FilterChain([
    # Only follow URLs with specific patterns
    URLPatternFilter(patterns=["*guide*", "*tutorial*"]),
    
    # Only crawl specific domains
    DomainFilter(
        allowed_domains=["docs.example.com"],
        blocked_domains=["old.docs.example.com"]
    ),
    
    # Only include specific content types
    ContentTypeFilter(allowed_types=["text/html"])
])

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=2,
        filter_chain=filter_chain
    )
)
```

### 4.3 Available Filter Types

Crawl4AI includes several specialized filters:

- **`URLPatternFilter`**: Matches URL patterns using wildcard syntax
- **`DomainFilter`**: Controls which domains to include or exclude
- **`ContentTypeFilter`**: Filters based on HTTP Content-Type
- **`ContentRelevanceFilter`**: Uses similarity to a text query
- **`SEOFilter`**: Evaluates SEO elements (meta tags, headers, etc.)

---

## 5. Using Scorers for Prioritized Crawling

Scorers assign priority values to discovered URLs, helping the crawler focus on the most relevant content first.

### 5.1 KeywordRelevanceScorer

```python
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy

# Create a keyword relevance scorer
keyword_scorer = KeywordRelevanceScorer(
    keywords=["crawl", "example", "async", "configuration"],
    weight=0.7  # Importance of this scorer (0.0 to 1.0)
)

config = CrawlerRunConfig(
    deep_crawl_strategy=BestFirstCrawlingStrategy(
        max_depth=2,
        url_scorer=keyword_scorer
    ),
    stream=True  # Recommended with BestFirstCrawling
)

# Results will come in order of relevance score
async with AsyncWebCrawler() as crawler:
    async for result in await crawler.arun("https://example.com", config=config):
        score = result.metadata.get("score", 0)
        print(f"Score: {score:.2f} | {result.url}")
```

**How scorers work:**
- Evaluate each discovered URL before crawling
- Calculate relevance based on various signals
- Help the crawler make intelligent choices about traversal order

---

## 6. Advanced Filtering Techniques

### 6.1 SEO Filter for Quality Assessment

The **SEOFilter** helps you identify pages with strong SEO characteristics:

```python
from crawl4ai.deep_crawling.filters import FilterChain, SEOFilter

# Create an SEO filter that looks for specific keywords in page metadata
seo_filter = SEOFilter(
    threshold=0.5,  # Minimum score (0.0 to 1.0)
    keywords=["tutorial", "guide", "documentation"]
)

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=FilterChain([seo_filter])
    )
)
```

### 6.2 Content Relevance Filter

The **ContentRelevanceFilter** analyzes the actual content of pages:

```python
from crawl4ai.deep_crawling.filters import FilterChain, ContentRelevanceFilter

# Create a content relevance filter
relevance_filter = ContentRelevanceFilter(
    query="Web crawling and data extraction with Python",
    threshold=0.7  # Minimum similarity score (0.0 to 1.0)
)

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=FilterChain([relevance_filter])
    )
)
```

This filter:
- Measures semantic similarity between query and page content
- It's a BM25-based relevance filter using head section content

---

## 7. Building a Complete Advanced Crawler

This example combines multiple techniques for a sophisticated crawl:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
    ContentTypeFilter
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

async def run_advanced_crawler():
    # Create a sophisticated filter chain
    filter_chain = FilterChain([
        # Domain boundaries
        DomainFilter(
            allowed_domains=["docs.example.com"],
            blocked_domains=["old.docs.example.com"]
        ),
        
        # URL patterns to include
        URLPatternFilter(patterns=["*guide*", "*tutorial*", "*blog*"]),
        
        # Content type filtering
        ContentTypeFilter(allowed_types=["text/html"])
    ])

    # Create a relevance scorer
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7
    )

    # Set up the configuration
    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=True
    )

    # Execute the crawl
    results = []
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.example.com", config=config):
            results.append(result)
            score = result.metadata.get("score", 0)
            depth = result.metadata.get("depth", 0)
            print(f"Depth: {depth} | Score: {score:.2f} | {result.url}")

    # Analyze the results
    print(f"Crawled {len(results)} high-value pages")
    print(f"Average score: {sum(r.metadata.get('score', 0) for r in results) / len(results):.2f}")

    # Group by depth
    depth_counts = {}
    for result in results:
        depth = result.metadata.get("depth", 0)
        depth_counts[depth] = depth_counts.get(depth, 0) + 1

    print("Pages crawled by depth:")
    for depth, count in sorted(depth_counts.items()):
        print(f"  Depth {depth}: {count} pages")

if __name__ == "__main__":
    asyncio.run(run_advanced_crawler())
```

---


## 8. Limiting and Controlling Crawl Size

### 8.1 Using max_pages

You can limit the total number of pages crawled with the `max_pages` parameter:

```python
# Limit to exactly 20 pages regardless of depth
strategy = BFSDeepCrawlStrategy(
    max_depth=3,
    max_pages=20
)
```

This feature is useful for:
- Controlling API costs
- Setting predictable execution times
- Focusing on the most important content
- Testing crawl configurations before full execution

### 8.2 Using score_threshold

For BFS and DFS strategies, you can set a minimum score threshold to only crawl high-quality pages:

```python
# Only follow links with scores above 0.4
strategy = DFSDeepCrawlStrategy(
    max_depth=2,
    url_scorer=KeywordRelevanceScorer(keywords=["api", "guide", "reference"]),
    score_threshold=0.4  # Skip URLs with scores below this value
)
```

Note that for BestFirstCrawlingStrategy, score_threshold is not needed since pages are already processed in order of highest score first.

## 9. Common Pitfalls & Tips

1.**Set realistic limits.** Be cautious with `max_depth` values > 3, which can exponentially increase crawl size. Use `max_pages` to set hard limits.

2.**Don't neglect the scoring component.** BestFirstCrawling works best with well-tuned scorers. Experiment with keyword weights for optimal prioritization.

3.**Be a good web citizen.**  Respect robots.txt. (disabled by default)
  
4.**Handle page errors gracefully.** Not all pages will be accessible. Check `result.status` when processing results.

5.**Balance breadth vs. depth.** Choose your strategy wisely - BFS for comprehensive coverage, DFS for deep exploration, BestFirst for focused relevance-based crawling.

---

## 10. Summary & Next Steps

In this **Deep Crawling with Crawl4AI** tutorial, you learned to:

- Configure **BFSDeepCrawlStrategy**, **DFSDeepCrawlStrategy**, and **BestFirstCrawlingStrategy**
- Process results in streaming or non-streaming mode
- Apply filters to target specific content
- Use scorers to prioritize the most relevant pages
- Limit crawls with `max_pages` and `score_threshold` parameters
- Build a complete advanced crawler with combined techniques

With these tools, you can efficiently extract structured data from websites at scale, focusing precisely on the content you need for your specific use case.

```


## File: docs/md_v2/core/docker-deployment.md

```md
# Crawl4AI Docker Guide 🐳

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Local Build](#local-build)
  - [Docker Hub](#docker-hub)
- [Dockerfile Parameters](#dockerfile-parameters)
- [Using the API](#using-the-api)
  - [Understanding Request Schema](#understanding-request-schema)
  - [REST API Examples](#rest-api-examples)
  - [Python SDK](#python-sdk)
- [Metrics & Monitoring](#metrics--monitoring)
- [Deployment Scenarios](#deployment-scenarios)
- [Complete Examples](#complete-examples)
- [Getting Help](#getting-help)

## Prerequisites

Before we dive in, make sure you have:
- Docker installed and running (version 20.10.0 or higher)
- At least 4GB of RAM available for the container
- Python 3.10+ (if using the Python SDK)
- Node.js 16+ (if using the Node.js examples)

> 💡 **Pro tip**: Run `docker info` to check your Docker installation and available resources.

## Installation

### Local Build

Let's get your local environment set up step by step!

#### 1. Building the Image

First, clone the repository and build the Docker image:

```bash
# Clone the repository
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai/deploy

# Build the Docker image
docker build --platform=linux/amd64 --no-cache -t crawl4ai .

# Or build for arm64
docker build --platform=linux/arm64 --no-cache -t crawl4ai .
```

#### 2. Environment Setup

If you plan to use LLMs (Language Models), you'll need to set up your API keys. Create a `.llm.env` file:

```env
# OpenAI
OPENAI_API_KEY=sk-your-key

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-key

# DeepSeek
DEEPSEEK_API_KEY=your-deepseek-key

# Check out https://docs.litellm.ai/docs/providers for more providers!
```

> 🔑 **Note**: Keep your API keys secure! Never commit them to version control.

#### 3. Running the Container

You have several options for running the container:

Basic run (no LLM support):
```bash
docker run -d -p 8000:8000 --name crawl4ai crawl4ai
```

With LLM support:
```bash
docker run -d -p 8000:8000 \
  --env-file .llm.env \
  --name crawl4ai \
  crawl4ai
```

Using host environment variables (Not a good practice, but works for local testing):
```bash
docker run -d -p 8000:8000 \
  --env-file .llm.env \
  --env "$(env)" \
  --name crawl4ai \
  crawl4ai
```

#### Multi-Platform Build
For distributing your image across different architectures, use `buildx`:

```bash
# Set up buildx builder
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t crawl4ai \
  --push \
  .
```

> 💡 **Note**: Multi-platform builds require Docker Buildx and need to be pushed to a registry.

#### Development Build
For development, you might want to enable all features:

```bash
docker build -t crawl4ai
  --build-arg INSTALL_TYPE=all \
  --build-arg PYTHON_VERSION=3.10 \
  --build-arg ENABLE_GPU=true \
  .
```

#### GPU-Enabled Build
If you plan to use GPU acceleration:

```bash
docker build -t crawl4ai
  --build-arg ENABLE_GPU=true \
  deploy/docker/
```

### Build Arguments Explained

| Argument | Description | Default | Options |
|----------|-------------|---------|----------|
| PYTHON_VERSION | Python version | 3.10 | 3.8, 3.9, 3.10 |
| INSTALL_TYPE | Feature set | default | default, all, torch, transformer |
| ENABLE_GPU | GPU support | false | true, false |
| APP_HOME | Install path | /app | any valid path |

### Build Best Practices

1. **Choose the Right Install Type**
   - `default`: Basic installation, smallest image, to be honest, I use this most of the time.
   - `all`: Full features, larger image (include transformer, and nltk, make sure you really need them)

2. **Platform Considerations**
   - Let Docker auto-detect platform unless you need cross-compilation
   - Use --platform for specific architecture requirements
   - Consider buildx for multi-architecture distribution

3. **Performance Optimization**
   - The image automatically includes platform-specific optimizations
   - AMD64 gets OpenMP optimizations
   - ARM64 gets OpenBLAS optimizations

### Docker Hub

> 🚧 Coming soon! The image will be available at `crawl4ai`. Stay tuned!

## Using the API

In the following sections, we discuss two ways to communicate with the Docker server. One option is to use the client SDK that I developed for Python, and I will soon develop one for Node.js. I highly recommend this approach to avoid mistakes. Alternatively, you can take a more technical route by using the JSON structure and passing it to all the URLs, which I will explain in detail.

### Python SDK

The SDK makes things easier! Here's how to use it:

```python
from crawl4ai.docker_client import Crawl4aiDockerClient
from crawl4ai import BrowserConfig, CrawlerRunConfig

async def main():
    async with Crawl4aiDockerClient(base_url="http://localhost:8000", verbose=True) as client:
      # If JWT is enabled, you can authenticate like this: (more on this later)
        # await client.authenticate("test@example.com")
        
        # Non-streaming crawl
        results = await client.crawl(
            ["https://example.com", "https://python.org"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=CrawlerRunConfig()
        )
        print(f"Non-streaming results: {results}")
        
        # Streaming crawl
        crawler_config = CrawlerRunConfig(stream=True)
        async for result in await client.crawl(
            ["https://example.com", "https://python.org"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=crawler_config
        ):
            print(f"Streamed result: {result}")
        
        # Get schema
        schema = await client.get_schema()
        print(f"Schema: {schema}")

if __name__ == "__main__":
    asyncio.run(main())
```

`Crawl4aiDockerClient` is an async context manager that handles the connection for you. You can pass in optional parameters for more control:

- `base_url` (str): Base URL of the Crawl4AI Docker server
- `timeout` (float): Default timeout for requests in seconds
- `verify_ssl` (bool): Whether to verify SSL certificates
- `verbose` (bool): Whether to show logging output
- `log_file` (str, optional): Path to log file if file logging is desired

This client SDK generates a properly structured JSON request for the server's HTTP API.

## Second Approach: Direct API Calls

This is super important! The API expects a specific structure that matches our Python classes. Let me show you how it works.

### Understanding Configuration Structure

Let's dive deep into how configurations work in Crawl4AI. Every configuration object follows a consistent pattern of `type` and `params`. This structure enables complex, nested configurations while maintaining clarity.

#### The Basic Pattern

Try this in Python to understand the structure:
```python
from crawl4ai import BrowserConfig

# Create a config and see its structure
config = BrowserConfig(headless=True)
print(config.dump())
```

This outputs:
```json
{
    "type": "BrowserConfig",
    "params": {
        "headless": true
    }
}
```

#### Simple vs Complex Values

The structure follows these rules:
- Simple values (strings, numbers, booleans, lists) are passed directly
- Complex values (classes, dictionaries) use the type-params pattern

For example, with dictionaries:
```json
{
    "browser_config": {
        "type": "BrowserConfig",
        "params": {
            "headless": true,           // Simple boolean - direct value
            "viewport": {               // Complex dictionary - needs type-params
                "type": "dict",
                "value": {
                    "width": 1200,
                    "height": 800
                }
            }
        }
    }
}
```

#### Strategy Pattern and Nesting

Strategies (like chunking or content filtering) demonstrate why we need this structure. Consider this chunking configuration:

```json
{
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "chunking_strategy": {
                "type": "RegexChunking",      // Strategy implementation
                "params": {
                    "patterns": ["\n\n", "\\.\\s+"]
                }
            }
        }
    }
}
```

Here, `chunking_strategy` accepts any chunking implementation. The `type` field tells the system which strategy to use, and `params` configures that specific strategy.

#### Complex Nested Example

Let's look at a more complex example with content filtering:

```json
{
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "markdown_generator": {
                "type": "DefaultMarkdownGenerator",
                "params": {
                    "content_filter": {
                        "type": "PruningContentFilter",
                        "params": {
                            "threshold": 0.48,
                            "threshold_type": "fixed"
                        }
                    }
                }
            }
        }
    }
}
```

This shows how deeply configurations can nest while maintaining a consistent structure.

#### Quick Grammar Overview
```
config := {
    "type": string,
    "params": {
        key: simple_value | complex_value
    }
}

simple_value := string | number | boolean | [simple_value]
complex_value := config | dict_value

dict_value := {
    "type": "dict",
    "value": object
}
```

#### Important Rules 🚨

- Always use the type-params pattern for class instances
- Use direct values for primitives (numbers, strings, booleans)
- Wrap dictionaries with {"type": "dict", "value": {...}}
- Arrays/lists are passed directly without type-params
- All parameters are optional unless specifically required

#### Pro Tip 💡

The easiest way to get the correct structure is to:
1. Create configuration objects in Python
2. Use the `dump()` method to see their JSON representation
3. Use that JSON in your API calls

Example:
```python
from crawl4ai import CrawlerRunConfig, PruningContentFilter

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed")
    ),
    cache_mode= CacheMode.BYPASS
)
print(config.dump())  # Use this JSON in your API calls
```


#### More Examples

**Advanced Crawler Configuration**

```json
{
    "urls": ["https://example.com"],
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "cache_mode": "bypass",
            "markdown_generator": {
                "type": "DefaultMarkdownGenerator",
                "params": {
                    "content_filter": {
                        "type": "PruningContentFilter",
                        "params": {
                            "threshold": 0.48,
                            "threshold_type": "fixed",
                            "min_word_threshold": 0
                        }
                    }
                }
            }
        }
    }
}
```

**Extraction Strategy**:

```json
{
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "extraction_strategy": {
                "type": "JsonCssExtractionStrategy",
                "params": {
                    "schema": {
                        "baseSelector": "article.post",
                        "fields": [
                            {"name": "title", "selector": "h1", "type": "text"},
                            {"name": "content", "selector": ".content", "type": "html"}
                        ]
                    }
                }
            }
        }
    }
}
```

**LLM Extraction Strategy**

```json
{
  "crawler_config": {
    "type": "CrawlerRunConfig",
    "params": {
      "extraction_strategy": {
        "type": "LLMExtractionStrategy",
        "params": {
          "instruction": "Extract article title, author, publication date and main content",
          "provider": "openai/gpt-4",
          "api_token": "your-api-token",
          "schema": {
            "type": "dict",
            "value": {
              "title": "Article Schema",
              "type": "object",
              "properties": {
                "title": {
                  "type": "string",
                  "description": "The article's headline"
                },
                "author": {
                  "type": "string",
                  "description": "The author's name"
                },
                "published_date": {
                  "type": "string",
                  "format": "date-time",
                  "description": "Publication date and time"
                },
                "content": {
                  "type": "string",
                  "description": "The main article content"
                }
              },
              "required": ["title", "content"]
            }
          }
        }
      }
    }
  }
}
```

**Deep Crawler Example**

```json
{
  "crawler_config": {
    "type": "CrawlerRunConfig",
    "params": {
      "deep_crawl_strategy": {
        "type": "BFSDeepCrawlStrategy",
        "params": {
          "max_depth": 3,
          "filter_chain": {
            "type": "FilterChain",
            "params": {
              "filters": [
                {
                  "type": "ContentTypeFilter",
                  "params": {
                    "allowed_types": ["text/html", "application/xhtml+xml"]
                  }
                },
                {
                  "type": "DomainFilter",
                  "params": {
                    "allowed_domains": ["blog.*", "docs.*"],
                  }
                }
              ]
            }
          },
          "url_scorer": {
            "type": "CompositeScorer",
            "params": {
              "scorers": [
                {
                  "type": "KeywordRelevanceScorer",
                  "params": {
                    "keywords": ["tutorial", "guide", "documentation"],
                  }
                },
                {
                  "type": "PathDepthScorer",
                  "params": {
                    "weight": 0.5,
                    "optimal_depth": 3  
                  }
                }
              ]
            }
          }
        }
      }
    }
  }
}
```

### REST API Examples

Let's look at some practical examples:

#### Simple Crawl

```python
import requests

crawl_payload = {
    "urls": ["https://example.com"],
    "browser_config": {"headless": True},
    "crawler_config": {"stream": False}
}
response = requests.post(
    "http://localhost:8000/crawl",
    # headers={"Authorization": f"Bearer {token}"},  # If JWT is enabled, more on this later
    json=crawl_payload
)
print(response.json())  # Print the response for debugging
```

#### Streaming Results

```python
async def test_stream_crawl(session, token: str):
    """Test the /crawl/stream endpoint with multiple URLs."""
    url = "http://localhost:8000/crawl/stream"
    payload = {
        "urls": [
            "https://example.com",
            "https://example.com/page1",  
            "https://example.com/page2",  
            "https://example.com/page3",  
        ],
        "browser_config": {"headless": True, "viewport": {"width": 1200}},
        "crawler_config": {"stream": True, "cache_mode": "bypass"}
    }

    # headers = {"Authorization": f"Bearer {token}"} # If JWT is enabled, more on this later
    
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            status = response.status
            print(f"Status: {status} (Expected: 200)")
            assert status == 200, f"Expected 200, got {status}"
            
            # Read streaming response line-by-line (NDJSON)
            async for line in response.content:
                if line:
                    data = json.loads(line.decode('utf-8').strip())
                    print(f"Streamed Result: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Error in streaming crawl test: {str(e)}")
```

## Metrics & Monitoring

Keep an eye on your crawler with these endpoints:

- `/health` - Quick health check
- `/metrics` - Detailed Prometheus metrics
- `/schema` - Full API schema

Example health check:
```bash
curl http://localhost:8000/health
```

## Deployment Scenarios

> 🚧 Coming soon! We'll cover:
> - Kubernetes deployment
> - Cloud provider setups (AWS, GCP, Azure)
> - High-availability configurations
> - Load balancing strategies

## Complete Examples

Check out the `examples` folder in our repository for full working examples! Here are two to get you started:
[Using Client SDK](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_python_sdk.py)
[Using REST API](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_python_rest_api.py)

## Server Configuration

The server's behavior can be customized through the `config.yml` file. Let's explore how to configure your Crawl4AI server for optimal performance and security.

### Understanding config.yml

The configuration file is located at `deploy/docker/config.yml`. You can either modify this file before building the image or mount a custom configuration when running the container.

Here's a detailed breakdown of the configuration options:

```yaml
# Application Configuration
app:
  title: "Crawl4AI API"           # Server title in OpenAPI docs
  version: "1.0.0"               # API version
  host: "0.0.0.0"               # Listen on all interfaces
  port: 8000                    # Server port
  reload: True                  # Enable hot reloading (development only)
  timeout_keep_alive: 300       # Keep-alive timeout in seconds

# Rate Limiting Configuration
rate_limiting:
  enabled: True                 # Enable/disable rate limiting
  default_limit: "100/minute"   # Rate limit format: "number/timeunit"
  trusted_proxies: []          # List of trusted proxy IPs
  storage_uri: "memory://"     # Use "redis://localhost:6379" for production

# Security Configuration
security:
  enabled: false               # Master toggle for security features
  jwt_enabled: true            # Enable JWT authentication
  https_redirect: True         # Force HTTPS
  trusted_hosts: ["*"]         # Allowed hosts (use specific domains in production)
  headers:                     # Security headers
    x_content_type_options: "nosniff"
    x_frame_options: "DENY"
    content_security_policy: "default-src 'self'"
    strict_transport_security: "max-age=63072000; includeSubDomains"

# Crawler Configuration
crawler:
  memory_threshold_percent: 95.0  # Memory usage threshold
  rate_limiter:
    base_delay: [1.0, 2.0]      # Min and max delay between requests
  timeouts:
    stream_init: 30.0           # Stream initialization timeout
    batch_process: 300.0        # Batch processing timeout

# Logging Configuration
logging:
  level: "INFO"                 # Log level (DEBUG, INFO, WARNING, ERROR)
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Observability Configuration
observability:
  prometheus:
    enabled: True              # Enable Prometheus metrics
    endpoint: "/metrics"       # Metrics endpoint
  health_check:
    endpoint: "/health"        # Health check endpoint
```

### JWT Authentication

When `security.jwt_enabled` is set to `true` in your config.yml, all endpoints require JWT authentication via bearer tokens. Here's how it works:

#### Getting a Token
```python
POST /token
Content-Type: application/json

{
    "email": "user@example.com"
}
```

The endpoint returns:
```json
{
    "email": "user@example.com",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
    "token_type": "bearer"
}
```

#### Using the Token
Add the token to your requests:
```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGci..." http://localhost:8000/crawl
```

Using the Python SDK:
```python
from crawl4ai.docker_client import Crawl4aiDockerClient

async with Crawl4aiDockerClient() as client:
    # Authenticate first
    await client.authenticate("user@example.com")
    
    # Now all requests will include the token automatically
    result = await client.crawl(urls=["https://example.com"])
```

#### Production Considerations 💡
The default implementation uses a simple email verification. For production use, consider:
- Email verification via OTP/magic links
- OAuth2 integration
- Rate limiting token generation
- Token expiration and refresh mechanisms
- IP-based restrictions

### Configuration Tips and Best Practices

1. **Production Settings** 🏭

   ```yaml
   app:
     reload: False              # Disable reload in production
     timeout_keep_alive: 120    # Lower timeout for better resource management
   
   rate_limiting:
     storage_uri: "redis://redis:6379"  # Use Redis for distributed rate limiting
     default_limit: "50/minute"         # More conservative rate limit
   
   security:
     enabled: true                      # Enable all security features
     trusted_hosts: ["your-domain.com"] # Restrict to your domain
   ```

2. **Development Settings** 🛠️

   ```yaml
   app:
     reload: True               # Enable hot reloading
     timeout_keep_alive: 300    # Longer timeout for debugging
   
   logging:
     level: "DEBUG"            # More verbose logging
   ```

3. **High-Traffic Settings** 🚦

   ```yaml
   crawler:
     memory_threshold_percent: 85.0  # More conservative memory limit
     rate_limiter:
       base_delay: [2.0, 4.0]       # More aggressive rate limiting
   ```

### Customizing Your Configuration

#### Method 1: Pre-build Configuration

```bash
# Copy and modify config before building
cd crawl4ai/deploy
vim custom-config.yml # Or use any editor

# Build with custom config
docker build --platform=linux/amd64 --no-cache -t crawl4ai:latest .
```

#### Method 2: Build-time Configuration

Use a custom config during build:

```bash
# Build with custom config
docker build --platform=linux/amd64 --no-cache \
  --build-arg CONFIG_PATH=/path/to/custom-config.yml \ 
  -t crawl4ai:latest .
```

#### Method 3: Runtime Configuration
```bash
# Mount custom config at runtime
docker run -d -p 8000:8000 \
  -v $(pwd)/custom-config.yml:/app/config.yml \
  crawl4ai-server:prod
```

> 💡 Note: When using Method 2, `/path/to/custom-config.yml` is relative to deploy directory.
> 💡 Note: When using Method 3, ensure your custom config file has all required fields as the container will use this instead of the built-in config.

### Configuration Recommendations

1. **Security First** 🔒
   - Always enable security in production
   - Use specific trusted_hosts instead of wildcards
   - Set up proper rate limiting to protect your server
   - Consider your environment before enabling HTTPS redirect

2. **Resource Management** 💻
   - Adjust memory_threshold_percent based on available RAM
   - Set timeouts according to your content size and network conditions
   - Use Redis for rate limiting in multi-container setups

3. **Monitoring** 📊
   - Enable Prometheus if you need metrics
   - Set DEBUG logging in development, INFO in production
   - Regular health check monitoring is crucial

4. **Performance Tuning** ⚡
   - Start with conservative rate limiter delays
   - Increase batch_process timeout for large content
   - Adjust stream_init timeout based on initial response times

## Getting Help

We're here to help you succeed with Crawl4AI! Here's how to get support:

- 📖 Check our [full documentation](https://docs.crawl4ai.com)
- 🐛 Found a bug? [Open an issue](https://github.com/unclecode/crawl4ai/issues)
- 💬 Join our [Discord community](https://discord.gg/crawl4ai)
- ⭐ Star us on GitHub to show support!

## Summary

In this guide, we've covered everything you need to get started with Crawl4AI's Docker deployment:
- Building and running the Docker container
- Configuring the environment
- Making API requests with proper typing
- Using the Python SDK
- Monitoring your deployment

Remember, the examples in the `examples` folder are your friends - they show real-world usage patterns that you can adapt for your needs.

Keep exploring, and don't hesitate to reach out if you need help! We're building something amazing together. 🚀

Happy crawling! 🕷️
```


## File: docs/md_v2/core/fit-markdown.md

```md
# Fit Markdown with Pruning & BM25

**Fit Markdown** is a specialized **filtered** version of your page’s markdown, focusing on the most relevant content. By default, Crawl4AI converts the entire HTML into a broad **raw_markdown**. With fit markdown, we apply a **content filter** algorithm (e.g., **Pruning** or **BM25**) to remove or rank low-value sections—such as repetitive sidebars, shallow text blocks, or irrelevancies—leaving a concise textual “core.”

---

## 1. How “Fit Markdown” Works

### 1.1 The `content_filter`

In **`CrawlerRunConfig`**, you can specify a **`content_filter`** to shape how content is pruned or ranked before final markdown generation. A filter’s logic is applied **before** or **during** the HTML→Markdown process, producing:

- **`result.markdown.raw_markdown`** (unfiltered)
- **`result.markdown.fit_markdown`** (filtered or “fit” version)
- **`result.markdown.fit_html`** (the corresponding HTML snippet that produced `fit_markdown`)


### 1.2 Common Filters

1. **PruningContentFilter** – Scores each node by text density, link density, and tag importance, discarding those below a threshold.  
2. **BM25ContentFilter** – Focuses on textual relevance using BM25 ranking, especially useful if you have a specific user query (e.g., “machine learning” or “food nutrition”).

---

## 2. PruningContentFilter

**Pruning** discards less relevant nodes based on **text density, link density, and tag importance**. It’s a heuristic-based approach—if certain sections appear too “thin” or too “spammy,” they’re pruned.

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

**Algorithmic Factors**:

- **Text density** – Encourages blocks that have a higher ratio of text to overall content.  
- **Link density** – Penalizes sections that are mostly links.  
- **Tag importance** – e.g., an `<article>` or `<p>` might be more important than a `<div>`.  
- **Structural context** – If a node is deeply nested or in a suspected sidebar, it might be deprioritized.

---

## 3. BM25ContentFilter

**BM25** is a classical text ranking algorithm often used in search engines. If you have a **user query** or rely on page metadata to derive a query, BM25 can identify which text chunks best match that query.

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

> In more advanced scenarios, you might see parameters like `use_stemming`, `case_sensitive`, or `priority_tags` to refine how text is tokenized or weighted.

---

## 4. Accessing the “Fit” Output

After the crawl, your “fit” content is found in **`result.markdown.fit_markdown`**. 

```python
fit_md = result.markdown.fit_markdown
fit_html = result.markdown.fit_html
```

If the content filter is **BM25**, you might see additional logic or references in `fit_markdown` that highlight relevant segments. If it’s **Pruning**, the text is typically well-cleaned but not necessarily matched to a query.

---

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

---

## 6. Combining with “word_count_threshold” & Exclusions

Remember you can also specify:

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

Thus, **multi-level** filtering occurs:

1. The crawler’s `excluded_tags` are removed from the HTML first.  
2. The content filter (Pruning, BM25, or custom) prunes or ranks the remaining text blocks.  
3. The final “fit” content is generated in `result.markdown.fit_markdown`.

---

## 7. Custom Filters

If you need a different approach (like a specialized ML model or site-specific heuristics), you can create a new class inheriting from `RelevantContentFilter` and implement `filter_content(html)`. Then inject it into your **markdown generator**:

```python
from crawl4ai.content_filter_strategy import RelevantContentFilter

class MyCustomFilter(RelevantContentFilter):
    def filter_content(self, html, min_word_threshold=None):
        # parse HTML, implement custom logic
        return [block for block in ... if ... some condition...]

```

**Steps**:

1. Subclass `RelevantContentFilter`.  
2. Implement `filter_content(...)`.  
3. Use it in your `DefaultMarkdownGenerator(content_filter=MyCustomFilter(...))`.

---

## 8. Final Thoughts

**Fit Markdown** is a crucial feature for:

- **Summaries**: Quickly get the important text from a cluttered page.  
- **Search**: Combine with **BM25** to produce content relevant to a query.  
- **AI Pipelines**: Filter out boilerplate so LLM-based extraction or summarization runs on denser text.

**Key Points**:
- **PruningContentFilter**: Great if you just want the “meatiest” text without a user query.  
- **BM25ContentFilter**: Perfect for query-based extraction or searching.  
- Combine with **`excluded_tags`, `exclude_external_links`, `word_count_threshold`** to refine your final “fit” text.  
- Fit markdown ends up in **`result.markdown.fit_markdown`**; eventually **`result.markdown.fit_markdown`** in future versions.

With these tools, you can **zero in** on the text that truly matters, ignoring spammy or boilerplate content, and produce a concise, relevant “fit markdown” for your AI or data pipelines. Happy pruning and searching!

- Last Updated: 2025-01-01
```


## File: docs/md_v2/core/installation.md

```md
# Installation & Setup (2023 Edition)

## 1. Basic Installation

```bash
pip install crawl4ai
```

This installs the **core** Crawl4AI library along with essential dependencies. **No** advanced features (like transformers or PyTorch) are included yet.

## 2. Initial Setup & Diagnostics

### 2.1 Run the Setup Command
After installing, call:

```bash
crawl4ai-setup
```

**What does it do?**
- Installs or updates required Playwright browsers (Chromium, Firefox, etc.)
- Performs OS-level checks (e.g., missing libs on Linux)
- Confirms your environment is ready to crawl

### 2.2 Diagnostics
Optionally, you can run **diagnostics** to confirm everything is functioning:

```bash
crawl4ai-doctor
```

This command attempts to:
- Check Python version compatibility
- Verify Playwright installation
- Inspect environment variables or library conflicts

If any issues arise, follow its suggestions (e.g., installing additional system packages) and re-run `crawl4ai-setup`.

---

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

**Expected** outcome:
- A headless browser session loads `example.com`
- Crawl4AI returns ~300 characters of markdown.  
If errors occur, rerun `crawl4ai-doctor` or manually ensure Playwright is installed correctly.

---

## 4. Advanced Installation (Optional)

**Warning**: Only install these **if you truly need them**. They bring in larger dependencies, including big models, which can increase disk usage and memory load significantly.

### 4.1 Torch, Transformers, or All

- **Text Clustering (Torch)**  
  ```bash
  pip install crawl4ai[torch]
  crawl4ai-setup
  ```
  Installs PyTorch-based features (e.g., cosine similarity or advanced semantic chunking).

- **Transformers**  
  ```bash
  pip install crawl4ai[transformer]
  crawl4ai-setup
  ```
  Adds Hugging Face-based summarization or generation strategies.

- **All Features**  
  ```bash
  pip install crawl4ai[all]
  crawl4ai-setup
  ```

#### (Optional) Pre-Fetching Models
```bash
crawl4ai-download-models
```
This step caches large models locally (if needed). **Only do this** if your workflow requires them.

---

## 5. Docker (Experimental)

We provide a **temporary** Docker approach for testing. **It’s not stable and may break** with future releases. We plan a major Docker revamp in a future stable version, 2025 Q1. If you still want to try:

```bash
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
```

You can then make POST requests to `http://localhost:11235/crawl` to perform crawls. **Production usage** is discouraged until our new Docker approach is ready (planned in Jan or Feb 2025).

---

## 6. Local Server Mode (Legacy)

Some older docs mention running Crawl4AI as a local server. This approach has been **partially replaced** by the new Docker-based prototype and upcoming stable server release. You can experiment, but expect major changes. Official local server instructions will arrive once the new Docker architecture is finalized.

---

## Summary

1. **Install** with `pip install crawl4ai` and run `crawl4ai-setup`.
2. **Diagnose** with `crawl4ai-doctor` if you see errors.
3. **Verify** by crawling `example.com` with minimal `BrowserConfig` + `CrawlerRunConfig`.
4. **Advanced** features (Torch, Transformers) are **optional**—avoid them if you don’t need them (they significantly increase resource usage).
5. **Docker** is **experimental**—use at your own risk until the stable version is released.
6. **Local server** references in older docs are largely deprecated; a new solution is in progress.

**Got questions?** Check [GitHub issues](https://github.com/unclecode/crawl4ai/issues) for updates or ask the community!
```


## File: docs/md_v2/core/link-media.md

```md
# Link & Media 

In this tutorial, you’ll learn how to:

1. Extract links (internal, external) from crawled pages  
2. Filter or exclude specific domains (e.g., social media or custom domains)  
3. Access and ma### 3.2 Excluding Images

#### Excluding External Images

If you're dealing with heavy pages or want to skip third-party images (advertisements, for example), you can turn on:

```python
crawler_cfg = CrawlerRunConfig(
    exclude_external_images=True
)
```

This setting attempts to discard images from outside the primary domain, keeping only those from the site you're crawling.

#### Excluding All Images

If you want to completely remove all images from the page to maximize performance and reduce memory usage, use:

```python
crawler_cfg = CrawlerRunConfig(
    exclude_all_images=True
)
```

This setting removes all images very early in the processing pipeline, which significantly improves memory efficiency and processing speed. This is particularly useful when:
- You don't need image data in your results
- You're crawling image-heavy pages that cause memory issues
- You want to focus only on text content
- You need to maximize crawling speeddata (especially images) in the crawl result  
4. Configure your crawler to exclude or prioritize certain images

> **Prerequisites**  
> - You have completed or are familiar with the [AsyncWebCrawler Basics](../core/simple-crawling.md) tutorial.  
> - You can run Crawl4AI in your environment (Playwright, Python, etc.).

---

Below is a revised version of the **Link Extraction** and **Media Extraction** sections that includes example data structures showing how links and media items are stored in `CrawlResult`. Feel free to adjust any field names or descriptions to match your actual output.

---

## 1. Link Extraction

### 1.1 `result.links`

When you call `arun()` or `arun_many()` on a URL, Crawl4AI automatically extracts links and stores them in the `links` field of `CrawlResult`. By default, the crawler tries to distinguish **internal** links (same domain) from **external** links (different domains).

**Basic Example**:

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

**Structure Example**:

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

---

## 2. Domain Filtering

Some websites contain hundreds of third-party or affiliate links. You can filter out certain domains at **crawl time** by configuring the crawler. The most relevant parameters in `CrawlerRunConfig` are:

- **`exclude_external_links`**: If `True`, discard any link pointing outside the root domain.  
- **`exclude_social_media_domains`**: Provide a list of social media platforms (e.g., `["facebook.com", "twitter.com"]`) to exclude from your crawl.  
- **`exclude_social_media_links`**: If `True`, automatically skip known social platforms.  
- **`exclude_domains`**: Provide a list of custom domains you want to exclude (e.g., `["spammyads.com", "tracker.net"]`).

### 2.1 Example: Excluding External & Social Media Links

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

### 2.2 Example: Excluding Specific Domains

If you want to let external links in, but specifically exclude a domain (e.g., `suspiciousads.com`), do this:

```python
crawler_cfg = CrawlerRunConfig(
    exclude_domains=["suspiciousads.com"]
)
```

This approach is handy when you still want external links but need to block certain sites you consider spammy.

---

## 3. Media Extraction

### 3.1 Accessing `result.media`

By default, Crawl4AI collects images, audio, video URLs, and data tables it finds on the page. These are stored in `result.media`, a dictionary keyed by media type (e.g., `images`, `videos`, `audio`, `tables`).

**Basic Example**:

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
    
    # Get tables
    tables = result.media.get("tables", [])
    print(f"Found {len(tables)} data tables in total.")
    for i, table in enumerate(tables):
        print(f"[Table {i}] Caption: {table.get('caption', 'No caption')}")
        print(f"           Columns: {len(table.get('headers', []))}")
        print(f"           Rows: {len(table.get('rows', []))}")
```

**Structure Example**:

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
  "tables": [
    {
      "headers": ["Name", "Age", "Location"],
      "rows": [
        ["John Doe", "34", "New York"],
        ["Jane Smith", "28", "San Francisco"],
        ["Alex Johnson", "42", "Chicago"]
      ],
      "caption": "Employee Directory",
      "summary": "Directory of company employees"
    },
    # More tables if present
  ]
}
```

Depending on your Crawl4AI version or scraping strategy, these dictionaries can include fields like:

- **`src`**: The media URL (e.g., image source)  
- **`alt`**: The alt text for images (if present)  
- **`desc`**: A snippet of nearby text or a short description (optional)  
- **`score`**: A heuristic relevance score if you’re using content-scoring features  
- **`width`**, **`height`**: If the crawler detects dimensions for the image/video  
- **`type`**: Usually `"image"`, `"video"`, or `"audio"`  
- **`group_id`**: If you’re grouping related media items, the crawler might assign an ID  

With these details, you can easily filter out or focus on certain images (for instance, ignoring images with very low scores or a different domain), or gather metadata for analytics.

### 3.2 Excluding External Images

If you’re dealing with heavy pages or want to skip third-party images (advertisements, for example), you can turn on:

```python
crawler_cfg = CrawlerRunConfig(
    exclude_external_images=True
)
```

This setting attempts to discard images from outside the primary domain, keeping only those from the site you’re crawling.

### 3.3 Working with Tables

Crawl4AI can detect and extract structured data from HTML tables. Tables are analyzed based on various criteria to determine if they are actual data tables (as opposed to layout tables), including:

- Presence of thead and tbody sections
- Use of th elements for headers
- Column consistency
- Text density
- And other factors

Tables that score above the threshold (default: 7) are extracted and stored in `result.media.tables`.

**Accessing Table Data**:

```python
if result.success:
    tables = result.media.get("tables", [])
    print(f"Found {len(tables)} data tables on the page")
    
    if tables:
        # Access the first table
        first_table = tables[0]
        print(f"Table caption: {first_table.get('caption', 'No caption')}")
        print(f"Headers: {first_table.get('headers', [])}")
        
        # Print the first 3 rows
        for i, row in enumerate(first_table.get('rows', [])[:3]):
            print(f"Row {i+1}: {row}")
```

**Configuring Table Extraction**:

You can adjust the sensitivity of the table detection algorithm with:

```python
crawler_cfg = CrawlerRunConfig(
    table_score_threshold=5  # Lower value = more tables detected (default: 7)
)
```

Each extracted table contains:
- `headers`: Column header names
- `rows`: List of rows, each containing cell values
- `caption`: Table caption text (if available)
- `summary`: Table summary attribute (if specified)

### 3.4 Additional Media Config

- **`screenshot`**: Set to `True` if you want a full-page screenshot stored as `base64` in `result.screenshot`.  
- **`pdf`**: Set to `True` if you want a PDF version of the page in `result.pdf`.  
- **`capture_mhtml`**: Set to `True` if you want an MHTML snapshot of the page in `result.mhtml`. This format preserves the entire web page with all its resources (CSS, images, scripts) in a single file, making it perfect for archiving or offline viewing.
- **`wait_for_images`**: If `True`, attempts to wait until images are fully loaded before final extraction.

#### Example: Capturing Page as MHTML

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

The MHTML format is particularly useful because:
- It captures the complete page state including all resources
- It can be opened in most modern browsers for offline viewing
- It preserves the page exactly as it appeared during crawling
- It's a single file, making it easy to store and transfer

---

## 4. Putting It All Together: Link & Media Filtering

Here’s a combined example demonstrating how to filter out external links, skip certain domains, and exclude external images:

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

---

## 5. Common Pitfalls & Tips

1. **Conflicting Flags**:  
   - `exclude_external_links=True` but then also specifying `exclude_social_media_links=True` is typically fine, but understand that the first setting already discards *all* external links. The second becomes somewhat redundant.  
   - `exclude_external_images=True` but want to keep some external images? Currently no partial domain-based setting for images, so you might need a custom approach or hook logic.

2. **Relevancy Scores**:  
   - If your version of Crawl4AI or your scraping strategy includes an `img["score"]`, it’s typically a heuristic based on size, position, or content analysis. Evaluate carefully if you rely on it.

3. **Performance**:  
   - Excluding certain domains or external images can speed up your crawl, especially for large, media-heavy pages.  
   - If you want a “full” link map, do *not* exclude them. Instead, you can post-filter in your own code.

4. **Social Media Lists**:  
   - `exclude_social_media_links=True` typically references an internal list of known social domains like Facebook, Twitter, LinkedIn, etc. If you need to add or remove from that list, look for library settings or a local config file (depending on your version).

---

**That’s it for Link & Media Analysis!** You’re now equipped to filter out unwanted sites and zero in on the images and videos that matter for your project.
### Table Extraction Tips

- Not all HTML tables are extracted - only those detected as "data tables" vs. layout tables.
- Tables with inconsistent cell counts, nested tables, or those used purely for layout may be skipped.
- If you're missing tables, try adjusting the `table_score_threshold` to a lower value (default is 7).

The table detection algorithm scores tables based on features like consistent columns, presence of headers, text density, and more. Tables scoring above the threshold are considered data tables worth extracting.

```


## File: docs/md_v2/core/local-files.md

```md
# Prefix-Based Input Handling in Crawl4AI

This guide will walk you through using the Crawl4AI library to crawl web pages, local HTML files, and raw HTML strings. We'll demonstrate these capabilities using a Wikipedia page as an example.

## Crawling a Web URL

To crawl a live web page, provide the URL starting with `http://` or `https://`, using a `CrawlerRunConfig` object:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig

async def crawl_web():
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/apple", 
            config=config
        )
        if result.success:
            print("Markdown Content:")
            print(result.markdown)
        else:
            print(f"Failed to crawl: {result.error_message}")

asyncio.run(crawl_web())
```

## Crawling a Local HTML File

To crawl a local HTML file, prefix the file path with `file://`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig

async def crawl_local_file():
    local_file_path = "/path/to/apple.html"  # Replace with your file path
    file_url = f"file://{local_file_path}"
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=file_url, config=config)
        if result.success:
            print("Markdown Content from Local File:")
            print(result.markdown)
        else:
            print(f"Failed to crawl local file: {result.error_message}")

asyncio.run(crawl_local_file())
```

## Crawling Raw HTML Content

To crawl raw HTML content, prefix the HTML string with `raw:`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig

async def crawl_raw_html():
    raw_html = "<html><body><h1>Hello, World!</h1></body></html>"
    raw_html_url = f"raw:{raw_html}"
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=raw_html_url, config=config)
        if result.success:
            print("Markdown Content from Raw HTML:")
            print(result.markdown)
        else:
            print(f"Failed to crawl raw HTML: {result.error_message}")

asyncio.run(crawl_raw_html())
```

---

# Complete Example

Below is a comprehensive script that:

1. Crawls the Wikipedia page for "Apple."
2. Saves the HTML content to a local file (`apple.html`).
3. Crawls the local HTML file and verifies the markdown length matches the original crawl.
4. Crawls the raw HTML content from the saved file and verifies consistency.

```python
import os
import sys
import asyncio
from pathlib import Path
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig

async def main():
    wikipedia_url = "https://en.wikipedia.org/wiki/apple"
    script_dir = Path(__file__).parent
    html_file_path = script_dir / "apple.html"

    async with AsyncWebCrawler() as crawler:
        # Step 1: Crawl the Web URL
        print("\n=== Step 1: Crawling the Wikipedia URL ===")
        web_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(url=wikipedia_url, config=web_config)

        if not result.success:
            print(f"Failed to crawl {wikipedia_url}: {result.error_message}")
            return

        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(result.html)
        web_crawl_length = len(result.markdown)
        print(f"Length of markdown from web crawl: {web_crawl_length}\n")

        # Step 2: Crawl from the Local HTML File
        print("=== Step 2: Crawling from the Local HTML File ===")
        file_url = f"file://{html_file_path.resolve()}"
        file_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        local_result = await crawler.arun(url=file_url, config=file_config)

        if not local_result.success:
            print(f"Failed to crawl local file {file_url}: {local_result.error_message}")
            return

        local_crawl_length = len(local_result.markdown)
        assert web_crawl_length == local_crawl_length, "Markdown length mismatch"
        print("✅ Markdown length matches between web and local file crawl.\n")

        # Step 3: Crawl Using Raw HTML Content
        print("=== Step 3: Crawling Using Raw HTML Content ===")
        with open(html_file_path, 'r', encoding='utf-8') as f:
            raw_html_content = f.read()
        raw_html_url = f"raw:{raw_html_content}"
        raw_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        raw_result = await crawler.arun(url=raw_html_url, config=raw_config)

        if not raw_result.success:
            print(f"Failed to crawl raw HTML content: {raw_result.error_message}")
            return

        raw_crawl_length = len(raw_result.markdown)
        assert web_crawl_length == raw_crawl_length, "Markdown length mismatch"
        print("✅ Markdown length matches between web and raw HTML crawl.\n")

        print("All tests passed successfully!")
    if html_file_path.exists():
        os.remove(html_file_path)

if __name__ == "__main__":
    asyncio.run(main())
```

---

# Conclusion

With the unified `url` parameter and prefix-based handling in **Crawl4AI**, you can seamlessly handle web URLs, local HTML files, and raw HTML content. Use `CrawlerRunConfig` for flexible and consistent configuration in all scenarios.
```


## File: docs/md_v2/core/markdown-generation.md

```md
# Markdown Generation Basics

One of Crawl4AI’s core features is generating **clean, structured markdown** from web pages. Originally built to solve the problem of extracting only the “actual” content and discarding boilerplate or noise, Crawl4AI’s markdown system remains one of its biggest draws for AI workflows.

In this tutorial, you’ll learn:

1. How to configure the **Default Markdown Generator**  
2. How **content filters** (BM25 or Pruning) help you refine markdown and discard junk  
3. The difference between raw markdown (`result.markdown`) and filtered markdown (`fit_markdown`)  

> **Prerequisites**  
> - You’ve completed or read [AsyncWebCrawler Basics](../core/simple-crawling.md) to understand how to run a simple crawl.  
> - You know how to configure `CrawlerRunConfig`.

---

## 1. Quick Example

Here’s a minimal code snippet that uses the **DefaultMarkdownGenerator** with no additional filtering:

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

**What’s happening?**  
- `CrawlerRunConfig( markdown_generator = DefaultMarkdownGenerator() )` instructs Crawl4AI to convert the final HTML into markdown at the end of each crawl.  
- The resulting markdown is accessible via `result.markdown`.

---

## 2. How Markdown Generation Works

### 2.1 HTML-to-Text Conversion (Forked & Modified)

Under the hood, **DefaultMarkdownGenerator** uses a specialized HTML-to-text approach that:

- Preserves headings, code blocks, bullet points, etc.  
- Removes extraneous tags (scripts, styles) that don’t add meaningful content.  
- Can optionally generate references for links or skip them altogether.

A set of **options** (passed as a dict) allows you to customize precisely how HTML converts to markdown. These map to standard html2text-like configuration plus your own enhancements (e.g., ignoring internal links, preserving certain tags verbatim, or adjusting line widths).

### 2.2 Link Citations & References

By default, the generator can convert `<a href="...">` elements into `[text][1]` citations, then place the actual links at the bottom of the document. This is handy for research workflows that demand references in a structured manner.

### 2.3 Optional Content Filters

Before or after the HTML-to-Markdown step, you can apply a **content filter** (like BM25 or Pruning) to reduce noise and produce a “fit_markdown”—a heavily pruned version focusing on the page’s main text. We’ll cover these filters shortly.

---

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

---

## 5. Content Filters

**Content filters** selectively remove or rank sections of text before turning them into Markdown. This is especially helpful if your page has ads, nav bars, or other clutter you don’t want.

### 5.1 BM25ContentFilter

If you have a **search query**, BM25 is a good choice:

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai import CrawlerRunConfig

bm25_filter = BM25ContentFilter(
    user_query="machine learning",
    bm25_threshold=1.2,
    use_stemming=True
)

md_generator = DefaultMarkdownGenerator(
    content_filter=bm25_filter,
    options={"ignore_links": True}
)

config = CrawlerRunConfig(markdown_generator=md_generator)
```

- **`user_query`**: The term you want to focus on. BM25 tries to keep only content blocks relevant to that query.  
- **`bm25_threshold`**: Raise it to keep fewer blocks; lower it to keep more.  
- **`use_stemming`**: If `True`, variations of words match (e.g., “learn,” “learning,” “learnt”).

**No query provided?** BM25 tries to glean a context from page metadata, or you can simply treat it as a scorched-earth approach that discards text with low generic score. Realistically, you want to supply a query for best results.

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

**When to Use PruningContentFilter**  
- You want a broad cleanup without a user query.  
- The page has lots of repeated sidebars, footers, or disclaimers that hamper text extraction.

### 5.3 LLMContentFilter

For intelligent content filtering and high-quality markdown generation, you can use the **LLMContentFilter**. This filter leverages LLMs to generate relevant markdown while preserving the original content's meaning and structure:

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
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)
        print(result.markdown.fit_markdown)  # Filtered markdown content
```

**Key Features:**
- **Intelligent Filtering**: Uses LLMs to understand and extract relevant content while maintaining context
- **Customizable Instructions**: Tailor the filtering process with specific instructions
- **Chunk Processing**: Handles large documents by processing them in chunks (controlled by `chunk_token_threshold`)
- **Parallel Processing**: For better performance, use smaller `chunk_token_threshold` (e.g., 2048 or 4096) to enable parallel processing of content chunks

**Two Common Use Cases:**

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

---

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

---

## 7. The `MarkdownGenerationResult` Object

If your library stores detailed markdown output in an object like `MarkdownGenerationResult`, you’ll see fields such as:

- **`raw_markdown`**: The direct HTML-to-markdown transformation (no filtering).  
- **`markdown_with_citations`**: A version that moves links to reference-style footnotes.  
- **`references_markdown`**: A separate string or section containing the gathered references.  
- **`fit_markdown`**: The filtered markdown if you used a content filter.  
- **`fit_html`**: The corresponding HTML snippet used to generate `fit_markdown` (helpful for debugging or advanced usage).

**Example**:

```python
md_obj = result.markdown  # your library’s naming may vary
print("RAW:\n", md_obj.raw_markdown)
print("CITED:\n", md_obj.markdown_with_citations)
print("REFERENCES:\n", md_obj.references_markdown)
print("FIT:\n", md_obj.fit_markdown)
```

**Why Does This Matter?**  
- You can supply `raw_markdown` to an LLM if you want the entire text.  
- Or feed `fit_markdown` into a vector database to reduce token usage.  
- `references_markdown` can help you keep track of link provenance.

---

Below is a **revised section** under “Combining Filters (BM25 + Pruning)” that demonstrates how you can run **two** passes of content filtering without re-crawling, by taking the HTML (or text) from a first pass and feeding it into the second filter. It uses real code patterns from the snippet you provided for **BM25ContentFilter**, which directly accepts **HTML** strings (and can also handle plain text with minimal adaptation).

---

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
2. **PruningContentFilter**: Takes HTML + optional parameters. It extracts blocks of text or partial HTML, removing headings/sections deemed “noise.” It returns a **list of text chunks**.  
3. **Combine or Transform**: We join these pruned chunks back into a single HTML-like string. (Alternatively, you could store them in a list for further logic—whatever suits your pipeline.)  
4. **BM25ContentFilter**: We feed the pruned string into `BM25ContentFilter` with a user query. This second pass further narrows the content to chunks relevant to “machine learning.”

**No Re-Crawling**: We used `raw_html` from the first pass, so there’s no need to run `arun()` again—**no second network request**.

### Tips & Variations

- **Plain Text vs. HTML**: If your pruned output is mostly text, BM25 can still handle it; just keep in mind it expects a valid string input. If you supply partial HTML (like `"<p>some text</p>"`), it will parse it as HTML.  
- **Chaining in a Single Pipeline**: If your code supports it, you can chain multiple filters automatically. Otherwise, manual two-pass filtering (as shown) is straightforward.  
- **Adjust Thresholds**: If you see too much or too little text in step one, tweak `threshold=0.5` or `min_word_threshold=50`. Similarly, `bm25_threshold=1.2` can be raised/lowered for more or fewer chunks in step two.

### One-Pass Combination?

If your codebase or pipeline design allows applying multiple filters in one pass, you could do so. But often it’s simpler—and more transparent—to run them sequentially, analyzing each step’s result.

**Bottom Line**: By **manually chaining** your filtering logic in two passes, you get powerful incremental control over the final content. First, remove “global” clutter with Pruning, then refine further with BM25-based query relevance—without incurring a second network crawl.

---

## 9. Common Pitfalls & Tips

1. **No Markdown Output?**  
   - Make sure the crawler actually retrieved HTML. If the site is heavily JS-based, you may need to enable dynamic rendering or wait for elements.  
   - Check if your content filter is too aggressive. Lower thresholds or disable the filter to see if content reappears.

2. **Performance Considerations**  
   - Very large pages with multiple filters can be slower. Consider `cache_mode` to avoid re-downloading.  
   - If your final use case is LLM ingestion, consider summarizing further or chunking big texts.

3. **Take Advantage of `fit_markdown`**  
   - Great for RAG pipelines, semantic search, or any scenario where extraneous boilerplate is unwanted.  
   - Still verify the textual quality—some sites have crucial data in footers or sidebars.

4. **Adjusting `html2text` Options**  
   - If you see lots of raw HTML slipping into the text, turn on `escape_html`.  
   - If code blocks look messy, experiment with `mark_code` or `handle_code_in_pre`.

---

## 10. Summary & Next Steps

In this **Markdown Generation Basics** tutorial, you learned to:

- Configure the **DefaultMarkdownGenerator** with HTML-to-text options.  
- Select different HTML sources using the `content_source` parameter.  
- Use **BM25ContentFilter** for query-specific extraction or **PruningContentFilter** for general noise removal.  
- Distinguish between raw and filtered markdown (`fit_markdown`).  
- Leverage the `MarkdownGenerationResult` object to handle different forms of output (citations, references, etc.).

Now you can produce high-quality Markdown from any website, focusing on exactly the content you need—an essential step for powering AI models, summarization pipelines, or knowledge-base queries.

**Last Updated**: 2025-01-01

```


## File: docs/md_v2/core/page-interaction.md

```md
# Page Interaction

Crawl4AI provides powerful features for interacting with **dynamic** webpages, handling JavaScript execution, waiting for conditions, and managing multi-step flows. By combining **js_code**, **wait_for**, and certain **CrawlerRunConfig** parameters, you can:

1. Click “Load More” buttons  
2. Fill forms and submit them  
3. Wait for elements or data to appear  
4. Reuse sessions across multiple steps  

Below is a quick overview of how to do it.

---

## 1. JavaScript Execution

### Basic Execution

**`js_code`** in **`CrawlerRunConfig`** accepts either a single JS string or a list of JS snippets.  
**Example**: We’ll scroll to the bottom of the page, then optionally click a “Load More” button.

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

---

## 2. Wait Conditions

### 2.1 CSS-Based Waiting

Sometimes, you just want to wait for a specific element to appear. For example:

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

**Key param**:
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

---

## 3. Handling Dynamic Content

Many modern sites require **multiple steps**: scrolling, clicking “Load More,” or updating via JavaScript. Below are typical patterns.

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

**Key params**:
- **`session_id="hn_session"`**: Keep the same page across multiple calls to `arun()`.
- **`js_only=True`**: We’re not performing a full reload, just applying JS in the existing page.
- **`wait_for`** with `js:`: Wait for item count to grow beyond 30.

---

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

**In reality**: Replace IDs or classes with the real site’s form selectors.

---

## 4. Timing Control

1. **`page_timeout`** (ms): Overall page load or script execution time limit.  
2. **`delay_before_return_html`** (seconds): Wait an extra moment before capturing the final HTML.  
3. **`mean_delay`** & **`max_range`**: If you call `arun_many()` with multiple URLs, these add a random pause between each request.

**Example**:

```python
config = CrawlerRunConfig(
    page_timeout=60000,  # 60s limit
    delay_before_return_html=2.5
)
```

---

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

**Key Points**:

- **`session_id`**: Keep the same page open.  
- **`js_code`** + **`wait_for`** + **`js_only=True`**: We do partial refreshes, waiting for new commits to appear.  
- **`cache_mode=CacheMode.BYPASS`** ensures we always see fresh data each step.

---

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

---

## 7. Relevant `CrawlerRunConfig` Parameters

Below are the key interaction-related parameters in `CrawlerRunConfig`. For a full list, see [Configuration Parameters](../api/parameters.md).

- **`js_code`**: JavaScript to run after initial load.  
- **`js_only`**: If `True`, no new page navigation—only JS in the existing session.  
- **`wait_for`**: CSS (`"css:..."`) or JS (`"js:..."`) expression to wait for.  
- **`session_id`**: Reuse the same page across calls.  
- **`cache_mode`**: Whether to read/write from the cache or bypass.  
- **`remove_overlay_elements`**: Remove certain popups automatically.  
- **`simulate_user`, `override_navigator`, `magic`**: Anti-bot or “human-like” interactions.

---

## 8. Conclusion

Crawl4AI’s **page interaction** features let you:

1. **Execute JavaScript** for scrolling, clicks, or form filling.  
2. **Wait** for CSS or custom JS conditions before capturing data.  
3. **Handle** multi-step flows (like “Load More”) with partial reloads or persistent sessions.  
4. Combine with **structured extraction** for dynamic sites.

With these tools, you can scrape modern, interactive webpages confidently. For advanced hooking, user simulation, or in-depth config, check the [API reference](../api/parameters.md) or related advanced docs. Happy scripting!
```


## File: docs/md_v2/core/quickstart.md

```md
# Getting Started with Crawl4AI

Welcome to **Crawl4AI**, an open-source LLM-friendly Web Crawler & Scraper. In this tutorial, you’ll:

1. Run your **first crawl** using minimal configuration.  
2. Generate **Markdown** output (and learn how it’s influenced by content filters).  
3. Experiment with a simple **CSS-based extraction** strategy.  
4. See a glimpse of **LLM-based extraction** (including open-source and closed-source model options).  
5. Crawl a **dynamic** page that loads content via JavaScript.

---

## 1. Introduction

Crawl4AI provides:

- An asynchronous crawler, **`AsyncWebCrawler`**.  
- Configurable browser and run settings via **`BrowserConfig`** and **`CrawlerRunConfig`**.  
- Automatic HTML-to-Markdown conversion via **`DefaultMarkdownGenerator`** (supports optional filters).  
- Multiple extraction strategies (LLM-based or “traditional” CSS/XPath-based).

By the end of this guide, you’ll have performed a basic crawl, generated Markdown, tried out two extraction strategies, and crawled a dynamic page that uses “Load More” buttons or JavaScript updates.

---

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

**What’s happening?**
- **`AsyncWebCrawler`** launches a headless browser (Chromium by default).
- It fetches `https://example.com`.
- Crawl4AI automatically converts the HTML into Markdown.

You now have a simple, working crawl!

---

## 3. Basic Configuration (Light Introduction)

Crawl4AI’s crawler can be heavily customized using two main classes:

1. **`BrowserConfig`**: Controls browser behavior (headless or full UI, user agent, JavaScript toggles, etc.).  
2. **`CrawlerRunConfig`**: Controls how each crawl runs (caching, extraction, timeouts, hooking, etc.).

Below is an example with minimal usage:

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

> IMPORTANT: By default cache mode is set to `CacheMode.ENABLED`. So to have fresh content, you need to set it to `CacheMode.BYPASS`

We’ll explore more advanced config in later tutorials (like enabling proxies, PDF output, multi-tab sessions, etc.). For now, just note how you pass these objects to manage crawling.

---

## 4. Generating Markdown Output

By default, Crawl4AI automatically generates Markdown from each crawled page. However, the exact output depends on whether you specify a **markdown generator** or **content filter**.

- **`result.markdown`**:  
  The direct HTML-to-Markdown conversion.  
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

---

## 5. Simple Data Extraction (CSS-based)

Crawl4AI can also extract structured data (JSON) using CSS or XPath selectors. Below is a minimal CSS-based example:

> **New!** Crawl4AI now provides a powerful utility to automatically generate extraction schemas using LLM. This is a one-time cost that gives you a reusable schema for fast, LLM-free extractions:

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

For a complete guide on schema generation and advanced usage, see [No-LLM Extraction Strategies](../extraction/no-llm-strategies.md).

Here's a basic extraction example:

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

**Why is this helpful?**
- Great for repetitive page structures (e.g., item listings, articles).
- No AI usage or costs.
- The crawler returns a JSON string you can parse or store.

> Tips: You can pass raw HTML to the crawler instead of a URL. To do so, prefix the HTML with `raw://`.

---

## 6. Simple Data Extraction (LLM-based)

For more complex or irregular pages, a language model can parse text intelligently into a structure you define. Crawl4AI supports **open-source** or **closed-source** providers:

- **Open-Source Models** (e.g., `ollama/llama3.3`, `no_token`)  
- **OpenAI Models** (e.g., `openai/gpt-4`, requires `api_token`)  
- Or any provider supported by the underlying library

Below is an example using **open-source** style (no token) and closed-source:

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

**What’s happening?**
- We define a Pydantic schema (`PricingInfo`) describing the fields we want.
- The LLM extraction strategy uses that schema and your instructions to transform raw text into structured JSON.
- Depending on the **provider** and **api_token**, you can use local models or a remote API.

---

## 7. Multi-URL Concurrency (Preview)

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

The example above shows two ways to handle multiple URLs:
1. **Streaming mode** (`stream=True`): Process results as they become available using `async for`
2. **Batch mode** (`stream=False`): Wait for all results to complete

For more advanced concurrency (e.g., a **semaphore-based** approach, **adaptive memory usage throttling**, or customized rate limiting), see [Advanced Multi-URL Crawling](../advanced/multi-url-crawling.md).

---

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

**Key Points**:

- **`BrowserConfig(headless=False)`**: We want to watch it click “Next Page.”  
- **`CrawlerRunConfig(...)`**: We specify the extraction strategy, pass `session_id` to reuse the same page.  
- **`js_code`** and **`wait_for`** are used for subsequent pages (`page > 0`) to click the “Next” button and wait for new commits to load.  
- **`js_only=True`** indicates we’re not re-navigating but continuing the existing session.  
- Finally, we call `kill_session()` to clean up the page and browser session.

---

## 9. Next Steps

Congratulations! You have:

1. Performed a basic crawl and printed Markdown.  
2. Used **content filters** with a markdown generator.  
3. Extracted JSON via **CSS** or **LLM** strategies.  
4. Handled **dynamic** pages with JavaScript triggers.

If you’re ready for more, check out:

- **Installation**: A deeper dive into advanced installs, Docker usage (experimental), or optional dependencies.  
- **Hooks & Auth**: Learn how to run custom JavaScript or handle logins with cookies, local storage, etc.  
- **Deployment**: Explore ephemeral testing in Docker or plan for the upcoming stable Docker release.  
- **Browser Management**: Delve into user simulation, stealth modes, and concurrency best practices.  

Crawl4AI is a powerful, flexible tool. Enjoy building out your scrapers, data pipelines, or AI-driven extraction flows. Happy crawling!
```


## File: docs/md_v2/core/simple-crawling.md

```md
# Simple Crawling

This guide covers the basics of web crawling with Crawl4AI. You'll learn how to set up a crawler, make your first request, and understand the response.

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
result = await crawler.arun(
    url="https://example.com",
    config=CrawlerRunConfig(fit_markdown=True)
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

Always check if the crawl was successful:

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

Here's a more comprehensive example demonstrating common usage patterns:

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

```


## File: docs/md_v2/advanced/advanced-features.md

```md
# Overview of Some Important Advanced Features 
(Proxy, PDF, Screenshot, SSL, Headers, & Storage State)

Crawl4AI offers multiple power-user features that go beyond simple crawling. This tutorial covers:

1. **Proxy Usage**  
2. **Capturing PDFs & Screenshots**  
3. **Handling SSL Certificates**  
4. **Custom Headers**  
5. **Session Persistence & Local Storage**  
6. **Robots.txt Compliance**  

> **Prerequisites**  
> - You have a basic grasp of [AsyncWebCrawler Basics](../core/simple-crawling.md)  
> - You know how to run or configure your Python environment with Playwright installed

---

## 1. Proxy Usage

If you need to route your crawl traffic through a proxy—whether for IP rotation, geo-testing, or privacy—Crawl4AI supports it via `BrowserConfig.proxy_config`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    browser_cfg = BrowserConfig(
        proxy_config={
            "server": "http://proxy.example.com:8080",
            "username": "myuser",
            "password": "mypass",
        },
        headless=True
    )
    crawler_cfg = CrawlerRunConfig(
        verbose=True
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://www.whatismyip.com/",
            config=crawler_cfg
        )
        if result.success:
            print("[OK] Page fetched via proxy.")
            print("Page HTML snippet:", result.html[:200])
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**  
- **`proxy_config`** expects a dict with `server` and optional auth credentials.  
- Many commercial proxies provide an HTTP/HTTPS “gateway” server that you specify in `server`.  
- If your proxy doesn’t need auth, omit `username`/`password`.

---

## 2. Capturing PDFs & Screenshots

Sometimes you need a visual record of a page or a PDF “printout.” Crawl4AI can do both in one pass:

```python
import os, asyncio
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

async def main():
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        screenshot=True,
        pdf=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/List_of_common_misconceptions",
            config=run_config
        )
        if result.success:
            print(f"Screenshot data present: {result.screenshot is not None}")
            print(f"PDF data present: {result.pdf is not None}")

            if result.screenshot:
                print(f"[OK] Screenshot captured, size: {len(result.screenshot)} bytes")
                with open("wikipedia_screenshot.png", "wb") as f:
                    f.write(b64decode(result.screenshot))
            else:
                print("[WARN] Screenshot data is None.")

            if result.pdf:
                print(f"[OK] PDF captured, size: {len(result.pdf)} bytes")
                with open("wikipedia_page.pdf", "wb") as f:
                    f.write(result.pdf)
            else:
                print("[WARN] PDF data is None.")

        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Why PDF + Screenshot?**  
- Large or complex pages can be slow or error-prone with “traditional” full-page screenshots.  
- Exporting a PDF is more reliable for very long pages. Crawl4AI automatically converts the first PDF page into an image if you request both.  

**Relevant Parameters**  
- **`pdf=True`**: Exports the current page as a PDF (base64-encoded in `result.pdf`).  
- **`screenshot=True`**: Creates a screenshot (base64-encoded in `result.screenshot`).  
- **`scan_full_page`** or advanced hooking can further refine how the crawler captures content.

---

## 3. Handling SSL Certificates

If you need to verify or export a site’s SSL certificate—for compliance, debugging, or data analysis—Crawl4AI can fetch it during the crawl:

```python
import asyncio, os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    
    config = CrawlerRunConfig(
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        
        if result.success and result.ssl_certificate:
            cert = result.ssl_certificate
            print("\nCertificate Information:")
            print(f"Issuer (CN): {cert.issuer.get('CN', '')}")
            print(f"Valid until: {cert.valid_until}")
            print(f"Fingerprint: {cert.fingerprint}")

            # Export in multiple formats:
            cert.to_json(os.path.join(tmp_dir, "certificate.json"))
            cert.to_pem(os.path.join(tmp_dir, "certificate.pem"))
            cert.to_der(os.path.join(tmp_dir, "certificate.der"))
            
            print("\nCertificate exported to JSON/PEM/DER in 'tmp' folder.")
        else:
            print("[ERROR] No certificate or crawl failed.")

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**  
- **`fetch_ssl_certificate=True`** triggers certificate retrieval.  
- `result.ssl_certificate` includes methods (`to_json`, `to_pem`, `to_der`) for saving in various formats (handy for server config, Java keystores, etc.).

---

## 4. Custom Headers

Sometimes you need to set custom headers (e.g., language preferences, authentication tokens, or specialized user-agent strings). You can do this in multiple ways:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Option 1: Set headers at the crawler strategy level
    crawler1 = AsyncWebCrawler(
        # The underlying strategy can accept headers in its constructor
        crawler_strategy=None  # We'll override below for clarity
    )
    crawler1.crawler_strategy.update_user_agent("MyCustomUA/1.0")
    crawler1.crawler_strategy.set_custom_headers({
        "Accept-Language": "fr-FR,fr;q=0.9"
    })
    result1 = await crawler1.arun("https://www.example.com")
    print("Example 1 result success:", result1.success)

    # Option 2: Pass headers directly to `arun()`
    crawler2 = AsyncWebCrawler()
    result2 = await crawler2.arun(
        url="https://www.example.com",
        headers={"Accept-Language": "es-ES,es;q=0.9"}
    )
    print("Example 2 result success:", result2.success)

if __name__ == "__main__":
    asyncio.run(main())
```

**Notes**  
- Some sites may react differently to certain headers (e.g., `Accept-Language`).  
- If you need advanced user-agent randomization or client hints, see [Identity-Based Crawling (Anti-Bot)](./identity-based-crawling.md) or use `UserAgentGenerator`.

---

## 5. Session Persistence & Local Storage

Crawl4AI can preserve cookies and localStorage so you can continue where you left off—ideal for logging into sites or skipping repeated auth flows.

### 5.1 `storage_state`

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    storage_dict = {
        "cookies": [
            {
                "name": "session",
                "value": "abcd1234",
                "domain": "example.com",
                "path": "/",
                "expires": 1699999999.0,
                "httpOnly": False,
                "secure": False,
                "sameSite": "None"
            }
        ],
        "origins": [
            {
                "origin": "https://example.com",
                "localStorage": [
                    {"name": "token", "value": "my_auth_token"}
                ]
            }
        ]
    }

    # Provide the storage state as a dictionary to start "already logged in"
    async with AsyncWebCrawler(
        headless=True,
        storage_state=storage_dict
    ) as crawler:
        result = await crawler.arun("https://example.com/protected")
        if result.success:
            print("Protected page content length:", len(result.html))
        else:
            print("Failed to crawl protected page")

if __name__ == "__main__":
    asyncio.run(main())
```

### 5.2 Exporting & Reusing State

You can sign in once, export the browser context, and reuse it later—without re-entering credentials.

- **`await context.storage_state(path="my_storage.json")`**: Exports cookies, localStorage, etc. to a file.  
- Provide `storage_state="my_storage.json"` on subsequent runs to skip the login step.

**See**: [Detailed session management tutorial](./session-management.md) or [Explanations → Browser Context & Managed Browser](./identity-based-crawling.md) for more advanced scenarios (like multi-step logins, or capturing after interactive pages).

---

## 6. Robots.txt Compliance

Crawl4AI supports respecting robots.txt rules with efficient caching:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Enable robots.txt checking in config
    config = CrawlerRunConfig(
        check_robots_txt=True  # Will check and respect robots.txt rules
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            "https://example.com",
            config=config
        )
        
        if not result.success and result.status_code == 403:
            print("Access denied by robots.txt")

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**
- Robots.txt files are cached locally for efficiency
- Cache is stored in `~/.crawl4ai/robots/robots_cache.db`
- Cache has a default TTL of 7 days
- If robots.txt can't be fetched, crawling is allowed
- Returns 403 status code if URL is disallowed

---

## Putting It All Together

Here’s a snippet that combines multiple “advanced” features (proxy, PDF, screenshot, SSL, custom headers, and session reuse) into one run. Normally, you’d tailor each setting to your project’s needs.

```python
import os, asyncio
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    # 1. Browser config with proxy + headless
    browser_cfg = BrowserConfig(
        proxy_config={
            "server": "http://proxy.example.com:8080",
            "username": "myuser",
            "password": "mypass",
        },
        headless=True,
    )

    # 2. Crawler config with PDF, screenshot, SSL, custom headers, and ignoring caches
    crawler_cfg = CrawlerRunConfig(
        pdf=True,
        screenshot=True,
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS,
        headers={"Accept-Language": "en-US,en;q=0.8"},
        storage_state="my_storage.json",  # Reuse session from a previous sign-in
        verbose=True,
    )

    # 3. Crawl
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url = "https://secure.example.com/protected", 
            config=crawler_cfg
        )
        
        if result.success:
            print("[OK] Crawled the secure page. Links found:", len(result.links.get("internal", [])))
            
            # Save PDF & screenshot
            if result.pdf:
                with open("result.pdf", "wb") as f:
                    f.write(b64decode(result.pdf))
            if result.screenshot:
                with open("result.png", "wb") as f:
                    f.write(b64decode(result.screenshot))
            
            # Check SSL cert
            if result.ssl_certificate:
                print("SSL Issuer CN:", result.ssl_certificate.issuer.get("CN", ""))
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Conclusion & Next Steps

You’ve now explored several **advanced** features:

- **Proxy Usage**  
- **PDF & Screenshot** capturing for large or critical pages  
- **SSL Certificate** retrieval & exporting  
- **Custom Headers** for language or specialized requests  
- **Session Persistence** via storage state
- **Robots.txt Compliance**

With these power tools, you can build robust scraping workflows that mimic real user behavior, handle secure sites, capture detailed snapshots, and manage sessions across multiple runs—streamlining your entire data collection pipeline.

**Last Updated**: 2025-01-01
```


## File: docs/md_v2/advanced/crawl-dispatcher.md

```md
# Crawl Dispatcher

We’re excited to announce a **Crawl Dispatcher** module that can handle **thousands** of crawling tasks simultaneously. By efficiently managing system resources (memory, CPU, network), this dispatcher ensures high-performance data extraction at scale. It also provides **real-time monitoring** of each crawler’s status, memory usage, and overall progress.

Stay tuned—this feature is **coming soon** in an upcoming release of Crawl4AI! For the latest news, keep an eye on our changelogs and follow [@unclecode](https://twitter.com/unclecode) on X.

Below is a **sample** of how the dispatcher’s performance monitor might look in action:

![Crawl Dispatcher Performance Monitor](../assets/images/dispatcher.png)


We can’t wait to bring you this streamlined, **scalable** approach to multi-URL crawling—**watch this space** for updates!
```


## File: docs/md_v2/advanced/file-downloading.md

```md
# Download Handling in Crawl4AI

This guide explains how to use Crawl4AI to handle file downloads during crawling. You'll learn how to trigger downloads, specify download locations, and access downloaded files.

## Enabling Downloads

To enable downloads, set the `accept_downloads` parameter in the `BrowserConfig` object and pass it to the crawler.

```python
from crawl4ai.async_configs import BrowserConfig, AsyncWebCrawler

async def main():
    config = BrowserConfig(accept_downloads=True)  # Enable downloads globally
    async with AsyncWebCrawler(config=config) as crawler:
        # ... your crawling logic ...

asyncio.run(main())
```

## Specifying Download Location

Specify the download directory using the `downloads_path` attribute in the `BrowserConfig` object. If not provided, Crawl4AI defaults to creating a "downloads" directory inside the `.crawl4ai` folder in your home directory.

```python
from crawl4ai.async_configs import BrowserConfig
import os

downloads_path = os.path.join(os.getcwd(), "my_downloads")  # Custom download path
os.makedirs(downloads_path, exist_ok=True)

config = BrowserConfig(accept_downloads=True, downloads_path=downloads_path)

async def main():
    async with AsyncWebCrawler(config=config) as crawler:
        result = await crawler.arun(url="https://example.com")
        # ...
```

## Triggering Downloads

Downloads are typically triggered by user interactions on a web page, such as clicking a download button. Use `js_code` in `CrawlerRunConfig` to simulate these actions and `wait_for` to allow sufficient time for downloads to start.

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig(
    js_code="""
        const downloadLink = document.querySelector('a[href$=".exe"]');
        if (downloadLink) {
            downloadLink.click();
        }
    """,
    wait_for=5  # Wait 5 seconds for the download to start
)

result = await crawler.arun(url="https://www.python.org/downloads/", config=config)
```

## Accessing Downloaded Files

The `downloaded_files` attribute of the `CrawlResult` object contains paths to downloaded files.

```python
if result.downloaded_files:
    print("Downloaded files:")
    for file_path in result.downloaded_files:
        print(f"- {file_path}")
        file_size = os.path.getsize(file_path)
        print(f"- File size: {file_size} bytes")
else:
    print("No files downloaded.")
```

## Example: Downloading Multiple Files

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os
from pathlib import Path

async def download_multiple_files(url: str, download_path: str):
    config = BrowserConfig(accept_downloads=True, downloads_path=download_path)
    async with AsyncWebCrawler(config=config) as crawler:
        run_config = CrawlerRunConfig(
            js_code="""
                const downloadLinks = document.querySelectorAll('a[download]');
                for (const link of downloadLinks) {
                    link.click();
                    // Delay between clicks
                    await new Promise(r => setTimeout(r, 2000));  
                }
            """,
            wait_for=10  # Wait for all downloads to start
        )
        result = await crawler.arun(url=url, config=run_config)

        if result.downloaded_files:
            print("Downloaded files:")
            for file in result.downloaded_files:
                print(f"- {file}")
        else:
            print("No files downloaded.")

# Usage
download_path = os.path.join(Path.home(), ".crawl4ai", "downloads")
os.makedirs(download_path, exist_ok=True)

asyncio.run(download_multiple_files("https://www.python.org/downloads/windows/", download_path))
```

## Important Considerations

- **Browser Context:** Downloads are managed within the browser context. Ensure `js_code` correctly targets the download triggers on the webpage.
- **Timing:** Use `wait_for` in `CrawlerRunConfig` to manage download timing.
- **Error Handling:** Handle errors to manage failed downloads or incorrect paths gracefully.
- **Security:** Scan downloaded files for potential security threats before use.

This revised guide ensures consistency with the `Crawl4AI` codebase by using `BrowserConfig` and `CrawlerRunConfig` for all download-related configurations. Let me know if further adjustments are needed!
```


## File: docs/md_v2/advanced/hooks-auth.md

```md
# Hooks & Auth in AsyncWebCrawler

Crawl4AI’s **hooks** let you customize the crawler at specific points in the pipeline:

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

>    **Identity-Based Crawling**: For robust auth, consider identity-based crawling (or passing a session ID) to preserve state. Run your initial login steps in a separate, well-defined process, then feed that session to your main crawl—rather than shoehorning complex authentication into early hooks. Check out [Identity-Based Crawling](../advanced/identity-based-crawling.md) for more details.

>    **Be Cautious**: Overwriting or removing elements in the wrong hook can compromise the final crawl. Keep hooks focused on smaller tasks (like route filters, custom headers), and let your main logic (crawling, data extraction) proceed normally.


Below is an example demonstration.

---

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

---

## Hook Lifecycle Summary

1. **`on_browser_created`**:  
   - Browser is up, but **no** pages or contexts yet.  
   - Light setup only—don’t try to open or close pages here (that belongs in `on_page_context_created`).

2. **`on_page_context_created`**:  
   - Perfect for advanced **auth** or route blocking.  
   - You have a **page** + **context** ready but haven’t navigated to the target URL yet.

3. **`before_goto`**:  
   - Right before navigation. Typically used for setting **custom headers** or logging the target URL.

4. **`after_goto`**:  
   - After page navigation is done. Good place for verifying content or waiting on essential elements. 

5. **`on_user_agent_updated`**:  
   - Whenever the user agent changes (for stealth or different UA modes).

6. **`on_execution_started`**:  
   - If you set `js_code` or run custom scripts, this runs once your JS is about to start.

7. **`before_retrieve_html`**:  
   - Just before the final HTML snapshot is taken. Often you do a final scroll or lazy-load triggers here.

8. **`before_return_html`**:  
   - The last hook before returning HTML to the `CrawlResult`. Good for logging HTML length or minor modifications.

---

## When to Handle Authentication

**Recommended**: Use **`on_page_context_created`** if you need to:

- Navigate to a login page or fill forms
- Set cookies or localStorage tokens
- Block resource routes to avoid ads

This ensures the newly created context is under your control **before** `arun()` navigates to the main URL.

---

## Additional Considerations

- **Session Management**: If you want multiple `arun()` calls to reuse a single session, pass `session_id=` in your `CrawlerRunConfig`. Hooks remain the same.  
- **Performance**: Hooks can slow down crawling if they do heavy tasks. Keep them concise.  
- **Error Handling**: If a hook fails, the overall crawl might fail. Catch exceptions or handle them gracefully.  
- **Concurrency**: If you run `arun_many()`, each URL triggers these hooks in parallel. Ensure your hooks are thread/async-safe.

---

## Conclusion

Hooks provide **fine-grained** control over:

- **Browser** creation (light tasks only)
- **Page** and **context** creation (auth, route blocking)
- **Navigation** phases
- **Final HTML** retrieval

Follow the recommended usage:
- **Login** or advanced tasks in `on_page_context_created`  
- **Custom headers** or logs in `before_goto` / `after_goto`  
- **Scrolling** or final checks in `before_retrieve_html` / `before_return_html`


```


## File: docs/md_v2/advanced/identity-based-crawling.md

```md
# Preserve Your Identity with Crawl4AI

Crawl4AI empowers you to navigate and interact with the web using your **authentic digital identity**, ensuring you’re recognized as a human and not mistaken for a bot. This tutorial covers:

1. **Managed Browsers** – The recommended approach for persistent profiles and identity-based crawling.  
2. **Magic Mode** – A simplified fallback solution for quick automation without persistent identity.

---

## 1. Managed Browsers: Your Digital Identity Solution

**Managed Browsers** let developers create and use **persistent browser profiles**. These profiles store local storage, cookies, and other session data, letting you browse as your **real self**—complete with logins, preferences, and cookies.

### Key Benefits

- **Authentic Browsing Experience**: Retain session data and browser fingerprints as though you’re a normal user.  
- **Effortless Configuration**: Once you log in or solve CAPTCHAs in your chosen data directory, you can re-run crawls without repeating those steps.  
- **Empowered Data Access**: If you can see the data in your own browser, you can automate its retrieval with your genuine identity.

---

Below is a **partial update** to your **Managed Browsers** tutorial, specifically the section about **creating a user-data directory** using **Playwright’s Chromium** binary rather than a system-wide Chrome/Edge. We’ll show how to **locate** that binary and launch it with a `--user-data-dir` argument to set up your profile. You can then point `BrowserConfig.user_data_dir` to that folder for subsequent crawls.

---

### Creating a User Data Directory (Command-Line Approach via Playwright)

If you installed Crawl4AI (which installs Playwright under the hood), you already have a Playwright-managed Chromium on your system. Follow these steps to launch that **Chromium** from your command line, specifying a **custom** data directory:

1. **Find** the Playwright Chromium binary:
   - On most systems, installed browsers go under a `~/.cache/ms-playwright/` folder or similar path.  
   - To see an overview of installed browsers, run:
     ```bash
     python -m playwright install --dry-run
     ```
     or
     ```bash
     playwright install --dry-run
     ```
     (depending on your environment). This shows where Playwright keeps Chromium.

   - For instance, you might see a path like:
     ```
     ~/.cache/ms-playwright/chromium-1234/chrome-linux/chrome
     ```
     on Linux, or a corresponding folder on macOS/Windows.

2. **Launch** the Playwright Chromium binary with a **custom** user-data directory:
   ```bash
   # Linux example
   ~/.cache/ms-playwright/chromium-1234/chrome-linux/chrome \
       --user-data-dir=/home/<you>/my_chrome_profile
   ```
   ```bash
   # macOS example (Playwright’s internal binary)
   ~/Library/Caches/ms-playwright/chromium-1234/chrome-mac/Chromium.app/Contents/MacOS/Chromium \
       --user-data-dir=/Users/<you>/my_chrome_profile
   ```
   ```powershell
   # Windows example (PowerShell/cmd)
   "C:\Users\<you>\AppData\Local\ms-playwright\chromium-1234\chrome-win\chrome.exe" ^
       --user-data-dir="C:\Users\<you>\my_chrome_profile"
   ```
   
   **Replace** the path with the actual subfolder indicated in your `ms-playwright` cache structure.  
   - This **opens** a fresh Chromium with your new or existing data folder.  
   - **Log into** any sites or configure your browser the way you want.  
   - **Close** when done—your profile data is saved in that folder.

3. **Use** that folder in **`BrowserConfig.user_data_dir`**:
   ```python
   from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

   browser_config = BrowserConfig(
       headless=True,
       use_managed_browser=True,
       user_data_dir="/home/<you>/my_chrome_profile",
       browser_type="chromium"
   )
   ```
   - Next time you run your code, it reuses that folder—**preserving** your session data, cookies, local storage, etc.

---

## 3. Using Managed Browsers in Crawl4AI

Once you have a data directory with your session data, pass it to **`BrowserConfig`**:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    # 1) Reference your persistent data directory
    browser_config = BrowserConfig(
        headless=True,             # 'True' for automated runs
        verbose=True,
        use_managed_browser=True,  # Enables persistent browser strategy
        browser_type="chromium",
        user_data_dir="/path/to/my-chrome-profile"
    )

    # 2) Standard crawl config
    crawl_config = CrawlerRunConfig(
        wait_for="css:.logged-in-content"
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com/private", config=crawl_config)
        if result.success:
            print("Successfully accessed private data with your identity!")
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

### Workflow

1. **Login** externally (via CLI or your normal Chrome with `--user-data-dir=...`).  
2. **Close** that browser.  
3. **Use** the same folder in `user_data_dir=` in Crawl4AI.  
4. **Crawl** – The site sees your identity as if you’re the same user who just logged in.

---

## 4. Magic Mode: Simplified Automation

If you **don’t** need a persistent profile or identity-based approach, **Magic Mode** offers a quick way to simulate human-like browsing without storing long-term data.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        config=CrawlerRunConfig(
            magic=True,  # Simplifies a lot of interaction
            remove_overlay_elements=True,
            page_timeout=60000
        )
    )
```

**Magic Mode**:

- Simulates a user-like experience  
- Randomizes user agent & navigator
- Randomizes interactions & timings  
- Masks automation signals  
- Attempts pop-up handling  

**But** it’s no substitute for **true** user-based sessions if you want a fully legitimate identity-based solution.

---

## 5. Comparing Managed Browsers vs. Magic Mode

| Feature                    | **Managed Browsers**                                           | **Magic Mode**                                     |
|----------------------------|---------------------------------------------------------------|-----------------------------------------------------|
| **Session Persistence**    | Full localStorage/cookies retained in user_data_dir           | No persistent data (fresh each run)                |
| **Genuine Identity**       | Real user profile with full rights & preferences              | Emulated user-like patterns, but no actual identity |
| **Complex Sites**          | Best for login-gated sites or heavy config                    | Simple tasks, minimal login or config needed        |
| **Setup**                  | External creation of user_data_dir, then use in Crawl4AI       | Single-line approach (`magic=True`)                 |
| **Reliability**            | Extremely consistent (same data across runs)                  | Good for smaller tasks, can be less stable          |

---

## 6. Using the BrowserProfiler Class

Crawl4AI provides a dedicated `BrowserProfiler` class for managing browser profiles, making it easy to create, list, and delete profiles for identity-based browsing.

### Creating and Managing Profiles with BrowserProfiler

The `BrowserProfiler` class offers a comprehensive API for browser profile management:

```python
import asyncio
from crawl4ai import BrowserProfiler

async def manage_profiles():
    # Create a profiler instance
    profiler = BrowserProfiler()
    
    # Create a profile interactively - opens a browser window
    profile_path = await profiler.create_profile(
        profile_name="my-login-profile"  # Optional: name your profile
    )
    
    print(f"Profile saved at: {profile_path}")
    
    # List all available profiles
    profiles = profiler.list_profiles()
    
    for profile in profiles:
        print(f"Profile: {profile['name']}")
        print(f"  Path: {profile['path']}")
        print(f"  Created: {profile['created']}")
        print(f"  Browser type: {profile['type']}")
    
    # Get a specific profile path by name
    specific_profile = profiler.get_profile_path("my-login-profile")
    
    # Delete a profile when no longer needed
    success = profiler.delete_profile("old-profile-name")
    
asyncio.run(manage_profiles())
```

**How profile creation works:**
1. A browser window opens for you to interact with
2. You log in to websites, set preferences, etc.
3. When you're done, press 'q' in the terminal to close the browser
4. The profile is saved in the Crawl4AI profiles directory
5. You can use the returned path with `BrowserConfig.user_data_dir`

### Interactive Profile Management

The `BrowserProfiler` also offers an interactive management console that guides you through profile creation, listing, and deletion:

```python
import asyncio
from crawl4ai import BrowserProfiler, AsyncWebCrawler, BrowserConfig

# Define a function to use a profile for crawling
async def crawl_with_profile(profile_path, url):
    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        user_data_dir=profile_path
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url)
        return result

async def main():
    # Create a profiler instance
    profiler = BrowserProfiler()
    
    # Launch the interactive profile manager
    # Passing the crawl function as a callback adds a "crawl with profile" option
    await profiler.interactive_manager(crawl_callback=crawl_with_profile)
    
asyncio.run(main())
```

### Legacy Methods

For backward compatibility, the previous methods on `ManagedBrowser` are still available, but they delegate to the new `BrowserProfiler` class:

```python
from crawl4ai.browser_manager import ManagedBrowser

# These methods still work but use BrowserProfiler internally
profiles = ManagedBrowser.list_profiles()
```

### Complete Example

See the full example in `docs/examples/identity_based_browsing.py` for a complete demonstration of creating and using profiles for authenticated browsing using the new `BrowserProfiler` class.

---

## 7. Summary

- **Create** your user-data directory either:
  - By launching Chrome/Chromium externally with `--user-data-dir=/some/path` 
  - Or by using the built-in `BrowserProfiler.create_profile()` method
  - Or through the interactive interface with `profiler.interactive_manager()`
- **Log in** or configure sites as needed, then close the browser
- **Reference** that folder in `BrowserConfig(user_data_dir="...")` + `use_managed_browser=True`
- **List and reuse** profiles with `BrowserProfiler.list_profiles()`
- **Manage** your profiles with the dedicated `BrowserProfiler` class
- Enjoy **persistent** sessions that reflect your real identity
- If you only need quick, ephemeral automation, **Magic Mode** might suffice

**Recommended**: Always prefer a **Managed Browser** for robust, identity-based crawling and simpler interactions with complex sites. Use **Magic Mode** for quick tasks or prototypes where persistent data is unnecessary.

With these approaches, you preserve your **authentic** browsing environment, ensuring the site sees you exactly as a normal user—no repeated logins or wasted time.
```


## File: docs/md_v2/advanced/lazy-loading.md

```md
## Handling Lazy-Loaded Images

Many websites now load images **lazily** as you scroll. If you need to ensure they appear in your final crawl (and in `result.media`), consider:

1. **`wait_for_images=True`** – Wait for images to fully load.  
2. **`scan_full_page`** – Force the crawler to scroll the entire page, triggering lazy loads.  
3. **`scroll_delay`** – Add small delays between scroll steps.  

**Note**: If the site requires multiple “Load More” triggers or complex interactions, see the [Page Interaction docs](../core/page-interaction.md).

### Example: Ensuring Lazy Images Appear

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl4ai.async_configs import CacheMode

async def main():
    config = CrawlerRunConfig(
        # Force the crawler to wait until images are fully loaded
        wait_for_images=True,

        # Option 1: If you want to automatically scroll the page to load images
        scan_full_page=True,  # Tells the crawler to try scrolling the entire page
        scroll_delay=0.5,     # Delay (seconds) between scroll steps

        # Option 2: If the site uses a 'Load More' or JS triggers for images,
        # you can also specify js_code or wait_for logic here.

        cache_mode=CacheMode.BYPASS,
        verbose=True
    )

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        result = await crawler.arun("https://www.example.com/gallery", config=config)
        
        if result.success:
            images = result.media.get("images", [])
            print("Images found:", len(images))
            for i, img in enumerate(images[:5]):
                print(f"[Image {i}] URL: {img['src']}, Score: {img.get('score','N/A')}")
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Explanation**:

- **`wait_for_images=True`**  
  The crawler tries to ensure images have finished loading before finalizing the HTML.  
- **`scan_full_page=True`**  
  Tells the crawler to attempt scrolling from top to bottom. Each scroll step helps trigger lazy loading.  
- **`scroll_delay=0.5`**  
  Pause half a second between each scroll step. Helps the site load images before continuing.

**When to Use**:

- **Lazy-Loading**: If images appear only when the user scrolls into view, `scan_full_page` + `scroll_delay` helps the crawler see them.  
- **Heavier Pages**: If a page is extremely long, be mindful that scanning the entire page can be slow. Adjust `scroll_delay` or the max scroll steps as needed.

---

## Combining with Other Link & Media Filters

You can still combine **lazy-load** logic with the usual **exclude_external_images**, **exclude_domains**, or link filtration:

```python
config = CrawlerRunConfig(
    wait_for_images=True,
    scan_full_page=True,
    scroll_delay=0.5,

    # Filter out external images if you only want local ones
    exclude_external_images=True,

    # Exclude certain domains for links
    exclude_domains=["spammycdn.com"],
)
```

This approach ensures you see **all** images from the main domain while ignoring external ones, and the crawler physically scrolls the entire page so that lazy-loading triggers.

---

## Tips & Troubleshooting

1. **Long Pages**  
   - Setting `scan_full_page=True` on extremely long or infinite-scroll pages can be resource-intensive.  
   - Consider using [hooks](../core/page-interaction.md) or specialized logic to load specific sections or “Load More” triggers repeatedly.

2. **Mixed Image Behavior**  
   - Some sites load images in batches as you scroll. If you’re missing images, increase your `scroll_delay` or call multiple partial scrolls in a loop with JS code or hooks.

3. **Combining with Dynamic Wait**  
   - If the site has a placeholder that only changes to a real image after a certain event, you might do `wait_for="css:img.loaded"` or a custom JS `wait_for`.

4. **Caching**  
   - If `cache_mode` is enabled, repeated crawls might skip some network fetches. If you suspect caching is missing new images, set `cache_mode=CacheMode.BYPASS` for fresh fetches.

---

With **lazy-loading** support, **wait_for_images**, and **scan_full_page** settings, you can capture the entire gallery or feed of images you expect—even if the site only loads them as the user scrolls. Combine these with the standard media filtering and domain exclusion for a complete link & media handling strategy.
```


## File: docs/md_v2/advanced/multi-url-crawling.md

```md
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

4. **`memory_wait_timeout`** (`float`, default: `600.0`)
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

```


## File: docs/md_v2/advanced/network-console-capture.md

```md
# Network Requests & Console Message Capturing

Crawl4AI can capture all network requests and browser console messages during a crawl, which is invaluable for debugging, security analysis, or understanding page behavior.

## Configuration

To enable network and console capturing, use these configuration options:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Enable both network request capture and console message capture
config = CrawlerRunConfig(
    capture_network_requests=True,  # Capture all network requests and responses
    capture_console_messages=True   # Capture all browser console output
)
```

## Example Usage

```python
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Enable both network request capture and console message capture
    config = CrawlerRunConfig(
        capture_network_requests=True,
        capture_console_messages=True
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=config
        )
        
        if result.success:
            # Analyze network requests
            if result.network_requests:
                print(f"Captured {len(result.network_requests)} network events")
                
                # Count request types
                request_count = len([r for r in result.network_requests if r.get("event_type") == "request"])
                response_count = len([r for r in result.network_requests if r.get("event_type") == "response"])
                failed_count = len([r for r in result.network_requests if r.get("event_type") == "request_failed"])
                
                print(f"Requests: {request_count}, Responses: {response_count}, Failed: {failed_count}")
                
                # Find API calls
                api_calls = [r for r in result.network_requests 
                            if r.get("event_type") == "request" and "api" in r.get("url", "")]
                if api_calls:
                    print(f"Detected {len(api_calls)} API calls:")
                    for call in api_calls[:3]:  # Show first 3
                        print(f"  - {call.get('method')} {call.get('url')}")
            
            # Analyze console messages
            if result.console_messages:
                print(f"Captured {len(result.console_messages)} console messages")
                
                # Group by type
                message_types = {}
                for msg in result.console_messages:
                    msg_type = msg.get("type", "unknown")
                    message_types[msg_type] = message_types.get(msg_type, 0) + 1
                
                print("Message types:", message_types)
                
                # Show errors (often the most important)
                errors = [msg for msg in result.console_messages if msg.get("type") == "error"]
                if errors:
                    print(f"Found {len(errors)} console errors:")
                    for err in errors[:2]:  # Show first 2
                        print(f"  - {err.get('text', '')[:100]}")
            
            # Export all captured data to a file for detailed analysis
            with open("network_capture.json", "w") as f:
                json.dump({
                    "url": result.url,
                    "network_requests": result.network_requests or [],
                    "console_messages": result.console_messages or []
                }, f, indent=2)
            
            print("Exported detailed capture data to network_capture.json")

if __name__ == "__main__":
    asyncio.run(main())
```

## Captured Data Structure

### Network Requests

The `result.network_requests` contains a list of dictionaries, each representing a network event with these common fields:

| Field | Description |
|-------|-------------|
| `event_type` | Type of event: `"request"`, `"response"`, or `"request_failed"` |
| `url` | The URL of the request |
| `timestamp` | Unix timestamp when the event was captured |

#### Request Event Fields

```json
{
  "event_type": "request",
  "url": "https://example.com/api/data.json",
  "method": "GET",
  "headers": {"User-Agent": "...", "Accept": "..."},
  "post_data": "key=value&otherkey=value",
  "resource_type": "fetch",
  "is_navigation_request": false,
  "timestamp": 1633456789.123
}
```

#### Response Event Fields

```json
{
  "event_type": "response",
  "url": "https://example.com/api/data.json",
  "status": 200,
  "status_text": "OK",
  "headers": {"Content-Type": "application/json", "Cache-Control": "..."},
  "from_service_worker": false,
  "request_timing": {"requestTime": 1234.56, "receiveHeadersEnd": 1234.78},
  "timestamp": 1633456789.456
}
```

#### Failed Request Event Fields

```json
{
  "event_type": "request_failed",
  "url": "https://example.com/missing.png",
  "method": "GET",
  "resource_type": "image",
  "failure_text": "net::ERR_ABORTED 404",
  "timestamp": 1633456789.789
}
```

### Console Messages

The `result.console_messages` contains a list of dictionaries, each representing a console message with these common fields:

| Field | Description |
|-------|-------------|
| `type` | Message type: `"log"`, `"error"`, `"warning"`, `"info"`, etc. |
| `text` | The message text |
| `timestamp` | Unix timestamp when the message was captured |

#### Console Message Example

```json
{
  "type": "error",
  "text": "Uncaught TypeError: Cannot read property 'length' of undefined",
  "location": "https://example.com/script.js:123:45",
  "timestamp": 1633456790.123
}
```

## Key Benefits

- **Full Request Visibility**: Capture all network activity including:
  - Requests (URLs, methods, headers, post data)
  - Responses (status codes, headers, timing)
  - Failed requests (with error messages)
  
- **Console Message Access**: View all JavaScript console output:
  - Log messages
  - Warnings
  - Errors with stack traces
  - Developer debugging information

- **Debugging Power**: Identify issues such as:
  - Failed API calls or resource loading
  - JavaScript errors affecting page functionality
  - CORS or other security issues
  - Hidden API endpoints and data flows

- **Security Analysis**: Detect:
  - Unexpected third-party requests
  - Data leakage in request payloads
  - Suspicious script behavior

- **Performance Insights**: Analyze:
  - Request timing data
  - Resource loading patterns
  - Potential bottlenecks

## Use Cases

1. **API Discovery**: Identify hidden endpoints and data flows in single-page applications
2. **Debugging**: Track down JavaScript errors affecting page functionality
3. **Security Auditing**: Detect unwanted third-party requests or data leakage
4. **Performance Analysis**: Identify slow-loading resources
5. **Ad/Tracker Analysis**: Detect and catalog advertising or tracking calls

This capability is especially valuable for complex sites with heavy JavaScript, single-page applications, or when you need to understand the exact communication happening between a browser and servers.
```


## File: docs/md_v2/advanced/proxy-security.md

```md
# Proxy 

## Basic Proxy Setup

Simple proxy configuration with `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig

# Using proxy URL
browser_config = BrowserConfig(proxy="http://proxy.example.com:8080")
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")

# Using SOCKS proxy
browser_config = BrowserConfig(proxy="socks5://proxy.example.com:1080")
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Authenticated Proxy

Use an authenticated proxy with `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig

proxy_config = {
    "server": "http://proxy.example.com:8080",
    "username": "user",
    "password": "pass"
}

browser_config = BrowserConfig(proxy_config=proxy_config)
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

Here's the corrected documentation:

## Rotating Proxies 

Example using a proxy rotation service dynamically:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def get_next_proxy():
    # Your proxy rotation logic here
    return {"server": "http://next.proxy.com:8080"}

async def main():
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig()
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # For each URL, create a new run config with different proxy
        for url in urls:
            proxy = await get_next_proxy()
            # Clone the config and update proxy - this creates a new browser context
            current_config = run_config.clone(proxy_config=proxy)
            result = await crawler.arun(url=url, config=current_config)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```


```


## File: docs/md_v2/advanced/session-management.md

```md
# Session Management

Session management in Crawl4AI is a powerful feature that allows you to maintain state across multiple requests, making it particularly suitable for handling complex multi-step crawling tasks. It enables you to reuse the same browser tab (or page object) across sequential actions and crawls, which is beneficial for:

- **Performing JavaScript actions before and after crawling.**
- **Executing multiple sequential crawls faster** without needing to reopen tabs or allocate memory repeatedly.

**Note:** This feature is designed for sequential workflows and is not suitable for parallel operations.

---

#### Basic Session Usage

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

---

#### Dynamic Content with Sessions

Here's an example of crawling GitHub commits across multiple pages while preserving session state:

```python
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.cache_context import CacheMode

async def crawl_dynamic_content():
    async with AsyncWebCrawler() as crawler:
        session_id = "github_commits_session"
        url = "https://github.com/microsoft/TypeScript/commits/main"
        all_commits = []

        # Define extraction schema
        schema = {
            "name": "Commit Extractor",
            "baseSelector": "li.Box-sc-g0xbh4-0",
            "fields": [{
                "name": "title", "selector": "h4.markdown-title", "type": "text"
            }],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema)

        # JavaScript and wait configurations
        js_next_page = """document.querySelector('a[data-testid="pagination-next-button"]').click();"""
        wait_for = """() => document.querySelectorAll('li.Box-sc-g0xbh4-0').length > 0"""

        # Crawl multiple pages
        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                extraction_strategy=extraction_strategy,
                js_code=js_next_page if page > 0 else None,
                wait_for=wait_for if page > 0 else None,
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            if result.success:
                commits = json.loads(result.extracted_content)
                all_commits.extend(commits)
                print(f"Page {page + 1}: Found {len(commits)} commits")

        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
        return all_commits
```

---

## Example 1: Basic Session-Based Crawling

A simple example using session-based crawling:

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

This example shows:
1. Reusing the same `session_id` across multiple requests.
2. Executing JavaScript to load more content dynamically.
3. Properly closing the session to free resources.

---

## Advanced Technique 1: Custom Execution Hooks

> Warning: You might feel confused by the end of the next few examples 😅, so make sure you are comfortable with the order of the parts before you start this.

Use custom hooks to handle complex scenarios, such as waiting for content to load dynamically:

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

This technique ensures new content loads before the next action.

---

## Advanced Technique 2: Integrated JavaScript Execution and Waiting

Combine JavaScript execution and waiting logic for concise handling of dynamic content:

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

---

#### Common Use Cases for Sessions

1. **Authentication Flows**: Login and interact with secured pages.

2. **Pagination Handling**: Navigate through multiple pages.

3. **Form Submissions**: Fill forms, submit, and process results.

4. **Multi-step Processes**: Complete workflows that span multiple actions.

5. **Dynamic Content Navigation**: Handle JavaScript-rendered or event-triggered content.

```


## File: docs/md_v2/advanced/ssl-certificate.md

```md
# `SSLCertificate` Reference

The **`SSLCertificate`** class encapsulates an SSL certificate’s data and allows exporting it in various formats (PEM, DER, JSON, or text). It’s used within **Crawl4AI** whenever you set **`fetch_ssl_certificate=True`** in your **`CrawlerRunConfig`**.  

## 1. Overview

**Location**: `crawl4ai/ssl_certificate.py`

```python
class SSLCertificate:
    """
    Represents an SSL certificate with methods to export in various formats.

    Main Methods:
    - from_url(url, timeout=10)
    - from_file(file_path)
    - from_binary(binary_data)
    - to_json(filepath=None)
    - to_pem(filepath=None)
    - to_der(filepath=None)
    ...

    Common Properties:
    - issuer
    - subject
    - valid_from
    - valid_until
    - fingerprint
    """
```

### Typical Use Case
1. You **enable** certificate fetching in your crawl by:
   ```python
   CrawlerRunConfig(fetch_ssl_certificate=True, ...)
   ```
2. After `arun()`, if `result.ssl_certificate` is present, it’s an instance of **`SSLCertificate`**.  
3. You can **read** basic properties (issuer, subject, validity) or **export** them in multiple formats.

---

## 2. Construction & Fetching

### 2.1 **`from_url(url, timeout=10)`**
Manually load an SSL certificate from a given URL (port 443). Typically used internally, but you can call it directly if you want:

```python
cert = SSLCertificate.from_url("https://example.com")
if cert:
    print("Fingerprint:", cert.fingerprint)
```

### 2.2 **`from_file(file_path)`**
Load from a file containing certificate data in ASN.1 or DER. Rarely needed unless you have local cert files:

```python
cert = SSLCertificate.from_file("/path/to/cert.der")
```

### 2.3 **`from_binary(binary_data)`**
Initialize from raw binary. E.g., if you captured it from a socket or another source:

```python
cert = SSLCertificate.from_binary(raw_bytes)
```

---

## 3. Common Properties

After obtaining a **`SSLCertificate`** instance (e.g. `result.ssl_certificate` from a crawl), you can read:

1. **`issuer`** *(dict)*  
   - E.g. `{"CN": "My Root CA", "O": "..."}`
2. **`subject`** *(dict)*  
   - E.g. `{"CN": "example.com", "O": "ExampleOrg"}`
3. **`valid_from`** *(str)*  
   - NotBefore date/time. Often in ASN.1/UTC format.
4. **`valid_until`** *(str)*  
   - NotAfter date/time.
5. **`fingerprint`** *(str)*  
   - The SHA-256 digest (lowercase hex).  
   - E.g. `"d14d2e..."`

---

## 4. Export Methods

Once you have a **`SSLCertificate`** object, you can **export** or **inspect** it:

### 4.1 **`to_json(filepath=None)` → `Optional[str]`**
- Returns a JSON string containing the parsed certificate fields.  
- If `filepath` is provided, saves it to disk instead, returning `None`.

**Usage**:
```python
json_data = cert.to_json()  # returns JSON string
cert.to_json("certificate.json")  # writes file, returns None
```

### 4.2 **`to_pem(filepath=None)` → `Optional[str]`**
- Returns a PEM-encoded string (common for web servers).  
- If `filepath` is provided, saves it to disk instead.

```python
pem_str = cert.to_pem()              # in-memory PEM string
cert.to_pem("/path/to/cert.pem")     # saved to file
```

### 4.3 **`to_der(filepath=None)` → `Optional[bytes]`**
- Returns the original DER (binary ASN.1) bytes.  
- If `filepath` is specified, writes the bytes there instead.

```python
der_bytes = cert.to_der()
cert.to_der("certificate.der")
```

### 4.4 (Optional) **`export_as_text()`**
- If you see a method like `export_as_text()`, it typically returns an OpenSSL-style textual representation.  
- Not always needed, but can help for debugging or manual inspection.

---

## 5. Example Usage in Crawl4AI

Below is a minimal sample showing how the crawler obtains an SSL cert from a site, then reads or exports it. The code snippet:

```python
import asyncio
import os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    tmp_dir = "tmp"
    os.makedirs(tmp_dir, exist_ok=True)

    config = CrawlerRunConfig(
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)
        if result.success and result.ssl_certificate:
            cert = result.ssl_certificate
            # 1. Basic Info
            print("Issuer CN:", cert.issuer.get("CN", ""))
            print("Valid until:", cert.valid_until)
            print("Fingerprint:", cert.fingerprint)
            
            # 2. Export
            cert.to_json(os.path.join(tmp_dir, "certificate.json"))
            cert.to_pem(os.path.join(tmp_dir, "certificate.pem"))
            cert.to_der(os.path.join(tmp_dir, "certificate.der"))
    
if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Notes & Best Practices

1. **Timeout**: `SSLCertificate.from_url` internally uses a default **10s** socket connect and wraps SSL.  
2. **Binary Form**: The certificate is loaded in ASN.1 (DER) form, then re-parsed by `OpenSSL.crypto`.  
3. **Validation**: This does **not** validate the certificate chain or trust store. It only fetches and parses.  
4. **Integration**: Within Crawl4AI, you typically just set `fetch_ssl_certificate=True` in `CrawlerRunConfig`; the final result’s `ssl_certificate` is automatically built.  
5. **Export**: If you need to store or analyze a cert, the `to_json` and `to_pem` are quite universal.

---

### Summary

- **`SSLCertificate`** is a convenience class for capturing and exporting the **TLS certificate** from your crawled site(s).  
- Common usage is in the **`CrawlResult.ssl_certificate`** field, accessible after setting `fetch_ssl_certificate=True`.  
- Offers quick access to essential certificate details (`issuer`, `subject`, `fingerprint`) and is easy to export (PEM, DER, JSON) for further analysis or server usage.

Use it whenever you need **insight** into a site’s certificate or require some form of cryptographic or compliance check.
```


## File: docs/md_v2/extraction/chunking.md

```md
# Chunking Strategies
Chunking strategies are critical for dividing large texts into manageable parts, enabling effective content processing and extraction. These strategies are foundational in cosine similarity-based extraction techniques, which allow users to retrieve only the most relevant chunks of content for a given query. Additionally, they facilitate direct integration into RAG (Retrieval-Augmented Generation) systems for structured and scalable workflows.

### Why Use Chunking?
1. **Cosine Similarity and Query Relevance**: Prepares chunks for semantic similarity analysis.
2. **RAG System Integration**: Seamlessly processes and stores chunks for retrieval.
3. **Structured Processing**: Allows for diverse segmentation methods, such as sentence-based, topic-based, or windowed approaches.

### Methods of Chunking

#### 1. Regex-Based Chunking
Splits text based on regular expression patterns, useful for coarse segmentation.

**Code Example**:
```python
class RegexChunking:
    def __init__(self, patterns=None):
        self.patterns = patterns or [r'\n\n']  # Default pattern for paragraphs

    def chunk(self, text):
        paragraphs = [text]
        for pattern in self.patterns:
            paragraphs = [seg for p in paragraphs for seg in re.split(pattern, p)]
        return paragraphs

# Example Usage
text = """This is the first paragraph.

This is the second paragraph."""
chunker = RegexChunking()
print(chunker.chunk(text))
```

#### 2. Sentence-Based Chunking
Divides text into sentences using NLP tools, ideal for extracting meaningful statements.

**Code Example**:
```python
from nltk.tokenize import sent_tokenize

class NlpSentenceChunking:
    def chunk(self, text):
        sentences = sent_tokenize(text)
        return [sentence.strip() for sentence in sentences]

# Example Usage
text = "This is sentence one. This is sentence two."
chunker = NlpSentenceChunking()
print(chunker.chunk(text))
```

#### 3. Topic-Based Segmentation
Uses algorithms like TextTiling to create topic-coherent chunks.

**Code Example**:
```python
from nltk.tokenize import TextTilingTokenizer

class TopicSegmentationChunking:
    def __init__(self):
        self.tokenizer = TextTilingTokenizer()

    def chunk(self, text):
        return self.tokenizer.tokenize(text)

# Example Usage
text = """This is an introduction.
This is a detailed discussion on the topic."""
chunker = TopicSegmentationChunking()
print(chunker.chunk(text))
```

#### 4. Fixed-Length Word Chunking
Segments text into chunks of a fixed word count.

**Code Example**:
```python
class FixedLengthWordChunking:
    def __init__(self, chunk_size=100):
        self.chunk_size = chunk_size

    def chunk(self, text):
        words = text.split()
        return [' '.join(words[i:i + self.chunk_size]) for i in range(0, len(words), self.chunk_size)]

# Example Usage
text = "This is a long text with many words to be chunked into fixed sizes."
chunker = FixedLengthWordChunking(chunk_size=5)
print(chunker.chunk(text))
```

#### 5. Sliding Window Chunking
Generates overlapping chunks for better contextual coherence.

**Code Example**:
```python
class SlidingWindowChunking:
    def __init__(self, window_size=100, step=50):
        self.window_size = window_size
        self.step = step

    def chunk(self, text):
        words = text.split()
        chunks = []
        for i in range(0, len(words) - self.window_size + 1, self.step):
            chunks.append(' '.join(words[i:i + self.window_size]))
        return chunks

# Example Usage
text = "This is a long text to demonstrate sliding window chunking."
chunker = SlidingWindowChunking(window_size=5, step=2)
print(chunker.chunk(text))
```

### Combining Chunking with Cosine Similarity
To enhance the relevance of extracted content, chunking strategies can be paired with cosine similarity techniques. Here’s an example workflow:

**Code Example**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CosineSimilarityExtractor:
    def __init__(self, query):
        self.query = query
        self.vectorizer = TfidfVectorizer()

    def find_relevant_chunks(self, chunks):
        vectors = self.vectorizer.fit_transform([self.query] + chunks)
        similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
        return [(chunks[i], similarities[i]) for i in range(len(chunks))]

# Example Workflow
text = """This is a sample document. It has multiple sentences. 
We are testing chunking and similarity."""

chunker = SlidingWindowChunking(window_size=5, step=3)
chunks = chunker.chunk(text)
query = "testing chunking"
extractor = CosineSimilarityExtractor(query)
relevant_chunks = extractor.find_relevant_chunks(chunks)

print(relevant_chunks)
```

```


## File: docs/md_v2/extraction/clustring-strategies.md

```md
# Cosine Strategy

The Cosine Strategy in Crawl4AI uses similarity-based clustering to identify and extract relevant content sections from web pages. This strategy is particularly useful when you need to find and extract content based on semantic similarity rather than structural patterns.

## How It Works

The Cosine Strategy:
1. Breaks down page content into meaningful chunks
2. Converts text into vector representations
3. Calculates similarity between chunks
4. Clusters similar content together
5. Ranks and filters content based on relevance

## Basic Usage

```python
from crawl4ai import CosineStrategy

strategy = CosineStrategy(
    semantic_filter="product reviews",    # Target content type
    word_count_threshold=10,             # Minimum words per cluster
    sim_threshold=0.3                    # Similarity threshold
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com/reviews",
        extraction_strategy=strategy
    )
    
    content = result.extracted_content
```

## Configuration Options

### Core Parameters

```python
CosineStrategy(
    # Content Filtering
    semantic_filter: str = None,       # Keywords/topic for content filtering
    word_count_threshold: int = 10,    # Minimum words per cluster
    sim_threshold: float = 0.3,        # Similarity threshold (0.0 to 1.0)
    
    # Clustering Parameters
    max_dist: float = 0.2,            # Maximum distance for clustering
    linkage_method: str = 'ward',      # Clustering linkage method
    top_k: int = 3,                   # Number of top categories to extract
    
    # Model Configuration
    model_name: str = 'sentence-transformers/all-MiniLM-L6-v2',  # Embedding model
    
    verbose: bool = False             # Enable logging
)
```

### Parameter Details

1. **semantic_filter**
   - Sets the target topic or content type
   - Use keywords relevant to your desired content
   - Example: "technical specifications", "user reviews", "pricing information"

2. **sim_threshold**
   - Controls how similar content must be to be grouped together
   - Higher values (e.g., 0.8) mean stricter matching
   - Lower values (e.g., 0.3) allow more variation
   ```python
   # Strict matching
   strategy = CosineStrategy(sim_threshold=0.8)
   
   # Loose matching
   strategy = CosineStrategy(sim_threshold=0.3)
   ```

3. **word_count_threshold**
   - Filters out short content blocks
   - Helps eliminate noise and irrelevant content
   ```python
   # Only consider substantial paragraphs
   strategy = CosineStrategy(word_count_threshold=50)
   ```

4. **top_k**
   - Number of top content clusters to return
   - Higher values return more diverse content
   ```python
   # Get top 5 most relevant content clusters
   strategy = CosineStrategy(top_k=5)
   ```

## Use Cases

### 1. Article Content Extraction
```python
strategy = CosineStrategy(
    semantic_filter="main article content",
    word_count_threshold=100,  # Longer blocks for articles
    top_k=1                   # Usually want single main content
)

result = await crawler.arun(
    url="https://example.com/blog/post",
    extraction_strategy=strategy
)
```

### 2. Product Review Analysis
```python
strategy = CosineStrategy(
    semantic_filter="customer reviews and ratings",
    word_count_threshold=20,   # Reviews can be shorter
    top_k=10,                 # Get multiple reviews
    sim_threshold=0.4         # Allow variety in review content
)
```

### 3. Technical Documentation
```python
strategy = CosineStrategy(
    semantic_filter="technical specifications documentation",
    word_count_threshold=30,
    sim_threshold=0.6,        # Stricter matching for technical content
    max_dist=0.3             # Allow related technical sections
)
```

## Advanced Features

### Custom Clustering
```python
strategy = CosineStrategy(
    linkage_method='complete',  # Alternative clustering method
    max_dist=0.4,              # Larger clusters
    model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'  # Multilingual support
)
```

### Content Filtering Pipeline
```python
strategy = CosineStrategy(
    semantic_filter="pricing plans features",
    word_count_threshold=15,
    sim_threshold=0.5,
    top_k=3
)

async def extract_pricing_features(url: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            extraction_strategy=strategy
        )
        
        if result.success:
            content = json.loads(result.extracted_content)
            return {
                'pricing_features': content,
                'clusters': len(content),
                'similarity_scores': [item['score'] for item in content]
            }
```

## Best Practices

1. **Adjust Thresholds Iteratively**
   - Start with default values
   - Adjust based on results
   - Monitor clustering quality

2. **Choose Appropriate Word Count Thresholds**
   - Higher for articles (100+)
   - Lower for reviews/comments (20+)
   - Medium for product descriptions (50+)

3. **Optimize Performance**
   ```python
   strategy = CosineStrategy(
       word_count_threshold=10,  # Filter early
       top_k=5,                 # Limit results
       verbose=True             # Monitor performance
   )
   ```

4. **Handle Different Content Types**
   ```python
   # For mixed content pages
   strategy = CosineStrategy(
       semantic_filter="product features",
       sim_threshold=0.4,      # More flexible matching
       max_dist=0.3,          # Larger clusters
       top_k=3                # Multiple relevant sections
   )
   ```

## Error Handling

```python
try:
    result = await crawler.arun(
        url="https://example.com",
        extraction_strategy=strategy
    )
    
    if result.success:
        content = json.loads(result.extracted_content)
        if not content:
            print("No relevant content found")
    else:
        print(f"Extraction failed: {result.error_message}")
        
except Exception as e:
    print(f"Error during extraction: {str(e)}")
```

The Cosine Strategy is particularly effective when:
- Content structure is inconsistent
- You need semantic understanding
- You want to find similar content blocks
- Structure-based extraction (CSS/XPath) isn't reliable

It works well with other strategies and can be used as a pre-processing step for LLM-based extraction.
```


## File: docs/md_v2/extraction/llm-strategies.md

```md
# Extracting JSON (LLM)

In some cases, you need to extract **complex or unstructured** information from a webpage that a simple CSS/XPath schema cannot easily parse. Or you want **AI**-driven insights, classification, or summarization. For these scenarios, Crawl4AI provides an **LLM-based extraction strategy** that:

1. Works with **any** large language model supported by [LightLLM](https://github.com/LightLLM) (Ollama, OpenAI, Claude, and more).  
2. Automatically splits content into chunks (if desired) to handle token limits, then combines results.  
3. Lets you define a **schema** (like a Pydantic model) or a simpler “block” extraction approach.

**Important**: LLM-based extraction can be slower and costlier than schema-based approaches. If your page data is highly structured, consider using [`JsonCssExtractionStrategy`](./no-llm-strategies.md) or [`JsonXPathExtractionStrategy`](./no-llm-strategies.md) first. But if you need AI to interpret or reorganize content, read on!

---

## 1. Why Use an LLM?

- **Complex Reasoning**: If the site’s data is unstructured, scattered, or full of natural language context.  
- **Semantic Extraction**: Summaries, knowledge graphs, or relational data that require comprehension.  
- **Flexible**: You can pass instructions to the model to do more advanced transformations or classification.

---

## 2. Provider-Agnostic via LightLLM

Crawl4AI uses a “provider string” (e.g., `"openai/gpt-4o"`, `"ollama/llama2.0"`, `"aws/titan"`) to identify your LLM. **Any** model that LightLLM supports is fair game. You just provide:

- **`provider`**: The `<provider>/<model_name>` identifier (e.g., `"openai/gpt-4"`, `"ollama/llama2"`, `"huggingface/google-flan"`, etc.).  
- **`api_token`**: If needed (for OpenAI, HuggingFace, etc.); local models or Ollama might not require it.  
- **`api_base`** (optional): If your provider has a custom endpoint.  

This means you **aren’t locked** into a single LLM vendor. Switch or experiment easily.

---

## 3. How LLM Extraction Works

### 3.1 Flow

1. **Chunking** (optional): The HTML or markdown is split into smaller segments if it’s very long (based on `chunk_token_threshold`, overlap, etc.).  
2. **Prompt Construction**: For each chunk, the library forms a prompt that includes your **`instruction`** (and possibly schema or examples).  
3. **LLM Inference**: Each chunk is sent to the model in parallel or sequentially (depending on your concurrency).  
4. **Combining**: The results from each chunk are merged and parsed into JSON.

### 3.2 `extraction_type`

- **`"schema"`**: The model tries to return JSON conforming to your Pydantic-based schema.  
- **`"block"`**: The model returns freeform text, or smaller JSON structures, which the library collects.  

For structured data, `"schema"` is recommended. You provide `schema=YourPydanticModel.model_json_schema()`.

---

## 4. Key Parameters

Below is an overview of important LLM extraction parameters. All are typically set inside `LLMExtractionStrategy(...)`. You then put that strategy in your `CrawlerRunConfig(..., extraction_strategy=...)`.

1. **`provider`** (str): e.g., `"openai/gpt-4"`, `"ollama/llama2"`.  
2. **`api_token`** (str): The API key or token for that model. May not be needed for local models.  
3. **`schema`** (dict): A JSON schema describing the fields you want. Usually generated by `YourModel.model_json_schema()`.  
4. **`extraction_type`** (str): `"schema"` or `"block"`.  
5. **`instruction`** (str): Prompt text telling the LLM what you want extracted. E.g., “Extract these fields as a JSON array.”  
6. **`chunk_token_threshold`** (int): Maximum tokens per chunk. If your content is huge, you can break it up for the LLM.  
7. **`overlap_rate`** (float): Overlap ratio between adjacent chunks. E.g., `0.1` means 10% of each chunk is repeated to preserve context continuity.  
8. **`apply_chunking`** (bool): Set `True` to chunk automatically. If you want a single pass, set `False`.  
9. **`input_format`** (str): Determines **which** crawler result is passed to the LLM. Options include:  
   - `"markdown"`: The raw markdown (default).  
   - `"fit_markdown"`: The filtered “fit” markdown if you used a content filter.  
   - `"html"`: The cleaned or raw HTML.  
10. **`extra_args`** (dict): Additional LLM parameters like `temperature`, `max_tokens`, `top_p`, etc.  
11. **`show_usage()`**: A method you can call to print out usage info (token usage per chunk, total cost if known).  

**Example**:

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

---

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

---

## 6. Chunking Details

### 6.1 `chunk_token_threshold`

If your page is large, you might exceed your LLM’s context window. **`chunk_token_threshold`** sets the approximate max tokens per chunk. The library calculates word→token ratio using `word_token_rate` (often ~0.75 by default). If chunking is enabled (`apply_chunking=True`), the text is split into segments.

### 6.2 `overlap_rate`

To keep context continuous across chunks, we can overlap them. E.g., `overlap_rate=0.1` means each subsequent chunk includes 10% of the previous chunk’s text. This is helpful if your needed info might straddle chunk boundaries.

### 6.3 Performance & Parallelism

By chunking, you can potentially process multiple chunks in parallel (depending on your concurrency settings and the LLM provider). This reduces total time if the site is huge or has many sections.

---

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

---

## 8. Token Usage & Show Usage

To keep track of tokens and cost, each chunk is processed with an LLM call. We record usage in:

- **`usages`** (list): token usage per chunk or call.  
- **`total_usage`**: sum of all chunk calls.  
- **`show_usage()`**: prints a usage report (if the provider returns usage data).

```python
llm_strategy = LLMExtractionStrategy(...)
# ...
llm_strategy.show_usage()
# e.g. “Total usage: 1241 tokens across 2 chunk calls”
```

If your model provider doesn’t return usage info, these fields might be partial or empty.

---

## 9. Example: Building a Knowledge Graph

Below is a snippet combining **`LLMExtractionStrategy`** with a Pydantic schema for a knowledge graph. Notice how we pass an **`instruction`** telling the model what to parse.

```python
import os
import json
import asyncio
from typing import List
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
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
        provider="openai/gpt-4",
        api_token=os.getenv('OPENAI_API_KEY'),
        schema=KnowledgeGraph.schema_json(),
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

        if result.success:
            with open("kb_result.json", "w", encoding="utf-8") as f:
                f.write(result.extracted_content)
            llm_strat.show_usage()
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Observations**:

- **`extraction_type="schema"`** ensures we get JSON fitting our `KnowledgeGraph`.  
- **`input_format="html"`** means we feed HTML to the model.  
- **`instruction`** guides the model to output a structured knowledge graph.  

---

## 10. Best Practices & Caveats

1. **Cost & Latency**: LLM calls can be slow or expensive. Consider chunking or smaller coverage if you only need partial data.  
2. **Model Token Limits**: If your page + instruction exceed the context window, chunking is essential.  
3. **Instruction Engineering**: Well-crafted instructions can drastically improve output reliability.  
4. **Schema Strictness**: `"schema"` extraction tries to parse the model output as JSON. If the model returns invalid JSON, partial extraction might happen, or you might get an error.  
5. **Parallel vs. Serial**: The library can process multiple chunks in parallel, but you must watch out for rate limits on certain providers.  
6. **Check Output**: Sometimes, an LLM might omit fields or produce extraneous text. You may want to post-validate with Pydantic or do additional cleanup.

---

## 11. Conclusion

**LLM-based extraction** in Crawl4AI is **provider-agnostic**, letting you choose from hundreds of models via LightLLM. It’s perfect for **semantically complex** tasks or generating advanced structures like knowledge graphs. However, it’s **slower** and potentially costlier than schema-based approaches. Keep these tips in mind:

- Put your LLM strategy **in `CrawlerRunConfig`**.  
- Use **`input_format`** to pick which form (markdown, HTML, fit_markdown) the LLM sees.  
- Tweak **`chunk_token_threshold`**, **`overlap_rate`**, and **`apply_chunking`** to handle large content efficiently.  
- Monitor token usage with `show_usage()`.

If your site’s data is consistent or repetitive, consider [`JsonCssExtractionStrategy`](./no-llm-strategies.md) first for speed and simplicity. But if you need an **AI-driven** approach, `LLMExtractionStrategy` offers a flexible, multi-provider solution for extracting structured JSON from any website.

**Next Steps**:

1. **Experiment with Different Providers**  
   - Try switching the `provider` (e.g., `"ollama/llama2"`, `"openai/gpt-4o"`, etc.) to see differences in speed, accuracy, or cost.  
   - Pass different `extra_args` like `temperature`, `top_p`, and `max_tokens` to fine-tune your results.

2. **Performance Tuning**  
   - If pages are large, tweak `chunk_token_threshold`, `overlap_rate`, or `apply_chunking` to optimize throughput.  
   - Check the usage logs with `show_usage()` to keep an eye on token consumption and identify potential bottlenecks.

3. **Validate Outputs**  
   - If using `extraction_type="schema"`, parse the LLM’s JSON with a Pydantic model for a final validation step.  
   - Log or handle any parse errors gracefully, especially if the model occasionally returns malformed JSON.

4. **Explore Hooks & Automation**  
   - Integrate LLM extraction with [hooks](../advanced/hooks-auth.md) for complex pre/post-processing.  
   - Use a multi-step pipeline: crawl, filter, LLM-extract, then store or index results for further analysis.

**Last Updated**: 2025-01-01

---

That’s it for **Extracting JSON (LLM)**—now you can harness AI to parse, classify, or reorganize data on the web. Happy crawling!
```


## File: docs/md_v2/extraction/no-llm-strategies.md

```md
# Extracting JSON (No LLM)

One of Crawl4AI’s **most powerful** features is extracting **structured JSON** from websites **without** relying on large language models. By defining a **schema** with CSS or XPath selectors, you can extract data instantly—even from complex or nested HTML structures—without the cost, latency, or environmental impact of an LLM.

**Why avoid LLM for basic extractions?**

1. **Faster & Cheaper**: No API calls or GPU overhead.  
2. **Lower Carbon Footprint**: LLM inference can be energy-intensive. A well-defined schema is practically carbon-free.  
3. **Precise & Repeatable**: CSS/XPath selectors do exactly what you specify. LLM outputs can vary or hallucinate.  
4. **Scales Readily**: For thousands of pages, schema-based extraction runs quickly and in parallel.

Below, we’ll explore how to craft these schemas and use them with **JsonCssExtractionStrategy** (or **JsonXPathExtractionStrategy** if you prefer XPath). We’ll also highlight advanced features like **nested fields** and **base element attributes**.

---

## 1. Intro to Schema-Based Extraction

A schema defines:

1. A **base selector** that identifies each “container” element on the page (e.g., a product row, a blog post card).  
2. **Fields** describing which CSS/XPath selectors to use for each piece of data you want to capture (text, attribute, HTML block, etc.).  
3. **Nested** or **list** types for repeated or hierarchical structures.  

For example, if you have a list of products, each one might have a name, price, reviews, and “related products.” This approach is faster and more reliable than an LLM for consistent, structured pages.

---

## 2. Simple Example: Crypto Prices

Let’s begin with a **simple** schema-based extraction using the `JsonCssExtractionStrategy`. Below is a snippet that extracts cryptocurrency prices from a site (similar to the legacy Coinbase example). Notice we **don’t** call any LLM:

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

**Highlights**:

- **`baseSelector`**: Tells us where each “item” (crypto row) is.  
- **`fields`**: Two fields (`coin_name`, `price`) using simple CSS selectors.  
- Each field defines a **`type`** (e.g., `text`, `attribute`, `html`, `regex`, etc.).

No LLM is needed, and the performance is **near-instant** for hundreds or thousands of items.

---

### **XPath Example with `raw://` HTML**

Below is a short example demonstrating **XPath** extraction plus the **`raw://`** scheme. We’ll pass a **dummy HTML** directly (no network request) and define the extraction strategy in `CrawlerRunConfig`.

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

**Key Points**:

1. **`JsonXPathExtractionStrategy`** is used instead of `JsonCssExtractionStrategy`.  
2. **`baseSelector`** and each field’s `"selector"` use **XPath** instead of CSS.  
3. **`raw://`** lets us pass `dummy_html` with no real network request—handy for local testing.  
4. Everything (including the extraction strategy) is in **`CrawlerRunConfig`**.  

That’s how you keep the config self-contained, illustrate **XPath** usage, and demonstrate the **raw** scheme for direct HTML input—all while avoiding the old approach of passing `extraction_strategy` directly to `arun()`.

---

## 3. Advanced Schema & Nested Structures

Real sites often have **nested** or repeated data—like categories containing products, which themselves have a list of reviews or features. For that, we can define **nested** or **list** (and even **nested_list**) fields.

### Sample E-Commerce HTML

We have a **sample e-commerce** HTML file on GitHub (example):
```
https://gist.githubusercontent.com/githubusercontent/2d7b8ba3cd8ab6cf3c8da771ddb36878/raw/1ae2f90c6861ce7dd84cc50d3df9920dee5e1fd2/sample_ecommerce.html
```
This snippet includes categories, products, features, reviews, and related items. Let’s see how to define a schema that fully captures that structure **without LLM**.

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

Key Takeaways:

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

If all goes well, you get a **structured** JSON array with each “category,” containing an array of `products`. Each product includes `details`, `features`, `reviews`, etc. All of that **without** an LLM.

---

## 4. Why “No LLM” Is Often Better

1. **Zero Hallucination**: Schema-based extraction doesn’t guess text. It either finds it or not.  
2. **Guaranteed Structure**: The same schema yields consistent JSON across many pages, so your downstream pipeline can rely on stable keys.  
3. **Speed**: LLM-based extraction can be 10–1000x slower for large-scale crawling.  
4. **Scalable**: Adding or updating a field is a matter of adjusting the schema, not re-tuning a model.

**When might you consider an LLM?** Possibly if the site is extremely unstructured or you want AI summarization. But always try a schema approach first for repeated or consistent data patterns.

---

## 5. Base Element Attributes & Additional Fields

It’s easy to **extract attributes** (like `href`, `src`, or `data-xxx`) from your base or nested elements using:

```json
{
  "name": "href",
  "type": "attribute",
  "attribute": "href",
  "default": null
}
```

You can define them in **`baseFields`** (extracted from the main container element) or in each field’s sub-lists. This is especially helpful if you need an item’s link or ID stored in the parent `<div>`.

---

## 6. Putting It All Together: Larger Example

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

---

## 7. Tips & Best Practices

1. **Inspect the DOM** in Chrome DevTools or Firefox’s Inspector to find stable selectors.  
2. **Start Simple**: Verify you can extract a single field. Then add complexity like nested objects or lists.  
3. **Test** your schema on partial HTML or a test page before a big crawl.  
4. **Combine with JS Execution** if the site loads content dynamically. You can pass `js_code` or `wait_for` in `CrawlerRunConfig`.  
5. **Look at Logs** when `verbose=True`: if your selectors are off or your schema is malformed, it’ll often show warnings.  
6. **Use baseFields** if you need attributes from the container element (e.g., `href`, `data-id`), especially for the “parent” item.  
7. **Performance**: For large pages, make sure your selectors are as narrow as possible.

---

## 8. Schema Generation Utility

While manually crafting schemas is powerful and precise, Crawl4AI now offers a convenient utility to **automatically generate** extraction schemas using LLM. This is particularly useful when:

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

1. **One-Time Cost**: While schema generation uses LLM, it's a one-time cost. The generated schema can be reused for unlimited extractions without further LLM calls.
2. **Smart Pattern Recognition**: The LLM analyzes the HTML structure and identifies common patterns, often producing more robust selectors than manual attempts.
3. **Automatic Nesting**: Complex nested structures are automatically detected and properly represented in the schema.
4. **Learning Tool**: The generated schemas serve as excellent examples for learning how to write your own schemas.

### Best Practices

1. **Review Generated Schemas**: While the generator is smart, always review and test the generated schema before using it in production.
2. **Provide Representative HTML**: The better your sample HTML represents the overall structure, the more accurate the generated schema will be.
3. **Consider Both CSS and XPath**: Try both schema types and choose the one that works best for your specific case.
4. **Cache Generated Schemas**: Since generation uses LLM, save successful schemas for reuse.
5. **API Token Security**: Never hardcode API tokens. Use environment variables or secure configuration management.
6. **Choose Provider Wisely**: 
   - Use OpenAI for production-quality schemas
   - Use Ollama for development, testing, or when you need a self-hosted solution

That's it for **Extracting JSON (No LLM)**! You've seen how schema-based approaches (either CSS or XPath) can handle everything from simple lists to deeply nested product catalogs—instantly, with minimal overhead. Enjoy building robust scrapers that produce consistent, structured JSON for your data pipelines!

---

## 9. Conclusion

With **JsonCssExtractionStrategy** (or **JsonXPathExtractionStrategy**), you can build powerful, **LLM-free** pipelines that:

- Scrape any consistent site for structured data.  
- Support nested objects, repeating lists, or advanced transformations.  
- Scale to thousands of pages quickly and reliably.

**Next Steps**:

- Combine your extracted JSON with advanced filtering or summarization in a second pass if needed.  
- For dynamic pages, combine strategies with `js_code` or infinite scroll hooking to ensure all content is loaded.

**Remember**: For repeated, structured data, you don’t need to pay for or wait on an LLM. A well-crafted schema plus CSS or XPath gets you the data faster, cleaner, and cheaper—**the real power** of Crawl4AI.

**Last Updated**: 2025-01-01

---

That’s it for **Extracting JSON (No LLM)**! You’ve seen how schema-based approaches (either CSS or XPath) can handle everything from simple lists to deeply nested product catalogs—instantly, with minimal overhead. Enjoy building robust scrapers that produce consistent, structured JSON for your data pipelines!
```

