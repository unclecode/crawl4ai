### Content Selection

Crawl4AI provides multiple ways to select and filter specific content from webpages. Learn how to precisely target the content you need.

#### CSS Selectors

Extract specific content using a `CrawlerRunConfig` with CSS selectors:

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig(css_selector=".main-article")  # Target main article content
result = await crawler.arun(url="https://crawl4ai.com", config=config)

config = CrawlerRunConfig(css_selector="article h1, article .content")  # Target heading and content
result = await crawler.arun(url="https://crawl4ai.com", config=config)
```

#### Content Filtering

Control content inclusion or exclusion with `CrawlerRunConfig`:

```python
config = CrawlerRunConfig(
    word_count_threshold=10,        # Minimum words per block
    excluded_tags=['form', 'header', 'footer', 'nav'],  # Excluded tags
    exclude_external_links=True,    # Remove external links
    exclude_social_media_links=True,  # Remove social media links
    exclude_external_images=True   # Remove external images
)

result = await crawler.arun(url="https://crawl4ai.com", config=config)
```

#### Iframe Content

Process iframe content by enabling specific options in `CrawlerRunConfig`:

```python
config = CrawlerRunConfig(
    process_iframes=True,          # Extract iframe content
    remove_overlay_elements=True  # Remove popups/modals that might block iframes
)

result = await crawler.arun(url="https://crawl4ai.com", config=config)
```

#### Structured Content Selection Using LLMs

Leverage LLMs for intelligent content extraction:

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel
from typing import List

class ArticleContent(BaseModel):
    title: str
    main_points: List[str]
    conclusion: str

strategy = LLMExtractionStrategy(
    provider="ollama/nemotron",
    schema=ArticleContent.schema(),
    instruction="Extract the main article title, key points, and conclusion"
)

config = CrawlerRunConfig(extraction_strategy=strategy)

result = await crawler.arun(url="https://crawl4ai.com", config=config)
article = json.loads(result.extracted_content)
```

#### Pattern-Based Selection

Extract content matching repetitive patterns:

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "name": "News Articles",
    "baseSelector": "article.news-item",
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
config = CrawlerRunConfig(extraction_strategy=strategy)

result = await crawler.arun(url="https://crawl4ai.com", config=config)
articles = json.loads(result.extracted_content)
```

#### Comprehensive Example

Combine different selection methods using `CrawlerRunConfig`:

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

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

    # Define configuration
    config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(article_schema),
        word_count_threshold=10,
        excluded_tags=['nav', 'footer'],
        exclude_external_links=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return json.loads(result.extracted_content)
```
