# Extraction Strategies (Condensed LLM-Friendly Reference)

> Extract structured data (JSON) and text blocks from HTML with LLM-based or clustering methods.

Streamlined parameters, usage, and code snippets for quick LLM reference.

## Input Formats

- **markdown** (default): Raw markdown from HTML
- **html**: Raw HTML content
- **fit_markdown**: Cleaned markdown (needs markdown_generator + content_filter)

```python
strategy = LLMExtractionStrategy(
    input_format="html",  # Choose format
    provider="openai/gpt-4",
    instruction="Extract data"
)

config = CrawlerRunConfig(
    extraction_strategy=strategy,
    markdown_generator=DefaultMarkdownGenerator(),  # For fit_markdown
    content_filter=PruningContentFilter()          # For fit_markdown
)
```

## LLMExtractionStrategy

- Uses LLM to extract structured data from HTML.
- Supports `instruction`, `schema`, `extraction_type`, `chunk_token_threshold`, `overlap_rate`, `input_format`.
```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
strategy = LLMExtractionStrategy(
    provider="openai",
    api_token="your_api_token",
    instruction="Extract prices",
    schema={"fields": [...]},
    extraction_type="schema",
    input_format="html"
)
```

## CosineStrategy

- Clusters content via semantic embeddings.
- Key params: `semantic_filter`, `word_count_threshold`, `sim_threshold`, `top_k`.
```python
from crawl4ai.extraction_strategy import CosineStrategy
strategy = CosineStrategy(
    semantic_filter="product reviews",
    word_count_threshold=20,
    sim_threshold=0.3,
    top_k=5
)
```

## JsonCssExtractionStrategy

- Extracts data using CSS selectors.
- `schema` defines `baseSelector`, `fields`.
```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
schema = {
  "baseSelector": ".product",
  "fields": [
    {"name":"title","selector":"h2","type":"text"},
    {"name":"price","selector":".price","type":"text"}
  ]
}
strategy = JsonCssExtractionStrategy(schema=schema)
```

## JsonXPathExtractionStrategy

- Similar to CSS but uses XPath.
- More stable against changing class names.
```python
from crawl4ai.extraction_strategy import JsonXPathExtractionStrategy
schema = {
  "baseSelector": "//div[@class='product']",
  "fields": [
    {"name":"title","selector":".//h2","type":"text"},
    {"name":"price","selector":".//span[@class='price']","type":"text"}
  ]
}
strategy = JsonXPathExtractionStrategy(schema=schema)
```

## Example Usage

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

config = CrawlerRunConfig(extraction_strategy=strategy)
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com", config=config)
    print(result.extracted_content)
```

## Optional

- [extraction_strategies.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/extraction_strategies.py)