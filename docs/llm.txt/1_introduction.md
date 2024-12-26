# Crawl4AI Quick Start Guide: Your All-in-One AI-Ready Web Crawling & AI Integration Solution

Crawl4AI, the **#1 trending GitHub repository**, streamlines web content extraction into AI-ready formats. Perfect for AI assistants, semantic search engines, or data pipelines, Crawl4AI transforms raw HTML into structured Markdown or JSON effortlessly. Integrate with LLMs, open-source models, or your own retrieval-augmented generation workflows.

**Key Links:**  
- **Website:** [https://crawl4ai.com](https://crawl4ai.com)  
- **GitHub:** [https://github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)  
- **Colab Notebook:** [Try on Google Colab](https://colab.research.google.com/drive/1SgRPrByQLzjRfwoRNq1wSGE9nYY_EE8C?usp=sharing)  
- **Quickstart Code Example:** [quickstart_async.config.py](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/quickstart_async.config.py)  
- **Examples Folder:** [Crawl4AI Examples](https://github.com/unclecode/crawl4ai/tree/main/docs/examples)

---

## Table of Contents
- [Crawl4AI Quick Start Guide: Your All-in-One AI-Ready Web Crawling \& AI Integration Solution](#crawl4ai-quick-start-guide-your-all-in-one-ai-ready-web-crawling--ai-integration-solution)
  - [Table of Contents](#table-of-contents)
  - [1. Introduction \& Key Concepts](#1-introduction--key-concepts)
  - [2. Installation \& Environment Setup](#2-installation--environment-setup)
  - [3. Core Concepts \& Configuration](#3-core-concepts--configuration)
  - [4. Basic Crawling \& Simple Extraction](#4-basic-crawling--simple-extraction)
  - [5. Markdown Generation \& AI-Optimized Output](#5-markdown-generation--ai-optimized-output)
  - [6. Structured Data Extraction (CSS, XPath, LLM)](#6-structured-data-extraction-css-xpath-llm)
  - [7. Advanced Extraction: LLM \& Open-Source Models](#7-advanced-extraction-llm--open-source-models)
  - [8. Page Interactions, JS Execution, \& Dynamic Content](#8-page-interactions-js-execution--dynamic-content)
  - [9. Media, Links, \& Metadata Handling](#9-media-links--metadata-handling)
  - [10. Authentication \& Identity Preservation](#10-authentication--identity-preservation)
    - [Manual Setup via User Data Directory](#manual-setup-via-user-data-directory)
    - [Using `storage_state`](#using-storage_state)
  - [11. Proxy \& Security Enhancements](#11-proxy--security-enhancements)
  - [12. Screenshots, PDFs \& File Downloads](#12-screenshots-pdfs--file-downloads)
  - [13. Caching \& Performance Optimization](#13-caching--performance-optimization)
  - [14. Hooks for Custom Logic](#14-hooks-for-custom-logic)
  - [15. Dockerization \& Scaling](#15-dockerization--scaling)
  - [16. Troubleshooting \& Common Pitfalls](#16-troubleshooting--common-pitfalls)
  - [17. Comprehensive End-to-End Example](#17-comprehensive-end-to-end-example)
  - [18. Further Resources \& Community](#18-further-resources--community)

---

## 1. Introduction & Key Concepts
Crawl4AI transforms websites into structured, AI-friendly data. It efficiently handles large-scale crawling, integrates with both proprietary and open-source LLMs, and optimizes content for semantic search or RAG pipelines.

**Quick Test:**
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def test_run():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown)

asyncio.run(test_run())
```

If you see Markdown output, everything is working!

**More info:** [See /docs/introduction](#) or [1_introduction.ex.md](https://github.com/unclecode/crawl4ai/blob/main/introduction.ex.md)

---

## 2. Installation & Environment Setup
```bash
pip install crawl4ai
crawl4ai-setup
playwright install chromium
```

**Try in Colab:**  
[Open Colab Notebook](https://colab.research.google.com/drive/1SgRPrByQLzjRfwoRNq1wSGE9nYY_EE8C?usp=sharing)

**More info:** [See /docs/configuration](#) or [2_configuration.md](https://github.com/unclecode/crawl4ai/blob/main/configuration.md)

---

## 3. Core Concepts & Configuration
Use `AsyncWebCrawler`, `CrawlerRunConfig`, and `BrowserConfig` to control crawling.

**Example config:**
```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(
    headless=True,
    viewport_width=1920,
    viewport_height=1080,
    text_mode=False,
    ignore_https_errors=True,
    java_script_enabled=True
)

run_config = CrawlerRunConfig(
    css_selector="article.main",
    word_count_threshold=50,
    excluded_tags=['nav','footer'],
    exclude_external_links=True,
    wait_for="css:.article-loaded",
    page_timeout=60000,
    delay_before_return_html=1.0,
    mean_delay=0.1, 
    max_range=0.3,
    process_iframes=True,
    remove_overlay_elements=True,
    js_code="""
        (async () => {
            window.scrollTo(0, document.body.scrollHeight);
            await new Promise(r => setTimeout(r, 2000));
            document.querySelector('.load-more')?.click();
        })();
    """
)

# Use: ENABLED, DISABLED, BYPASS, READ_ONLY, WRITE_ONLY
# run_config.cache_mode = CacheMode.ENABLED
```

**Prefixes:**
- `http://` or `https://` for live pages
- `file://local.html` for local
- `raw:<html>` for raw HTML strings

**More info:** [See /docs/async_webcrawler](#) or [3_async_webcrawler.ex.md](https://github.com/unclecode/crawl4ai/blob/main/async_webcrawler.ex.md)

---

## 4. Basic Crawling & Simple Extraction
```python
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://news.example.com/article", config=run_config)
    print(result.markdown) # Basic markdown content
```

**More info:** [See /docs/browser_context_page](#) or [4_browser_context_page.ex.md](https://github.com/unclecode/crawl4ai/blob/main/browser_context_page.ex.md)

---

## 5. Markdown Generation & AI-Optimized Output

After crawling, `result.markdown_v2` provides:
- `raw_markdown`: Unfiltered markdown
- `markdown_with_citations`: Links as references at the bottom
- `references_markdown`: A separate list of reference links
- `fit_markdown`: Filtered, relevant markdown (e.g., after BM25)
- `fit_html`: The HTML used to produce `fit_markdown`

**Example:**
```python
print("RAW:", result.markdown_v2.raw_markdown[:200])
print("CITED:", result.markdown_v2.markdown_with_citations[:200])
print("REFERENCES:", result.markdown_v2.references_markdown)
print("FIT MARKDOWN:", result.markdown_v2.fit_markdown)
```

For AI training, `fit_markdown` focuses on the most relevant content.

**More info:** [See /docs/markdown_generation](#) or [5_markdown_generation.ex.md](https://github.com/unclecode/crawl4ai/blob/main/markdown_generation.ex.md)

---

## 6. Structured Data Extraction (CSS, XPath, LLM)
Extract JSON data without LLMs:

**CSS:**
```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
  "name": "Products",
  "baseSelector": ".product",
  "fields": [
    {"name": "title", "selector": "h2", "type": "text"},
    {"name": "price", "selector": ".price", "type": "text"}
  ]
}
run_config.extraction_strategy = JsonCssExtractionStrategy(schema)
```

**XPath:**
```python
from crawl4ai.extraction_strategy import JsonXPathExtractionStrategy

xpath_schema = {
  "name": "Articles",
  "baseSelector": "//div[@class='article']",
  "fields": [
    {"name":"headline","selector":".//h1","type":"text"},
    {"name":"summary","selector":".//p[@class='summary']","type":"text"}
  ]
}
run_config.extraction_strategy = JsonXPathExtractionStrategy(xpath_schema)
```

**More info:** [See /docs/extraction_strategies](#) or [7_extraction_strategies.ex.md](https://github.com/unclecode/crawl4ai/blob/main/extraction_strategies.ex.md)

---

## 7. Advanced Extraction: LLM & Open-Source Models
Use LLMExtractionStrategy for complex tasks. Works with OpenAI or open-source models (e.g., Ollama).

```python
from pydantic import BaseModel
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class TravelData(BaseModel):
    destination: str
    attractions: list

run_config.extraction_strategy = LLMExtractionStrategy(
    provider="ollama/nemotron",
    schema=TravelData.schema(),
    instruction="Extract destination and top attractions."
)
```

**More info:** [See /docs/extraction_strategies](#) or [7_extraction_strategies.ex.md](https://github.com/unclecode/crawl4ai/blob/main/extraction_strategies.ex.md)

---

## 8. Page Interactions, JS Execution, & Dynamic Content
Insert `js_code` and use `wait_for` to ensure content loads. Example:
```python
run_config.js_code = """
(async () => {
   document.querySelector('.load-more')?.click();
   await new Promise(r => setTimeout(r, 2000));
})();
"""
run_config.wait_for = "css:.item-loaded"
```

**More info:** [See /docs/page_interaction](#) or [11_page_interaction.md](https://github.com/unclecode/crawl4ai/blob/main/page_interaction.md)

---

## 9. Media, Links, & Metadata Handling
`result.media["images"]`: List of images with `src`, `score`, `alt`. Score indicates relevance.

`result.media["videos"]`, `result.media["audios"]` similarly hold media info.

`result.links["internal"]`, `result.links["external"]`, `result.links["social"]`: Categorized links. Each link has `href`, `text`, `context`, `type`.

`result.metadata`: Title, description, keywords, author.

**Example:**
```python
# Images
for img in result.media["images"]:
    print("Image:", img["src"], "Score:", img["score"], "Alt:", img.get("alt","N/A"))

# Links
for link in result.links["external"]:
    print("External Link:", link["href"], "Text:", link["text"])

# Metadata
print("Page Title:", result.metadata["title"])
print("Description:", result.metadata["description"])
```

**More info:** [See /docs/content_selection](#) or [8_content_selection.ex.md](https://github.com/unclecode/crawl4ai/blob/main/content_selection.ex.md)

---

## 10. Authentication & Identity Preservation

### Manual Setup via User Data Directory
1. **Open Chrome with a custom user data dir:**
   ```bash
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="C:\MyChromeProfile"
   ```
   On macOS:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --user-data-dir="/Users/username/ChromeProfiles/MyProfile"
   ```

2. **Log in to sites, solve CAPTCHAs, adjust settings manually.**  
   The browser saves cookies/localStorage in that directory.

3. **Use `user_data_dir` in `BrowserConfig`:**
   ```python
   browser_config = BrowserConfig(
       headless=True,
       user_data_dir="/Users/username/ChromeProfiles/MyProfile"
   )
   ```

   Now the crawler starts with those cookies, sessions, etc.

### Using `storage_state`
Alternatively, export and reuse storage states:
```python
browser_config = BrowserConfig(
    headless=True,
    storage_state="mystate.json"  # Pre-saved state
)
```

No repeated logins needed.

**More info:** [See /docs/storage_state](#) or [16_storage_state.md](https://github.com/unclecode/crawl4ai/blob/main/storage_state.md)

---

## 11. Proxy & Security Enhancements
Use `proxy_config` for authenticated proxies:
```python
browser_config.proxy_config = {
    "server": "http://proxy.example.com:8080",
    "username": "proxyuser",
    "password": "proxypass"
}
```

Combine with `headers` or `ignore_https_errors` as needed.

**More info:** [See /docs/proxy_security](#) or [14_proxy_security.md](https://github.com/unclecode/crawl4ai/blob/main/proxy_security.md)

---

## 12. Screenshots, PDFs & File Downloads
Enable `screenshot=True` or `pdf=True` in `CrawlerRunConfig`:

```python
run_config.screenshot = True
run_config.pdf = True
```

After crawling:
```python
if result.screenshot:
    with open("page.png", "wb") as f:
        f.write(result.screenshot)

if result.pdf:
    with open("page.pdf", "wb") as f:
        f.write(result.pdf)
```

**File Downloads:**
```python
browser_config.accept_downloads = True
browser_config.downloads_path = "./downloads"
run_config.js_code = """document.querySelector('a.download')?.click();"""

# After crawl:
print("Downloaded files:", result.downloaded_files)
```

**More info:** [See /docs/screenshot_and_pdf_export](#) or [15_screenshot_and_pdf_export.md](https://github.com/unclecode/crawl4ai/blob/main/screenshot_and_pdf_export.md)  
Also [10_file_download.md](https://github.com/unclecode/crawl4ai/blob/main/file_download.md)

---

## 13. Caching & Performance Optimization
Set `cache_mode` to reuse fetch results:
```python
from crawl4ai import CacheMode
run_config.cache_mode = CacheMode.ENABLED
```

Adjust delays, increase concurrency, or use `text_mode=True` for faster extraction.

**More info:** [See /docs/cache_modes](#) or [9_cache_modes.md](https://github.com/unclecode/crawl4ai/blob/main/cache_modes.md)

---

## 14. Hooks for Custom Logic
Hooks let you run code at specific lifecycle events without creating pages manually in `on_browser_created`.

Use `on_page_context_created` to apply routing or modify page contexts before crawling the URL:

**Example Hook:**
```python
async def on_page_context_created_hook(context, page, **kwargs):
    # Block all images to speed up load
    await context.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())
    print("[HOOK] Image requests blocked")

async with AsyncWebCrawler(config=browser_config) as crawler:
    crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created_hook)
    result = await crawler.arun("https://imageheavy.example.com", config=run_config)
    print("Crawl finished with images blocked.")
```

This hook is clean and doesn’t create a separate page itself—it just modifies the current context/page setup.

**More info:** [See /docs/hooks_auth](#) or [13_hooks_auth.md](https://github.com/unclecode/crawl4ai/blob/main/hooks_auth.md)

---

## 15. Dockerization & Scaling
Use Docker images:

- AMD64 basic:
```bash
docker pull unclecode/crawl4ai:basic-amd64
docker run -p 11235:11235 unclecode/crawl4ai:basic-amd64
```

- ARM64 for M1/M2:
```bash
docker pull unclecode/crawl4ai:basic-arm64
docker run -p 11235:11235 unclecode/crawl4ai:basic-arm64
```

- GPU support:
```bash
docker pull unclecode/crawl4ai:gpu-amd64
docker run --gpus all -p 11235:11235 unclecode/crawl4ai:gpu-amd64
```

Scale with load balancers or Kubernetes.

**More info:** [See /docs/proxy_security (for proxy) or relevant Docker instructions in README](#)

---

## 16. Troubleshooting & Common Pitfalls
- Empty results? Relax filters, check selectors.
- Timeouts? Increase `page_timeout` or refine `wait_for`.
- CAPTCHAs? Use `user_data_dir` or `storage_state` after manual solving.
- JS errors? Try headful mode for debugging.

Check [examples](https://github.com/unclecode/crawl4ai/tree/main/docs/examples) & [quickstart_async.config.py](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/quickstart_async.config.py) for more code.

---

## 17. Comprehensive End-to-End Example
Combine hooks, JS execution, PDF saving, LLM extraction—see [quickstart_async.config.py](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/quickstart_async.config.py) for a full example.

---

## 18. Further Resources & Community
- **Docs:** [https://crawl4ai.com](https://crawl4ai.com)  
- **Issues & PRs:** [https://github.com/unclecode/crawl4ai/issues](https://github.com/unclecode/crawl4ai/issues)

Follow [@unclecode](https://x.com/unclecode) for news & community updates.

**Happy Crawling!**  
Leverage Crawl4AI to feed your AI models with clean, structured web data today.