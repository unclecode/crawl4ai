### Extraction Strategies

#### 1. LLMExtractionStrategy
```python
LLMExtractionStrategy(
    # Core Parameters
    provider: str = DEFAULT_PROVIDER,  # LLM provider (e.g., "openai/gpt-4", "huggingface/...", "ollama/...")
    api_token: Optional[str] = None,  # API token for the provider
    instruction: str = None,  # Custom instruction for extraction
    schema: Dict = None,  # Pydantic model schema for structured extraction
    extraction_type: str = "block",  # Type of extraction: "block" or "schema"
    
    # Chunking Parameters
    chunk_token_threshold: int = CHUNK_TOKEN_THRESHOLD,  # Maximum tokens per chunk
    overlap_rate: float = OVERLAP_RATE,  # Overlap between chunks
    word_token_rate: float = WORD_TOKEN_RATE,  # Conversion rate from words to tokens
    apply_chunking: bool = True,  # Whether to apply text chunking
    
    # API Configuration
    base_url: str = None,  # Base URL for API calls
    api_base: str = None,  # Alternative base URL
    extra_args: Dict = {},  # Additional provider-specific arguments
    
    verbose: bool = False  # Enable verbose logging
)
```

Usage Example:
```python
class NewsArticle(BaseModel):
    title: str
    content: str

strategy = LLMExtractionStrategy(
    provider="ollama/nemotron",
    api_token="your-token",
    schema=NewsArticle.schema(),
    instruction="Extract news article content with title and main text"
)

result = await crawler.arun(url="https://example.com", extraction_strategy=strategy)
```

#### 2. JsonCssExtractionStrategy
```python
JsonCssExtractionStrategy(
    schema: Dict[str, Any],  # Schema defining extraction rules
    verbose: bool = False  # Enable verbose logging
)

# Schema Structure
schema = {
    "name": str,  # Name of the extraction schema
    "baseSelector": str,  # CSS selector for base elements
    "fields": [
        {
            "name": str,  # Field name
            "selector": str,  # CSS selector
            "type": str,  # Field type: "text", "attribute", "html", "regex", "nested", "list", "nested_list"
            "attribute": str,  # For type="attribute"
            "pattern": str,  # For type="regex"
            "transform": str,  # Optional: "lowercase", "uppercase", "strip"
            "default": Any,  # Default value if extraction fails
            "fields": List[Dict],  # For nested/list types
        }
    ]
}
```

Usage Example:
```python
schema = {
    "name": "News Articles",
    "baseSelector": "article.news-item",
    "fields": [
        {
            "name": "title",
            "selector": "h1",
            "type": "text",
            "transform": "strip"
        },
        {
            "name": "date",
            "selector": ".date",
            "type": "attribute",
            "attribute": "datetime"
        }
    ]
}

strategy = JsonCssExtractionStrategy(schema)
result = await crawler.arun(url="https://example.com", extraction_strategy=strategy)
```

#### 3. CosineStrategy
```python
CosineStrategy(
    # Content Filtering
    semantic_filter: str = None,  # Keyword filter for document filtering
    word_count_threshold: int = 10,  # Minimum words per cluster
    sim_threshold: float = 0.3,  # Similarity threshold for filtering
    
    # Clustering Parameters
    max_dist: float = 0.2,  # Maximum distance for clustering
    linkage_method: str = 'ward',  # Clustering linkage method
    top_k: int = 3,  # Number of top categories to extract
    
    # Model Configuration
    model_name: str = 'sentence-transformers/all-MiniLM-L6-v2',  # Embedding model
    
    verbose: bool = False  # Enable verbose logging
)
```

### Chunking Strategies

#### 1. RegexChunking
```python
RegexChunking(
    patterns: List[str] = None  # List of regex patterns for splitting text
    # Default pattern: [r'\n\n']
)
```

Usage Example:
```python
chunker = RegexChunking(patterns=[r'\n\n', r'\.\s+'])  # Split on double newlines and sentences
chunks = chunker.chunk(text)
```

#### 2. SlidingWindowChunking
```python
SlidingWindowChunking(
    window_size: int = 100,  # Size of the window in words
    step: int = 50,  # Number of words to slide the window
)
```

Usage Example:
```python
chunker = SlidingWindowChunking(window_size=200, step=100)
chunks = chunker.chunk(text)  # Creates overlapping chunks of 200 words, moving 100 words at a time
```

#### 3. OverlappingWindowChunking
```python
OverlappingWindowChunking(
    window_size: int = 1000,  # Size of each chunk in words
    overlap: int = 100  # Number of words to overlap between chunks
)
```

Usage Example:
```python
chunker = OverlappingWindowChunking(window_size=500, overlap=50)
chunks = chunker.chunk(text)  # Creates 500-word chunks with 50-word overlap
```
