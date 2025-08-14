Crawl Result and Output
=======================

When you call `arun()` on a page, Crawl4AI returns a **`CrawlResult`** object containing everything you might need—raw HTML, a cleaned version, optional screenshots or PDFs, structured extraction results, and more. This document explains those fields and how they map to different output types.

---

1. The `CrawlResult` Model
--------------------------

Below is the core schema. Each field captures a different aspect of the crawl’s result:

```
class MarkdownGenerationResult(BaseModel):
    raw_markdown: str
    markdown_with_citations: str
    references_markdown: str
    fit_markdown: Optional[str] = None
    fit_html: Optional[str] = None

class CrawlResult(BaseModel):
    url: str
    html: str
    fit_html: Optional[str] = None
    success: bool
    cleaned_html: Optional[str] = None
    media: Dict[str, List[Dict]] = {}
    links: Dict[str, List[Dict]] = {}
    downloaded_files: Optional[List[str]] = None
    js_execution_result: Optional[Dict[str, Any]] = None
    screenshot: Optional[str] = None
    pdf: Optional[bytes] = None
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
    redirected_url: Optional[str] = None
    network_requests: Optional[List[Dict[str, Any]]] = None
    console_messages: Optional[List[Dict[str, Any]]] = None
    tables: List[Dict] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
```

### Table: Key Fields in `CrawlResult`

| Field (Name & Type) | Description |
| --- | --- |
| **url (`str`)** | The final or actual URL crawled (in case of redirects). |
| **html (`str`)** | Original, unmodified page HTML. Good for debugging or custom processing. |
| **fit\_html (`Optional[str]`)** | Preprocessed HTML optimized for extraction and content filtering. |
| **success (`bool`)** | `True` if the crawl completed without major errors, else `False`. |
| **cleaned\_html (`Optional[str]`)** | Sanitized HTML with scripts/styles removed; can exclude tags if configured via `excluded_tags` etc. |
| **media (`Dict[str, List[Dict]]`)** | Extracted media info (images, audio, etc.), each with attributes like `src`, `alt`, `score`, etc. |
| **links (`Dict[str, List[Dict]]`)** | Extracted link data, split by `internal` and `external`. Each link usually has `href`, `text`, etc. |
| **downloaded\_files (`Optional[List[str]]`)** | If `accept_downloads=True` in `BrowserConfig`, this lists the filepaths of saved downloads. |
| **js\_execution\_result (`Optional[Dict[str, Any]]`)** | Results from JavaScript execution during crawling. |
| **screenshot (`Optional[str]`)** | Screenshot of the page (base64-encoded) if `screenshot=True`. |
| **pdf (`Optional[bytes]`)** | PDF of the page if `pdf=True`. |
| **mhtml (`Optional[str]`)** | MHTML snapshot of the page if `capture_mhtml=True`. Contains the full page with all resources. |
| **markdown (`Optional[str or MarkdownGenerationResult]`)** | It holds a `MarkdownGenerationResult`. Over time, this will be consolidated into `markdown`. The generator can provide raw markdown, citations, references, and optionally `fit_markdown`. |
| **extracted\_content (`Optional[str]`)** | The output of a structured extraction (CSS/LLM-based) stored as JSON string or other text. |
| **metadata (`Optional[dict]`)** | Additional info about the crawl or extracted data. |
| **error\_message (`Optional[str]`)** | If `success=False`, contains a short description of what went wrong. |
| **session\_id (`Optional[str]`)** | The ID of the session used for multi-page or persistent crawling. |
| **response\_headers (`Optional[dict]`)** | HTTP response headers, if captured. |
| **status\_code (`Optional[int]`)** | HTTP status code (e.g., 200 for OK). |
| **ssl\_certificate (`Optional[SSLCertificate]`)** | SSL certificate info if `fetch_ssl_certificate=True`. |
| **dispatch\_result (`Optional[DispatchResult]`)** | Additional concurrency and resource usage information when crawling URLs in parallel. |
| **redirected\_url (`Optional[str]`)** | The URL after any redirects (different from `url` which is the final URL). |
| **network\_requests (`Optional[List[Dict[str, Any]]]`)** | List of network requests, responses, and failures captured during the crawl if `capture_network_requests=True`. |
| **console\_messages (`Optional[List[Dict[str, Any]]]`)** | List of browser console messages captured during the crawl if `capture_console_messages=True`. |
| **tables (`List[Dict]`)** | Table data extracted from HTML tables with structure `[{headers, rows, caption, summary}]`. |

---