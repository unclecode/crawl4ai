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

| Field (Name & Type)                       | Description                                                                                         |
|-------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **url (`str`)**                           | The final or actual URL crawled (in case of redirects).                                             |
| **html (`str`)**                          | Original, unmodified page HTML. Good for debugging or custom processing.                            |
| **fit_html (`Optional[str]`)**            | Preprocessed HTML optimized for extraction and content filtering.                                    |
| **success (`bool`)**                      | `True` if the crawl completed without major errors, else `False`.                                   |
| **cleaned_html (`Optional[str]`)**        | Sanitized HTML with scripts/styles removed; can exclude tags if configured via `excluded_tags` etc. |
| **media (`Dict[str, List[Dict]]`)**       | Extracted media info (images, audio, etc.), each with attributes like `src`, `alt`, `score`, etc.   |
| **links (`Dict[str, List[Dict]]`)**       | Extracted link data, split by `internal` and `external`. Each link usually has `href`, `text`, etc. |
| **downloaded_files (`Optional[List[str]]`)** | If `accept_downloads=True` in `BrowserConfig`, this lists the filepaths of saved downloads.         |
| **js_execution_result (`Optional[Dict[str, Any]]`)** | Results from JavaScript execution during crawling. |
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
| **dispatch_result (`Optional[DispatchResult]`)** | Additional concurrency and resource usage information when crawling URLs in parallel.               |
| **redirected_url (`Optional[str]`)**      | The URL after any redirects (different from `url` which is the final URL).                          |
| **network_requests (`Optional[List[Dict[str, Any]]]`)** | List of network requests, responses, and failures captured during the crawl if `capture_network_requests=True`. |
| **console_messages (`Optional[List[Dict[str, Any]]]`)** | List of browser console messages captured during the crawl if `capture_console_messages=True`.       |
| **tables (`List[Dict]`)**                 | Table data extracted from HTML tables with structure `[{headers, rows, caption, summary}]`.           |

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

## 5. More Fields: Links, Media, Tables and More

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

### 5.3 `tables`

The `tables` field contains structured data extracted from HTML tables found on the crawled page. Tables are analyzed based on various criteria to determine if they are actual data tables (as opposed to layout tables), including:

- Presence of thead and tbody sections
- Use of th elements for headers
- Column consistency
- Text density
- And other factors

Tables that score above the threshold (default: 7) are extracted and stored in result.tables.

### Accessing Table data:
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.w3schools.com/html/html_tables.asp",
            config=CrawlerRunConfig(
                table_score_threshold=7  # Minimum score for table detection
            )
        )

        if result.success and result.tables:
            print(f"Found {len(result.tables)} tables")

            for i, table in enumerate(result.tables):
                print(f"\nTable {i+1}:")
                print(f"Caption: {table.get('caption', 'No caption')}")
                print(f"Headers: {table['headers']}")
                print(f"Rows: {len(table['rows'])}")

                # Print first few rows as example
                for j, row in enumerate(table['rows'][:3]):
                    print(f"  Row {j+1}: {row}")

if __name__ == "__main__":
    asyncio.run(main())

```

### Configuring Table Extraction:

You can adjust the sensitivity of the table detection algorithm with:

```python
config = CrawlerRunConfig(
    table_score_threshold=5  # Lower value = more tables detected (default: 7)
)
```

Each extracted table contains: 

- `headers`: Column header names 
- `rows`: List of rows, each containing cell values
- `caption`: Table caption text (if available) 
- `summary`: Table summary attribute (if specified)

### Table Extraction Tips

- Not all HTML tables are extracted - only those detected as "data tables" vs. layout tables.
- Tables with inconsistent cell counts, nested tables, or those used purely for layout may be skipped.
- If you're missing tables, try adjusting the `table_score_threshold` to a lower value (default is 7).

The table detection algorithm scores tables based on features like consistent columns, presence of headers, text density, and more. Tables scoring above the threshold are considered data tables worth extracting.


### 5.4 `screenshot`, `pdf`, and `mhtml`

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

### 5.5 `ssl_certificate`

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