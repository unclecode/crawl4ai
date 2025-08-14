[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/advanced/adaptive-strategies/)


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
    * Adaptive Strategies
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
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [Advanced Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/#advanced-adaptive-strategies)
  * [Overview](https://docs.crawl4ai.com/advanced/adaptive-strategies/#overview)
  * [The Three-Layer Scoring System](https://docs.crawl4ai.com/advanced/adaptive-strategies/#the-three-layer-scoring-system)
  * [Link Ranking Algorithm](https://docs.crawl4ai.com/advanced/adaptive-strategies/#link-ranking-algorithm)
  * [Domain-Specific Configurations](https://docs.crawl4ai.com/advanced/adaptive-strategies/#domain-specific-configurations)
  * [Performance Optimization](https://docs.crawl4ai.com/advanced/adaptive-strategies/#performance-optimization)
  * [Debugging & Analysis](https://docs.crawl4ai.com/advanced/adaptive-strategies/#debugging-analysis)
  * [Custom Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/#custom-strategies)
  * [Best Practices](https://docs.crawl4ai.com/advanced/adaptive-strategies/#best-practices)
  * [Next Steps](https://docs.crawl4ai.com/advanced/adaptive-strategies/#next-steps)


# Advanced Adaptive Strategies
## Overview
While the default adaptive crawling configuration works well for most use cases, understanding the underlying strategies and scoring mechanisms allows you to fine-tune the crawler for specific domains and requirements.
## The Three-Layer Scoring System
### 1. Coverage Score
Coverage measures how comprehensively your knowledge base covers the query terms and related concepts.
#### Mathematical Foundation
```
Coverage(K, Q) = Σ(t ∈ Q) score(t, K) / |Q|

where score(t, K) = doc_coverage(t) × (1 + freq_boost(t))
Copy
```

#### Components
  * **Document Coverage** : Percentage of documents containing the term
  * **Frequency Boost** : Logarithmic bonus for term frequency
  * **Query Decomposition** : Handles multi-word queries intelligently


#### Tuning Coverage
```
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
Copy
```

### 2. Consistency Score
Consistency evaluates whether the information across pages is coherent and non-contradictory.
#### How It Works
  1. Extracts key statements from each document
  2. Compares statements across documents
  3. Measures agreement vs. contradiction
  4. Returns normalized score (0-1)


#### Practical Impact
  * **High consistency ( >0.8)**: Information is reliable and coherent
  * **Medium consistency (0.5-0.8)** : Some variation, but generally aligned
  * **Low consistency ( <0.5)**: Conflicting information, need more sources


### 3. Saturation Score
Saturation detects when new pages stop providing novel information.
#### Detection Algorithm
```
# Tracks new unique terms per page
new_terms_page_1 = 50
new_terms_page_2 = 30  # 60% of first
new_terms_page_3 = 15  # 50% of second
new_terms_page_4 = 5   # 33% of third
# Saturation detected: rapidly diminishing returns
Copy
```

#### Configuration
```
config = AdaptiveConfig(
    min_gain_threshold=0.1  # Stop if <10% new information
)
Copy
```

## Link Ranking Algorithm
### Expected Information Gain
Each uncrawled link is scored based on:
```
ExpectedGain(link) = Relevance × Novelty × Authority
Copy
```

#### 1. Relevance Scoring
Uses BM25 algorithm on link preview text:
```
relevance = BM25(link.preview_text, query)
Copy
```

Factors: - Term frequency in preview - Inverse document frequency - Preview length normalization
#### 2. Novelty Estimation
Measures how different the link appears from already-crawled content:
```
novelty = 1 - max_similarity(preview, knowledge_base)
Copy
```

Prevents crawling duplicate or highly similar pages.
#### 3. Authority Calculation
URL structure and domain analysis:
```
authority = f(domain_rank, url_depth, url_structure)
Copy
```

Factors: - Domain reputation - URL depth (fewer slashes = higher authority) - Clean URL structure
### Custom Link Scoring
```
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
Copy
```

## Domain-Specific Configurations
### Technical Documentation
```
tech_doc_config = AdaptiveConfig(
    confidence_threshold=0.85,
    max_pages=30,
    top_k_links=3,
    min_gain_threshold=0.05  # Keep crawling for small gains
)
Copy
```

Rationale: - High threshold ensures comprehensive coverage - Lower gain threshold captures edge cases - Moderate link following for depth
### News & Articles
```
news_config = AdaptiveConfig(
    confidence_threshold=0.6,
    max_pages=10,
    top_k_links=5,
    min_gain_threshold=0.15  # Stop quickly on repetition
)
Copy
```

Rationale: - Lower threshold (articles often repeat information) - Higher gain threshold (avoid duplicate stories) - More links per page (explore different perspectives)
### E-commerce
```
ecommerce_config = AdaptiveConfig(
    confidence_threshold=0.7,
    max_pages=20,
    top_k_links=2,
    min_gain_threshold=0.1
)
Copy
```

Rationale: - Balanced threshold for product variations - Focused link following (avoid infinite products) - Standard gain threshold
### Research & Academic
```
research_config = AdaptiveConfig(
    confidence_threshold=0.9,
    max_pages=50,
    top_k_links=4,
    min_gain_threshold=0.02  # Very low - capture citations
)
Copy
```

Rationale: - Very high threshold for completeness - Many pages allowed for thorough research - Very low gain threshold to capture references
## Performance Optimization
### Memory Management
```
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
Copy
```

### Parallel Processing
```
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
Copy
```

### Caching Strategy
```
# Enable caching for repeated crawls
async with AsyncWebCrawler(
    config=BrowserConfig(
        cache_mode=CacheMode.ENABLED
    )
) as crawler:
    adaptive = AdaptiveCrawler(crawler, config)
Copy
```

## Debugging & Analysis
### Enable Verbose Logging
```
import logging

logging.basicConfig(level=logging.DEBUG)
adaptive = AdaptiveCrawler(crawler, config, verbose=True)
Copy
```

### Analyze Crawl Patterns
```
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
Copy
```

### Export for Analysis
```
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
Copy
```

## Custom Strategies
### Implementing a Custom Strategy
```
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
Copy
```

### Combining Strategies
```
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
Copy
```

## Best Practices
### 1. Start Conservative
Begin with default settings and adjust based on results:
```
# Start with defaults
result = await adaptive.digest(url, query)

# Analyze and adjust
if adaptive.confidence < 0.7:
    config.max_pages += 10
    config.confidence_threshold -= 0.1
Copy
```

### 2. Monitor Resource Usage
```
import psutil

# Check memory before large crawls
memory_percent = psutil.virtual_memory().percent
if memory_percent > 80:
    config.max_pages = min(config.max_pages, 20)
Copy
```

### 3. Use Domain Knowledge
```
# For API documentation
if "api" in start_url:
    config.top_k_links = 2  # APIs have clear structure

# For blogs
if "blog" in start_url:
    config.min_gain_threshold = 0.2  # Avoid similar posts
Copy
```

### 4. Validate Results
```
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
Copy
```

## Next Steps
  * Explore [Custom Strategy Implementation](https://docs.crawl4ai.com/advanced/tutorials/custom-adaptive-strategies.md)
  * Learn about [Knowledge Base Management](https://docs.crawl4ai.com/advanced/tutorials/knowledge-base-management.md)
  * See [Performance Benchmarks](https://docs.crawl4ai.com/advanced/benchmarks/adaptive-performance.md)


#### On this page
  * [Overview](https://docs.crawl4ai.com/advanced/adaptive-strategies/#overview)
  * [The Three-Layer Scoring System](https://docs.crawl4ai.com/advanced/adaptive-strategies/#the-three-layer-scoring-system)
  * [1. Coverage Score](https://docs.crawl4ai.com/advanced/adaptive-strategies/#1-coverage-score)
  * [Mathematical Foundation](https://docs.crawl4ai.com/advanced/adaptive-strategies/#mathematical-foundation)
  * [Components](https://docs.crawl4ai.com/advanced/adaptive-strategies/#components)
  * [Tuning Coverage](https://docs.crawl4ai.com/advanced/adaptive-strategies/#tuning-coverage)
  * [2. Consistency Score](https://docs.crawl4ai.com/advanced/adaptive-strategies/#2-consistency-score)
  * [How It Works](https://docs.crawl4ai.com/advanced/adaptive-strategies/#how-it-works)
  * [Practical Impact](https://docs.crawl4ai.com/advanced/adaptive-strategies/#practical-impact)
  * [3. Saturation Score](https://docs.crawl4ai.com/advanced/adaptive-strategies/#3-saturation-score)
  * [Detection Algorithm](https://docs.crawl4ai.com/advanced/adaptive-strategies/#detection-algorithm)
  * [Configuration](https://docs.crawl4ai.com/advanced/adaptive-strategies/#configuration)
  * [Link Ranking Algorithm](https://docs.crawl4ai.com/advanced/adaptive-strategies/#link-ranking-algorithm)
  * [Expected Information Gain](https://docs.crawl4ai.com/advanced/adaptive-strategies/#expected-information-gain)
  * [1. Relevance Scoring](https://docs.crawl4ai.com/advanced/adaptive-strategies/#1-relevance-scoring)
  * [2. Novelty Estimation](https://docs.crawl4ai.com/advanced/adaptive-strategies/#2-novelty-estimation)
  * [3. Authority Calculation](https://docs.crawl4ai.com/advanced/adaptive-strategies/#3-authority-calculation)
  * [Custom Link Scoring](https://docs.crawl4ai.com/advanced/adaptive-strategies/#custom-link-scoring)
  * [Domain-Specific Configurations](https://docs.crawl4ai.com/advanced/adaptive-strategies/#domain-specific-configurations)
  * [Technical Documentation](https://docs.crawl4ai.com/advanced/adaptive-strategies/#technical-documentation)
  * [News & Articles](https://docs.crawl4ai.com/advanced/adaptive-strategies/#news-articles)
  * [E-commerce](https://docs.crawl4ai.com/advanced/adaptive-strategies/#e-commerce)
  * [Research & Academic](https://docs.crawl4ai.com/advanced/adaptive-strategies/#research-academic)
  * [Performance Optimization](https://docs.crawl4ai.com/advanced/adaptive-strategies/#performance-optimization)
  * [Memory Management](https://docs.crawl4ai.com/advanced/adaptive-strategies/#memory-management)
  * [Parallel Processing](https://docs.crawl4ai.com/advanced/adaptive-strategies/#parallel-processing)
  * [Caching Strategy](https://docs.crawl4ai.com/advanced/adaptive-strategies/#caching-strategy)
  * [Debugging & Analysis](https://docs.crawl4ai.com/advanced/adaptive-strategies/#debugging-analysis)
  * [Enable Verbose Logging](https://docs.crawl4ai.com/advanced/adaptive-strategies/#enable-verbose-logging)
  * [Analyze Crawl Patterns](https://docs.crawl4ai.com/advanced/adaptive-strategies/#analyze-crawl-patterns)
  * [Export for Analysis](https://docs.crawl4ai.com/advanced/adaptive-strategies/#export-for-analysis)
  * [Custom Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/#custom-strategies)
  * [Implementing a Custom Strategy](https://docs.crawl4ai.com/advanced/adaptive-strategies/#implementing-a-custom-strategy)
  * [Combining Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/#combining-strategies)
  * [Best Practices](https://docs.crawl4ai.com/advanced/adaptive-strategies/#best-practices)
  * [1. Start Conservative](https://docs.crawl4ai.com/advanced/adaptive-strategies/#1-start-conservative)
  * [2. Monitor Resource Usage](https://docs.crawl4ai.com/advanced/adaptive-strategies/#2-monitor-resource-usage)
  * [3. Use Domain Knowledge](https://docs.crawl4ai.com/advanced/adaptive-strategies/#3-use-domain-knowledge)
  * [4. Validate Results](https://docs.crawl4ai.com/advanced/adaptive-strategies/#4-validate-results)
  * [Next Steps](https://docs.crawl4ai.com/advanced/adaptive-strategies/#next-steps)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
