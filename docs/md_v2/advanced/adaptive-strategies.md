# Advanced Adaptive Strategies

## Overview

While the default adaptive crawling configuration works well for most use cases, understanding the underlying strategies and scoring mechanisms allows you to fine-tune the crawler for specific domains and requirements.

## The Three-Layer Scoring System

### 1. Coverage Score

Coverage measures how comprehensively your knowledge base covers the query terms and related concepts.

#### Mathematical Foundation

```python
Coverage(K, Q) = Σ(t ∈ Q) score(t, K) / |Q|

where score(t, K) = doc_coverage(t) × (1 + freq_boost(t))
```

#### Components

- **Document Coverage**: Percentage of documents containing the term
- **Frequency Boost**: Logarithmic bonus for term frequency
- **Query Decomposition**: Handles multi-word queries intelligently

#### Tuning Coverage

```python
# For technical documentation with specific terminology
config = AdaptiveConfig(
    confidence_threshold=0.85,  # Require high coverage
    top_k_links=5              # Cast wider net
)

# For general topics with synonyms
config = AdaptiveConfig(
    confidence_threshold=0.6,   # Lower threshold
    top_k_links=2              # More focused
)
```

### 2. Consistency Score

Consistency evaluates whether the information across pages is coherent and non-contradictory.

#### How It Works

1. Extracts key statements from each document
2. Compares statements across documents
3. Measures agreement vs. contradiction
4. Returns normalized score (0-1)

#### Practical Impact

- **High consistency (>0.8)**: Information is reliable and coherent
- **Medium consistency (0.5-0.8)**: Some variation, but generally aligned
- **Low consistency (<0.5)**: Conflicting information, need more sources

### 3. Saturation Score

Saturation detects when new pages stop providing novel information.

#### Detection Algorithm

```python
# Tracks new unique terms per page
new_terms_page_1 = 50
new_terms_page_2 = 30  # 60% of first
new_terms_page_3 = 15  # 50% of second
new_terms_page_4 = 5   # 33% of third
# Saturation detected: rapidly diminishing returns
```

#### Configuration

```python
config = AdaptiveConfig(
    min_gain_threshold=0.1  # Stop if <10% new information
)
```

## Link Ranking Algorithm

### Expected Information Gain

Each uncrawled link is scored based on:

```python
ExpectedGain(link) = Relevance × Novelty × Authority
```

#### 1. Relevance Scoring

Uses BM25 algorithm on link preview text:

```python
relevance = BM25(link.preview_text, query)
```

Factors:
- Term frequency in preview
- Inverse document frequency
- Preview length normalization

#### 2. Novelty Estimation

Measures how different the link appears from already-crawled content:

```python
novelty = 1 - max_similarity(preview, knowledge_base)
```

Prevents crawling duplicate or highly similar pages.

#### 3. Authority Calculation

URL structure and domain analysis:

```python
authority = f(domain_rank, url_depth, url_structure)
```

Factors:
- Domain reputation
- URL depth (fewer slashes = higher authority)
- Clean URL structure

### Custom Link Scoring

```python
class CustomLinkScorer:
    def score(self, link: Link, query: str, state: CrawlState) -> float:
        # Prioritize specific URL patterns
        if "/api/reference/" in link.href:
            return 2.0  # Double the score
        
        # Deprioritize certain sections
        if "/archive/" in link.href:
            return 0.1  # Reduce score by 90%
        
        # Default scoring
        return 1.0

# Use with adaptive crawler
adaptive = AdaptiveCrawler(
    crawler,
    config=config,
    link_scorer=CustomLinkScorer()
)
```

## Domain-Specific Configurations

### Technical Documentation

```python
tech_doc_config = AdaptiveConfig(
    confidence_threshold=0.85,
    max_pages=30,
    top_k_links=3,
    min_gain_threshold=0.05  # Keep crawling for small gains
)
```

Rationale:
- High threshold ensures comprehensive coverage
- Lower gain threshold captures edge cases
- Moderate link following for depth

### News & Articles

```python
news_config = AdaptiveConfig(
    confidence_threshold=0.6,
    max_pages=10,
    top_k_links=5,
    min_gain_threshold=0.15  # Stop quickly on repetition
)
```

Rationale:
- Lower threshold (articles often repeat information)
- Higher gain threshold (avoid duplicate stories)
- More links per page (explore different perspectives)

### E-commerce

```python
ecommerce_config = AdaptiveConfig(
    confidence_threshold=0.7,
    max_pages=20,
    top_k_links=2,
    min_gain_threshold=0.1
)
```

Rationale:
- Balanced threshold for product variations
- Focused link following (avoid infinite products)
- Standard gain threshold

### Research & Academic

```python
research_config = AdaptiveConfig(
    confidence_threshold=0.9,
    max_pages=50,
    top_k_links=4,
    min_gain_threshold=0.02  # Very low - capture citations
)
```

Rationale:
- Very high threshold for completeness
- Many pages allowed for thorough research
- Very low gain threshold to capture references

## Performance Optimization

### Memory Management

```python
# For large crawls, use streaming
config = AdaptiveConfig(
    max_pages=100,
    save_state=True,
    state_path="large_crawl.json"
)

# Periodically clean state
if len(state.knowledge_base) > 1000:
    # Keep only most relevant
    state.knowledge_base = get_top_relevant(state.knowledge_base, 500)
```

### Parallel Processing

```python
# Use multiple start points
start_urls = [
    "https://docs.example.com/intro",
    "https://docs.example.com/api",
    "https://docs.example.com/guides"
]

# Crawl in parallel
tasks = [
    adaptive.digest(url, query)
    for url in start_urls
]
results = await asyncio.gather(*tasks)
```

### Caching Strategy

```python
# Enable caching for repeated crawls
async with AsyncWebCrawler(
    config=BrowserConfig(
        cache_mode=CacheMode.ENABLED
    )
) as crawler:
    adaptive = AdaptiveCrawler(crawler, config)
```

## Debugging & Analysis

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
adaptive = AdaptiveCrawler(crawler, config, verbose=True)
```

### Analyze Crawl Patterns

```python
# After crawling
state = await adaptive.digest(start_url, query)

# Analyze link selection
print("Link selection order:")
for i, url in enumerate(state.crawl_order):
    print(f"{i+1}. {url}")

# Analyze term discovery
print("\nTerm discovery rate:")
for i, new_terms in enumerate(state.new_terms_history):
    print(f"Page {i+1}: {new_terms} new terms")

# Analyze score progression
print("\nScore progression:")
print(f"Coverage: {state.metrics['coverage_history']}")
print(f"Saturation: {state.metrics['saturation_history']}")
```

### Export for Analysis

```python
# Export detailed metrics
import json

metrics = {
    "query": query,
    "total_pages": len(state.crawled_urls),
    "confidence": adaptive.confidence,
    "coverage_stats": adaptive.coverage_stats,
    "crawl_order": state.crawl_order,
    "term_frequencies": dict(state.term_frequencies),
    "new_terms_history": state.new_terms_history
}

with open("crawl_analysis.json", "w") as f:
    json.dump(metrics, f, indent=2)
```

## Custom Strategies

### Implementing a Custom Strategy

```python
from crawl4ai.adaptive_crawler import BaseStrategy

class DomainSpecificStrategy(BaseStrategy):
    def calculate_coverage(self, state: CrawlState) -> float:
        # Custom coverage calculation
        # e.g., weight certain terms more heavily
        pass
    
    def calculate_consistency(self, state: CrawlState) -> float:
        # Custom consistency logic
        # e.g., domain-specific validation
        pass
    
    def rank_links(self, links: List[Link], state: CrawlState) -> List[Link]:
        # Custom link ranking
        # e.g., prioritize specific URL patterns
        pass

# Use custom strategy
adaptive = AdaptiveCrawler(
    crawler,
    config=config,
    strategy=DomainSpecificStrategy()
)
```

### Combining Strategies

```python
class HybridStrategy(BaseStrategy):
    def __init__(self):
        self.strategies = [
            TechnicalDocStrategy(),
            SemanticSimilarityStrategy(),
            URLPatternStrategy()
        ]
    
    def calculate_confidence(self, state: CrawlState) -> float:
        # Weighted combination of strategies
        scores = [s.calculate_confidence(state) for s in self.strategies]
        weights = [0.5, 0.3, 0.2]
        return sum(s * w for s, w in zip(scores, weights))
```

## Best Practices

### 1. Start Conservative

Begin with default settings and adjust based on results:

```python
# Start with defaults
result = await adaptive.digest(url, query)

# Analyze and adjust
if adaptive.confidence < 0.7:
    config.max_pages += 10
    config.confidence_threshold -= 0.1
```

### 2. Monitor Resource Usage

```python
import psutil

# Check memory before large crawls
memory_percent = psutil.virtual_memory().percent
if memory_percent > 80:
    config.max_pages = min(config.max_pages, 20)
```

### 3. Use Domain Knowledge

```python
# For API documentation
if "api" in start_url:
    config.top_k_links = 2  # APIs have clear structure
    
# For blogs
if "blog" in start_url:
    config.min_gain_threshold = 0.2  # Avoid similar posts
```

### 4. Validate Results

```python
# Always validate the knowledge base
relevant_content = adaptive.get_relevant_content(top_k=10)

# Check coverage
query_terms = set(query.lower().split())
covered_terms = set()

for doc in relevant_content:
    content_lower = doc['content'].lower()
    for term in query_terms:
        if term in content_lower:
            covered_terms.add(term)

coverage_ratio = len(covered_terms) / len(query_terms)
print(f"Query term coverage: {coverage_ratio:.0%}")
```

## Next Steps

- Explore [Custom Strategy Implementation](../tutorials/custom-adaptive-strategies.md)
- Learn about [Knowledge Base Management](../tutorials/knowledge-base-management.md)
- See [Performance Benchmarks](../benchmarks/adaptive-performance.md)