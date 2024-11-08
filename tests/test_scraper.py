# basic_scraper_example.py
from crawl4ai.scraper import (
    AsyncWebScraper,
    BFSScraperStrategy,
    FilterChain,
    URLPatternFilter,
    ContentTypeFilter
)
from crawl4ai.async_webcrawler import AsyncWebCrawler

async def basic_scraper_example():
    """
    Basic example: Scrape a blog site for articles
    - Crawls only HTML pages
    - Stays within the blog section
    - Collects all results at once
    """
    # Create a simple filter chain
    filter_chain = FilterChain([
        # Only crawl pages within the blog section
        URLPatternFilter("*/blog/*"),
        # Only process HTML pages
        ContentTypeFilter(["text/html"])
    ])

    # Initialize the strategy with basic configuration
    strategy = BFSScraperStrategy(
        max_depth=2,  # Only go 2 levels deep
        filter_chain=filter_chain,
        url_scorer=None,  # Use default scoring
        max_concurrent=3  # Limit concurrent requests
    )

    # Create the crawler and scraper
    crawler = AsyncWebCrawler()
    scraper = AsyncWebScraper(crawler, strategy)

    # Start scraping
    try:
        result = await scraper.ascrape("https://example.com/blog/")
        
        # Process results
        print(f"Crawled {len(result.crawled_urls)} pages:")
        for url, data in result.extracted_data.items():
            print(f"- {url}: {len(data.html)} bytes")
            
    except Exception as e:
        print(f"Error during scraping: {e}")

# advanced_scraper_example.py
import logging
from crawl4ai.scraper import (
    AsyncWebScraper,
    BFSScraperStrategy,
    FilterChain,
    URLPatternFilter,
    ContentTypeFilter,
    DomainFilter,
    KeywordRelevanceScorer,
    PathDepthScorer,
    FreshnessScorer,
    CompositeScorer
)
from crawl4ai.async_webcrawler import AsyncWebCrawler

async def advanced_scraper_example():
    """
    Advanced example: Intelligent news site scraping
    - Uses all filter types
    - Implements sophisticated scoring
    - Streams results
    - Includes monitoring and logging
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("advanced_scraper")

    # Create sophisticated filter chain
    filter_chain = FilterChain([
        # Domain control
        DomainFilter(
            allowed_domains=["example.com", "blog.example.com"],
            blocked_domains=["ads.example.com", "tracker.example.com"]
        ),
        # URL patterns
        URLPatternFilter([
            "*/article/*",
            "*/news/*",
            "*/blog/*",
            re.compile(r"\d{4}/\d{2}/.*")  # Date-based URLs
        ]),
        # Content types
        ContentTypeFilter([
            "text/html",
            "application/xhtml+xml"
        ])
    ])

    # Create composite scorer
    scorer = CompositeScorer([
        # Prioritize by keywords
        KeywordRelevanceScorer(
            keywords=["news", "breaking", "update", "latest"],
            weight=1.0
        ),
        # Prefer optimal URL structure
        PathDepthScorer(
            optimal_depth=3,
            weight=0.7
        ),
        # Prioritize fresh content
        FreshnessScorer(weight=0.9)
    ])

    # Initialize strategy with advanced configuration
    strategy = BFSScraperStrategy(
        max_depth=4,
        filter_chain=filter_chain,
        url_scorer=scorer,
        max_concurrent=5,
        min_crawl_delay=1
    )

    # Create crawler and scraper
    crawler = AsyncWebCrawler()
    scraper = AsyncWebScraper(crawler, strategy)

    # Track statistics
    stats = {
        'processed': 0,
        'errors': 0,
        'total_size': 0
    }

    try:
        # Use streaming mode
        async for result in scraper.ascrape("https://example.com/news/", stream=True):
            stats['processed'] += 1
            
            if result.success:
                stats['total_size'] += len(result.html)
                logger.info(f"Processed: {result.url}")
                
                # Print scoring information
                for scorer_name, score in result.scores.items():
                    logger.debug(f"{scorer_name}: {score:.2f}")
            else:
                stats['errors'] += 1
                logger.error(f"Failed to process {result.url}: {result.error_message}")

            # Log progress regularly
            if stats['processed'] % 10 == 0:
                logger.info(f"Progress: {stats['processed']} URLs processed")

    except Exception as e:
        logger.error(f"Scraping error: {e}")
    
    finally:
        # Print final statistics
        logger.info("Scraping completed:")
        logger.info(f"- URLs processed: {stats['processed']}")
        logger.info(f"- Errors: {stats['errors']}")
        logger.info(f"- Total content size: {stats['total_size'] / 1024:.2f} KB")
        
        # Print filter statistics
        for filter_ in filter_chain.filters:
            logger.info(f"{filter_.name} stats:")
            logger.info(f"- Passed: {filter_.stats.passed_urls}")
            logger.info(f"- Rejected: {filter_.stats.rejected_urls}")
        
        # Print scorer statistics
        logger.info("Scoring statistics:")
        logger.info(f"- Average score: {scorer.stats.average_score:.2f}")
        logger.info(f"- Score range: {scorer.stats.min_score:.2f} - {scorer.stats.max_score:.2f}")

if __name__ == "__main__":
    import asyncio
    
    # Run basic example
    print("Running basic scraper example...")
    asyncio.run(basic_scraper_example())
    
    print("\nRunning advanced scraper example...")
    asyncio.run(advanced_scraper_example())