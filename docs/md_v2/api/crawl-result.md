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

Below is a **field-by-field** explanation and possible usage patterns.

---

## 1. Basic Crawl Info

### 1.1 **`url`** *(str)*  
**What**: The final crawled URL (after any redirects).  
**Usage**:
```python
print(result.url)  # e.g., "https://example.com/"
```

### 1.2 **`success`** *(bool)*  
**What**: `True` if the crawl pipeline ended without major errors; `False` otherwise.  
**Usage**:
```python
if not result.success:
    print(f"Crawl failed: {result.error_message}")
```

### 1.3 **`status_code`** *(Optional[int])*  
**What**: The page's HTTP status code (e.g., 200, 404).  
**Usage**:
```python
if result.status_code == 404:
    print("Page not found!")
```

### 1.4 **`error_message`** *(Optional[str])*  
**What**: If `success=False`, a textual description of the failure.  
**Usage**:
```python
if not result.success:
    print("Error:", result.error_message)
```

### 1.5 **`session_id`** *(Optional[str])*  
**What**: The ID used for reusing a browser context across multiple calls.  
**Usage**:
```python
# If you used session_id="login_session" in CrawlerRunConfig, see it here:
print("Session:", result.session_id)
```

### 1.6 **`response_headers`** *(Optional[dict])*  
**What**: Final HTTP response headers.  
**Usage**:
```python
if result.response_headers:
    print("Server:", result.response_headers.get("Server", "Unknown"))
```

### 1.7 **`ssl_certificate`** *(Optional[SSLCertificate])*  
**What**: If `fetch_ssl_certificate=True` in your CrawlerRunConfig, **`result.ssl_certificate`** contains a  [**`SSLCertificate`**](../advanced/ssl-certificate.md) object describing the site's certificate. You can export the cert in multiple formats (PEM/DER/JSON) or access its properties like `issuer`, 
 `subject`, `valid_from`, `valid_until`, etc. 
**Usage**:
```python
if result.ssl_certificate:
    print("Issuer:", result.ssl_certificate.issuer)
```

---

## 2. Raw / Cleaned Content

### 2.1 **`html`** *(str)*  
**What**: The **original** unmodified HTML from the final page load.  
**Usage**:
```python
# Possibly large
print(len(result.html))
```

### 2.2 **`cleaned_html`** *(Optional[str])*  
**What**: A sanitized HTML version—scripts, styles, or excluded tags are removed based on your `CrawlerRunConfig`.  
**Usage**:
```python
print(result.cleaned_html[:500])  # Show a snippet
```


---

## 3. Markdown Fields

### 3.1 The Markdown Generation Approach

Crawl4AI can convert HTML→Markdown, optionally including:

- **Raw** markdown  
- **Links as citations** (with a references section)  
- **Fit** markdown if a **content filter** is used (like Pruning or BM25)


**`MarkdownGenerationResult`** includes:
- **`raw_markdown`** *(str)*: The full HTML→Markdown conversion.  
- **`markdown_with_citations`** *(str)*: Same markdown, but with link references as academic-style citations.  
- **`references_markdown`** *(str)*: The reference list or footnotes at the end.  
- **`fit_markdown`** *(Optional[str])*: If content filtering (Pruning/BM25) was applied, the filtered "fit" text.  
- **`fit_html`** *(Optional[str])*: The HTML that led to `fit_markdown`.

**Usage**:
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
**Usage**:
```python
print(result.markdown.raw_markdown[:200])
print(result.markdown.fit_markdown)
print(result.markdown.fit_html)
```
**Important**: "Fit" content (in `fit_markdown`/`fit_html`) exists in result.markdown, only if you used a **filter** (like **PruningContentFilter** or **BM25ContentFilter**) within a `MarkdownGenerationStrategy`.

---

## 4. Media & Links

### 4.1 **`media`** *(Dict[str, List[Dict]])*  
**What**: Contains info about discovered images, videos, or audio. Typically keys: `"images"`, `"videos"`, `"audios"`.  
**Common Fields** in each item:

- `src` *(str)*: Media URL  
- `alt` or `title` *(str)*: Descriptive text  
- `score` *(float)*: Relevance score if the crawler's heuristic found it "important"  
- `desc` or `description` *(Optional[str])*: Additional context extracted from surrounding text  

**Usage**:
```python
images = result.media.get("images", [])
for img in images:
    if img.get("score", 0) > 5:
        print("High-value image:", img["src"])
```

### 4.2 **`links`** *(Dict[str, List[Dict]])*  
**What**: Holds internal and external link data. Usually two keys: `"internal"` and `"external"`.  
**Common Fields**:

- `href` *(str)*: The link target  
- `text` *(str)*: Link text  
- `title` *(str)*: Title attribute  
- `context` *(str)*: Surrounding text snippet  
- `domain` *(str)*: If external, the domain

**Usage**:
```python
for link in result.links["internal"]:
    print(f"Internal link to {link['href']} with text {link['text']}")
```

---

## 5. Additional Fields

### 5.1 **`extracted_content`** *(Optional[str])*  
**What**: If you used **`extraction_strategy`** (CSS, LLM, etc.), the structured output (JSON).  
**Usage**:
```python
if result.extracted_content:
    data = json.loads(result.extracted_content)
    print(data)
```

### 5.2 **`downloaded_files`** *(Optional[List[str]])*  
**What**: If `accept_downloads=True` in your `BrowserConfig` + `downloads_path`, lists local file paths for downloaded items.  
**Usage**:
```python
if result.downloaded_files:
    for file_path in result.downloaded_files:
        print("Downloaded:", file_path)
```

### 5.3 **`screenshot`** *(Optional[str])*  
**What**: Base64-encoded screenshot if `screenshot=True` in `CrawlerRunConfig`.  
**Usage**:
```python
import base64
if result.screenshot:
    with open("page.png", "wb") as f:
        f.write(base64.b64decode(result.screenshot))
```

### 5.4 **`pdf`** *(Optional[bytes])*  
**What**: Raw PDF bytes if `pdf=True` in `CrawlerRunConfig`.  
**Usage**:
```python
if result.pdf:
    with open("page.pdf", "wb") as f:
        f.write(result.pdf)
```

### 5.5 **`mhtml`** *(Optional[str])*  
**What**: MHTML snapshot of the page if `capture_mhtml=True` in `CrawlerRunConfig`. MHTML (MIME HTML) format preserves the entire web page with all its resources (CSS, images, scripts, etc.) in a single file.  
**Usage**:
```python
if result.mhtml:
    with open("page.mhtml", "w", encoding="utf-8") as f:
        f.write(result.mhtml)
```

### 5.6 **`metadata`** *(Optional[dict])*  
**What**: Page-level metadata if discovered (title, description, OG data, etc.).  
**Usage**:
```python
if result.metadata:
    print("Title:", result.metadata.get("title"))
    print("Author:", result.metadata.get("author"))
```

---

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

---

## 7. Network Requests & Console Messages

When you enable network and console message capturing in `CrawlerRunConfig` using `capture_network_requests=True` and `capture_console_messages=True`, the `CrawlResult` will include these fields:

### 7.1 **`network_requests`** *(Optional[List[Dict[str, Any]]])*
**What**: A list of dictionaries containing information about all network requests, responses, and failures captured during the crawl.
**Structure**:
- Each item has an `event_type` field that can be `"request"`, `"response"`, or `"request_failed"`.
- Request events include `url`, `method`, `headers`, `post_data`, `resource_type`, and `is_navigation_request`.
- Response events include `url`, `status`, `status_text`, `headers`, and `request_timing`.
- Failed request events include `url`, `method`, `resource_type`, and `failure_text`.
- All events include a `timestamp` field.

**Usage**:
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
**What**: A list of dictionaries containing all browser console messages captured during the crawl.
**Structure**:
- Each item has a `type` field indicating the message type (e.g., `"log"`, `"error"`, `"warning"`, etc.).
- The `text` field contains the actual message text.
- Some messages include `location` information (URL, line, column).
- All messages include a `timestamp` field.

**Usage**:
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

These fields provide deep visibility into the page's network activity and browser console, which is invaluable for debugging, security analysis, and understanding complex web applications.

For more details on network and console capturing, see the [Network & Console Capture documentation](../advanced/network-console-capture.md).

---

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

---

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