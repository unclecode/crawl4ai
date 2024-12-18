# Content Selection

Crawl4AI provides multiple ways to select and filter specific content from webpages. Learn how to precisely target the content you need.

## CSS Selectors

The simplest way to extract specific content:

```python
# Extract specific content using CSS selector
result = await crawler.arun(
    url="https://example.com",
    css_selector=".main-article"  # Target main article content
)

# Multiple selectors
result = await crawler.arun(
    url="https://example.com",
    css_selector="article h1, article .content"  # Target heading and content
)
```

## Content Filtering

Control what content is included or excluded:

```python
result = await crawler.arun(
    url="https://example.com",
    # Content thresholds
    word_count_threshold=10,        # Minimum words per block
    
    # Tag exclusions
    excluded_tags=['form', 'header', 'footer', 'nav'],
    
    # Link filtering
    exclude_external_links=True,    # Remove external links
    exclude_social_media_links=True,  # Remove social media links
    
    # Media filtering
    exclude_external_images=True   # Remove external images
)
```

## Iframe Content

Process content inside iframes:

```python
result = await crawler.arun(
    url="https://example.com",
    process_iframes=True,  # Extract iframe content
    remove_overlay_elements=True  # Remove popups/modals that might block iframes
)
```

## Structured Content Selection

### Using LLMs for Smart Selection

Use LLMs to intelligently extract specific types of content:

```python
from pydantic import BaseModel
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class ArticleContent(BaseModel):
    title: str
    main_points: List[str]
    conclusion: str

strategy = LLMExtractionStrategy(
    provider="ollama/nemotron",  # Works with any supported LLM
    schema=ArticleContent.schema(),
    instruction="Extract the main article title, key points, and conclusion"
)

result = await crawler.arun(
    url="https://example.com",
    extraction_strategy=strategy
)
article = json.loads(result.extracted_content)
```

### Pattern-Based Selection

For repeated content patterns (like product listings, news feeds):

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "name": "News Articles",
    "baseSelector": "article.news-item",  # Repeated element
    "fields": [
        {"name": "headline", "selector": "h2", "type": "text"},
        {"name": "summary", "selector": ".summary", "type": "text"},
        {"name": "category", "selector": ".category", "type": "text"},
        {
            "name": "metadata",
            "type": "nested",
            "fields": [
                {"name": "author", "selector": ".author", "type": "text"},
                {"name": "date", "selector": ".date", "type": "text"}
            ]
        }
    ]
}

strategy = JsonCssExtractionStrategy(schema)
result = await crawler.arun(
    url="https://example.com",
    extraction_strategy=strategy
)
articles = json.loads(result.extracted_content)
```

## Domain-Based Filtering

Control content based on domains:

```python
result = await crawler.arun(
    url="https://example.com",
    exclude_domains=["ads.com", "tracker.com"],
    exclude_social_media_domains=["facebook.com", "twitter.com"],  # Custom social media domains to exclude
    exclude_social_media_links=True
)
```

## Media Selection

Select specific types of media:

```python
result = await crawler.arun(url="https://example.com")

# Access different media types
images = result.media["images"]  # List of image details
videos = result.media["videos"]  # List of video details
audios = result.media["audios"]  # List of audio details

# Image with metadata
for image in images:
    print(f"URL: {image['src']}")
    print(f"Alt text: {image['alt']}")
    print(f"Description: {image['desc']}")
    print(f"Relevance score: {image['score']}")
```

## Comprehensive Example

Here's how to combine different selection methods:

```python
async def extract_article_content(url: str):
    # Define structured extraction
    article_schema = {
        "name": "Article",
        "baseSelector": "article.main",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": ".content", "type": "text"}
        ]
    }
    
    # Define LLM extraction
    class ArticleAnalysis(BaseModel):
        key_points: List[str]
        sentiment: str
        category: str

    async with AsyncWebCrawler() as crawler:
        # Get structured content
        pattern_result = await crawler.arun(
            url=url,
            extraction_strategy=JsonCssExtractionStrategy(article_schema),
            word_count_threshold=10,
            excluded_tags=['nav', 'footer'],
            exclude_external_links=True
        )
        
        # Get semantic analysis
        analysis_result = await crawler.arun(
            url=url,
            extraction_strategy=LLMExtractionStrategy(
                provider="ollama/nemotron",
                schema=ArticleAnalysis.schema(),
                instruction="Analyze the article content"
            )
        )
        
        # Combine results
        return {
            "article": json.loads(pattern_result.extracted_content),
            "analysis": json.loads(analysis_result.extracted_content),
            "media": pattern_result.media
        }
```