[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/api/digest/)


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
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [digest()](https://docs.crawl4ai.com/api/digest/#digest)
  * [Method Signature](https://docs.crawl4ai.com/api/digest/#method-signature)
  * [Parameters](https://docs.crawl4ai.com/api/digest/#parameters)
  * [Return Value](https://docs.crawl4ai.com/api/digest/#return-value)
  * [How It Works](https://docs.crawl4ai.com/api/digest/#how-it-works)
  * [Examples](https://docs.crawl4ai.com/api/digest/#examples)
  * [Query Best Practices](https://docs.crawl4ai.com/api/digest/#query-best-practices)
  * [Performance Considerations](https://docs.crawl4ai.com/api/digest/#performance-considerations)
  * [Error Handling](https://docs.crawl4ai.com/api/digest/#error-handling)
  * [Stopping Conditions](https://docs.crawl4ai.com/api/digest/#stopping-conditions)
  * [See Also](https://docs.crawl4ai.com/api/digest/#see-also)


# digest()
The `digest()` method is the primary interface for adaptive web crawling. It intelligently crawls websites starting from a given URL, guided by a query, and automatically determines when sufficient information has been gathered.
## Method Signature
```
async def digest(
    start_url: str,
    query: str,
    resume_from: Optional[Union[str, Path]] = None
) -> CrawlState
Copy
```

## Parameters
### start_url
  * **Type** : `str`
  * **Required** : Yes
  * **Description** : The starting URL for the crawl. This should be a valid HTTP/HTTPS URL that serves as the entry point for information gathering.


### query
  * **Type** : `str`
  * **Required** : Yes
  * **Description** : The search query that guides the crawling process. This should contain key terms related to the information you're seeking. The crawler uses this to evaluate relevance and determine which links to follow.


### resume_from
  * **Type** : `Optional[Union[str, Path]]`
  * **Default** : `None`
  * **Description** : Path to a previously saved crawl state file. When provided, the crawler resumes from the saved state instead of starting fresh.


## Return Value
Returns a `CrawlState` object containing:
  * **crawled_urls** (`Set[str]`): All URLs that have been crawled
  * **knowledge_base** (`List[CrawlResult]`): Collection of crawled pages with content
  * **pending_links** (`List[Link]`): Links discovered but not yet crawled
  * **metrics** (`Dict[str, float]`): Performance and quality metrics
  * **query** (`str`): The original query
  * Additional statistical information for scoring


## How It Works
The `digest()` method implements an intelligent crawling algorithm:
  1. **Initial Crawl** : Starts from the provided URL
  2. **Link Analysis** : Evaluates all discovered links for relevance
  3. **Scoring** : Uses three metrics to assess information sufficiency:
  4. **Coverage** : How well the query terms are covered
  5. **Consistency** : Information coherence across pages
  6. **Saturation** : Diminishing returns detection
  7. **Adaptive Selection** : Chooses the most promising links to follow
  8. **Stopping Decision** : Automatically stops when confidence threshold is reached


## Examples
### Basic Usage
```
async with AsyncWebCrawler() as crawler:
    adaptive = AdaptiveCrawler(crawler)

    state = await adaptive.digest(
        start_url="https://docs.python.org/3/",
        query="async await context managers"
    )

    print(f"Crawled {len(state.crawled_urls)} pages")
    print(f"Confidence: {adaptive.confidence:.0%}")
Copy
```

### With Configuration
```
config = AdaptiveConfig(
    confidence_threshold=0.9,  # Require high confidence
    max_pages=30,             # Allow more pages
    top_k_links=3             # Follow top 3 links per page
)

adaptive = AdaptiveCrawler(crawler, config=config)

state = await adaptive.digest(
    start_url="https://api.example.com/docs",
    query="authentication endpoints rate limits"
)
Copy
```

### Resuming a Previous Crawl
```
# First crawl - may be interrupted
state1 = await adaptive.digest(
    start_url="https://example.com",
    query="machine learning algorithms"
)

# Save state (if not auto-saved)
state1.save("ml_crawl_state.json")

# Later, resume from saved state
state2 = await adaptive.digest(
    start_url="https://example.com",
    query="machine learning algorithms",
    resume_from="ml_crawl_state.json"
)
Copy
```

### With Progress Monitoring
```
state = await adaptive.digest(
    start_url="https://docs.example.com",
    query="api reference"
)

# Monitor progress
print(f"Pages crawled: {len(state.crawled_urls)}")
print(f"New terms discovered: {state.new_terms_history}")
print(f"Final confidence: {adaptive.confidence:.2%}")

# View detailed statistics
adaptive.print_stats(detailed=True)
Copy
```

## Query Best Practices
  1. **Be Specific** : Use descriptive terms that appear in target content
```
# Good
query = "python async context managers implementation"

# Too broad
query = "python programming"
Copy
```

  2. **Include Key Terms** : Add technical terms you expect to find
```
query = "oauth2 jwt refresh tokens authorization"
Copy
```

  3. **Multiple Concepts** : Combine related concepts for comprehensive coverage
```
query = "rest api pagination sorting filtering"
Copy
```



## Performance Considerations
  * **Initial URL** : Choose a page with good navigation (e.g., documentation index)
  * **Query Length** : 3-8 terms typically work best
  * **Link Density** : Sites with clear navigation crawl more efficiently
  * **Caching** : Enable caching for repeated crawls of the same domain


## Error Handling
```
try:
    state = await adaptive.digest(
        start_url="https://example.com",
        query="search terms"
    )
except Exception as e:
    print(f"Crawl failed: {e}")
    # State is auto-saved if save_state=True in config
Copy
```

## Stopping Conditions
The crawl stops when any of these conditions are met:
  1. **Confidence Threshold** : Reached the configured confidence level
  2. **Page Limit** : Crawled the maximum number of pages
  3. **Diminishing Returns** : Expected information gain below threshold
  4. **No Relevant Links** : No promising links remain to follow


## See Also
  * [AdaptiveCrawler Class](https://docs.crawl4ai.com/api/adaptive-crawler/)
  * [Adaptive Crawling Guide](https://docs.crawl4ai.com/core/adaptive-crawling/)
  * [Configuration Options](https://docs.crawl4ai.com/core/adaptive-crawling/#configuration-options)


#### On this page
  * [Method Signature](https://docs.crawl4ai.com/api/digest/#method-signature)
  * [Parameters](https://docs.crawl4ai.com/api/digest/#parameters)
  * [start_url](https://docs.crawl4ai.com/api/digest/#start_url)
  * [query](https://docs.crawl4ai.com/api/digest/#query)
  * [resume_from](https://docs.crawl4ai.com/api/digest/#resume_from)
  * [Return Value](https://docs.crawl4ai.com/api/digest/#return-value)
  * [How It Works](https://docs.crawl4ai.com/api/digest/#how-it-works)
  * [Examples](https://docs.crawl4ai.com/api/digest/#examples)
  * [Basic Usage](https://docs.crawl4ai.com/api/digest/#basic-usage)
  * [With Configuration](https://docs.crawl4ai.com/api/digest/#with-configuration)
  * [Resuming a Previous Crawl](https://docs.crawl4ai.com/api/digest/#resuming-a-previous-crawl)
  * [With Progress Monitoring](https://docs.crawl4ai.com/api/digest/#with-progress-monitoring)
  * [Query Best Practices](https://docs.crawl4ai.com/api/digest/#query-best-practices)
  * [Performance Considerations](https://docs.crawl4ai.com/api/digest/#performance-considerations)
  * [Error Handling](https://docs.crawl4ai.com/api/digest/#error-handling)
  * [Stopping Conditions](https://docs.crawl4ai.com/api/digest/#stopping-conditions)
  * [See Also](https://docs.crawl4ai.com/api/digest/#see-also)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
