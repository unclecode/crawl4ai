### AsyncWebCrawler Constructor Parameters
```python
AsyncWebCrawler(
    # Core Browser Settings
    browser_type: str = "chromium",  # Options: "chromium", "firefox", "webkit"
    headless: bool = True,  # Whether to run browser in headless mode
    verbose: bool = False,  # Enable verbose logging
    
    # Cache Settings
    always_by_pass_cache: bool = False,  # Always bypass cache regardless of run settings
    base_directory: str = str(Path.home()),  # Base directory for cache storage
    
    # Network Settings
    proxy: str = None,  # Simple proxy URL (e.g., "http://proxy.example.com:8080")
    proxy_config: Dict = None,  # Advanced proxy settings with auth: {"server": str, "username": str, "password": str}
    
    # Browser Behavior
    sleep_on_close: bool = False,  # Wait before closing browser
    
    # Other Settings passed to AsyncPlaywrightCrawlerStrategy
    user_agent: str = None,  # Custom user agent string
    headers: Dict[str, str] = {},  # Custom HTTP headers
    js_code: Union[str, List[str]] = None,  # Default JavaScript to execute
)
```

### arun() Method Parameters
```python
arun(
    # Core Parameters
    url: str,  # Required: URL to crawl
    
    # Content Selection
    css_selector: str = None,  # CSS selector to extract specific content
    word_count_threshold: int = MIN_WORD_THRESHOLD,  # Minimum words for content blocks
    
    # Cache Control
    bypass_cache: bool = False,  # Bypass cache for this request
    
    # Session Management
    session_id: str = None,  # Session identifier for persistent browsing
    
    # Screenshot Options
    screenshot: bool = False,  # Take page screenshot
    screenshot_wait_for: float = None,  # Wait time before screenshot
    
    # Content Processing
    process_iframes: bool = False,  # Process iframe content
    remove_overlay_elements: bool = False,  # Remove popups/modals
    
    # Anti-Bot/Detection
    simulate_user: bool = False,  # Simulate human-like behavior
    override_navigator: bool = False,  # Override navigator properties
    magic: bool = False,  # Enable all anti-detection features
    
    # Content Filtering
    excluded_tags: List[str] = None,  # HTML tags to exclude
    exclude_external_links: bool = False,  # Remove external links
    exclude_social_media_links: bool = False,  # Remove social media links
    exclude_external_images: bool = False,  # Remove external images
    exclude_social_media_domains: List[str] = None,  # Additional social media domains to exclude
    remove_forms: bool = False,  # Remove all form elements
    
    # JavaScript Handling
    js_code: Union[str, List[str]] = None,  # JavaScript to execute
    js_only: bool = False,  # Only execute JavaScript without reloading page
    wait_for: str = None,  # Wait condition (CSS selector or JS function)
    
    # Page Loading
    page_timeout: int = 60000,  # Page load timeout in milliseconds
    delay_before_return_html: float = None,  # Wait before returning HTML
    
    # Debug Options
    log_console: bool = False,  # Log browser console messages
    
    # Content Format Control
    only_text: bool = False,  # Extract only text content
    keep_data_attributes: bool = False,  # Keep data-* attributes in HTML
    
    # Markdown Options
    include_links_on_markdown: bool = False,  # Include links in markdown output
    html2text: Dict = {},  # HTML to text conversion options
    
    # Extraction Strategy
    extraction_strategy: ExtractionStrategy = None,  # Strategy for structured data extraction
    
    # Advanced Browser Control
    user_agent: str = None,  # Override user agent for this request
)
```

### Extraction Strategy Parameters
```python
# JsonCssExtractionStrategy
{
    "name": str,  # Name of extraction schema
    "baseSelector": str,  # Base CSS selector
    "fields": [
        {
            "name": str,  # Field name
            "selector": str,  # CSS selector
            "type": str,  # Data type ("text", etc.)
            "transform": str = None  # Optional transformation
        }
    ]
}

# LLMExtractionStrategy
{
    "provider": str,  # LLM provider (e.g., "openai/gpt-4", "huggingface/...", "ollama/...")
    "api_token": str,  # API token
    "schema": dict,  # Pydantic model schema
    "extraction_type": str,  # Type of extraction ("schema", etc.)
    "instruction": str,  # Extraction instruction
    "extra_args": dict = None,  # Additional provider-specific arguments
    "extra_headers": dict = None  # Additional HTTP headers
}
```

### HTML to Text Conversion Options (html2text parameter)
```python
{
    "escape_dot": bool = True,  # Escape dots in text
    # Other html2text library options
}
```


### CrawlResult Fields

```python
class CrawlResult(BaseModel):
    # Basic Information
    url: str  # The crawled URL
    # Example: "https://example.com"
    
    success: bool  # Whether the crawl was successful
    # Example: True/False
    
    status_code: Optional[int]  # HTTP status code
    # Example: 200, 404, 500
    
    # Content Fields
    html: str  # Raw HTML content
    # Example: "<html><body>...</body></html>"
    
    cleaned_html: Optional[str]  # HTML after cleaning and processing
    # Example: "<article><p>Clean content...</p></article>"
    
    fit_html: Optional[str]  # Most relevant HTML content after content cleaning strategy
    # Example: "<div><p>Most relevant content...</p></div>"
    
    markdown: Optional[str]  # HTML converted to markdown
    # Example: "# Title\n\nContent paragraph..."
    
    fit_markdown: Optional[str]  # Most relevant content in markdown
    # Example: "# Main Article\n\nKey content..."
    
    # Media Content
    media: Dict[str, List[Dict]] = {}  # Extracted media information
    # Example: {
    #     "images": [
    #         {
    #             "src": "https://example.com/image.jpg",
    #             "alt": "Image description",
    #             "desc": "Contextual description",
    #             "score": 5,  # Relevance score
    #             "type": "image"
    #         }
    #     ],
    #     "videos": [
    #         {
    #             "src": "https://example.com/video.mp4",
    #             "alt": "Video title",
    #             "type": "video",
    #             "description": "Video context"
    #         }
    #     ],
    #     "audios": [
    #         {
    #             "src": "https://example.com/audio.mp3",
    #             "alt": "Audio title",
    #             "type": "audio",
    #             "description": "Audio context"
    #         }
    #     ]
    # }
    
    # Link Information
    links: Dict[str, List[Dict]] = {}  # Extracted links
    # Example: {
    #     "internal": [
    #         {
    #             "href": "https://example.com/page",
    #             "text": "Link text",
    #             "title": "Link title"
    #         }
    #     ],
    #     "external": [
    #         {
    #             "href": "https://external.com",
    #             "text": "External link text",
    #             "title": "External link title"
    #         }
    #     ]
    # }
    
    # Extraction Results
    extracted_content: Optional[str]  # Content from extraction strategy
    # Example for JsonCssExtractionStrategy:
    # '[{"title": "Article 1", "date": "2024-03-20"}, ...]'
    # Example for LLMExtractionStrategy:
    # '{"entities": [...], "relationships": [...]}'
    
    # Additional Information
    metadata: Optional[dict] = None  # Page metadata
    # Example: {
    #     "title": "Page Title",
    #     "description": "Meta description",
    #     "keywords": ["keyword1", "keyword2"],
    #     "author": "Author Name",
    #     "published_date": "2024-03-20"
    # }
    
    screenshot: Optional[str] = None  # Base64 encoded screenshot
    # Example: "iVBORw0KGgoAAAANSUhEUgAA..."
    
    error_message: Optional[str] = None  # Error message if crawl failed
    # Example: "Failed to load page: timeout"
    
    session_id: Optional[str] = None  # Session identifier
    # Example: "session_123456"
    
    response_headers: Optional[dict] = None  # HTTP response headers
    # Example: {
    #     "content-type": "text/html",
    #     "server": "nginx/1.18.0",
    #     "date": "Wed, 20 Mar 2024 12:00:00 GMT"
    # }
```

### Common Usage Patterns:

1. Basic Content Extraction:
```python
result = await crawler.arun(url="https://example.com")
print(result.markdown)  # Clean, readable content
print(result.cleaned_html)  # Cleaned HTML
```

2. Media Analysis:
```python
result = await crawler.arun(url="https://example.com")
for image in result.media["images"]:
    if image["score"] > 3:  # High-relevance images
        print(f"High-quality image: {image['src']}")
```

3. Link Analysis:
```python
result = await crawler.arun(url="https://example.com")
internal_links = [link["href"] for link in result.links["internal"]]
external_links = [link["href"] for link in result.links["external"]]
```

4. Structured Data Extraction:
```python
result = await crawler.arun(
    url="https://example.com",
    extraction_strategy=my_strategy
)
structured_data = json.loads(result.extracted_content)
```

5. Error Handling:
```python
result = await crawler.arun(url="https://example.com")
if not result.success:
    print(f"Crawl failed: {result.error_message}")
    print(f"Status code: {result.status_code}")
```

