# Output Formats

Crawl4AI provides multiple output formats to suit different needs, from raw HTML to structured data using LLM or pattern-based extraction.

## Basic Formats

```python
result = await crawler.arun(url="https://example.com")

# Access different formats
raw_html = result.html           # Original HTML
clean_html = result.cleaned_html # Sanitized HTML
markdown = result.markdown       # Standard markdown
fit_md = result.fit_markdown    # Most relevant content in markdown
```

## Raw HTML

Original, unmodified HTML from the webpage. Useful when you need to:
- Preserve the exact page structure
- Process HTML with your own tools
- Debug page issues

```python
result = await crawler.arun(url="https://example.com")
print(result.html)  # Complete HTML including headers, scripts, etc.
```

## Cleaned HTML

Sanitized HTML with unnecessary elements removed. Automatically:
- Removes scripts and styles
- Cleans up formatting
- Preserves semantic structure

```python
result = await crawler.arun(
    url="https://example.com",
    excluded_tags=['form', 'header', 'footer'],  # Additional tags to remove
    keep_data_attributes=False  # Remove data-* attributes
)
print(result.cleaned_html)
```

## Standard Markdown

HTML converted to clean markdown format. Great for:
- Content analysis
- Documentation
- Readability

```python
result = await crawler.arun(
    url="https://example.com",
    include_links_on_markdown=True  # Include links in markdown
)
print(result.markdown)
```

## Fit Markdown

Most relevant content extracted and converted to markdown. Ideal for:
- Article extraction
- Main content focus
- Removing boilerplate

```python
result = await crawler.arun(url="https://example.com")
print(result.fit_markdown)  # Only the main content
```

## Structured Data Extraction

Crawl4AI offers two powerful approaches for structured data extraction:

### 1. LLM-Based Extraction

Use any LLM (OpenAI, HuggingFace, Ollama, etc.) to extract structured data with high accuracy:

```python
from pydantic import BaseModel
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class KnowledgeGraph(BaseModel):
    entities: List[dict]
    relationships: List[dict]

strategy = LLMExtractionStrategy(
    provider="ollama/nemotron",  # or "huggingface/...", "ollama/..."
    api_token="your-token",   # not needed for Ollama
    schema=KnowledgeGraph.schema(),
    instruction="Extract entities and relationships from the content"
)

result = await crawler.arun(
    url="https://example.com",
    extraction_strategy=strategy
)
knowledge_graph = json.loads(result.extracted_content)
```

### 2. Pattern-Based Extraction

For pages with repetitive patterns (e.g., product listings, article feeds), use JsonCssExtractionStrategy:

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "name": "Product Listing",
    "baseSelector": ".product-card",  # Repeated element
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
        {"name": "description", "selector": ".desc", "type": "text"}
    ]
}

strategy = JsonCssExtractionStrategy(schema)
result = await crawler.arun(
    url="https://example.com",
    extraction_strategy=strategy
)
products = json.loads(result.extracted_content)
```

## Content Customization

### HTML to Text Options

Configure markdown conversion:

```python
result = await crawler.arun(
    url="https://example.com",
    html2text={
        "escape_dot": False,
        "body_width": 0,
        "protect_links": True,
        "unicode_snob": True
    }
)
```

### Content Filters

Control what content is included:

```python
result = await crawler.arun(
    url="https://example.com",
    word_count_threshold=10,        # Minimum words per block
    exclude_external_links=True,    # Remove external links
    exclude_external_images=True,   # Remove external images
    excluded_tags=['form', 'nav']   # Remove specific HTML tags
)
```

## Comprehensive Example

Here's how to use multiple output formats together:

```python
async def crawl_content(url: str):
    async with AsyncWebCrawler() as crawler:
        # Extract main content with fit markdown
        result = await crawler.arun(
            url=url,
            word_count_threshold=10,
            exclude_external_links=True
        )
        
        # Get structured data using LLM
        llm_result = await crawler.arun(
            url=url,
            extraction_strategy=LLMExtractionStrategy(
                provider="ollama/nemotron",
                schema=YourSchema.schema(),
                instruction="Extract key information"
            )
        )
        
        # Get repeated patterns (if any)
        pattern_result = await crawler.arun(
            url=url,
            extraction_strategy=JsonCssExtractionStrategy(your_schema)
        )
        
        return {
            "main_content": result.fit_markdown,
            "structured_data": json.loads(llm_result.extracted_content),
            "pattern_data": json.loads(pattern_result.extracted_content),
            "media": result.media
        }
```