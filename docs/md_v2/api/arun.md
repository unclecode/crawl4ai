# Complete Parameter Guide for arun()

The following parameters can be passed to the `arun()` method. They are organized by their primary usage context and functionality.

## Core Parameters

```python
await crawler.arun(
    url="https://example.com",   # Required: URL to crawl
    verbose=True,               # Enable detailed logging
    bypass_cache=False,         # Skip cache for this request
    warmup=True                # Whether to run warmup check
)
```

## Content Processing Parameters

### Text Processing
```python
await crawler.arun(
    word_count_threshold=10,                # Minimum words per content block
    image_description_min_word_threshold=5,  # Minimum words for image descriptions
    only_text=False,                        # Extract only text content
    excluded_tags=['form', 'nav'],          # HTML tags to exclude
    keep_data_attributes=False,             # Preserve data-* attributes
)
```

### Content Selection
```python
await crawler.arun(
    css_selector=".main-content",  # CSS selector for content extraction
    remove_forms=True,             # Remove all form elements
    remove_overlay_elements=True,  # Remove popups/modals/overlays
)
```

### Link Handling
```python
await crawler.arun(
    exclude_external_links=True,          # Remove external links
    exclude_social_media_links=True,      # Remove social media links
    exclude_external_images=True,         # Remove external images
    exclude_domains=["ads.example.com"],  # Specific domains to exclude
    social_media_domains=[               # Additional social media domains
        "facebook.com",
        "twitter.com",
        "instagram.com"
    ]
)
```

## Browser Control Parameters

### Basic Browser Settings
```python
await crawler.arun(
    headless=True,                # Run browser in headless mode
    browser_type="chromium",      # Browser engine: "chromium", "firefox", "webkit"
    page_timeout=60000,          # Page load timeout in milliseconds
    user_agent="custom-agent",    # Custom user agent
)
```

### Navigation and Waiting
```python
await crawler.arun(
    wait_for="css:.dynamic-content",  # Wait for element/condition
    delay_before_return_html=2.0,     # Wait before returning HTML (seconds)
)
```

### JavaScript Execution
```python
await crawler.arun(
    js_code=[                     # JavaScript to execute (string or list)
        "window.scrollTo(0, document.body.scrollHeight);",
        "document.querySelector('.load-more').click();"
    ],
    js_only=False,               # Only execute JavaScript without reloading page
)
```

### Anti-Bot Features
```python
await crawler.arun(
    magic=True,              # Enable all anti-detection features
    simulate_user=True,      # Simulate human behavior
    override_navigator=True  # Override navigator properties
)
```

### Session Management
```python
await crawler.arun(
    session_id="my_session",  # Session identifier for persistent browsing
)
```

### Screenshot Options
```python
await crawler.arun(
    screenshot=True,              # Take page screenshot
    screenshot_wait_for=2.0,      # Wait before screenshot (seconds)
)
```

### Proxy Configuration
```python
await crawler.arun(
    proxy="http://proxy.example.com:8080",     # Simple proxy URL
    proxy_config={                             # Advanced proxy settings
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass"
    }
)
```

## Content Extraction Parameters

### Extraction Strategy
```python
await crawler.arun(
    extraction_strategy=LLMExtractionStrategy(
        provider="ollama/llama2",
        schema=MySchema.schema(),
        instruction="Extract specific data"
    )
)
```

### Chunking Strategy
```python
await crawler.arun(
    chunking_strategy=RegexChunking(
        patterns=[r'\n\n', r'\.\s+']
    )
)
```

### HTML to Text Options
```python
await crawler.arun(
    html2text={
        "ignore_links": False,
        "ignore_images": False,
        "escape_dot": False,
        "body_width": 0,
        "protect_links": True,
        "unicode_snob": True
    }
)
```

## Debug Options
```python
await crawler.arun(
    log_console=True,   # Log browser console messages
)
```

## Parameter Interactions and Notes

1. **Magic Mode Combinations**
   ```python
   # Full anti-detection setup
   await crawler.arun(
       magic=True,
       headless=False,
       simulate_user=True,
       override_navigator=True
   )
   ```

2. **Dynamic Content Handling**
   ```python
   # Handle lazy-loaded content
   await crawler.arun(
       js_code="window.scrollTo(0, document.body.scrollHeight);",
       wait_for="css:.lazy-content",
       delay_before_return_html=2.0
   )
   ```

3. **Content Extraction Pipeline**
   ```python
   # Complete extraction setup
   await crawler.arun(
       css_selector=".main-content",
       word_count_threshold=20,
       extraction_strategy=my_strategy,
       chunking_strategy=my_chunking,
       process_iframes=True,
       remove_overlay_elements=True
   )
   ```

## Best Practices

1. **Performance Optimization**
   ```python
   await crawler.arun(
       bypass_cache=False,           # Use cache when possible
       word_count_threshold=10,      # Filter out noise
       process_iframes=False         # Skip iframes if not needed
   )
   ```

2. **Reliable Scraping**
   ```python
   await crawler.arun(
       magic=True,                   # Enable anti-detection
       delay_before_return_html=1.0, # Wait for dynamic content
       page_timeout=60000           # Longer timeout for slow pages
   )
   ```

3. **Clean Content**
   ```python
   await crawler.arun(
       remove_overlay_elements=True,  # Remove popups
       excluded_tags=['nav', 'aside'],# Remove unnecessary elements
       keep_data_attributes=False     # Remove data attributes
   )
   ```