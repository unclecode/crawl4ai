# Extraction Strategies Overview

Crawl4AI provides powerful extraction strategies to help you get structured data from web pages. Each strategy is designed for specific use cases and offers different approaches to data extraction.

## Available Strategies

### [LLM-Based Extraction](llm.md)

`LLMExtractionStrategy` uses Language Models to extract structured data from web content. This approach is highly flexible and can understand content semantically.

```python
from pydantic import BaseModel
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class Product(BaseModel):
    name: str
    price: float
    description: str

strategy = LLMExtractionStrategy(
    provider="ollama/llama2",
    schema=Product.schema(),
    instruction="Extract product details from the page"
)

result = await crawler.arun(
    url="https://example.com/product",
    extraction_strategy=strategy
)
```

**Best for:**
- Complex data structures
- Content requiring interpretation
- Flexible content formats
- Natural language processing

### [CSS-Based Extraction](css.md)

`JsonCssExtractionStrategy` extracts data using CSS selectors. This is fast, reliable, and perfect for consistently structured pages.

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "name": "Product Listing",
    "baseSelector": ".product-card",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
        {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"}
    ]
}

strategy = JsonCssExtractionStrategy(schema)

result = await crawler.arun(
    url="https://example.com/products",
    extraction_strategy=strategy
)
```

**Best for:**
- E-commerce product listings
- News article collections
- Structured content pages
- High-performance needs

### [Cosine Strategy](cosine.md)

`CosineStrategy` uses similarity-based clustering to identify and extract relevant content sections.

```python
from crawl4ai.extraction_strategy import CosineStrategy

strategy = CosineStrategy(
    semantic_filter="product reviews",    # Content focus
    word_count_threshold=10,             # Minimum words per cluster
    sim_threshold=0.3,                   # Similarity threshold
    max_dist=0.2,                        # Maximum cluster distance
    top_k=3                             # Number of top clusters to extract
)

result = await crawler.arun(
    url="https://example.com/reviews",
    extraction_strategy=strategy
)
```

**Best for:**
- Content similarity analysis
- Topic clustering
- Relevant content extraction
- Pattern recognition in text

## Strategy Selection Guide

Choose your strategy based on these factors:

1. **Content Structure**
   - Well-structured HTML → Use CSS Strategy
   - Natural language text → Use LLM Strategy
   - Mixed/Complex content → Use Cosine Strategy

2. **Performance Requirements**
   - Fastest: CSS Strategy
   - Moderate: Cosine Strategy
   - Variable: LLM Strategy (depends on provider)

3. **Accuracy Needs**
   - Highest structure accuracy: CSS Strategy
   - Best semantic understanding: LLM Strategy
   - Best content relevance: Cosine Strategy

## Combining Strategies

You can combine strategies for more powerful extraction:

```python
# First use CSS strategy for initial structure
css_result = await crawler.arun(
    url="https://example.com",
    extraction_strategy=css_strategy
)

# Then use LLM for semantic analysis
llm_result = await crawler.arun(
    url="https://example.com",
    extraction_strategy=llm_strategy
)
```

## Common Use Cases

1. **E-commerce Scraping**
   ```python
   # CSS Strategy for product listings
   schema = {
       "name": "Products",
       "baseSelector": ".product",
       "fields": [
           {"name": "name", "selector": ".title", "type": "text"},
           {"name": "price", "selector": ".price", "type": "text"}
       ]
   }
   ```

2. **News Article Extraction**
   ```python
   # LLM Strategy for article content
   class Article(BaseModel):
       title: str
       content: str
       author: str
       date: str

   strategy = LLMExtractionStrategy(
       provider="ollama/llama2",
       schema=Article.schema()
   )
   ```

3. **Content Analysis**
   ```python
   # Cosine Strategy for topic analysis
   strategy = CosineStrategy(
       semantic_filter="technology trends",
       top_k=5
   )
   ```

## Best Practices

1. **Choose the Right Strategy**
   - Start with CSS for structured data
   - Use LLM for complex interpretation
   - Try Cosine for content relevance

2. **Optimize Performance**
   - Cache LLM results
   - Keep CSS selectors specific
   - Tune similarity thresholds

3. **Handle Errors**
   ```python
   result = await crawler.arun(
       url="https://example.com",
       extraction_strategy=strategy
   )
   
   if not result.success:
       print(f"Extraction failed: {result.error_message}")
   else:
       data = json.loads(result.extracted_content)
   ```

Each strategy has its strengths and optimal use cases. Explore the detailed documentation for each strategy to learn more about their specific features and configurations.