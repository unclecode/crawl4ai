# CallbackURLFilter - Custom URL Filtering for Deep Crawling

The `CallbackURLFilter` is a flexible URL filter that allows you to implement custom logic for determining which URLs should be crawled during deep crawling operations.

## Overview

While crawl4ai provides several built-in filters (DomainFilter, URLPatternFilter, ContentTypeFilter, etc.), sometimes you need more complex or specific filtering logic. The `CallbackURLFilter` allows you to provide a custom function that decides whether a URL should be crawled.

## Basic Usage

```python
from crawl4ai import CallbackURLFilter, FilterChain, BFSDeepCrawlStrategy
from urllib.parse import urlparse

# Define a custom filter function
def my_filter(url: str) -> bool:
    """Only crawl URLs that contain 'docs' in the path."""
    parsed = urlparse(url)
    return 'docs' in parsed.path

# Create the filter
custom_filter = CallbackURLFilter(callback=my_filter)

# Use it in a filter chain
filter_chain = FilterChain([custom_filter])

# Apply to deep crawl strategy
strategy = BFSDeepCrawlStrategy(
    max_depth=2,
    filter_chain=filter_chain
)
```

## Advanced Examples

### 1. Path-Based Filtering (Same Path Only)

This example shows how to limit crawling to URLs under a specific path:

```python
from urllib.parse import urlparse

def create_path_filter(start_url: str):
    """Create a filter that only allows URLs under the starting path."""
    parsed_start = urlparse(start_url)
    start_domain = parsed_start.netloc
    start_path = parsed_start.path.rstrip('/')
    
    def path_filter(url: str) -> bool:
        try:
            parsed = urlparse(url)
            
            # Must be same domain
            if parsed.netloc != start_domain:
                return False
            
            # Must be under the starting path
            url_path = parsed.path.rstrip('/')
            return url_path.startswith(start_path + '/') or url_path == start_path
            
        except Exception:
            return False
    
    return path_filter

# Usage
start_url = "https://docs.github.com/en/github-models"
path_filter = CallbackURLFilter(
    callback=create_path_filter(start_url),
    name="SamePathFilter"
)
```

### 2. Complex Multi-Condition Filter

```python
async def advanced_filter(url: str) -> bool:
    """Filter with multiple conditions."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Exclude archive/old content
    if any(pattern in path for pattern in ['/archive/', '/deprecated/', '/old/']):
        return False
    
    # Only allow specific file types
    if path.endswith(('.pdf', '.zip', '.exe')):
        return False
    
    # Exclude very long URLs (likely dynamic content)
    if len(url) > 200:
        return False
    
    # Must have certain keywords in path
    if not any(keyword in path for keyword in ['api', 'guide', 'tutorial']):
        return False
    
    return True

# The filter supports both sync and async callbacks
filter = CallbackURLFilter(callback=advanced_filter)
```

### 3. Query Parameter Filtering

```python
from urllib.parse import urlparse, parse_qs

def query_filter(url: str) -> bool:
    """Filter based on query parameters."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    # Exclude URLs with certain parameters
    if 'print' in params or 'download' in params:
        return False
    
    # Only include URLs with specific parameter values
    if 'version' in params:
        version = params['version'][0]
        if version not in ['v2', 'v3', 'latest']:
            return False
    
    return True

filter = CallbackURLFilter(callback=query_filter, name="QueryFilter")
```

### 4. Combining with Other Filters

```python
from crawl4ai import (
    FilterChain, 
    DomainFilter, 
    ContentTypeFilter,
    CallbackURLFilter
)

# Custom filter for specific logic
def custom_logic(url: str) -> bool:
    # Your custom logic here
    return '/blog/' not in url  # Exclude blog posts

# Combine multiple filters
filter_chain = FilterChain([
    DomainFilter(allowed_domains=["example.com"]),
    ContentTypeFilter(allowed_types=["text/html"]),
    CallbackURLFilter(callback=custom_logic, name="NoBlogFilter")
])

# Use in deep crawl
strategy = BFSDeepCrawlStrategy(
    max_depth=3,
    max_pages=50,
    filter_chain=filter_chain
)
```

## Complete Example

Here's a complete example that crawls documentation with path filtering:

```python
import asyncio
from urllib.parse import urlparse
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BFSDeepCrawlStrategy,
    FilterChain,
    CallbackURLFilter,
    DomainFilter
)

async def crawl_docs_with_path_filter():
    """Crawl documentation staying within a specific path."""
    
    start_url = "https://docs.python.org/3/library/"
    
    # Create path filter
    parsed_start = urlparse(start_url)
    start_path = parsed_start.path.rstrip('/')
    
    def path_filter(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc != parsed_start.netloc:
            return False
        url_path = parsed.path.rstrip('/')
        return url_path.startswith(start_path)
    
    # Set up filters
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["docs.python.org"]),
        CallbackURLFilter(callback=path_filter, name="LibraryPathFilter")
    ])
    
    # Configure strategy
    strategy = BFSDeepCrawlStrategy(
        max_depth=2,
        max_pages=20,
        filter_chain=filter_chain
    )
    
    # Run crawl
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            deep_crawl_strategy=strategy,
            verbose=True
        )
        
        results = await crawler.arun(url=start_url, config=config)
        
        print(f"Crawled {len(results)} pages")
        for result in results:
            print(f"- {result.url}")

# Run the example
asyncio.run(crawl_docs_with_path_filter())
```

## Key Features

1. **Flexible Logic**: Implement any custom filtering logic you need
2. **Sync/Async Support**: Callbacks can be either regular functions or async coroutines
3. **Error Handling**: Exceptions in callbacks are caught and logged, returning False
4. **Statistics**: Like all filters, tracks passed/failed URL counts
5. **Composable**: Works seamlessly with FilterChain and other filters

## Best Practices

1. **Keep filters fast**: Filter functions are called for every discovered URL
2. **Handle exceptions**: Always use try/except in your filter logic
3. **Be specific**: More specific filters reduce unnecessary crawling
4. **Test thoroughly**: Test your filters with various URL patterns before deploying
5. **Use descriptive names**: Pass a meaningful `name` parameter for debugging

## Performance Considerations

- Filter functions are called frequently, so keep them efficient
- Avoid making network requests inside filter functions
- Use caching (e.g., `@lru_cache`) for expensive computations
- Consider using sync functions instead of async when possible for better performance 