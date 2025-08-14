[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/api/crawl-result/)


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
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * CrawlResult
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [CrawlResult Reference](https://docs.crawl4ai.com/api/crawl-result/#crawlresult-reference)
  * [1. Basic Crawl Info](https://docs.crawl4ai.com/api/crawl-result/#1-basic-crawl-info)
  * [2. Raw / Cleaned Content](https://docs.crawl4ai.com/api/crawl-result/#2-raw-cleaned-content)
  * [3. Markdown Fields](https://docs.crawl4ai.com/api/crawl-result/#3-markdown-fields)
  * [4. Media & Links](https://docs.crawl4ai.com/api/crawl-result/#4-media-links)
  * [5. Additional Fields](https://docs.crawl4ai.com/api/crawl-result/#5-additional-fields)
  * [6. dispatch_result (optional)](https://docs.crawl4ai.com/api/crawl-result/#6-dispatch_result-optional)
  * [7. Network Requests & Console Messages](https://docs.crawl4ai.com/api/crawl-result/#7-network-requests-console-messages)
  * [8. Example: Accessing Everything](https://docs.crawl4ai.com/api/crawl-result/#8-example-accessing-everything)
  * [9. Key Points & Future](https://docs.crawl4ai.com/api/crawl-result/#9-key-points-future)


#  `CrawlResult` Reference
The **`CrawlResult`**class encapsulates everything returned after a single crawl operation. It provides the**raw or processed content** , details on links and media, plus optional metadata (like screenshots, PDFs, or extracted JSON).
**Location** : `crawl4ai/crawler/models.py` (for reference)
```
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
Copy
```

Below is a **field-by-field** explanation and possible usage patterns.
* * *
## 1. Basic Crawl Info
### 1.1 **`url`**_(str)_
**What** : The final crawled URL (after any redirects).
**Usage** :
```
print(result.url)  # e.g., "https://example.com/"
Copy
```

### 1.2 **`success`**_(bool)_
**What** : `True` if the crawl pipeline ended without major errors; `False` otherwise.
**Usage** :
```
if not result.success:
    print(f"Crawl failed: {result.error_message}")
Copy
```

### 1.3 **`status_code`**_(Optional[int])_
**What** : The page's HTTP status code (e.g., 200, 404).
**Usage** :
```
if result.status_code == 404:
    print("Page not found!")
Copy
```

### 1.4 **`error_message`**_(Optional[str])_
**What** : If `success=False`, a textual description of the failure.
**Usage** :
```
if not result.success:
    print("Error:", result.error_message)
Copy
```

### 1.5 **`session_id`**_(Optional[str])_
**What** : The ID used for reusing a browser context across multiple calls.
**Usage** :
```
# If you used session_id="login_session" in CrawlerRunConfig, see it here:
print("Session:", result.session_id)
Copy
```

### 1.6 **`response_headers`**_(Optional[dict])_
**What** : Final HTTP response headers.
**Usage** :
```
if result.response_headers:
    print("Server:", result.response_headers.get("Server", "Unknown"))
Copy
```

### 1.7 **`ssl_certificate`**_(Optional[SSLCertificate])_
**What** : If `fetch_ssl_certificate=True` in your CrawlerRunConfig, **`result.ssl_certificate`**contains a[**`SSLCertificate`**](https://docs.crawl4ai.com/advanced/ssl-certificate/)object describing the site's certificate. You can export the cert in multiple formats (PEM/DER/JSON) or access its properties like`issuer`, `subject`, `valid_from`, `valid_until`, etc. **Usage** :
```
if result.ssl_certificate:
    print("Issuer:", result.ssl_certificate.issuer)
Copy
```

* * *
## 2. Raw / Cleaned Content
### 2.1 **`html`**_(str)_
**What** : The **original** unmodified HTML from the final page load.
**Usage** :
```
# Possibly large
print(len(result.html))
Copy
```

### 2.2 **`cleaned_html`**_(Optional[str])_
**What** : A sanitized HTML version—scripts, styles, or excluded tags are removed based on your `CrawlerRunConfig`.
**Usage** :
```
print(result.cleaned_html[:500])  # Show a snippet
Copy
```

* * *
## 3. Markdown Fields
### 3.1 The Markdown Generation Approach
Crawl4AI can convert HTML→Markdown, optionally including:
  * **Raw** markdown
  * **Links as citations** (with a references section)
  * **Fit** markdown if a **content filter** is used (like Pruning or BM25)


**`MarkdownGenerationResult`**includes: -**`raw_markdown`**_(str)_ : The full HTML→Markdown conversion.
- **`markdown_with_citations`**_(str)_ : Same markdown, but with link references as academic-style citations.
- **`references_markdown`**_(str)_ : The reference list or footnotes at the end.
- **`fit_markdown`**_(Optional[str])_ : If content filtering (Pruning/BM25) was applied, the filtered "fit" text.
- **`fit_html`**_(Optional[str])_ : The HTML that led to `fit_markdown`.
**Usage** :
```
if result.markdown:
    md_res = result.markdown
    print("Raw MD:", md_res.raw_markdown[:300])
    print("Citations MD:", md_res.markdown_with_citations[:300])
    print("References:", md_res.references_markdown)
    if md_res.fit_markdown:
        print("Pruned text:", md_res.fit_markdown[:300])
Copy
```

### 3.2 **`markdown`**_(Optional[Union[str, MarkdownGenerationResult]])_
**What** : Holds the `MarkdownGenerationResult`.
**Usage** :
```
print(result.markdown.raw_markdown[:200])
print(result.markdown.fit_markdown)
print(result.markdown.fit_html)
Copy
```

**Important** : "Fit" content (in `fit_markdown`/`fit_html`) exists in result.markdown, only if you used a **filter** (like **PruningContentFilter** or **BM25ContentFilter**) within a `MarkdownGenerationStrategy`.
* * *
## 4. Media & Links
### 4.1 **`media`**_(Dict[str, List[Dict]])_
**What** : Contains info about discovered images, videos, or audio. Typically keys: `"images"`, `"videos"`, `"audios"`.
**Common Fields** in each item:
  * `src` _(str)_ : Media URL
  * `alt` or `title` _(str)_ : Descriptive text
  * `score` _(float)_ : Relevance score if the crawler's heuristic found it "important"
  * `desc` or `description` _(Optional[str])_ : Additional context extracted from surrounding text


**Usage** :
```
images = result.media.get("images", [])
for img in images:
    if img.get("score", 0) > 5:
        print("High-value image:", img["src"])
Copy
```

### 4.2 **`links`**_(Dict[str, List[Dict]])_
**What** : Holds internal and external link data. Usually two keys: `"internal"` and `"external"`.
**Common Fields** :
  * `href` _(str)_ : The link target
  * `text` _(str)_ : Link text
  * `title` _(str)_ : Title attribute
  * `context` _(str)_ : Surrounding text snippet
  * `domain` _(str)_ : If external, the domain


**Usage** :
```
for link in result.links["internal"]:
    print(f"Internal link to {link['href']} with text {link['text']}")
Copy
```

* * *
## 5. Additional Fields
### 5.1 **`extracted_content`**_(Optional[str])_
**What** : If you used **`extraction_strategy`**(CSS, LLM, etc.), the structured output (JSON).
**Usage** :
```
if result.extracted_content:
    data = json.loads(result.extracted_content)
    print(data)
Copy
```

### 5.2 **`downloaded_files`**_(Optional[List[str]])_
**What** : If `accept_downloads=True` in your `BrowserConfig` + `downloads_path`, lists local file paths for downloaded items.
**Usage** :
```
if result.downloaded_files:
    for file_path in result.downloaded_files:
        print("Downloaded:", file_path)
Copy
```

### 5.3 **`screenshot`**_(Optional[str])_
**What** : Base64-encoded screenshot if `screenshot=True` in `CrawlerRunConfig`.
**Usage** :
```
import base64
if result.screenshot:
    with open("page.png", "wb") as f:
        f.write(base64.b64decode(result.screenshot))
Copy
```

### 5.4 **`pdf`**_(Optional[bytes])_
**What** : Raw PDF bytes if `pdf=True` in `CrawlerRunConfig`.
**Usage** :
```
if result.pdf:
    with open("page.pdf", "wb") as f:
        f.write(result.pdf)
Copy
```

### 5.5 **`mhtml`**_(Optional[str])_
**What** : MHTML snapshot of the page if `capture_mhtml=True` in `CrawlerRunConfig`. MHTML (MIME HTML) format preserves the entire web page with all its resources (CSS, images, scripts, etc.) in a single file.
**Usage** :
```
if result.mhtml:
    with open("page.mhtml", "w", encoding="utf-8") as f:
        f.write(result.mhtml)
Copy
```

### 5.6 **`metadata`**_(Optional[dict])_
**What** : Page-level metadata if discovered (title, description, OG data, etc.).
**Usage** :
```
if result.metadata:
    print("Title:", result.metadata.get("title"))
    print("Author:", result.metadata.get("author"))
Copy
```

* * *
## 6. `dispatch_result` (optional)
A `DispatchResult` object providing additional concurrency and resource usage information when crawling URLs in parallel (e.g., via `arun_many()` with custom dispatchers). It contains:
  * **`task_id`**: A unique identifier for the parallel task.
  * **`memory_usage`**(float): The memory (in MB) used at the time of completion.
  * **`peak_memory`**(float): The peak memory usage (in MB) recorded during the task's execution.
  * **`start_time`**/**`end_time`**(datetime): Time range for this crawling task.
  * **`error_message`**(str): Any dispatcher- or concurrency-related error encountered.


```
# Example usage:
for result in results:
    if result.success and result.dispatch_result:
        dr = result.dispatch_result
        print(f"URL: {result.url}, Task ID: {dr.task_id}")
        print(f"Memory: {dr.memory_usage:.1f} MB (Peak: {dr.peak_memory:.1f} MB)")
        print(f"Duration: {dr.end_time - dr.start_time}")
Copy
```

> **Note** : This field is typically populated when using `arun_many(...)` alongside a **dispatcher** (e.g., `MemoryAdaptiveDispatcher` or `SemaphoreDispatcher`). If no concurrency or dispatcher is used, `dispatch_result` may remain `None`.
* * *
## 7. Network Requests & Console Messages
When you enable network and console message capturing in `CrawlerRunConfig` using `capture_network_requests=True` and `capture_console_messages=True`, the `CrawlResult` will include these fields:
### 7.1 **`network_requests`**_(Optional[List[Dict[str, Any]]])_
**What** : A list of dictionaries containing information about all network requests, responses, and failures captured during the crawl. **Structure** : - Each item has an `event_type` field that can be `"request"`, `"response"`, or `"request_failed"`. - Request events include `url`, `method`, `headers`, `post_data`, `resource_type`, and `is_navigation_request`. - Response events include `url`, `status`, `status_text`, `headers`, and `request_timing`. - Failed request events include `url`, `method`, `resource_type`, and `failure_text`. - All events include a `timestamp` field.
**Usage** :
```
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
Copy
```

### 7.2 **`console_messages`**_(Optional[List[Dict[str, Any]]])_
**What** : A list of dictionaries containing all browser console messages captured during the crawl. **Structure** : - Each item has a `type` field indicating the message type (e.g., `"log"`, `"error"`, `"warning"`, etc.). - The `text` field contains the actual message text. - Some messages include `location` information (URL, line, column). - All messages include a `timestamp` field.
**Usage** :
```
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
Copy
```

These fields provide deep visibility into the page's network activity and browser console, which is invaluable for debugging, security analysis, and understanding complex web applications.
For more details on network and console capturing, see the [Network & Console Capture documentation](https://docs.crawl4ai.com/advanced/network-console-capture/).
* * *
## 8. Example: Accessing Everything
```
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
Copy
```

* * *
## 9. Key Points & Future
1. **Deprecated legacy properties of CrawlResult**
- `markdown_v2` - Deprecated in v0.5. Just use `markdown`. It holds the `MarkdownGenerationResult` now! - `fit_markdown` and `fit_html` - Deprecated in v0.5. They can now be accessed via `MarkdownGenerationResult` in `result.markdown`. eg: `result.markdown.fit_markdown` and `result.markdown.fit_html`
2. **Fit Content**
- **`fit_markdown`**and**`fit_html`**appear in MarkdownGenerationResult, only if you used a content filter (like**PruningContentFilter** or **BM25ContentFilter**) inside your **MarkdownGenerationStrategy** or set them directly.
- If no filter is used, they remain `None`.
3. **References & Citations**
- If you enable link citations in your `DefaultMarkdownGenerator` (`options={"citations": True}`), you’ll see `markdown_with_citations` plus a **`references_markdown`**block. This helps large language models or academic-like referencing.
4. **Links & Media**
- `links["internal"]` and `links["external"]` group discovered anchors by domain.
- `media["images"]` / `["videos"]` / `["audios"]` store extracted media elements with optional scoring or context.
5. **Error Cases**
- If `success=False`, check `error_message` (e.g., timeouts, invalid URLs).
- `status_code` might be `None` if we failed before an HTTP response.
Use **`CrawlResult`**to glean all final outputs and feed them into your data pipelines, AI models, or archives. With the synergy of a properly configured**BrowserConfig** and **CrawlerRunConfig** , the crawler can produce robust, structured results here in **`CrawlResult`**.
#### On this page
  * [1. Basic Crawl Info](https://docs.crawl4ai.com/api/crawl-result/#1-basic-crawl-info)
  * [1.1 url (str)](https://docs.crawl4ai.com/api/crawl-result/#11-url-str)
  * [1.2 success (bool)](https://docs.crawl4ai.com/api/crawl-result/#12-success-bool)
  * [1.3 status_code (Optional[int])](https://docs.crawl4ai.com/api/crawl-result/#13-status_code-optionalint)
  * [1.4 error_message (Optional[str])](https://docs.crawl4ai.com/api/crawl-result/#14-error_message-optionalstr)
  * [1.5 session_id (Optional[str])](https://docs.crawl4ai.com/api/crawl-result/#15-session_id-optionalstr)
  * [1.6 response_headers (Optional[dict])](https://docs.crawl4ai.com/api/crawl-result/#16-response_headers-optionaldict)
  * [1.7 ssl_certificate (Optional[SSLCertificate])](https://docs.crawl4ai.com/api/crawl-result/#17-ssl_certificate-optionalsslcertificate)
  * [2. Raw / Cleaned Content](https://docs.crawl4ai.com/api/crawl-result/#2-raw-cleaned-content)
  * [2.1 html (str)](https://docs.crawl4ai.com/api/crawl-result/#21-html-str)
  * [2.2 cleaned_html (Optional[str])](https://docs.crawl4ai.com/api/crawl-result/#22-cleaned_html-optionalstr)
  * [3. Markdown Fields](https://docs.crawl4ai.com/api/crawl-result/#3-markdown-fields)
  * [3.1 The Markdown Generation Approach](https://docs.crawl4ai.com/api/crawl-result/#31-the-markdown-generation-approach)
  * [3.2 markdown (Optional[Union[str, MarkdownGenerationResult]])](https://docs.crawl4ai.com/api/crawl-result/#32-markdown-optionalunionstr-markdowngenerationresult)
  * [4. Media & Links](https://docs.crawl4ai.com/api/crawl-result/#4-media-links)
  * [4.1 media (Dict[str, List[Dict]])](https://docs.crawl4ai.com/api/crawl-result/#41-media-dictstr-listdict)
  * [4.2 links (Dict[str, List[Dict]])](https://docs.crawl4ai.com/api/crawl-result/#42-links-dictstr-listdict)
  * [5. Additional Fields](https://docs.crawl4ai.com/api/crawl-result/#5-additional-fields)
  * [5.1 extracted_content (Optional[str])](https://docs.crawl4ai.com/api/crawl-result/#51-extracted_content-optionalstr)
  * [5.2 downloaded_files (Optional[List[str]])](https://docs.crawl4ai.com/api/crawl-result/#52-downloaded_files-optionalliststr)
  * [5.3 screenshot (Optional[str])](https://docs.crawl4ai.com/api/crawl-result/#53-screenshot-optionalstr)
  * [5.4 pdf (Optional[bytes])](https://docs.crawl4ai.com/api/crawl-result/#54-pdf-optionalbytes)
  * [5.5 mhtml (Optional[str])](https://docs.crawl4ai.com/api/crawl-result/#55-mhtml-optionalstr)
  * [5.6 metadata (Optional[dict])](https://docs.crawl4ai.com/api/crawl-result/#56-metadata-optionaldict)
  * [6. dispatch_result (optional)](https://docs.crawl4ai.com/api/crawl-result/#6-dispatch_result-optional)
  * [7. Network Requests & Console Messages](https://docs.crawl4ai.com/api/crawl-result/#7-network-requests-console-messages)
  * [7.1 network_requests (Optional[List[Dict[str, Any]]])](https://docs.crawl4ai.com/api/crawl-result/#71-network_requests-optionallistdictstr-any)
  * [7.2 console_messages (Optional[List[Dict[str, Any]]])](https://docs.crawl4ai.com/api/crawl-result/#72-console_messages-optionallistdictstr-any)
  * [8. Example: Accessing Everything](https://docs.crawl4ai.com/api/crawl-result/#8-example-accessing-everything)
  * [9. Key Points & Future](https://docs.crawl4ai.com/api/crawl-result/#9-key-points-future)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
