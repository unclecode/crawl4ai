### 1. Basic Web Crawling
```python
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
    print(result.markdown)  # Get clean markdown content
    print(result.html)      # Get raw HTML
    print(result.cleaned_html)  # Get cleaned HTML
```

### 2. Browser Control Options
- Multiple Browser Support
```python
# Choose between different browser engines
crawler = AsyncWebCrawler(browser_type="firefox")  # or "chromium", "webkit"
crawler = AsyncWebCrawler(headless=False)  # For visible browser
```

- Proxy Configuration
```python
crawler = AsyncWebCrawler(proxy="http://proxy.example.com:8080")
# Or with authentication
crawler = AsyncWebCrawler(proxy_config={
    "server": "http://proxy.example.com:8080",
    "username": "user",
    "password": "pass"
})
```

### 3. Content Selection & Filtering
- CSS Selector Support
```python
result = await crawler.arun(
    url="https://example.com",
    css_selector=".main-content"  # Extract specific content
)
```

- Content Filtering Options
```python
result = await crawler.arun(
    url="https://example.com",
    word_count_threshold=10,  # Minimum words per block
    excluded_tags=['form', 'header'],  # Tags to exclude
    exclude_external_links=True,  # Remove external links
    exclude_social_media_links=True,  # Remove social media links
    exclude_external_images=True  # Remove external images
)
```

### 4. Dynamic Content Handling
- JavaScript Execution
```python
result = await crawler.arun(
    url="https://example.com",
    js_code="window.scrollTo(0, document.body.scrollHeight)"  # Execute custom JS
)
```

- Wait Conditions
```python
result = await crawler.arun(
    url="https://example.com",
    wait_for="css:.my-element",  # Wait for element
    wait_for="js:() => document.readyState === 'complete'"  # Wait for condition
)
```

### 5. Anti-Bot Protection Handling
```python
result = await crawler.arun(
    url="https://example.com",
    simulate_user=True,  # Simulate human behavior
    override_navigator=True,  # Mask automation signals
    magic=True  # Enable all anti-detection features
)
```

### 6. Session Management
```python
session_id = "my_session"
result1 = await crawler.arun(url="https://example.com/page1", session_id=session_id)
result2 = await crawler.arun(url="https://example.com/page2", session_id=session_id)
await crawler.crawler_strategy.kill_session(session_id)
```

### 7. Media Handling
- Screenshot Capture
```python
result = await crawler.arun(
    url="https://example.com",
    screenshot=True
)
base64_screenshot = result.screenshot
```

- Media Extraction
```python
result = await crawler.arun(url="https://example.com")
print(result.media['images'])  # List of images
print(result.media['videos'])  # List of videos
print(result.media['audios'])  # List of audio files
```

### 8. Structured Data Extraction
- CSS-based Extraction
```python
schema = {
    "name": "News Articles",
    "baseSelector": "article",
    "fields": [
        {"name": "title", "selector": "h1", "type": "text"},
        {"name": "date", "selector": ".date", "type": "text"}
    ]
}
extraction_strategy = JsonCssExtractionStrategy(schema)
result = await crawler.arun(
    url="https://example.com",
    extraction_strategy=extraction_strategy
)
structured_data = json.loads(result.extracted_content)
```

- LLM-based Extraction (Multiple Providers)
```python
class NewsArticle(BaseModel):
    title: str
    summary: str

strategy = LLMExtractionStrategy(
    provider="ollama/nemotron",  # or "huggingface/...", "ollama/..."
    api_token="your-token",
    schema=NewsArticle.schema(),
    instruction="Extract news article details..."
)
result = await crawler.arun(
    url="https://example.com",
    extraction_strategy=strategy
)
```

### 9. Content Cleaning & Processing
```python
result = await crawler.arun(
    url="https://example.com",
    remove_overlay_elements=True,  # Remove popups/modals
    process_iframes=True,  # Process iframe content
)
print(result.fit_markdown)  # Get most relevant content
print(result.fit_html)     # Get cleaned HTML
```
