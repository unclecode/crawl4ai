from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawl import (
    BFSDeepCrawlStrategy,
    FilterChain,
    URLPatternFilter,
    ContentTypeFilter,
    DomainFilter,
    KeywordRelevanceScorer,
    PathDepthScorer,
    FreshnessScorer,
    CompositeScorer,
)
from crawl4ai.async_webcrawler import AsyncWebCrawler
import re
import time
import logging

browser_config = BrowserConfig(headless=True, viewport_width=800, viewport_height=600)


async def basic_example():
    """
    Basic example: Deep crawl a blog site for articles
    - Crawls only HTML pages
    - Stays within the blog section
    - Collects all results at once
    """
    # Create a simple filter chain
    filter_chain = FilterChain(
        [
            # Only crawl pages within the blog section
            URLPatternFilter("*/basic/*"),
            # Only process HTML pages
            ContentTypeFilter(["text/html"]),
        ]
    )

    # Initialize the strategy with basic configuration
    bfs_strategy = BFSDeepCrawlStrategy(
        max_depth=2,  # Only go 2 levels deep
        filter_chain=filter_chain,
        url_scorer=None,  # Use default scoring
        process_external_links=True,
    )

    # Create the crawler
    async with AsyncWebCrawler(
        config=browser_config,
    ) as crawler:
        # Start scraping
        try:
            results = await crawler.arun(
                "https://crawl4ai.com/mkdocs",
                CrawlerRunConfig(deep_crawl_strategy=bfs_strategy),
            )
            # Process results
            print(f"Crawled {len(results)} pages:")
            for result in results:
                print(f"- {result.url}: {len(result.html)} bytes")

        except Exception as e:
            print(f"Error during scraping: {e}")


async def advanced_example():
    """
    Advanced example: Intelligent news site crawling
    - Uses all filter types
    - Implements sophisticated scoring
    - Streams results
    - Includes monitoring and logging
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("advanced_deep_crawler")

    # Create sophisticated filter chain
    filter_chain = FilterChain(
        [
            # Domain control
            DomainFilter(
                allowed_domains=["techcrunch.com"],
                blocked_domains=["login.techcrunch.com", "legal.yahoo.com"],
            ),
            # URL patterns
            URLPatternFilter(
                [
                    "*/article/*",
                    "*/news/*",
                    "*/blog/*",
                    re.compile(r"\d{4}/\d{2}/.*"),  # Date-based URLs
                ]
            ),
            # Content types
            ContentTypeFilter(["text/html", "application/xhtml+xml"]),
        ]
    )

    # Create composite scorer
    scorer = CompositeScorer(
        [
            # Prioritize by keywords
            KeywordRelevanceScorer(
                keywords=["news", "breaking", "update", "latest"], weight=1.0
            ),
            # Prefer optimal URL structure
            PathDepthScorer(optimal_depth=3, weight=0.7),
            # Prioritize fresh content
            FreshnessScorer(weight=0.9),
        ]
    )

    # Initialize strategy with advanced configuration
    bfs_strategy = BFSDeepCrawlStrategy(
        max_depth=2, filter_chain=filter_chain, url_scorer=scorer
    )

    # Create crawler
    async with AsyncWebCrawler(
        config=browser_config,
    ) as crawler:

        # Track statistics
        stats = {"processed": 0, "errors": 0, "total_size": 0}

        try:
            # Use streaming mode
            results = []
            result_generator = await crawler.arun(
                "https://techcrunch.com",
                config=CrawlerRunConfig(deep_crawl_strategy=bfs_strategy, stream=True),
            )
            async for result in result_generator:
                stats["processed"] += 1

                if result.success:
                    stats["total_size"] += len(result.html)
                    logger.info(
                        f"Processed at depth: {result.depth} with score: {result.score:.3f} : \n {result.url}"
                    )
                    results.append(result)
                else:
                    stats["errors"] += 1
                    logger.error(
                        f"Failed to process {result.url}: {result.error_message}"
                    )

                # Log progress regularly
                if stats["processed"] % 10 == 0:
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
            logger.info(
                f"- Score range: {scorer.stats.min_score:.2f} - {scorer.stats.max_score:.2f}"
            )


async def basic_example_many_urls():
    filter_chain = FilterChain(
        [
            URLPatternFilter("*/basic/*"),
            ContentTypeFilter(["text/html"]),
        ]
    )
    # Initialize the strategy with basic configuration
    bfs_strategy = BFSDeepCrawlStrategy(
        max_depth=2,  # Only go 2 levels deep
        filter_chain=filter_chain,
        url_scorer=None,  # Use default scoring
        process_external_links=False,
    )

    # Create the crawler
    async with AsyncWebCrawler(
        config=browser_config,
    ) as crawler:
        # Start scraping
        try:
            results = await crawler.arun_many(
                urls=["https://crawl4ai.com/mkdocs","https://aravindkarnam.com"],
                config=CrawlerRunConfig(deep_crawl_strategy=bfs_strategy),
            )
            # Process results
            print(f"Crawled {len(results)} pages:")
            for url_result in results:
                for result in url_result:
                    print(f"- {result.url}: {len(result.html)} bytes")

        except Exception as e:
            print(f"Error during scraping: {e}")

async def basic_example_many_urls_stream():
    filter_chain = FilterChain(
        [
            URLPatternFilter("*/basic/*"),
            ContentTypeFilter(["text/html"]),
        ]
    )
    # Initialize the strategy with basic configuration
    bfs_strategy = BFSDeepCrawlStrategy(
        max_depth=2,  # Only go 2 levels deep
        filter_chain=filter_chain,
        url_scorer=None,  # Use default scoring
        process_external_links=False,
    )

    # Create the crawler
    async with AsyncWebCrawler(
        config=browser_config,
    ) as crawler:
        # Start scraping
        try:
            async for result in await crawler.arun_many(
                urls=["https://crawl4ai.com/mkdocs","https://aravindkarnam.com"],
                config=CrawlerRunConfig(deep_crawl_strategy=bfs_strategy,stream=True),
            ):
            # Process results
                print(f"- {result.url}: {len(result.html)} bytes")
        except Exception as e:
            print(f"Error during scraping: {e}")

if __name__ == "__main__":
    import asyncio
    import time

    # Run basic example
    start_time = time.perf_counter()
    print("Running basic Deep crawl example...")
    asyncio.run(basic_example())
    end_time = time.perf_counter()
    print(f"Basic deep crawl example completed in {end_time - start_time:.2f} seconds")

    # Run advanced example
    print("\nRunning advanced deep crawl example...")
    asyncio.run(advanced_example())

    print("\nRunning advanced deep crawl example with arun_many...")
    asyncio.run(basic_example_many_urls())

    print("\nRunning advanced deep crawl example with arun_many streaming enabled...")
    asyncio.run(basic_example_many_urls_stream())
