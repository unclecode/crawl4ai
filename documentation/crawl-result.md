`CrawlResult` Reference
=======================

The **`CrawlResult`** class encapsulates everything returned after a single crawl operation. It provides the **raw or processed content**, details on links and media, plus optional metadata (like screenshots, PDFs, or extracted JSON).

**Location**: `crawl4ai/crawler/models.py` (for reference)

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
```

Below is a **field-by-field** explanation and possible usage patterns.

---

1. Basic Crawl Info
-------------------

### 1.1 **`url`** *(str)*

**What**: The final crawled URL (after any redirects).
**Usage**:

```
print(result.url)  # e.g., "https://example.com/"
```

### 1.2 **`success`** *(bool)*

**What**: `True` if the crawl pipeline ended without major errors; `False` otherwise.
**Usage**:

```
if not result.success:
    print(f"Crawl failed: {result.error_message}")
```

### 1.3 **`status_code`** *(Optional[int])*

**What**: The page's HTTP status code (e.g., 200, 404).
**Usage**:

```
if result.status_code == 404:
    print("Page not found!")
```

### 1.4 **`error_message`** *(Optional[str])*

**What**: If `success=False`, a textual description of the failure.
**Usage**:

```
if not result.success:
    print("Error:", result.error_message)
```

### 1.5 **`session_id`** *(Optional[str])*

**What**: The ID used for reusing a browser context across multiple calls.
**Usage**:

```
# If you used session_id="login_session" in CrawlerRunConfig, see it here:
print("Session:", result.session_id)
```

### 1.6 **`response_headers`** *(Optional[dict])*

**What**: Final HTTP response headers.
**Usage**:

```
if result.response_headers:
    print("Server:", result.response_headers.get("Server", "Unknown"))
```

### 1.7 **`ssl_certificate`** *(Optional[SSLCertificate])*

**What**: If `fetch_ssl_certificate=True` in your CrawlerRunConfig, **`result.ssl_certificate`** contains a [**`SSLCertificate`**](../../advanced/ssl-certificate/) object describing the site's certificate. You can export the cert in multiple formats (PEM/DER/JSON) or access its properties like `issuer`,
`subject`, `valid_from`, `valid_until`, etc.
**Usage**:

```
if result.ssl_certificate:
    print("Issuer:", result.ssl_certificate.issuer)
```

---