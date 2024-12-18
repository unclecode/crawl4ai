# Browser Configuration

Crawl4AI supports multiple browser engines and offers extensive configuration options for browser behavior.

## Browser Types

Choose from three browser engines:

```python
# Chromium (default)
async with AsyncWebCrawler(browser_type="chromium") as crawler:
    result = await crawler.arun(url="https://example.com")

# Firefox
async with AsyncWebCrawler(browser_type="firefox") as crawler:
    result = await crawler.arun(url="https://example.com")

# WebKit
async with AsyncWebCrawler(browser_type="webkit") as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Basic Configuration

Common browser settings:

```python
async with AsyncWebCrawler(
    headless=True,           # Run in headless mode (no GUI)
    verbose=True,           # Enable detailed logging
    sleep_on_close=False    # No delay when closing browser
) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Identity Management

Control how your crawler appears to websites:

```python
# Custom user agent
async with AsyncWebCrawler(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
) as crawler:
    result = await crawler.arun(url="https://example.com")

# Custom headers
headers = {
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache"
}
async with AsyncWebCrawler(headers=headers) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Screenshot Capabilities

Capture page screenshots with enhanced error handling:

```python
result = await crawler.arun(
    url="https://example.com",
    screenshot=True,                # Enable screenshot
    screenshot_wait_for=2.0        # Wait 2 seconds before capture
)

if result.screenshot:  # Base64 encoded image
    import base64
    with open("screenshot.png", "wb") as f:
        f.write(base64.b64decode(result.screenshot))
```

## Timeouts and Waiting

Control page loading behavior:

```python
result = await crawler.arun(
    url="https://example.com",
    page_timeout=60000,              # Page load timeout (ms)
    delay_before_return_html=2.0,    # Wait before content capture
    wait_for="css:.dynamic-content"  # Wait for specific element
)
```

## JavaScript Execution

Execute custom JavaScript before crawling:

```python
# Single JavaScript command
result = await crawler.arun(
    url="https://example.com",
    js_code="window.scrollTo(0, document.body.scrollHeight);"
)

# Multiple commands
js_commands = [
    "window.scrollTo(0, document.body.scrollHeight);",
    "document.querySelector('.load-more').click();"
]
result = await crawler.arun(
    url="https://example.com",
    js_code=js_commands
)
```

## Proxy Configuration

Use proxies for enhanced access:

```python
# Simple proxy
async with AsyncWebCrawler(
    proxy="http://proxy.example.com:8080"
) as crawler:
    result = await crawler.arun(url="https://example.com")

# Proxy with authentication
proxy_config = {
    "server": "http://proxy.example.com:8080",
    "username": "user",
    "password": "pass"
}
async with AsyncWebCrawler(proxy_config=proxy_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Anti-Detection Features

Enable stealth features to avoid bot detection:

```python
result = await crawler.arun(
    url="https://example.com",
    simulate_user=True,        # Simulate human behavior
    override_navigator=True,   # Mask automation signals
    magic=True               # Enable all anti-detection features
)
```

## Handling Dynamic Content

Configure browser to handle dynamic content:

```python
# Wait for dynamic content
result = await crawler.arun(
    url="https://example.com",
    wait_for="js:() => document.querySelector('.content').children.length > 10",
    process_iframes=True     # Process iframe content
)

# Handle lazy-loaded images
result = await crawler.arun(
    url="https://example.com",
    js_code="window.scrollTo(0, document.body.scrollHeight);",
    delay_before_return_html=2.0  # Wait for images to load
)
```

## Comprehensive Example

Here's how to combine various browser configurations:

```python
async def crawl_with_advanced_config(url: str):
    async with AsyncWebCrawler(
        # Browser setup
        browser_type="chromium",
        headless=True,
        verbose=True,
        
        # Identity
        user_agent="Custom User Agent",
        headers={"Accept-Language": "en-US"},
        
        # Proxy setup
        proxy="http://proxy.example.com:8080"
    ) as crawler:
        result = await crawler.arun(
            url=url,
            # Content handling
            process_iframes=True,
            screenshot=True,
            
            # Timing
            page_timeout=60000,
            delay_before_return_html=2.0,
            
            # Anti-detection
            magic=True,
            simulate_user=True,
            
            # Dynamic content
            js_code=[
                "window.scrollTo(0, document.body.scrollHeight);",
                "document.querySelector('.load-more')?.click();"
            ],
            wait_for="css:.dynamic-content"
        )
        
        return {
            "content": result.markdown,
            "screenshot": result.screenshot,
            "success": result.success
        }
```