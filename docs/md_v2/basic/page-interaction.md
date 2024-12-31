# Page Interaction

Crawl4AI provides powerful features for interacting with dynamic webpages, handling JavaScript execution, and managing page events.

## JavaScript Execution

### Basic Execution

```python
from crawl4ai.async_configs import CrawlerRunConfig

# Single JavaScript command
config = CrawlerRunConfig(
    js_code="window.scrollTo(0, document.body.scrollHeight);"
)
result = await crawler.arun(url="https://example.com", config=config)

# Multiple commands
js_commands = [
    "window.scrollTo(0, document.body.scrollHeight);",
    "document.querySelector('.load-more').click();",
    "document.querySelector('#consent-button').click();"
]
config = CrawlerRunConfig(js_code=js_commands)
result = await crawler.arun(url="https://example.com", config=config)
```

## Wait Conditions

### CSS-Based Waiting

Wait for elements to appear:

```python
config = CrawlerRunConfig(wait_for="css:.dynamic-content")  # Wait for element with class 'dynamic-content'
result = await crawler.arun(url="https://example.com", config=config)
```

### JavaScript-Based Waiting

Wait for custom conditions:

```python
# Wait for number of elements
wait_condition = """() => {
    return document.querySelectorAll('.item').length > 10;
}"""

config = CrawlerRunConfig(wait_for=f"js:{wait_condition}")
result = await crawler.arun(url="https://example.com", config=config)

# Wait for dynamic content to load
wait_for_content = """() => {
    const content = document.querySelector('.content');
    return content && content.innerText.length > 100;
}"""

config = CrawlerRunConfig(wait_for=f"js:{wait_for_content}")
result = await crawler.arun(url="https://example.com", config=config)
```

## Handling Dynamic Content

### Load More Content

Handle infinite scroll or load more buttons:

```python
config = CrawlerRunConfig(
    js_code=[
        "window.scrollTo(0, document.body.scrollHeight);",  # Scroll to bottom
        "const loadMore = document.querySelector('.load-more'); if(loadMore) loadMore.click();"  # Click load more
    ],
    wait_for="js:() => document.querySelectorAll('.item').length > previousCount"  # Wait for new content
)
result = await crawler.arun(url="https://example.com", config=config)
```

### Form Interaction

Handle forms and inputs:

```python
js_form_interaction = """
    document.querySelector('#search').value = 'search term';  // Fill form fields
    document.querySelector('form').submit();                 // Submit form
"""

config = CrawlerRunConfig(
    js_code=js_form_interaction,
    wait_for="css:.results"  # Wait for results to load
)
result = await crawler.arun(url="https://example.com", config=config)
```

## Timing Control

### Delays and Timeouts

Control timing of interactions:

```python
config = CrawlerRunConfig(
    page_timeout=60000,              # Page load timeout (ms)
    delay_before_return_html=2.0     # Wait before capturing content
)
result = await crawler.arun(url="https://example.com", config=config)
```

## Complex Interactions Example

Here's an example of handling a dynamic page with multiple interactions:

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def crawl_dynamic_content():
    async with AsyncWebCrawler() as crawler:
        # Initial page load
        config = CrawlerRunConfig(
            js_code="document.querySelector('.cookie-accept')?.click();",  # Handle cookie consent
            wait_for="css:.main-content"
        )
        result = await crawler.arun(url="https://example.com", config=config)

        # Load more content
        session_id = "dynamic_session"  # Keep session for multiple interactions
        
        for page in range(3):  # Load 3 pages of content
            config = CrawlerRunConfig(
                session_id=session_id,
                js_code=[
                    "window.scrollTo(0, document.body.scrollHeight);",  # Scroll to bottom
                    "window.previousCount = document.querySelectorAll('.item').length;",  # Store item count
                    "document.querySelector('.load-more')?.click();"   # Click load more
                ],
                wait_for="""() => {
                    const currentCount = document.querySelectorAll('.item').length;
                    return currentCount > window.previousCount;
                }""",
                js_only=(page > 0)  # Execute JS without reloading page for subsequent interactions
            )
            result = await crawler.arun(url="https://example.com", config=config)
            print(f"Page {page + 1} items:", len(result.cleaned_html))

        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
```

## Using with Extraction Strategies

Combine page interaction with structured extraction:

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig

# Pattern-based extraction after interaction
schema = {
    "name": "Dynamic Items",
    "baseSelector": ".item",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "description", "selector": ".desc", "type": "text"}
    ]
}

config = CrawlerRunConfig(
    js_code="window.scrollTo(0, document.body.scrollHeight);",
    wait_for="css:.item:nth-child(10)",  # Wait for 10 items
    extraction_strategy=JsonCssExtractionStrategy(schema)
)
result = await crawler.arun(url="https://example.com", config=config)

# Or use LLM to analyze dynamic content
class ContentAnalysis(BaseModel):
    topics: List[str]
    summary: str

config = CrawlerRunConfig(
    js_code="document.querySelector('.show-more').click();",
    wait_for="css:.full-content",
    extraction_strategy=LLMExtractionStrategy(
        provider="ollama/nemotron",
        schema=ContentAnalysis.schema(),
        instruction="Analyze the full content"
    )
)
result = await crawler.arun(url="https://example.com", config=config)
```
