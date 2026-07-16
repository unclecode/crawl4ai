import asyncio
from typing import List

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BFSDeepCrawlStrategy,
    CrawlResult,
    FilterChain,
    DomainFilter,
    URLPatternFilter,
)

# Import necessary classes from crawl4ai library:
# - AsyncWebCrawler: The main class for web crawling.
# - CrawlerRunConfig: Configuration class for crawler behavior.
# - BFSDeepCrawlStrategy: Breadth-First Search deep crawling strategy.
# - CrawlResult: Data model for individual crawl results.
# - FilterChain: Used to chain multiple URL filters.
# - URLPatternFilter: Filter URLs based on patterns.
# You had from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, which is also correct,
# but for simplicity and consistency, we will use the direct import from crawl4ai in this example, as it is re-exported in __init__.py

async def basic_deep_crawl():
    """
    Performs a basic deep crawl starting from a seed URL, demonstrating:
    - Breadth-First Search (BFS) deep crawling strategy.
    - Filtering URLs based on URL patterns.
    - Accessing crawl results and metadata.
    """

    # 1. Define URL Filters:
    # Create a URLPatternFilter to include only URLs containing "text".
    # This filter will be used to restrict crawling to URLs that are likely to contain textual content.
    url_filter = URLPatternFilter(
        patterns=[
            "*text*", # Include URLs that contain "text" in their path or URL
        ]
    )

    # Create a DomainFilter to allow only URLs from the "groq.com" domain and block URLs from the "example.com" domain.
    # This filter will be used to restrict crawling to URLs within the "groq.com" domain.
    domain_filter = DomainFilter(
        allowed_domains=["groq.com"],
        blocked_domains=["example.com"],
    )

    # 2. Configure CrawlerRunConfig for Deep Crawling:
    # Configure CrawlerRunConfig to use BFSDeepCrawlStrategy for deep crawling.
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2,  # Set the maximum depth of crawling to 2 levels from the start URL
            max_pages=10, # Limit the total number of pages to crawl to 10, to prevent excessive crawling
            include_external=False, # Set to False to only crawl URLs within the same domain as the start URL
            filter_chain=FilterChain(filters=[url_filter, domain_filter]), # Apply the URLPatternFilter and DomainFilter to filter URLs during deep crawl
        ),
        verbose=True, # Enable verbose logging to see detailed output during crawling
    )

    # 3. Initialize and Run AsyncWebCrawler:
    # Use AsyncWebCrawler as a context manager for automatic start and close.
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            # url="https://docs.crawl4ai.com", # Uncomment to use crawl4ai documentation as start URL
            url="https://console.groq.com/docs", # Set the start URL for deep crawling to Groq documentation
            config=config, # Pass the configured CrawlerRunConfig to arun method
        )

        # 4. Process and Print Crawl Results:
        # Iterate through the list of CrawlResult objects returned by the deep crawl.
        for result in results:
            # Print the URL and its crawl depth from the metadata for each crawled URL.
            print(f"URL: {result.url}, Depth: {result.metadata.get('depth', 0)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(basic_deep_crawl())
