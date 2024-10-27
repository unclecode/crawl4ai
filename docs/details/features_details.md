I'll expand the outline with detailed descriptions and examples based on all the provided files. I'll start with the first few sections:

### 1. Basic Web Crawling
Basic web crawling provides the foundation for extracting content from websites. The library supports both simple single-page crawling and recursive website crawling.

```python
# Simple page crawling
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
    print(result.html)        # Raw HTML
    print(result.markdown)    # Cleaned markdown
    print(result.cleaned_html)  # Cleaned HTML

# Recursive website crawling
class SimpleWebsiteScraper:
    def __init__(self, crawler: AsyncWebCrawler):
        self.crawler = crawler

    async def scrape(self, start_url: str, max_depth: int):
        results = await self.scrape_recursive(start_url, max_depth)
        return results

# Usage
async with AsyncWebCrawler() as crawler:
    scraper = SimpleWebsiteScraper(crawler)
    results = await scraper.scrape("https://example.com", depth=2)
```

### 2. Browser Control Options
The library provides extensive control over browser behavior, allowing customization of browser type, headless mode, and proxy settings.

```python
# Browser Type Selection
async with AsyncWebCrawler(
    browser_type="firefox",  # Options: "chromium", "firefox", "webkit"
    headless=False,         # For visible browser
    verbose=True           # Enable logging
) as crawler:
    result = await crawler.arun(url="https://example.com")

# Proxy Configuration
async with AsyncWebCrawler(
    proxy_config={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass"
    },
    headers={
        "User-Agent": "Custom User Agent",
        "Accept-Language": "en-US,en;q=0.9"
    }
) as crawler:
    result = await crawler.arun(url="https://example.com")
```

### 3. Content Selection & Filtering
The library offers multiple ways to select and filter content, from CSS selectors to word count thresholds.

```python
# CSS Selector and Content Filtering
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        css_selector="article.main-content",  # Extract specific content
        word_count_threshold=10,              # Minimum words per block
        excluded_tags=['form', 'header'],     # Tags to exclude
        exclude_external_links=True,          # Remove external links
        exclude_social_media_links=True,      # Remove social media links
        exclude_domains=["pinterest.com", "facebook.com"]  # Exclude specific domains
    )

# Custom HTML to Text Options
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        html2text={
            "escape_dot": False,
            "links_each_paragraph": True,
            "protect_links": True
        }
    )
```

### 4. Dynamic Content Handling
The library provides sophisticated handling of dynamic content with JavaScript execution and wait conditions.

```python
# JavaScript Execution and Wait Conditions
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        js_code=[
            "window.scrollTo(0, document.body.scrollHeight);",
            "document.querySelector('.load-more').click();"
        ],
        wait_for="css:.dynamic-content",  # Wait for element
        delay_before_return_html=2.0      # Wait after JS execution
    )

# Smart Wait Conditions
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        wait_for="""() => {
            return document.querySelectorAll('.item').length > 10;
        }""",
        page_timeout=60000  # 60 seconds timeout
    )
```

### 5. Advanced Link Analysis
The library provides comprehensive link analysis capabilities, distinguishing between internal and external links, with options for filtering and processing.

```python
# Basic Link Analysis
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
    
    # Access internal and external links
    for internal_link in result.links['internal']:
        print(f"Internal: {internal_link['href']} - {internal_link['text']}")
    
    for external_link in result.links['external']:
        print(f"External: {external_link['href']} - {external_link['text']}")

# Advanced Link Filtering
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        exclude_external_links=True,          # Remove all external links
        exclude_social_media_links=True,      # Remove social media links
        exclude_social_media_domains=[                # Custom social media domains
            "facebook.com", "twitter.com", "instagram.com"
        ],
        exclude_domains=["pinterest.com"]     # Specific domains to exclude
    )
```

### 6. Anti-Bot Protection Handling
The library includes sophisticated anti-detection mechanisms to handle websites with bot protection.

```python
# Basic Anti-Detection
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        simulate_user=True,        # Simulate human behavior
        override_navigator=True    # Override navigator properties
    )

# Advanced Anti-Detection with Magic Mode
async with AsyncWebCrawler(headless=False) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        magic=True,               # Enable all anti-detection features
        remove_overlay_elements=True,  # Remove popups/modals automatically
        # Custom navigator properties
        js_code="""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
    )
```

### 7. Session Management
Session management allows maintaining state across multiple requests and handling cookies.

```python
# Basic Session Management
async with AsyncWebCrawler() as crawler:
    session_id = "my_session"
    
    # Login
    login_result = await crawler.arun(
        url="https://example.com/login",
        session_id=session_id,
        js_code="document.querySelector('form').submit();"
    )
    
    # Use same session for subsequent requests
    protected_result = await crawler.arun(
        url="https://example.com/protected",
        session_id=session_id
    )
    
    # Clean up session
    await crawler.crawler_strategy.kill_session(session_id)

# Advanced Session with Custom Cookies
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        session_id="custom_session",
        cookies=[{
            "name": "sessionId",
            "value": "abc123",
            "domain": "example.com"
        }]
    )
```

### 8. Screenshot and Media Handling
The library provides comprehensive media handling capabilities, including screenshots and media content extraction.

```python
# Screenshot Capture
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        screenshot=True,
        screenshot_wait_for=2.0  # Wait before taking screenshot
    )
    
    # Save screenshot
    if result.screenshot:
        with open("screenshot.png", "wb") as f:
            f.write(base64.b64decode(result.screenshot))

# Media Extraction
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
    
    # Process images with metadata
    for image in result.media['images']:
        print(f"Image: {image['src']}")
        print(f"Alt text: {image['alt']}")
        print(f"Context: {image['desc']}")
        print(f"Relevance score: {image['score']}")
    
    # Process videos and audio
    for video in result.media['videos']:
        print(f"Video: {video['src']}")
    for audio in result.media['audios']:
        print(f"Audio: {audio['src']}")
```

### 9. Structured Data Extraction & Chunking
The library supports multiple strategies for structured data extraction and content chunking.

```python
# LLM-based Extraction
class NewsArticle(BaseModel):
    title: str
    content: str
    author: str

extraction_strategy = LLMExtractionStrategy(
    provider='openai/gpt-4',
    api_token="your-token",
    schema=NewsArticle.schema(),
    instruction="Extract news article details",
    chunk_token_threshold=1000,
    overlap_rate=0.1
)

# CSS-based Extraction
schema = {
    "name": "Product Listing",
    "baseSelector": ".product-card",
    "fields": [
        {
            "name": "title",
            "selector": "h2",
            "type": "text"
        },
        {
            "name": "price",
            "selector": ".price",
            "type": "text",
            "transform": "strip"
        }
    ]
}

css_strategy = JsonCssExtractionStrategy(schema)

# Text Chunking
from crawl4ai.chunking_strategy import OverlappingWindowChunking

chunking_strategy = OverlappingWindowChunking(
    window_size=1000,
    overlap=100
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        extraction_strategy=extraction_strategy,
        chunking_strategy=chunking_strategy
    )
```


### 10. Content Cleaning & Processing
The library provides extensive content cleaning and processing capabilities, ensuring high-quality output in various formats.

```python
# Basic Content Cleaning
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        remove_overlay_elements=True,  # Remove popups/modals
        process_iframes=True,          # Process iframe content
        word_count_threshold=10        # Minimum words per block
    )
    
    print(result.cleaned_html)    # Clean HTML
    print(result.fit_html)        # Most relevant HTML content
    print(result.fit_markdown)    # Most relevant markdown content

# Advanced Content Processing
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        excluded_tags=['form', 'header', 'footer', 'nav'],
        html2text={
            "escape_dot": False,
            "body_width": 0,
            "protect_links": True,
            "unicode_snob": True,
            "ignore_links": False,
            "ignore_images": False,
            "ignore_emphasis": False,
            "bypass_tables": False,
            "ignore_tables": False
        }
    )
```

### Advanced Usage Patterns

#### 1. Combining Multiple Features
```python
async with AsyncWebCrawler(
    browser_type="chromium",
    headless=False,
    verbose=True
) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        # Anti-bot measures
        magic=True,
        simulate_user=True,
        
        # Content selection
        css_selector="article.main",
        word_count_threshold=10,
        
        # Dynamic content handling
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        wait_for="css:.dynamic-content",
        
        # Content filtering
        exclude_external_links=True,
        exclude_social_media_links=True,
        
        # Media handling
        screenshot=True,
        process_iframes=True,
        
        # Content cleaning
        remove_overlay_elements=True
    )
```

#### 2. Custom Extraction Pipeline
```python
# Define custom schemas and strategies
class Article(BaseModel):
    title: str
    content: str
    date: str

# CSS extraction for initial content
css_schema = {
    "name": "Article Extraction",
    "baseSelector": "article",
    "fields": [
        {"name": "title", "selector": "h1", "type": "text"},
        {"name": "content", "selector": ".content", "type": "html"},
        {"name": "date", "selector": ".date", "type": "text"}
    ]
}

# LLM processing for semantic analysis
llm_strategy = LLMExtractionStrategy(
    provider="ollama/nemotron",
    api_token="your-token",
    schema=Article.schema(),
    instruction="Extract and clean article content"
)

# Chunking strategy for large content
chunking = OverlappingWindowChunking(window_size=1000, overlap=100)

async with AsyncWebCrawler() as crawler:
    # First pass: Extract structure
    css_result = await crawler.arun(
        url="https://example.com",
        extraction_strategy=JsonCssExtractionStrategy(css_schema)
    )
    
    # Second pass: Semantic processing
    llm_result = await crawler.arun(
        url="https://example.com",
        extraction_strategy=llm_strategy,
        chunking_strategy=chunking
    )
```

#### 3. Website Crawling with Custom Processing
```python
class CustomWebsiteCrawler:
    def __init__(self, crawler: AsyncWebCrawler):
        self.crawler = crawler
        self.results = {}

    async def process_page(self, url: str) -> Dict:
        result = await self.crawler.arun(
            url=url,
            magic=True,
            word_count_threshold=10,
            exclude_external_links=True,
            process_iframes=True,
            remove_overlay_elements=True
        )
        
        # Process internal links
        internal_links = [
            link['href'] for link in result.links['internal']
            if self._is_valid_link(link['href'])
        ]
        
        # Extract media
        media_urls = [img['src'] for img in result.media['images']]
        
        return {
            'content': result.markdown,
            'links': internal_links,
            'media': media_urls,
            'metadata': result.metadata
        }

    async def crawl_website(self, start_url: str, max_depth: int = 2):
        visited = set()
        queue = [(start_url, 0)]
        
        while queue:
            url, depth = queue.pop(0)
            if depth > max_depth or url in visited:
                continue
                
            visited.add(url)
            self.results[url] = await self.process_page(url)
```

