# digest()

The `digest()` method is the primary interface for adaptive web crawling. It intelligently crawls websites starting from a given URL, guided by a query, and automatically determines when sufficient information has been gathered.

## Method Signature

```python
async def digest(
    start_url: str,
    query: str,
    resume_from: Optional[Union[str, Path]] = None
) -> CrawlState
```

## Parameters

### start_url
- **Type**: `str`
- **Required**: Yes
- **Description**: The starting URL for the crawl. This should be a valid HTTP/HTTPS URL that serves as the entry point for information gathering.

### query
- **Type**: `str`  
- **Required**: Yes
- **Description**: The search query that guides the crawling process. This should contain key terms related to the information you're seeking. The crawler uses this to evaluate relevance and determine which links to follow.

### resume_from
- **Type**: `Optional[Union[str, Path]]`
- **Default**: `None`
- **Description**: Path to a previously saved crawl state file. When provided, the crawler resumes from the saved state instead of starting fresh.

## Return Value

Returns a `CrawlState` object containing:

- **crawled_urls** (`Set[str]`): All URLs that have been crawled
- **knowledge_base** (`List[CrawlResult]`): Collection of crawled pages with content
- **pending_links** (`List[Link]`): Links discovered but not yet crawled
- **metrics** (`Dict[str, float]`): Performance and quality metrics
- **query** (`str`): The original query
- Additional statistical information for scoring

## How It Works

The `digest()` method implements an intelligent crawling algorithm:

1. **Initial Crawl**: Starts from the provided URL
2. **Link Analysis**: Evaluates all discovered links for relevance
3. **Scoring**: Uses three metrics to assess information sufficiency:
   - **Coverage**: How well the query terms are covered
   - **Consistency**: Information coherence across pages
   - **Saturation**: Diminishing returns detection
4. **Adaptive Selection**: Chooses the most promising links to follow
5. **Stopping Decision**: Automatically stops when confidence threshold is reached

## Examples

### Basic Usage

```python
async with AsyncWebCrawler() as crawler:
    adaptive = AdaptiveCrawler(crawler)
    
    state = await adaptive.digest(
        start_url="https://docs.python.org/3/",
        query="async await context managers"
    )
    
    print(f"Crawled {len(state.crawled_urls)} pages")
    print(f"Confidence: {adaptive.confidence:.0%}")
```

### With Configuration

```python
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
```

### Resuming a Previous Crawl

```python
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
```

### With Progress Monitoring

```python
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
```

## Query Best Practices

1. **Be Specific**: Use descriptive terms that appear in target content
   ```python
   # Good
   query = "python async context managers implementation"
   
   # Too broad
   query = "python programming"
   ```

2. **Include Key Terms**: Add technical terms you expect to find
   ```python
   query = "oauth2 jwt refresh tokens authorization"
   ```

3. **Multiple Concepts**: Combine related concepts for comprehensive coverage
   ```python
   query = "rest api pagination sorting filtering"
   ```

## Performance Considerations

- **Initial URL**: Choose a page with good navigation (e.g., documentation index)
- **Query Length**: 3-8 terms typically work best
- **Link Density**: Sites with clear navigation crawl more efficiently
- **Caching**: Enable caching for repeated crawls of the same domain

## Error Handling

```python
try:
    state = await adaptive.digest(
        start_url="https://example.com",
        query="search terms"
    )
except Exception as e:
    print(f"Crawl failed: {e}")
    # State is auto-saved if save_state=True in config
```

## Stopping Conditions

The crawl stops when any of these conditions are met:

1. **Confidence Threshold**: Reached the configured confidence level
2. **Page Limit**: Crawled the maximum number of pages
3. **Diminishing Returns**: Expected information gain below threshold
4. **No Relevant Links**: No promising links remain to follow

## See Also

- [AdaptiveCrawler Class](adaptive-crawler.md)
- [Adaptive Crawling Guide](../core/adaptive-crawling.md)
- [Configuration Options](../core/adaptive-crawling.md#configuration-options)