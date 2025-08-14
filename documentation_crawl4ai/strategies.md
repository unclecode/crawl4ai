[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/api/strategies/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * [URL Seeding](https://docs.crawl4ai.com/core/url-seeding/)
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * [Fit Markdown](https://docs.crawl4ai.com/core/fit-markdown/)
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * [SSL Certificate](https://docs.crawl4ai.com/advanced/ssl-certificate/)
    * [Network & Console Capture](https://docs.crawl4ai.com/advanced/network-console-capture/)
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * Strategies
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [Extraction & Chunking Strategies API](https://docs.crawl4ai.com/api/strategies/#extraction-chunking-strategies-api)
  * [Extraction Strategies](https://docs.crawl4ai.com/api/strategies/#extraction-strategies)
  * [Chunking Strategies](https://docs.crawl4ai.com/api/strategies/#chunking-strategies)
  * [Usage Examples](https://docs.crawl4ai.com/api/strategies/#usage-examples)
  * [Best Practices](https://docs.crawl4ai.com/api/strategies/#best-practices)


# Extraction & Chunking Strategies API
This documentation covers the API reference for extraction and chunking strategies in Crawl4AI.
## Extraction Strategies
All extraction strategies inherit from the base `ExtractionStrategy` class and implement two key methods: - `extract(url: str, html: str) -> List[Dict[str, Any]]` - `run(url: str, sections: List[str]) -> List[Dict[str, Any]]`
### LLMExtractionStrategy
Used for extracting structured data using Language Models.
```
LLMExtractionStrategy(
    # Required Parameters
    provider: str = DEFAULT_PROVIDER,     # LLM provider (e.g., "ollama/llama2")
    api_token: Optional[str] = None,      # API token

    # Extraction Configuration
    instruction: str = None,              # Custom extraction instruction
    schema: Dict = None,                  # Pydantic model schema for structured data
    extraction_type: str = "block",       # "block" or "schema"

    # Chunking Parameters
    chunk_token_threshold: int = 4000,    # Maximum tokens per chunk
    overlap_rate: float = 0.1,           # Overlap between chunks
    word_token_rate: float = 0.75,       # Word to token conversion rate
    apply_chunking: bool = True,         # Enable/disable chunking

    # API Configuration
    base_url: str = None,                # Base URL for API
    extra_args: Dict = {},               # Additional provider arguments
    verbose: bool = False                # Enable verbose logging
)
Copy
```

### RegexExtractionStrategy
Used for fast pattern-based extraction of common entities using regular expressions.
```
RegexExtractionStrategy(
    # Pattern Configuration
    pattern: IntFlag = RegexExtractionStrategy.Nothing,  # Bit flags of built-in patterns to use
    custom: Optional[Dict[str, str]] = None,           # Custom pattern dictionary {label: regex}

    # Input Format
    input_format: str = "fit_html",                    # "html", "markdown", "text" or "fit_html"
)

# Built-in Patterns as Bit Flags
RegexExtractionStrategy.Email           # Email addresses
RegexExtractionStrategy.PhoneIntl       # International phone numbers
RegexExtractionStrategy.PhoneUS         # US-format phone numbers
RegexExtractionStrategy.Url             # HTTP/HTTPS URLs
RegexExtractionStrategy.IPv4            # IPv4 addresses
RegexExtractionStrategy.IPv6            # IPv6 addresses
RegexExtractionStrategy.Uuid            # UUIDs
RegexExtractionStrategy.Currency        # Currency values (USD, EUR, etc)
RegexExtractionStrategy.Percentage      # Percentage values
RegexExtractionStrategy.Number          # Numeric values
RegexExtractionStrategy.DateIso         # ISO format dates
RegexExtractionStrategy.DateUS          # US format dates
RegexExtractionStrategy.Time24h         # 24-hour format times
RegexExtractionStrategy.PostalUS        # US postal codes
RegexExtractionStrategy.PostalUK        # UK postal codes
RegexExtractionStrategy.HexColor        # HTML hex color codes
RegexExtractionStrategy.TwitterHandle   # Twitter handles
RegexExtractionStrategy.Hashtag         # Hashtags
RegexExtractionStrategy.MacAddr         # MAC addresses
RegexExtractionStrategy.Iban            # International bank account numbers
RegexExtractionStrategy.CreditCard      # Credit card numbers
RegexExtractionStrategy.All             # All available patterns
Copy
```

### CosineStrategy
Used for content similarity-based extraction and clustering.
```
CosineStrategy(
    # Content Filtering
    semantic_filter: str = None,        # Topic/keyword filter
    word_count_threshold: int = 10,     # Minimum words per cluster
    sim_threshold: float = 0.3,         # Similarity threshold

    # Clustering Parameters
    max_dist: float = 0.2,             # Maximum cluster distance
    linkage_method: str = 'ward',       # Clustering method
    top_k: int = 3,                    # Top clusters to return

    # Model Configuration
    model_name: str = 'sentence-transformers/all-MiniLM-L6-v2',  # Embedding model

    verbose: bool = False              # Enable verbose logging
)
Copy
```

### JsonCssExtractionStrategy
Used for CSS selector-based structured data extraction.
```
JsonCssExtractionStrategy(
    schema: Dict[str, Any],    # Extraction schema
    verbose: bool = False      # Enable verbose logging
)

# Schema Structure
schema = {
    "name": str,              # Schema name
    "baseSelector": str,      # Base CSS selector
    "fields": [               # List of fields to extract
        {
            "name": str,      # Field name
            "selector": str,  # CSS selector
            "type": str,     # Field type: "text", "attribute", "html", "regex"
            "attribute": str, # For type="attribute"
            "pattern": str,  # For type="regex"
            "transform": str, # Optional: "lowercase", "uppercase", "strip"
            "default": Any    # Default value if extraction fails
        }
    ]
}
Copy
```

## Chunking Strategies
All chunking strategies inherit from `ChunkingStrategy` and implement the `chunk(text: str) -> list` method.
### RegexChunking
Splits text based on regex patterns.
```
RegexChunking(
    patterns: List[str] = None  # Regex patterns for splitting
                               # Default: [r'\n\n']
)
Copy
```

### SlidingWindowChunking
Creates overlapping chunks with a sliding window approach.
```
SlidingWindowChunking(
    window_size: int = 100,    # Window size in words
    step: int = 50             # Step size between windows
)
Copy
```

### OverlappingWindowChunking
Creates chunks with specified overlap.
```
OverlappingWindowChunking(
    window_size: int = 1000,   # Chunk size in words
    overlap: int = 100         # Overlap size in words
)
Copy
```

## Usage Examples
### LLM Extraction
```
from pydantic import BaseModel
from crawl4ai import LLMExtractionStrategy
from crawl4ai import LLMConfig

# Define schema
class Article(BaseModel):
    title: str
    content: str
    author: str

# Create strategy
strategy = LLMExtractionStrategy(
    llm_config = LLMConfig(provider="ollama/llama2"),
    schema=Article.schema(),
    instruction="Extract article details"
)

# Use with crawler
result = await crawler.arun(
    url="https://example.com/article",
    extraction_strategy=strategy
)

# Access extracted data
data = json.loads(result.extracted_content)
Copy
```

### Regex Extraction
```
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, RegexExtractionStrategy

# Method 1: Use built-in patterns
strategy = RegexExtractionStrategy(
    pattern = RegexExtractionStrategy.Email | RegexExtractionStrategy.Url
)

# Method 2: Use custom patterns
price_pattern = {"usd_price": r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?"}
strategy = RegexExtractionStrategy(custom=price_pattern)

# Method 3: Generate pattern with LLM assistance (one-time)
from crawl4ai import LLMConfig

async with AsyncWebCrawler() as crawler:
    # Get sample HTML first
    sample_result = await crawler.arun("https://example.com/products")
    html = sample_result.fit_html

    # Generate regex pattern once
    pattern = RegexExtractionStrategy.generate_pattern(
        label="price",
        html=html,
        query="Product prices in USD format",
        llm_config=LLMConfig(provider="openai/gpt-4o-mini")
    )

    # Save pattern for reuse
    import json
    with open("price_pattern.json", "w") as f:
        json.dump(pattern, f)

    # Use pattern for extraction (no LLM calls)
    strategy = RegexExtractionStrategy(custom=pattern)
    result = await crawler.arun(
        url="https://example.com/products",
        config=CrawlerRunConfig(extraction_strategy=strategy)
    )

    # Process results
    data = json.loads(result.extracted_content)
    for item in data:
        print(f"{item['label']}: {item['value']}")
Copy
```

### CSS Extraction
```
from crawl4ai import JsonCssExtractionStrategy

# Define schema
schema = {
    "name": "Product List",
    "baseSelector": ".product-card",
    "fields": [
        {
            "name": "title",
            "selector": "h2.title",
            "type": "text"
        },
        {
            "name": "price",
            "selector": ".price",
            "type": "text",
            "transform": "strip"
        },
        {
            "name": "image",
            "selector": "img",
            "type": "attribute",
            "attribute": "src"
        }
    ]
}

# Create and use strategy
strategy = JsonCssExtractionStrategy(schema)
result = await crawler.arun(
    url="https://example.com/products",
    extraction_strategy=strategy
)
Copy
```

### Content Chunking
```
from crawl4ai.chunking_strategy import OverlappingWindowChunking
from crawl4ai import LLMConfig

# Create chunking strategy
chunker = OverlappingWindowChunking(
    window_size=500,  # 500 words per chunk
    overlap=50        # 50 words overlap
)

# Use with extraction strategy
strategy = LLMExtractionStrategy(
    llm_config = LLMConfig(provider="ollama/llama2"),
    chunking_strategy=chunker
)

result = await crawler.arun(
    url="https://example.com/long-article",
    extraction_strategy=strategy
)
Copy
```

## Best Practices
  1. **Choose the Right Strategy**
  2. Use `RegexExtractionStrategy` for common data types like emails, phones, URLs, dates
  3. Use `JsonCssExtractionStrategy` for well-structured HTML with consistent patterns
  4. Use `LLMExtractionStrategy` for complex, unstructured content requiring reasoning
  5. Use `CosineStrategy` for content similarity and clustering
  6. **Strategy Selection Guide**
```
Is the target data a common type (email/phone/date/URL)?
→ RegexExtractionStrategy

Does the page have consistent HTML structure?
→ JsonCssExtractionStrategy or JsonXPathExtractionStrategy

Is the data semantically complex or unstructured?
→ LLMExtractionStrategy

Need to find content similar to a specific topic?
→ CosineStrategy
Copy
```

  7. **Optimize Chunking**
```
# For long documents
strategy = LLMExtractionStrategy(
    chunk_token_threshold=2000,  # Smaller chunks
    overlap_rate=0.1           # 10% overlap
)
Copy
```

  8. **Combine Strategies for Best Performance**
```
# First pass: Extract structure with CSS
css_strategy = JsonCssExtractionStrategy(product_schema)
css_result = await crawler.arun(url, config=CrawlerRunConfig(extraction_strategy=css_strategy))
product_data = json.loads(css_result.extracted_content)

# Second pass: Extract specific fields with regex
descriptions = [product["description"] for product in product_data]
regex_strategy = RegexExtractionStrategy(
    pattern=RegexExtractionStrategy.Email | RegexExtractionStrategy.PhoneUS,
    custom={"dimension": r"\d+x\d+x\d+ (?:cm|in)"}
)

# Process descriptions with regex
for text in descriptions:
    matches = regex_strategy.extract("", text)  # Direct extraction
Copy
```

  9. **Handle Errors**
```
try:
    result = await crawler.arun(
        url="https://example.com",
        extraction_strategy=strategy
    )
    if result.success:
        content = json.loads(result.extracted_content)
except Exception as e:
    print(f"Extraction failed: {e}")
Copy
```

  10. **Monitor Performance**
```
strategy = CosineStrategy(
    verbose=True,  # Enable logging
    word_count_threshold=20,  # Filter short content
    top_k=5  # Limit results
)
Copy
```

  11. **Cache Generated Patterns**
```
# For RegexExtractionStrategy pattern generation
import json
from pathlib import Path

cache_dir = Path("./pattern_cache")
cache_dir.mkdir(exist_ok=True)
pattern_file = cache_dir / "product_pattern.json"

if pattern_file.exists():
    with open(pattern_file) as f:
        pattern = json.load(f)
else:
    # Generate once with LLM
    pattern = RegexExtractionStrategy.generate_pattern(...)
    with open(pattern_file, "w") as f:
        json.dump(pattern, f)
Copy
```



#### On this page
  * [Extraction Strategies](https://docs.crawl4ai.com/api/strategies/#extraction-strategies)
  * [LLMExtractionStrategy](https://docs.crawl4ai.com/api/strategies/#llmextractionstrategy)
  * [RegexExtractionStrategy](https://docs.crawl4ai.com/api/strategies/#regexextractionstrategy)
  * [CosineStrategy](https://docs.crawl4ai.com/api/strategies/#cosinestrategy)
  * [JsonCssExtractionStrategy](https://docs.crawl4ai.com/api/strategies/#jsoncssextractionstrategy)
  * [Chunking Strategies](https://docs.crawl4ai.com/api/strategies/#chunking-strategies)
  * [RegexChunking](https://docs.crawl4ai.com/api/strategies/#regexchunking)
  * [SlidingWindowChunking](https://docs.crawl4ai.com/api/strategies/#slidingwindowchunking)
  * [OverlappingWindowChunking](https://docs.crawl4ai.com/api/strategies/#overlappingwindowchunking)
  * [Usage Examples](https://docs.crawl4ai.com/api/strategies/#usage-examples)
  * [LLM Extraction](https://docs.crawl4ai.com/api/strategies/#llm-extraction)
  * [Regex Extraction](https://docs.crawl4ai.com/api/strategies/#regex-extraction)
  * [CSS Extraction](https://docs.crawl4ai.com/api/strategies/#css-extraction)
  * [Content Chunking](https://docs.crawl4ai.com/api/strategies/#content-chunking)
  * [Best Practices](https://docs.crawl4ai.com/api/strategies/#best-practices)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
