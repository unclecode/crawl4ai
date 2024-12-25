# Crawl4AI Content Selection (LLM-Friendly Reference)

> Minimal, code-oriented reference for selecting and filtering webpage content using Crawl4AI.

## Quick Start

```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler

async def run():
    config = CrawlerRunConfig(css_selector=".main-article")
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        print(result.extracted_content)
```

## CSS Selectors

- Use `css_selector="selector"` to target specific content.

```python
config = CrawlerRunConfig(css_selector="article h1, article .content")
result = await crawler.arun(url="...", config=config)
```

## Content Filtering

- `word_count_threshold`: int
- `excluded_tags`: list of tags
- `exclude_external_links`: bool
- `exclude_social_media_links`: bool
- `exclude_external_images`: bool

```python
config = CrawlerRunConfig(
    word_count_threshold=10,
    excluded_tags=["form","header","footer","nav"],
    exclude_external_links=True,
    exclude_social_media_links=True,
    exclude_external_images=True
)
```

## Iframe Content

- `process_iframes`: bool
- `remove_overlay_elements`: bool

```python
config = CrawlerRunConfig(
    process_iframes=True,
    remove_overlay_elements=True
)
```

## LLM-Based Extraction

- Use `LLMExtractionStrategy(provider="...")` with `schema=...` and `instruction="..."`

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel

class ArticleContent(BaseModel):
    title: str
    main_points: list[str]
    conclusion: str

strategy = LLMExtractionStrategy(
    provider="ollama/nemotron",
    schema=ArticleContent.schema(),
    instruction="Extract title, points, conclusion"
)

config = CrawlerRunConfig(extraction_strategy=strategy)
```

## Pattern-Based Selection (JsonCssExtractionStrategy)

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "name": "News Articles",
    "baseSelector": "article.news-item",
    "fields": [
        {"name":"headline","selector":"h2","type":"text"},
        {"name":"summary","selector":".summary","type":"text"},
        {"name":"category","selector":".category","type":"text"},
        {
            "name":"metadata",
            "type":"nested",
            "fields":[
                {"name":"author","selector":".author","type":"text"},
                {"name":"date","selector":".date","type":"text"}
            ]
        }
    ]
}

config = CrawlerRunConfig(extraction_strategy=JsonCssExtractionStrategy(schema))
```

## Combined Example

```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

article_schema = {
    "name":"Article",
    "baseSelector":"article.main",
    "fields":[
        {"name":"title","selector":"h1","type":"text"},
        {"name":"content","selector":".content","type":"text"}
    ]
}

config = CrawlerRunConfig(
    extraction_strategy=JsonCssExtractionStrategy(article_schema),
    word_count_threshold=10,
    excluded_tags=["nav","footer"],
    exclude_external_links=True
)
```

## Optional

- [async_webcrawler.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/async_webcrawler.py)
- [async_crawler_strategy.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/async_crawler_strategy.py)