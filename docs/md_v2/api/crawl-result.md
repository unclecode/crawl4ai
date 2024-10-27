# CrawlResult

The `CrawlResult` class represents the result of a web crawling operation. It provides access to various forms of extracted content and metadata from the crawled webpage.

## Class Definition

```python
class CrawlResult(BaseModel):
    """Result of a web crawling operation."""
    
    # Basic Information
    url: str                                # Crawled URL
    success: bool                           # Whether crawl succeeded
    status_code: Optional[int] = None       # HTTP status code
    error_message: Optional[str] = None     # Error message if failed
    
    # Content
    html: str                              # Raw HTML content
    cleaned_html: Optional[str] = None      # Cleaned HTML
    fit_html: Optional[str] = None          # Most relevant HTML content
    markdown: Optional[str] = None          # HTML converted to markdown
    fit_markdown: Optional[str] = None      # Most relevant markdown content
    
    # Extracted Data
    extracted_content: Optional[str] = None  # Content from extraction strategy
    media: Dict[str, List[Dict]] = {}       # Extracted media information
    links: Dict[str, List[Dict]] = {}       # Extracted links
    metadata: Optional[dict] = None         # Page metadata
    
    # Additional Data
    screenshot: Optional[str] = None         # Base64 encoded screenshot
    session_id: Optional[str] = None         # Session identifier
    response_headers: Optional[dict] = None  # HTTP response headers
```

## Properties and Their Data Structures

### Basic Information

```python
# Access basic information
result = await crawler.arun(url="https://example.com")

print(result.url)          # "https://example.com"
print(result.success)      # True/False
print(result.status_code)  # 200, 404, etc.
print(result.error_message)  # Error details if failed
```

### Content Properties

#### HTML Content
```python
# Raw HTML
html_content = result.html

# Cleaned HTML (removed ads, popups, etc.)
clean_content = result.cleaned_html

# Most relevant HTML content
main_content = result.fit_html
```

#### Markdown Content
```python
# Full markdown version
markdown_content = result.markdown

# Most relevant markdown content
main_content = result.fit_markdown
```

### Media Content

The media dictionary contains organized media elements:

```python
# Structure
media = {
    "images": [
        {
            "src": str,           # Image URL
            "alt": str,           # Alt text
            "desc": str,          # Contextual description
            "score": float,       # Relevance score (0-10)
            "type": str,          # "image"
            "width": int,         # Image width (if available)
            "height": int,        # Image height (if available)
            "context": str,       # Surrounding text
            "lazy": bool          # Whether image was lazy-loaded
        }
    ],
    "videos": [
        {
            "src": str,           # Video URL
            "type": str,          # "video"
            "title": str,         # Video title
            "poster": str,        # Thumbnail URL
            "duration": str,      # Video duration
            "description": str    # Video description
        }
    ],
    "audios": [
        {
            "src": str,           # Audio URL
            "type": str,          # "audio"
            "title": str,         # Audio title
            "duration": str,      # Audio duration
            "description": str    # Audio description
        }
    ]
}

# Example usage
for image in result.media["images"]:
    if image["score"] > 5:  # High-relevance images
        print(f"High-quality image: {image['src']}")
        print(f"Context: {image['context']}")
```

### Link Analysis

The links dictionary organizes discovered links:

```python
# Structure
links = {
    "internal": [
        {
            "href": str,          # URL
            "text": str,          # Link text
            "title": str,         # Title attribute
            "type": str,          # Link type (nav, content, etc.)
            "context": str,       # Surrounding text
            "score": float        # Relevance score
        }
    ],
    "external": [
        {
            "href": str,          # External URL
            "text": str,          # Link text
            "title": str,         # Title attribute
            "domain": str,        # Domain name
            "type": str,          # Link type
            "context": str        # Surrounding text
        }
    ]
}

# Example usage
for link in result.links["internal"]:
    print(f"Internal link: {link['href']}")
    print(f"Context: {link['context']}")
```

### Metadata

The metadata dictionary contains page information:

```python
# Structure
metadata = {
    "title": str,                # Page title
    "description": str,          # Meta description
    "keywords": List[str],       # Meta keywords
    "author": str,              # Author information
    "published_date": str,      # Publication date
    "modified_date": str,       # Last modified date
    "language": str,            # Page language
    "canonical_url": str,       # Canonical URL
    "og_data": Dict,           # Open Graph data
    "twitter_data": Dict       # Twitter card data
}

# Example usage
if result.metadata:
    print(f"Title: {result.metadata['title']}")
    print(f"Author: {result.metadata.get('author', 'Unknown')}")
```

### Extracted Content

Content from extraction strategies:

```python
# For LLM or CSS extraction strategies
if result.extracted_content:
    structured_data = json.loads(result.extracted_content)
    print(structured_data)
```

### Screenshot

Base64 encoded screenshot:

```python
# Save screenshot if available
if result.screenshot:
    import base64
    
    # Decode and save
    with open("screenshot.png", "wb") as f:
        f.write(base64.b64decode(result.screenshot))
```

## Usage Examples

### Basic Content Access
```python
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
    
    if result.success:
        # Get clean content
        print(result.fit_markdown)
        
        # Process images
        for image in result.media["images"]:
            if image["score"] > 7:
                print(f"High-quality image: {image['src']}")
```

### Complete Data Processing
```python
async def process_webpage(url: str) -> Dict:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        
        if not result.success:
            raise Exception(f"Crawl failed: {result.error_message}")
        
        return {
            "content": result.fit_markdown,
            "images": [
                img for img in result.media["images"]
                if img["score"] > 5
            ],
            "internal_links": [
                link["href"] for link in result.links["internal"]
            ],
            "metadata": result.metadata,
            "status": result.status_code
        }
```

### Error Handling
```python
async def safe_crawl(url: str) -> Dict:
    async with AsyncWebCrawler() as crawler:
        try:
            result = await crawler.arun(url=url)
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message,
                    "status": result.status_code
                }
            
            return {
                "success": True,
                "content": result.fit_markdown,
                "status": result.status_code
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status": None
            }
```

## Best Practices

1. **Always Check Success**
```python
if not result.success:
    print(f"Error: {result.error_message}")
    return
```

2. **Use fit_markdown for Articles**
```python
# Better for article content
content = result.fit_markdown if result.fit_markdown else result.markdown
```

3. **Filter Media by Score**
```python
relevant_images = [
    img for img in result.media["images"]
    if img["score"] > 5
]
```

4. **Handle Missing Data**
```python
metadata = result.metadata or {}
title = metadata.get('title', 'Unknown Title')
```