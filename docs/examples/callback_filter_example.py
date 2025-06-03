"""
Example demonstrating the use of CallbackURLFilter for custom URL filtering in deep crawling.

This example shows how to implement path-based filtering to constrain crawling to specific
sections of a website, similar to the "Same path only" vs "Entire domain" functionality.
"""

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


def create_path_scope_filter(start_url: str, scope: str = "same_path"):
    """
    Create a path-based filter callback for controlling crawl scope.
    
    Args:
        start_url: The initial URL to start crawling from
        scope: Either "same_path" (only URLs under the starting path) or 
               "entire_domain" (any path on the same domain)
    
    Returns:
        A filter function that can be used with CallbackURLFilter
    """
    parsed_start = urlparse(start_url)
    start_domain = parsed_start.netloc
    start_path = parsed_start.path.rstrip('/')
    
    def path_filter(url: str) -> bool:
        """Filter URLs based on the specified scope."""
        try:
            parsed = urlparse(url)
            
            # Always check domain first
            if parsed.netloc != start_domain:
                return False
            
            if scope == "same_path":
                # Only allow URLs under the starting path
                url_path = parsed.path.rstrip('/')
                # Check if URL path starts with our start path
                return url_path.startswith(start_path + '/') or url_path == start_path
            else:
                # entire_domain - allow any path on the same domain
                return True
                
        except Exception:
            return False
    
    return path_filter


async def example_path_scoped_crawl():
    """
    Example: Crawl GitHub Models documentation, staying within the /en/github-models path.
    """
    print("=== Path-Scoped Crawling Example ===\n")
    
    start_url = "https://docs.github.com/en/github-models"
    
    # Create a path filter that only allows URLs under /en/github-models
    path_filter_callback = create_path_scope_filter(start_url, scope="same_path")
    
    # Create the callback filter
    callback_filter = CallbackURLFilter(
        callback=path_filter_callback,
        name="GitHubModelsPathFilter"
    )
    
    # Combine with domain filter for extra safety
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["docs.github.com"]),
        callback_filter
    ])
    
    # Configure deep crawl strategy
    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_depth=2,
        max_pages=10,
        filter_chain=filter_chain
    )
    
    # Create crawler config
    config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_strategy,
        verbose=True
    )
    
    # Run the crawl
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url=start_url, config=config)
        
        print(f"\nCrawled {len(results)} pages:")
        for i, result in enumerate(results, 1):
            depth = result.metadata.get('depth', 0)
            print(f"{i}. Depth {depth}: {result.url}")
        
        # Show unique paths crawled
        print("\nUnique paths crawled:")
        paths = sorted(set(urlparse(r.url).path for r in results))
        for path in paths:
            print(f"  {path}")


async def example_custom_filter():
    """
    Example: Custom filter for API documentation with specific requirements.
    """
    print("\n\n=== Custom API Documentation Filter Example ===\n")
    
    # Create a custom filter for API documentation
    async def api_doc_filter(url: str) -> bool:
        """
        Custom filter for API documentation:
        - Must be in /api/ path
        - Must not be deprecated endpoints
        - Must not be internal/private endpoints
        - Exclude download/export URLs
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Must be in API section
        if '/api/' not in path:
            return False
        
        # Exclude deprecated endpoints
        if any(term in path for term in ['/deprecated/', '/legacy/', '/v1/']):
            return False
        
        # Exclude internal/private endpoints
        if any(term in path for term in ['/internal/', '/private/', '/_']):
            return False
        
        # Exclude download/export URLs
        if any(term in parsed.query.lower() for term in ['download', 'export', 'format=pdf']):
            return False
        
        # Exclude non-documentation file types
        if path.endswith(('.pdf', '.zip', '.tar.gz', '.json', '.xml')):
            return False
        
        return True
    
    # Create the filter
    api_filter = CallbackURLFilter(
        callback=api_doc_filter,
        name="APIDocumentationFilter"
    )
    
    # Example usage with a hypothetical API docs site
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["api.example.com"]),
        api_filter
    ])
    
    strategy = BFSDeepCrawlStrategy(
        max_depth=3,
        max_pages=50,
        filter_chain=filter_chain
    )
    
    print("Filter configured for API documentation crawling:")
    print("- Only /api/ paths")
    print("- Excludes deprecated/legacy/v1 endpoints")
    print("- Excludes internal/private endpoints")
    print("- Excludes download/export URLs")
    print("- Excludes non-documentation files")


async def example_dynamic_filter():
    """
    Example: Dynamic filter that changes behavior based on crawl progress.
    """
    print("\n\n=== Dynamic Filter Example ===\n")
    
    # Track crawled URLs
    crawled_paths = set()
    
    def dynamic_filter(url: str) -> bool:
        """
        Dynamic filter that adapts based on what's been crawled:
        - Avoids similar paths if we already have examples
        - Prioritizes diverse content
        """
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # Skip if we already have 3 examples from this section
        if len(path_parts) > 1:
            section = path_parts[0]
            section_count = sum(1 for p in crawled_paths if p.startswith(f"/{section}/"))
            if section_count >= 3:
                return False
        
        # Skip if very similar to existing paths
        for existing in crawled_paths:
            if existing in parsed.path or parsed.path in existing:
                return False
        
        # Add to tracked paths (in real implementation, do this after successful crawl)
        crawled_paths.add(parsed.path)
        return True
    
    dynamic_callback_filter = CallbackURLFilter(
        callback=dynamic_filter,
        name="DynamicDiversityFilter"
    )
    
    print("Dynamic filter configured to:")
    print("- Limit to 3 pages per section")
    print("- Avoid redundant/similar paths")
    print("- Encourage content diversity")


async def main():
    """Run all examples."""
    # Example 1: Path-scoped crawling
    await example_path_scoped_crawl()
    
    # Example 2: Custom API documentation filter
    await example_custom_filter()
    
    # Example 3: Dynamic filter
    await example_dynamic_filter()
    
    print("\n✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main()) 