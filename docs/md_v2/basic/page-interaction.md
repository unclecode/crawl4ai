# Page Interaction

Crawl4AI provides powerful features for interacting with dynamic webpages, handling JavaScript execution, and managing page events.

## JavaScript Execution

### Basic Execution

```python
# Single JavaScript command
result = await crawler.arun(
    url="https://example.com",
    js_code="window.scrollTo(0, document.body.scrollHeight);"
)

# Multiple commands
js_commands = [
    "window.scrollTo(0, document.body.scrollHeight);",
    "document.querySelector('.load-more').click();",
    "document.querySelector('#consent-button').click();"
]
result = await crawler.arun(
    url="https://example.com",
    js_code=js_commands
)
```

## Wait Conditions

### CSS-Based Waiting

Wait for elements to appear:

```python
result = await crawler.arun(
    url="https://example.com",
    wait_for="css:.dynamic-content"  # Wait for element with class 'dynamic-content'
)
```

### JavaScript-Based Waiting

Wait for custom conditions:

```python
# Wait for number of elements
wait_condition = """() => {
    return document.querySelectorAll('.item').length > 10;
}"""

result = await crawler.arun(
    url="https://example.com",
    wait_for=f"js:{wait_condition}"
)

# Wait for dynamic content to load
wait_for_content = """() => {
    const content = document.querySelector('.content');
    return content && content.innerText.length > 100;
}"""

result = await crawler.arun(
    url="https://example.com",
    wait_for=f"js:{wait_for_content}"
)
```

## Handling Dynamic Content

### Load More Content

Handle infinite scroll or load more buttons:

```python
# Scroll and wait pattern
result = await crawler.arun(
    url="https://example.com",
    js_code=[
        # Scroll to bottom
        "window.scrollTo(0, document.body.scrollHeight);",
        # Click load more if exists
        "const loadMore = document.querySelector('.load-more'); if(loadMore) loadMore.click();"
    ],
    # Wait for new content
    wait_for="js:() => document.querySelectorAll('.item').length > previousCount"
)
```

### Form Interaction

Handle forms and inputs:

```python
js_form_interaction = """
    // Fill form fields
    document.querySelector('#search').value = 'search term';
    // Submit form
    document.querySelector('form').submit();
"""

result = await crawler.arun(
    url="https://example.com",
    js_code=js_form_interaction,
    wait_for="css:.results"  # Wait for results to load
)
```

## Timing Control

### Delays and Timeouts

Control timing of interactions:

```python
result = await crawler.arun(
    url="https://example.com",
    page_timeout=60000,              # Page load timeout (ms)
    delay_before_return_html=2.0,    # Wait before capturing content
)
```

## Complex Interactions Example

Here's an example of handling a dynamic page with multiple interactions:

```python
async def crawl_dynamic_content():
    async with AsyncWebCrawler() as crawler:
        # Initial page load
        result = await crawler.arun(
            url="https://example.com",
            # Handle cookie consent
            js_code="document.querySelector('.cookie-accept')?.click();",
            wait_for="css:.main-content"
        )

        # Load more content
        session_id = "dynamic_session"  # Keep session for multiple interactions
        
        for page in range(3):  # Load 3 pages of content
            result = await crawler.arun(
                url="https://example.com",
                session_id=session_id,
                js_code=[
                    # Scroll to bottom
                    "window.scrollTo(0, document.body.scrollHeight);",
                    # Store current item count
                    "window.previousCount = document.querySelectorAll('.item').length;",
                    # Click load more
                    "document.querySelector('.load-more')?.click();"
                ],
                # Wait for new items
                wait_for="""() => {
                    const currentCount = document.querySelectorAll('.item').length;
                    return currentCount > window.previousCount;
                }""",
                # Only execute JS without reloading page
                js_only=True if page > 0 else False
            )
            
            # Process content after each load
            print(f"Page {page + 1} items:", len(result.cleaned_html))
            
        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
```

## Using with Extraction Strategies

Combine page interaction with structured extraction:

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy

# Pattern-based extraction after interaction
schema = {
    "name": "Dynamic Items",
    "baseSelector": ".item",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "description", "selector": ".desc", "type": "text"}
    ]
}

result = await crawler.arun(
    url="https://example.com",
    js_code="window.scrollTo(0, document.body.scrollHeight);",
    wait_for="css:.item:nth-child(10)",  # Wait for 10 items
    extraction_strategy=JsonCssExtractionStrategy(schema)
)

# Or use LLM to analyze dynamic content
class ContentAnalysis(BaseModel):
    topics: List[str]
    summary: str

result = await crawler.arun(
    url="https://example.com",
    js_code="document.querySelector('.show-more').click();",
    wait_for="css:.full-content",
    extraction_strategy=LLMExtractionStrategy(
        provider="ollama/nemotron",
        schema=ContentAnalysis.schema(),
        instruction="Analyze the full content"
    )
)
```