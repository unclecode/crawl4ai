# `CrawlResult` Reference

The **`CrawlResult`** class encapsulates everything returned after a single crawl operation. It provides the **raw or processed content**, details on links and media, plus optional metadata (like screenshots, PDFs, or extracted JSON).

**Location**: `crawl4ai/crawler/models.py` (for reference)

```python
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
    markdown: Optional[Union[str, MarkdownGenerationResult]] = None
    markdown_v2: Optional[MarkdownGenerationResult] = None
    fit_markdown: Optional[str] = None
    fit_html: Optional[str] = None
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
**What**: The page’s HTTP status code (e.g., 200, 404).  
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
**What**: If `fetch_ssl_certificate=True` in your CrawlerRunConfig, **`result.ssl_certificate`** contains a  [**`SSLCertificate`**](../advanced/ssl-certificate.md) object describing the site’s certificate. You can export the cert in multiple formats (PEM/DER/JSON) or access its properties like `issuer`, 
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

### 2.3 **`fit_html`** *(Optional[str])*  
**What**: If a **content filter** or heuristic (e.g., Pruning/BM25) modifies the HTML, the “fit” or post-filter version.  
**When**: This is **only** present if your `markdown_generator` or `content_filter` produces it.  
**Usage**:
```python
if result.fit_html:
    print("High-value HTML content:", result.fit_html[:300])
```

---

## 3. Markdown Fields

### 3.1 The Markdown Generation Approach

Crawl4AI can convert HTML→Markdown, optionally including:

- **Raw** markdown  
- **Links as citations** (with a references section)  
- **Fit** markdown if a **content filter** is used (like Pruning or BM25)

### 3.2 **`markdown_v2`** *(Optional[MarkdownGenerationResult])*  
**What**: The **structured** object holding multiple markdown variants. Soon to be consolidated into `markdown`.  

**`MarkdownGenerationResult`** includes:
- **`raw_markdown`** *(str)*: The full HTML→Markdown conversion.  
- **`markdown_with_citations`** *(str)*: Same markdown, but with link references as academic-style citations.  
- **`references_markdown`** *(str)*: The reference list or footnotes at the end.  
- **`fit_markdown`** *(Optional[str])*: If content filtering (Pruning/BM25) was applied, the filtered “fit” text.  
- **`fit_html`** *(Optional[str])*: The HTML that led to `fit_markdown`.

**Usage**:
```python
if result.markdown_v2:
    md_res = result.markdown_v2
    print("Raw MD:", md_res.raw_markdown[:300])
    print("Citations MD:", md_res.markdown_with_citations[:300])
    print("References:", md_res.references_markdown)
    if md_res.fit_markdown:
        print("Pruned text:", md_res.fit_markdown[:300])
```

### 3.3 **`markdown`** *(Optional[Union[str, MarkdownGenerationResult]])*  
**What**: In future versions, `markdown` will fully replace `markdown_v2`. Right now, it might be a `str` or a `MarkdownGenerationResult`.  
**Usage**:
```python
# Soon, you might see:
if isinstance(result.markdown, MarkdownGenerationResult):
    print(result.markdown.raw_markdown[:200])
else:
    print(result.markdown)
```

### 3.4 **`fit_markdown`** *(Optional[str])*  
**What**: A direct reference to the final filtered markdown (legacy approach).  
**When**: This is set if a filter or content strategy explicitly writes there. Usually overshadowed by `markdown_v2.fit_markdown`.  
**Usage**:
```python
print(result.fit_markdown)  # Legacy field, prefer result.markdown_v2.fit_markdown
```

**Important**: “Fit” content (in `fit_markdown`/`fit_html`) only exists if you used a **filter** (like **PruningContentFilter** or **BM25ContentFilter**) within a `MarkdownGenerationStrategy`.

---

## 4. Media & Links

### 4.1 **`media`** *(Dict[str, List[Dict]])*  
**What**: Contains info about discovered images, videos, or audio. Typically keys: `"images"`, `"videos"`, `"audios"`.  
**Common Fields** in each item:

- `src` *(str)*: Media URL  
- `alt` or `title` *(str)*: Descriptive text  
- `score` *(float)*: Relevance score if the crawler’s heuristic found it “important”  
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

### 5.5 **`metadata`** *(Optional[dict])*  
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
- **`peak_memory`** (float): The peak memory usage (in MB) recorded during the task’s execution.
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

## 7. Example: Accessing Everything

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
    if result.markdown_v2:
        print("Raw Markdown:", result.markdown_v2.raw_markdown[:300])
        print("Citations Markdown:", result.markdown_v2.markdown_with_citations[:300])
        if result.markdown_v2.fit_markdown:
            print("Fit Markdown:", result.markdown_v2.fit_markdown[:200])
    else:
        print("Raw Markdown (legacy):", result.markdown[:200] if result.markdown else "N/A")

    # Media & Links
    if "images" in result.media:
        print("Image count:", len(result.media["images"]))
    if "internal" in result.links:
        print("Internal link count:", len(result.links["internal"]))

    # Extraction strategy result
    if result.extracted_content:
        print("Structured data:", result.extracted_content)
    
    # Screenshot/PDF
    if result.screenshot:
        print("Screenshot length:", len(result.screenshot))
    if result.pdf:
        print("PDF bytes length:", len(result.pdf))
```

---

## 8. Key Points & Future

1. **`markdown_v2` vs `markdown`**  
   - Right now, `markdown_v2` is the more robust container (`MarkdownGenerationResult`), providing **raw_markdown**, **markdown_with_citations**, references, plus possible **fit_markdown**.  
   - In future versions, everything will unify under **`markdown`**. If you rely on advanced features (citations, fit content), check `markdown_v2`.

2. **Fit Content**  
   - **`fit_markdown`** and **`fit_html`** appear only if you used a content filter (like **PruningContentFilter** or **BM25ContentFilter**) inside your **MarkdownGenerationStrategy** or set them directly.  
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