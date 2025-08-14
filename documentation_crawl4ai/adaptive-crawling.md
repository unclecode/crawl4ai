[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/core/adaptive-crawling/)


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
    * Adaptive Crawling
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
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [Adaptive Web Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/#adaptive-web-crawling)
  * [Introduction](https://docs.crawl4ai.com/core/adaptive-crawling/#introduction)
  * [Key Concepts](https://docs.crawl4ai.com/core/adaptive-crawling/#key-concepts)
  * [Quick Start](https://docs.crawl4ai.com/core/adaptive-crawling/#quick-start)
  * [Crawling Strategies](https://docs.crawl4ai.com/core/adaptive-crawling/#crawling-strategies)
  * [When to Use Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/#when-to-use-adaptive-crawling)
  * [Understanding the Output](https://docs.crawl4ai.com/core/adaptive-crawling/#understanding-the-output)
  * [Persistence and Resumption](https://docs.crawl4ai.com/core/adaptive-crawling/#persistence-and-resumption)
  * [Best Practices](https://docs.crawl4ai.com/core/adaptive-crawling/#best-practices)
  * [Examples](https://docs.crawl4ai.com/core/adaptive-crawling/#examples)
  * [Next Steps](https://docs.crawl4ai.com/core/adaptive-crawling/#next-steps)
  * [FAQ](https://docs.crawl4ai.com/core/adaptive-crawling/#faq)


# Adaptive Web Crawling
## Introduction
Traditional web crawlers follow predetermined patterns, crawling pages blindly without knowing when they've gathered enough information. **Adaptive Crawling** changes this paradigm by introducing intelligence into the crawling process.
Think of it like research: when you're looking for information, you don't read every book in the library. You stop when you've found sufficient information to answer your question. That's exactly what Adaptive Crawling does for web scraping.
## Key Concepts
### The Problem It Solves
When crawling websites for specific information, you face two challenges: 1. **Under-crawling** : Stopping too early and missing crucial information 2. **Over-crawling** : Wasting resources by crawling irrelevant pages
Adaptive Crawling solves both by using a three-layer scoring system that determines when you have "enough" information.
### How It Works
The AdaptiveCrawler uses three metrics to measure information sufficiency:
  * **Coverage** : How well your collected pages cover the query terms
  * **Consistency** : Whether the information is coherent across pages
  * **Saturation** : Detecting when new pages aren't adding new information


When these metrics indicate sufficient information has been gathered, crawling stops automatically.
## Quick Start
### Basic Usage
```
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
Copy
```

### Configuration Options
```
from crawl4ai import AdaptiveConfig

config = AdaptiveConfig(
    confidence_threshold=0.8,    # Stop when 80% confident (default: 0.7)
    max_pages=30,               # Maximum pages to crawl (default: 20)
    top_k_links=5,              # Links to follow per page (default: 3)
    min_gain_threshold=0.05     # Minimum expected gain to continue (default: 0.1)
)

adaptive = AdaptiveCrawler(crawler, config)
Copy
```

## Crawling Strategies
Adaptive Crawling supports two distinct strategies for determining information sufficiency:
### Statistical Strategy (Default)
The statistical strategy uses pure information theory and term-based analysis:
  * **Fast and efficient** - No API calls or model loading
  * **Term-based coverage** - Analyzes query term presence and distribution
  * **No external dependencies** - Works offline
  * **Best for** : Well-defined queries with specific terminology


```
# Default configuration uses statistical strategy
config = AdaptiveConfig(
    strategy="statistical",  # This is the default
    confidence_threshold=0.8
)
Copy
```

### Embedding Strategy
The embedding strategy uses semantic embeddings for deeper understanding:
  * **Semantic understanding** - Captures meaning beyond exact term matches
  * **Query expansion** - Automatically generates query variations
  * **Gap-driven selection** - Identifies semantic gaps in knowledge
  * **Validation-based stopping** - Uses held-out queries to validate coverage
  * **Best for** : Complex queries, ambiguous topics, conceptual understanding


```
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
Copy
```

### Strategy Comparison
Feature | Statistical | Embedding
---|---|---
**Speed** | Very fast | Moderate (API calls)
**Cost** | Free | Depends on provider
**Accuracy** | Good for exact terms | Excellent for concepts
**Dependencies** | None | Embedding model/API
**Query Understanding** | Literal | Semantic
**Best Use Case** | Technical docs, specific terms | Research, broad topics
### Embedding Strategy Configuration
The embedding strategy offers fine-tuned control through several parameters:
```
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
Copy
```

### Handling Irrelevant Queries
The embedding strategy can detect when a query is completely unrelated to the content:
```
# This will stop quickly with low confidence
result = await adaptive.digest(
    start_url="https://docs.python.org/3/",
    query="how to cook pasta"  # Irrelevant to Python docs
)

# Check if query was irrelevant
if result.metrics.get('is_irrelevant', False):
    print("Query is unrelated to the content!")
Copy
```

## When to Use Adaptive Crawling
### Perfect For:
  * **Research Tasks** : Finding comprehensive information about a topic
  * **Question Answering** : Gathering sufficient context to answer specific queries
  * **Knowledge Base Building** : Creating focused datasets for AI/ML applications
  * **Competitive Intelligence** : Collecting complete information about specific products/features


### Not Recommended For:
  * **Full Site Archiving** : When you need every page regardless of content
  * **Structured Data Extraction** : When targeting specific, known page patterns
  * **Real-time Monitoring** : When you need continuous updates


## Understanding the Output
### Confidence Score
The confidence score (0-1) indicates how sufficient the gathered information is: - **0.0-0.3** : Insufficient information, needs more crawling - **0.3-0.6** : Partial information, may answer basic queries - **0.6-0.7** : Good coverage, can answer most queries - **0.7-1.0** : Excellent coverage, comprehensive information
### Statistics Display
```
adaptive.print_stats(detailed=False)  # Summary table
adaptive.print_stats(detailed=True)   # Detailed metrics
Copy
```

The summary shows: - Pages crawled vs. confidence achieved - Coverage, consistency, and saturation scores - Crawling efficiency metrics
## Persistence and Resumption
### Saving Progress
```
config = AdaptiveConfig(
    save_state=True,
    state_path="my_crawl_state.json"
)

# Crawl will auto-save progress
result = await adaptive.digest(start_url, query)
Copy
```

### Resuming a Crawl
```
# Resume from saved state
result = await adaptive.digest(
    start_url,
    query,
    resume_from="my_crawl_state.json"
)
Copy
```

### Exporting Knowledge Base
```
# Export collected pages to JSONL
adaptive.export_knowledge_base("knowledge_base.jsonl")

# Import into another session
new_adaptive = AdaptiveCrawler(crawler)
new_adaptive.import_knowledge_base("knowledge_base.jsonl")
Copy
```

## Best Practices
### 1. Query Formulation
  * Use specific, descriptive queries
  * Include key terms you expect to find
  * Avoid overly broad queries


### 2. Threshold Tuning
  * Start with default (0.7) for general use
  * Lower to 0.5-0.6 for exploratory crawling
  * Raise to 0.8+ for exhaustive coverage


### 3. Performance Optimization
  * Use appropriate `max_pages` limits
  * Adjust `top_k_links` based on site structure
  * Enable caching for repeat crawls


### 4. Link Selection
  * The crawler prioritizes links based on:
  * Relevance to query
  * Expected information gain
  * URL structure and depth


## Examples
### Research Assistant
```
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
Copy
```

### Knowledge Base Builder
```
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
Copy
```

### API Documentation Crawler
```
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
Copy
```

## Next Steps
  * Learn about [Advanced Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
  * Explore the [AdaptiveCrawler API Reference](https://docs.crawl4ai.com/api/adaptive-crawler/)
  * See more [Examples](https://github.com/unclecode/crawl4ai/tree/main/docs/examples/adaptive_crawling)


## FAQ
**Q: How is this different from traditional crawling?** A: Traditional crawling follows fixed patterns (BFS/DFS). Adaptive crawling makes intelligent decisions about which links to follow and when to stop based on information gain.
**Q: Can I use this with JavaScript-heavy sites?** A: Yes! AdaptiveCrawler inherits all capabilities from AsyncWebCrawler, including JavaScript execution.
**Q: How does it handle large websites?** A: The algorithm naturally limits crawling to relevant sections. Use `max_pages` as a safety limit.
**Q: Can I customize the scoring algorithms?** A: Advanced users can implement custom strategies. See [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/).
#### On this page
  * [Introduction](https://docs.crawl4ai.com/core/adaptive-crawling/#introduction)
  * [Key Concepts](https://docs.crawl4ai.com/core/adaptive-crawling/#key-concepts)
  * [The Problem It Solves](https://docs.crawl4ai.com/core/adaptive-crawling/#the-problem-it-solves)
  * [How It Works](https://docs.crawl4ai.com/core/adaptive-crawling/#how-it-works)
  * [Quick Start](https://docs.crawl4ai.com/core/adaptive-crawling/#quick-start)
  * [Basic Usage](https://docs.crawl4ai.com/core/adaptive-crawling/#basic-usage)
  * [Configuration Options](https://docs.crawl4ai.com/core/adaptive-crawling/#configuration-options)
  * [Crawling Strategies](https://docs.crawl4ai.com/core/adaptive-crawling/#crawling-strategies)
  * [Statistical Strategy (Default)](https://docs.crawl4ai.com/core/adaptive-crawling/#statistical-strategy-default)
  * [Embedding Strategy](https://docs.crawl4ai.com/core/adaptive-crawling/#embedding-strategy)
  * [Strategy Comparison](https://docs.crawl4ai.com/core/adaptive-crawling/#strategy-comparison)
  * [Embedding Strategy Configuration](https://docs.crawl4ai.com/core/adaptive-crawling/#embedding-strategy-configuration)
  * [Handling Irrelevant Queries](https://docs.crawl4ai.com/core/adaptive-crawling/#handling-irrelevant-queries)
  * [When to Use Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/#when-to-use-adaptive-crawling)
  * [Perfect For:](https://docs.crawl4ai.com/core/adaptive-crawling/#perfect-for)
  * [Not Recommended For:](https://docs.crawl4ai.com/core/adaptive-crawling/#not-recommended-for)
  * [Understanding the Output](https://docs.crawl4ai.com/core/adaptive-crawling/#understanding-the-output)
  * [Confidence Score](https://docs.crawl4ai.com/core/adaptive-crawling/#confidence-score)
  * [Statistics Display](https://docs.crawl4ai.com/core/adaptive-crawling/#statistics-display)
  * [Persistence and Resumption](https://docs.crawl4ai.com/core/adaptive-crawling/#persistence-and-resumption)
  * [Saving Progress](https://docs.crawl4ai.com/core/adaptive-crawling/#saving-progress)
  * [Resuming a Crawl](https://docs.crawl4ai.com/core/adaptive-crawling/#resuming-a-crawl)
  * [Exporting Knowledge Base](https://docs.crawl4ai.com/core/adaptive-crawling/#exporting-knowledge-base)
  * [Best Practices](https://docs.crawl4ai.com/core/adaptive-crawling/#best-practices)
  * [1. Query Formulation](https://docs.crawl4ai.com/core/adaptive-crawling/#1-query-formulation)
  * [2. Threshold Tuning](https://docs.crawl4ai.com/core/adaptive-crawling/#2-threshold-tuning)
  * [3. Performance Optimization](https://docs.crawl4ai.com/core/adaptive-crawling/#3-performance-optimization)
  * [4. Link Selection](https://docs.crawl4ai.com/core/adaptive-crawling/#4-link-selection)
  * [Examples](https://docs.crawl4ai.com/core/adaptive-crawling/#examples)
  * [Research Assistant](https://docs.crawl4ai.com/core/adaptive-crawling/#research-assistant)
  * [Knowledge Base Builder](https://docs.crawl4ai.com/core/adaptive-crawling/#knowledge-base-builder)
  * [API Documentation Crawler](https://docs.crawl4ai.com/core/adaptive-crawling/#api-documentation-crawler)
  * [Next Steps](https://docs.crawl4ai.com/core/adaptive-crawling/#next-steps)
  * [FAQ](https://docs.crawl4ai.com/core/adaptive-crawling/#faq)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
