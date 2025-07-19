# Adaptive Web Crawling

## Introduction

Traditional web crawlers follow predetermined patterns, crawling pages blindly without knowing when they've gathered enough information. **Adaptive Crawling** changes this paradigm by introducing intelligence into the crawling process.

Think of it like research: when you're looking for information, you don't read every book in the library. You stop when you've found sufficient information to answer your question. That's exactly what Adaptive Crawling does for web scraping.

## Key Concepts

### The Problem It Solves

When crawling websites for specific information, you face two challenges:
1. **Under-crawling**: Stopping too early and missing crucial information
2. **Over-crawling**: Wasting resources by crawling irrelevant pages

Adaptive Crawling solves both by using a three-layer scoring system that determines when you have "enough" information.

### How It Works

The AdaptiveCrawler uses three metrics to measure information sufficiency:

- **Coverage**: How well your collected pages cover the query terms
- **Consistency**: Whether the information is coherent across pages  
- **Saturation**: Detecting when new pages aren't adding new information

When these metrics indicate sufficient information has been gathered, crawling stops automatically.

## Quick Start

### Basic Usage

```python
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        # Create an adaptive crawler (config is optional)
        adaptive = AdaptiveCrawler(crawler)
        
        # Start crawling with a query
        result = await adaptive.digest(
            start_url="https://docs.python.org/3/",
            query="async context managers"
        )
        
        # View statistics
        adaptive.print_stats()
        
        # Get the most relevant content
        relevant_pages = adaptive.get_relevant_content(top_k=5)
        for page in relevant_pages:
            print(f"- {page['url']} (score: {page['score']:.2f})")
```

### Configuration Options

```python
from crawl4ai import AdaptiveConfig

config = AdaptiveConfig(
    confidence_threshold=0.8,    # Stop when 80% confident (default: 0.7)
    max_pages=30,               # Maximum pages to crawl (default: 20)
    top_k_links=5,              # Links to follow per page (default: 3)
    min_gain_threshold=0.05     # Minimum expected gain to continue (default: 0.1)
)

adaptive = AdaptiveCrawler(crawler, config)
```

## Crawling Strategies

Adaptive Crawling supports two distinct strategies for determining information sufficiency:

### Statistical Strategy (Default)

The statistical strategy uses pure information theory and term-based analysis:

- **Fast and efficient** - No API calls or model loading
- **Term-based coverage** - Analyzes query term presence and distribution
- **No external dependencies** - Works offline
- **Best for**: Well-defined queries with specific terminology

```python
# Default configuration uses statistical strategy
config = AdaptiveConfig(
    strategy="statistical",  # This is the default
    confidence_threshold=0.8
)
```

### Embedding Strategy

The embedding strategy uses semantic embeddings for deeper understanding:

- **Semantic understanding** - Captures meaning beyond exact term matches
- **Query expansion** - Automatically generates query variations
- **Gap-driven selection** - Identifies semantic gaps in knowledge
- **Validation-based stopping** - Uses held-out queries to validate coverage
- **Best for**: Complex queries, ambiguous topics, conceptual understanding

```python
# Configure embedding strategy
config = AdaptiveConfig(
    strategy="embedding",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",  # Default
    n_query_variations=10,  # Generate 10 query variations
    embedding_min_confidence_threshold=0.1  # Stop if completely irrelevant
)

# With custom embedding provider (e.g., OpenAI)
config = AdaptiveConfig(
    strategy="embedding",
    embedding_llm_config={
        'provider': 'openai/text-embedding-3-small',
        'api_token': 'your-api-key'
    }
)
```

### Strategy Comparison

| Feature | Statistical | Embedding |
|---------|------------|-----------|
| **Speed** | Very fast | Moderate (API calls) |
| **Cost** | Free | Depends on provider |
| **Accuracy** | Good for exact terms | Excellent for concepts |
| **Dependencies** | None | Embedding model/API |
| **Query Understanding** | Literal | Semantic |
| **Best Use Case** | Technical docs, specific terms | Research, broad topics |

### Embedding Strategy Configuration

The embedding strategy offers fine-tuned control through several parameters:

```python
config = AdaptiveConfig(
    strategy="embedding",
    
    # Model configuration
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    embedding_llm_config=None,  # Use for API-based embeddings
    
    # Query expansion
    n_query_variations=10,  # Number of query variations to generate
    
    # Coverage parameters
    embedding_coverage_radius=0.2,  # Distance threshold for coverage
    embedding_k_exp=3.0,  # Exponential decay factor (higher = stricter)
    
    # Stopping criteria
    embedding_min_relative_improvement=0.1,  # Min improvement to continue
    embedding_validation_min_score=0.3,  # Min validation score
    embedding_min_confidence_threshold=0.1,  # Below this = irrelevant
    
    # Link selection
    embedding_overlap_threshold=0.85,  # Similarity for deduplication
    
    # Display confidence mapping
    embedding_quality_min_confidence=0.7,  # Min displayed confidence
    embedding_quality_max_confidence=0.95  # Max displayed confidence
)
```

### Handling Irrelevant Queries

The embedding strategy can detect when a query is completely unrelated to the content:

```python
# This will stop quickly with low confidence
result = await adaptive.digest(
    start_url="https://docs.python.org/3/",
    query="how to cook pasta"  # Irrelevant to Python docs
)

# Check if query was irrelevant
if result.metrics.get('is_irrelevant', False):
    print("Query is unrelated to the content!")
```

## When to Use Adaptive Crawling

### Perfect For:
- **Research Tasks**: Finding comprehensive information about a topic
- **Question Answering**: Gathering sufficient context to answer specific queries
- **Knowledge Base Building**: Creating focused datasets for AI/ML applications
- **Competitive Intelligence**: Collecting complete information about specific products/features

### Not Recommended For:
- **Full Site Archiving**: When you need every page regardless of content
- **Structured Data Extraction**: When targeting specific, known page patterns
- **Real-time Monitoring**: When you need continuous updates

## Understanding the Output

### Confidence Score

The confidence score (0-1) indicates how sufficient the gathered information is:
- **0.0-0.3**: Insufficient information, needs more crawling
- **0.3-0.6**: Partial information, may answer basic queries
- **0.6-0.7**: Good coverage, can answer most queries
- **0.7-1.0**: Excellent coverage, comprehensive information

### Statistics Display

```python
adaptive.print_stats(detailed=False)  # Summary table
adaptive.print_stats(detailed=True)   # Detailed metrics
```

The summary shows:
- Pages crawled vs. confidence achieved
- Coverage, consistency, and saturation scores
- Crawling efficiency metrics

## Persistence and Resumption

### Saving Progress

```python
config = AdaptiveConfig(
    save_state=True,
    state_path="my_crawl_state.json"
)

# Crawl will auto-save progress
result = await adaptive.digest(start_url, query)
```

### Resuming a Crawl

```python
# Resume from saved state
result = await adaptive.digest(
    start_url,
    query,
    resume_from="my_crawl_state.json"
)
```

### Exporting Knowledge Base

```python
# Export collected pages to JSONL
adaptive.export_knowledge_base("knowledge_base.jsonl")

# Import into another session
new_adaptive = AdaptiveCrawler(crawler)
new_adaptive.import_knowledge_base("knowledge_base.jsonl")
```

## Best Practices

### 1. Query Formulation
- Use specific, descriptive queries
- Include key terms you expect to find
- Avoid overly broad queries

### 2. Threshold Tuning
- Start with default (0.7) for general use
- Lower to 0.5-0.6 for exploratory crawling
- Raise to 0.8+ for exhaustive coverage

### 3. Performance Optimization
- Use appropriate `max_pages` limits
- Adjust `top_k_links` based on site structure
- Enable caching for repeat crawls

### 4. Link Selection
- The crawler prioritizes links based on:
  - Relevance to query
  - Expected information gain
  - URL structure and depth

## Examples

### Research Assistant

```python
# Gather information about a programming concept
result = await adaptive.digest(
    start_url="https://realpython.com",
    query="python decorators implementation patterns"
)

# Get the most relevant excerpts
for doc in adaptive.get_relevant_content(top_k=3):
    print(f"\nFrom: {doc['url']}")
    print(f"Relevance: {doc['score']:.2%}")
    print(doc['content'][:500] + "...")
```

### Knowledge Base Builder

```python
# Build a focused knowledge base about machine learning
queries = [
    "supervised learning algorithms",
    "neural network architectures", 
    "model evaluation metrics"
]

for query in queries:
    await adaptive.digest(
        start_url="https://scikit-learn.org/stable/",
        query=query
    )
    
# Export combined knowledge base
adaptive.export_knowledge_base("ml_knowledge.jsonl")
```

### API Documentation Crawler

```python
# Intelligently crawl API documentation
config = AdaptiveConfig(
    confidence_threshold=0.85,  # Higher threshold for completeness
    max_pages=30
)

adaptive = AdaptiveCrawler(crawler, config)
result = await adaptive.digest(
    start_url="https://api.example.com/docs",
    query="authentication endpoints rate limits"
)
```

## Next Steps

- Learn about [Advanced Adaptive Strategies](../advanced/adaptive-strategies.md)
- Explore the [AdaptiveCrawler API Reference](../api/adaptive-crawler.md)
- See more [Examples](https://github.com/unclecode/crawl4ai/tree/main/docs/examples/adaptive_crawling)

## FAQ

**Q: How is this different from traditional crawling?**
A: Traditional crawling follows fixed patterns (BFS/DFS). Adaptive crawling makes intelligent decisions about which links to follow and when to stop based on information gain.

**Q: Can I use this with JavaScript-heavy sites?**
A: Yes! AdaptiveCrawler inherits all capabilities from AsyncWebCrawler, including JavaScript execution.

**Q: How does it handle large websites?**
A: The algorithm naturally limits crawling to relevant sections. Use `max_pages` as a safety limit.

**Q: Can I customize the scoring algorithms?**
A: Advanced users can implement custom strategies. See [Adaptive Strategies](../advanced/adaptive-strategies.md).