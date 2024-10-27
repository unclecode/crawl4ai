# AsyncWebCrawler

The `AsyncWebCrawler` class is the main interface for web crawling operations. It provides asynchronous web crawling capabilities with extensive configuration options.

## Constructor

```python
AsyncWebCrawler(
    # Browser Settings
    browser_type: str = "chromium",         # Options: "chromium", "firefox", "webkit"
    headless: bool = True,                  # Run browser in headless mode
    verbose: bool = False,                  # Enable verbose logging
    
    # Cache Settings
    always_by_pass_cache: bool = False,     # Always bypass cache
    base_directory: str = str(Path.home()), # Base directory for cache
    
    # Network Settings
    proxy: str = None,                      # Simple proxy URL
    proxy_config: Dict = None,              # Advanced proxy configuration
    
    # Browser Behavior
    sleep_on_close: bool = False,           # Wait before closing browser
    
    # Custom Settings
    user_agent: str = None,                 # Custom user agent
    headers: Dict[str, str] = {},           # Custom HTTP headers
    js_code: Union[str, List[str]] = None,  # Default JavaScript to execute
)
```

### Parameters in Detail

#### Browser Settings

- **browser_type** (str, optional)
  - Default: `"chromium"`
  - Options: `"chromium"`, `"firefox"`, `"webkit"`
  - Controls which browser engine to use
  ```python
  # Example: Using Firefox
  crawler = AsyncWebCrawler(browser_type="firefox")
  ```

- **headless** (bool, optional)
  - Default: `True`
  - When `True`, browser runs without GUI
  - Set to `False` for debugging
  ```python
  # Visible browser for debugging
  crawler = AsyncWebCrawler(headless=False)
  ```

- **verbose** (bool, optional)
  - Default: `False`
  - Enables detailed logging
  ```python
  # Enable detailed logging
  crawler = AsyncWebCrawler(verbose=True)
  ```

#### Cache Settings

- **always_by_pass_cache** (bool, optional)
  - Default: `False`
  - When `True`, always fetches fresh content
  ```python
  # Always fetch fresh content
  crawler = AsyncWebCrawler(always_by_pass_cache=True)
  ```

- **base_directory** (str, optional)
  - Default: User's home directory
  - Base path for cache storage
  ```python
  # Custom cache directory
  crawler = AsyncWebCrawler(base_directory="/path/to/cache")
  ```

#### Network Settings

- **proxy** (str, optional)
  - Simple proxy URL
  ```python
  # Using simple proxy
  crawler = AsyncWebCrawler(proxy="http://proxy.example.com:8080")
  ```

- **proxy_config** (Dict, optional)
  - Advanced proxy configuration with authentication
  ```python
  # Advanced proxy with auth
  crawler = AsyncWebCrawler(proxy_config={
      "server": "http://proxy.example.com:8080",
      "username": "user",
      "password": "pass"
  })
  ```

#### Browser Behavior

- **sleep_on_close** (bool, optional)
  - Default: `False`
  - Adds delay before closing browser
  ```python
  # Wait before closing
  crawler = AsyncWebCrawler(sleep_on_close=True)
  ```

#### Custom Settings

- **user_agent** (str, optional)
  - Custom user agent string
  ```python
  # Custom user agent
  crawler = AsyncWebCrawler(
      user_agent="Mozilla/5.0 (Custom Agent) Chrome/90.0"
  )
  ```

- **headers** (Dict[str, str], optional)
  - Custom HTTP headers
  ```python
  # Custom headers
  crawler = AsyncWebCrawler(
      headers={
          "Accept-Language": "en-US",
          "Custom-Header": "Value"
      }
  )
  ```

- **js_code** (Union[str, List[str]], optional)
  - Default JavaScript to execute on each page
  ```python
  # Default JavaScript
  crawler = AsyncWebCrawler(
      js_code=[
          "window.scrollTo(0, document.body.scrollHeight);",
          "document.querySelector('.load-more').click();"
      ]
  )
  ```

## Methods

### arun()

The primary method for crawling web pages.

```python
async def arun(
    # Required
    url: str,                              # URL to crawl
    
    # Content Selection
    css_selector: str = None,              # CSS selector for content
    word_count_threshold: int = 10,        # Minimum words per block
    
    # Cache Control
    bypass_cache: bool = False,            # Bypass cache for this request
    
    # Session Management
    session_id: str = None,                # Session identifier
    
    # Screenshot Options
    screenshot: bool = False,              # Take screenshot
    screenshot_wait_for: float = None,     # Wait before screenshot
    
    # Content Processing
    process_iframes: bool = False,         # Process iframe content
    remove_overlay_elements: bool = False, # Remove popups/modals
    
    # Anti-Bot Settings
    simulate_user: bool = False,           # Simulate human behavior
    override_navigator: bool = False,      # Override navigator properties
    magic: bool = False,                   # Enable all anti-detection
    
    # Content Filtering
    excluded_tags: List[str] = None,       # HTML tags to exclude
    exclude_external_links: bool = False,  # Remove external links
    exclude_social_media_links: bool = False, # Remove social media links
    
    # JavaScript Handling
    js_code: Union[str, List[str]] = None, # JavaScript to execute
    wait_for: str = None,                  # Wait condition
    
    # Page Loading
    page_timeout: int = 60000,            # Page load timeout (ms)
    delay_before_return_html: float = None, # Wait before return
    
    # Extraction
    extraction_strategy: ExtractionStrategy = None  # Extraction strategy
) -> CrawlResult:
```

### Usage Examples

#### Basic Crawling
```python
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
```

#### Advanced Crawling
```python
async with AsyncWebCrawler(
    browser_type="firefox",
    verbose=True,
    headers={"Custom-Header": "Value"}
) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        css_selector=".main-content",
        word_count_threshold=20,
        process_iframes=True,
        magic=True,
        wait_for="css:.dynamic-content",
        screenshot=True
    )
```

#### Session Management
```python
async with AsyncWebCrawler() as crawler:
    # First request
    result1 = await crawler.arun(
        url="https://example.com/login",
        session_id="my_session"
    )
    
    # Subsequent request using same session
    result2 = await crawler.arun(
        url="https://example.com/protected",
        session_id="my_session"
    )
```

## Context Manager

AsyncWebCrawler implements the async context manager protocol:

```python
async def __aenter__(self) -> 'AsyncWebCrawler':
    # Initialize browser and resources
    return self

async def __aexit__(self, *args):
    # Cleanup resources
    pass
```

Always use AsyncWebCrawler with async context manager:
```python
async with AsyncWebCrawler() as crawler:
    # Your crawling code here
    pass
```

## Best Practices

1. **Resource Management**
```python
# Always use context manager
async with AsyncWebCrawler() as crawler:
    # Crawler will be properly cleaned up
    pass
```

2. **Error Handling**
```python
try:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        if not result.success:
            print(f"Crawl failed: {result.error_message}")
except Exception as e:
    print(f"Error: {str(e)}")
```

3. **Performance Optimization**
```python
# Enable caching for better performance
crawler = AsyncWebCrawler(
    always_by_pass_cache=False,
    verbose=True
)
```

4. **Anti-Detection**
```python
# Maximum stealth
crawler = AsyncWebCrawler(
    headless=True,
    user_agent="Mozilla/5.0...",
    headers={"Accept-Language": "en-US"}
)
result = await crawler.arun(
    url="https://example.com",
    magic=True,
    simulate_user=True
)
```

## Note on Browser Types

Each browser type has its characteristics:

- **chromium**: Best overall compatibility
- **firefox**: Good for specific use cases
- **webkit**: Lighter weight, good for basic crawling

Choose based on your specific needs:
```python
# High compatibility
crawler = AsyncWebCrawler(browser_type="chromium")

# Memory efficient
crawler = AsyncWebCrawler(browser_type="webkit")
```