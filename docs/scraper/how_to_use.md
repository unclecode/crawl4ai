# Scraper Examples Guide

This guide provides two complete examples of using the crawl4ai scraper: a basic implementation for simple use cases and an advanced implementation showcasing all features.

## Basic Example

The basic example demonstrates a simple blog scraping scenario:

```python
from crawl4ai.scraper import AsyncWebScraper, BFSScraperStrategy, FilterChain

# Create simple filter chain
filter_chain = FilterChain([
    URLPatternFilter("*/blog/*"),
    ContentTypeFilter(["text/html"])
])

# Initialize strategy
strategy = BFSScraperStrategy(
    max_depth=2,
    filter_chain=filter_chain,
    url_scorer=None,
    max_concurrent=3
)

# Create and run scraper
crawler = AsyncWebCrawler()
scraper = AsyncWebScraper(crawler, strategy)
result = await scraper.ascrape("https://example.com/blog/")
```

### Features Demonstrated
- Basic URL filtering
- Simple content type filtering
- Depth control
- Concurrent request limiting
- Result collection

## Advanced Example

The advanced example shows a sophisticated news site scraping setup with all features enabled:

```python
# Create comprehensive filter chain
filter_chain = FilterChain([
    DomainFilter(
        allowed_domains=["example.com"],
        blocked_domains=["ads.example.com"]
    ),
    URLPatternFilter([
        "*/article/*",
        re.compile(r"\d{4}/\d{2}/.*")
    ]),
    ContentTypeFilter(["text/html"])
])

# Create intelligent scorer
scorer = CompositeScorer([
    KeywordRelevanceScorer(
        keywords=["news", "breaking"],
        weight=1.0
    ),
    PathDepthScorer(optimal_depth=3, weight=0.7),
    FreshnessScorer(weight=0.9)
])

# Initialize advanced strategy
strategy = BFSScraperStrategy(
    max_depth=4,
    filter_chain=filter_chain,
    url_scorer=scorer,
    max_concurrent=5
)
```

### Features Demonstrated
1. **Advanced Filtering**
   - Domain filtering
   - Pattern matching
   - Content type control

2. **Intelligent Scoring**
   - Keyword relevance
   - Path optimization
   - Freshness priority

3. **Monitoring**
   - Progress tracking
   - Error handling
   - Statistics collection

4. **Resource Management**
   - Concurrent processing
   - Rate limiting
   - Cleanup handling

## Running the Examples

```bash
# Basic usage
python basic_scraper_example.py

# Advanced usage with logging
PYTHONPATH=. python advanced_scraper_example.py
```

## Example Output

### Basic Example
```
Crawled 15 pages:
- https://example.com/blog/post1: 24560 bytes
- https://example.com/blog/post2: 18920 bytes
...
```

### Advanced Example
```
INFO: Starting crawl of https://example.com/news/
INFO: Processed: https://example.com/news/breaking/story1
DEBUG: KeywordScorer: 0.85
DEBUG: FreshnessScorer: 0.95
INFO: Progress: 10 URLs processed
...
INFO: Scraping completed:
INFO: - URLs processed: 50
INFO: - Errors: 2
INFO: - Total content size: 1240.50 KB
```

## Customization

### Adding Custom Filters
```python
class CustomFilter(URLFilter):
    def apply(self, url: str) -> bool:
        # Your custom filtering logic
        return True

filter_chain.add_filter(CustomFilter())
```

### Custom Scoring Logic
```python
class CustomScorer(URLScorer):
    def _calculate_score(self, url: str) -> float:
        # Your custom scoring logic
        return 1.0

scorer = CompositeScorer([
    CustomScorer(weight=1.0),
    ...
])
```

## Best Practices

1. **Start Simple**
   - Begin with basic filtering
   - Add features incrementally
   - Test thoroughly at each step

2. **Monitor Performance**
   - Watch memory usage
   - Track processing times
   - Adjust concurrency as needed

3. **Handle Errors**
   - Implement proper error handling
   - Log important events
   - Track error statistics

4. **Optimize Resources**
   - Set appropriate delays
   - Limit concurrent requests
   - Use streaming for large crawls

## Troubleshooting

Common issues and solutions:

1. **Too Many Requests**
   ```python
   strategy = BFSScraperStrategy(
       max_concurrent=3,  # Reduce concurrent requests
       min_crawl_delay=2  # Increase delay between requests
   )
   ```

2. **Memory Issues**
   ```python
   # Use streaming mode for large crawls
   async for result in scraper.ascrape(url, stream=True):
       process_result(result)
   ```

3. **Missing Content**
   ```python
   # Check your filter chain
   filter_chain = FilterChain([
       URLPatternFilter("*"),  # Broaden patterns
       ContentTypeFilter(["*"])  # Accept all content
   ])
   ```

For more examples and use cases, visit our [GitHub repository](https://github.com/example/crawl4ai/examples).