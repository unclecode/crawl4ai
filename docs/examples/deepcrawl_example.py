import asyncio
import time

from crawl4ai import CrawlerRunConfig, AsyncWebCrawler, CacheMode
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter,
    ContentRelevanceFilter,
    SEOFilter,
)
from crawl4ai.deep_crawling.scorers import (
    KeywordRelevanceScorer,
)


# 1️⃣ Basic Deep Crawl Setup
async def basic_deep_crawl():
    """
    PART 1: Basic Deep Crawl setup - Demonstrates a simple two-level deep crawl.

    This function shows:
    - How to set up BFSDeepCrawlStrategy (Breadth-First Search)
    - Setting depth and domain parameters
    - Processing the results to show the hierarchy
    """
    print("\n===== BASIC DEEP CRAWL SETUP =====")

    # Configure a 2-level deep crawl using Breadth-First Search strategy
    # max_depth=2 means: initial page (depth 0) + 2 more levels
    # include_external=False means: only follow links within the same domain
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=2, include_external=False),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True,  # Show progress during crawling
    )

    async with AsyncWebCrawler() as crawler:
        start_time = time.perf_counter()
        results = await crawler.arun(url="https://docs.crawl4ai.com", config=config)

        # Group results by depth to visualize the crawl tree
        pages_by_depth = {}
        for result in results:
            depth = result.metadata.get("depth", 0)
            if depth not in pages_by_depth:
                pages_by_depth[depth] = []
            pages_by_depth[depth].append(result.url)

        print(f"✅ Crawled {len(results)} pages total")

        # Display crawl structure by depth
        for depth, urls in sorted(pages_by_depth.items()):
            print(f"\nDepth {depth}: {len(urls)} pages")
            # Show first 3 URLs for each depth as examples
            for url in urls[:3]:
                print(f"  → {url}")
            if len(urls) > 3:
                print(f"  ... and {len(urls) - 3} more")

        print(
            f"\n✅ Performance: {len(results)} pages in {time.perf_counter() - start_time:.2f} seconds"
        )

# 2️⃣ Stream vs. Non-Stream Execution
async def stream_vs_nonstream():
    """
    PART 2: Demonstrates the difference between stream and non-stream execution.

    Non-stream: Waits for all results before processing
    Stream: Processes results as they become available
    """
    print("\n===== STREAM VS. NON-STREAM EXECUTION =====")

    # Common configuration for both examples
    base_config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1, include_external=False),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=False,
    )

    async with AsyncWebCrawler() as crawler:
        # NON-STREAMING MODE
        print("\n📊 NON-STREAMING MODE:")
        print("  In this mode, all results are collected before being returned.")

        non_stream_config = base_config.clone()
        non_stream_config.stream = False

        start_time = time.perf_counter()
        results = await crawler.arun(
            url="https://docs.crawl4ai.com", config=non_stream_config
        )

        print(f"  ✅ Received all {len(results)} results at once")
        print(f"  ✅ Total duration: {time.perf_counter() - start_time:.2f} seconds")

        # STREAMING MODE
        print("\n📊 STREAMING MODE:")
        print("  In this mode, results are processed as they become available.")

        stream_config = base_config.clone()
        stream_config.stream = True

        start_time = time.perf_counter()
        result_count = 0
        first_result_time = None

        async for result in await crawler.arun(
            url="https://docs.crawl4ai.com", config=stream_config
        ):
            result_count += 1
            if result_count == 1:
                first_result_time = time.perf_counter() - start_time
                print(
                    f"  ✅ First result received after {first_result_time:.2f} seconds: {result.url}"
                )
            elif result_count % 5 == 0:  # Show every 5th result for brevity
                print(f"  → Result #{result_count}: {result.url}")

        print(f"  ✅ Total: {result_count} results")
        print(f"  ✅ First result: {first_result_time:.2f} seconds")
        print(f"  ✅ All results: {time.perf_counter() - start_time:.2f} seconds")
        print("\n🔍 Key Takeaway: Streaming allows processing results immediately")

# 3️⃣ Introduce Filters & Scorers
async def filters_and_scorers():
    """
    PART 3: Demonstrates the use of filters and scorers for more targeted crawling.

    This function progressively adds:
    1. A single URL pattern filter
    2. Multiple filters in a chain
    3. Scorers for prioritizing pages
    """
    print("\n===== FILTERS AND SCORERS =====")

    async with AsyncWebCrawler() as crawler:
        # SINGLE FILTER EXAMPLE
        print("\n📊 EXAMPLE 1: SINGLE URL PATTERN FILTER")
        print("  Only crawl pages containing 'core' in the URL")

        # Create a filter that only allows URLs with 'guide' in them
        url_filter = URLPatternFilter(patterns=["*core*"])

        config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=1,
                include_external=False,
                filter_chain=FilterChain([url_filter]),  # Single filter
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            cache_mode=CacheMode.BYPASS,
            verbose=True,
        )

        results = await crawler.arun(url="https://docs.crawl4ai.com", config=config)

        print(f"  ✅ Crawled {len(results)} pages matching '*core*'")
        for result in results[:3]:  # Show first 3 results
            print(f"  → {result.url}")
        if len(results) > 3:
            print(f"  ... and {len(results) - 3} more")

        # MULTIPLE FILTERS EXAMPLE
        print("\n📊 EXAMPLE 2: MULTIPLE FILTERS IN A CHAIN")
        print("  Only crawl pages that:")
        print("  1. Contain '2024' in the URL")
        print("  2. Are from 'techcrunch.com'")
        print("  3. Are of text/html or application/javascript content type")

        # Create a chain of filters
        filter_chain = FilterChain(
            [
                URLPatternFilter(patterns=["*2024*"]),
                DomainFilter(
                    allowed_domains=["techcrunch.com"],
                    blocked_domains=["guce.techcrunch.com", "oidc.techcrunch.com"],
                ),
                ContentTypeFilter(
                    allowed_types=["text/html", "application/javascript"]
                ),
            ]
        )

        config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=1, include_external=False, filter_chain=filter_chain
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            verbose=True,
        )

        results = await crawler.arun(url="https://techcrunch.com", config=config)

        print(f"  ✅ Crawled {len(results)} pages after applying all filters")
        for result in results[:3]:
            print(f"  → {result.url}")
        if len(results) > 3:
            print(f"  ... and {len(results) - 3} more")

        # SCORERS EXAMPLE
        print("\n📊 EXAMPLE 3: USING A KEYWORD RELEVANCE SCORER")
        print(
            "Score pages based on relevance to keywords: 'crawl', 'example', 'async', 'configuration','javascript','css'"
        )

        # Create a keyword relevance scorer
        keyword_scorer = KeywordRelevanceScorer(
            keywords=["crawl", "example", "async", "configuration","javascript","css"], weight=1
        )

        config = CrawlerRunConfig(
            deep_crawl_strategy=BestFirstCrawlingStrategy(  
                max_depth=1, include_external=False, url_scorer=keyword_scorer
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            stream=True,
        )

        results = []
        async for result in await crawler.arun(
            url="https://docs.crawl4ai.com", config=config
        ):
            results.append(result)
            score = result.metadata.get("score")
            print(f"  → Score: {score:.2f} | {result.url}")

        print(f"  ✅ Crawler prioritized {len(results)} pages by relevance score")
        print("  🔍 Note: BestFirstCrawlingStrategy visits highest-scoring pages first")

# 4️⃣ Advanced Filters
async def advanced_filters():
    """
    PART 4: Demonstrates advanced filtering techniques for specialized crawling.

    This function covers:
    - SEO filters
    - Text relevancy filtering
    - Combining advanced filters
    """
    print("\n===== ADVANCED FILTERS =====")

    async with AsyncWebCrawler() as crawler:
        # SEO FILTER EXAMPLE
        print("\n📊 EXAMPLE 1: SEO FILTERS")
        print(
            "Quantitative SEO quality assessment filter based searching keywords in the head section"
        )

        seo_filter = SEOFilter(
            threshold=0.5, keywords=["dynamic", "interaction", "javascript"]
        )

        config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=1, filter_chain=FilterChain([seo_filter])
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            verbose=True,
            cache_mode=CacheMode.BYPASS,
        )

        results = await crawler.arun(url="https://docs.crawl4ai.com", config=config)

        print(f"  ✅ Found {len(results)} pages with relevant keywords")
        for result in results:
            print(f"  → {result.url}")

        # ADVANCED TEXT RELEVANCY FILTER
        print("\n📊 EXAMPLE 2: ADVANCED TEXT RELEVANCY FILTER")

        # More sophisticated content relevance filter
        relevance_filter = ContentRelevanceFilter(
            query="Interact with the web using your authentic digital identity",
            threshold=0.7,
        )

        config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=1, filter_chain=FilterChain([relevance_filter])
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            verbose=True,
            cache_mode=CacheMode.BYPASS,
        )

        results = await crawler.arun(url="https://docs.crawl4ai.com", config=config)

        print(f"  ✅ Found {len(results)} pages")
        for result in results:
            relevance_score = result.metadata.get("relevance_score", 0)
            print(f"  → Score: {relevance_score:.2f} | {result.url}")

# 5️⃣ Max Pages and Score Thresholds
async def max_pages_and_thresholds():
    """
    PART 5: Demonstrates using max_pages and score_threshold parameters with different strategies.
    
    This function shows:
    - How to limit the number of pages crawled
    - How to set score thresholds for more targeted crawling
    - Comparing BFS, DFS, and Best-First strategies with these parameters
    """
    print("\n===== MAX PAGES AND SCORE THRESHOLDS =====")
    
    from crawl4ai.deep_crawling import DFSDeepCrawlStrategy
    
    async with AsyncWebCrawler() as crawler:
        # Define a common keyword scorer for all examples
        keyword_scorer = KeywordRelevanceScorer(
            keywords=["browser", "crawler", "web", "automation"], 
            weight=1.0
        )
        
        # EXAMPLE 1: BFS WITH MAX PAGES
        print("\n📊 EXAMPLE 1: BFS STRATEGY WITH MAX PAGES LIMIT")
        print("  Limit the crawler to a maximum of 5 pages")
        
        bfs_config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=2, 
                include_external=False,
                url_scorer=keyword_scorer,
                max_pages=5  # Only crawl 5 pages
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            verbose=True,
            cache_mode=CacheMode.BYPASS,
        )
        
        results = await crawler.arun(url="https://docs.crawl4ai.com", config=bfs_config)
        
        print(f"  ✅ Crawled exactly {len(results)} pages as specified by max_pages")
        for result in results:
            depth = result.metadata.get("depth", 0)
            print(f"  → Depth: {depth} | {result.url}")
            
        # EXAMPLE 2: DFS WITH SCORE THRESHOLD
        print("\n📊 EXAMPLE 2: DFS STRATEGY WITH SCORE THRESHOLD")
        print("  Only crawl pages with a relevance score above 0.5")
        
        dfs_config = CrawlerRunConfig(
            deep_crawl_strategy=DFSDeepCrawlStrategy(
                max_depth=2,
                include_external=False, 
                url_scorer=keyword_scorer,
                score_threshold=0.7,  # Only process URLs with scores above 0.5
                max_pages=10
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            verbose=True,
            cache_mode=CacheMode.BYPASS,
        )
        
        results = await crawler.arun(url="https://docs.crawl4ai.com", config=dfs_config)
        
        print(f"  ✅ Crawled {len(results)} pages with scores above threshold")
        for result in results:
            score = result.metadata.get("score", 0)
            depth = result.metadata.get("depth", 0)
            print(f"  → Depth: {depth} | Score: {score:.2f} | {result.url}")
            
        # EXAMPLE 3: BEST-FIRST WITH BOTH CONSTRAINTS
        print("\n📊 EXAMPLE 3: BEST-FIRST STRATEGY WITH BOTH CONSTRAINTS")
        print("  Limit to 7 pages with scores above 0.3, prioritizing highest scores")
        
        bf_config = CrawlerRunConfig(
            deep_crawl_strategy=BestFirstCrawlingStrategy(
                max_depth=2,
                include_external=False,
                url_scorer=keyword_scorer,
                max_pages=7,          # Limit to 7 pages total
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            verbose=True,
            cache_mode=CacheMode.BYPASS,
            stream=True,
        )
        
        results = []
        async for result in await crawler.arun(url="https://docs.crawl4ai.com", config=bf_config):
            results.append(result)
            score = result.metadata.get("score", 0)
            depth = result.metadata.get("depth", 0)
            print(f"  → Depth: {depth} | Score: {score:.2f} | {result.url}")
            
        print(f"  ✅ Crawled {len(results)} high-value pages with scores above 0.3")
        if results:
            avg_score = sum(r.metadata.get('score', 0) for r in results) / len(results)
            print(f"  ✅ Average score: {avg_score:.2f}")
            print("  🔍 Note: BestFirstCrawlingStrategy visited highest-scoring pages first")

# 6️⃣ Wrap-Up and Key Takeaways
async def wrap_up():
    """
    PART 6: Wrap-Up and Key Takeaways

    Summarize the key concepts learned in this tutorial.
    """
    print("\n===== COMPLETE CRAWLER EXAMPLE =====")
    print("Combining filters, scorers, and streaming for an optimized crawl")

    # Create a sophisticated filter chain
    filter_chain = FilterChain(
        [
            DomainFilter(
                allowed_domains=["docs.crawl4ai.com"],
                blocked_domains=["old.docs.crawl4ai.com"],
            ),
            URLPatternFilter(patterns=["*core*", "*advanced*", "*blog*"]),
            ContentTypeFilter(allowed_types=["text/html"]),
        ]
    )

    # Create a composite scorer that combines multiple scoring strategies
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"], weight=0.7
    )
    # Set up the configuration
    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=1,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer,
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=True,
    )

    # Execute the crawl
    results = []
    start_time = time.perf_counter()

    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(
            url="https://docs.crawl4ai.com", config=config
        ):
            results.append(result)
            score = result.metadata.get("score", 0)
            depth = result.metadata.get("depth", 0)
            print(f"→ Depth: {depth} | Score: {score:.2f} | {result.url}")

    duration = time.perf_counter() - start_time

    # Summarize the results
    print(f"\n✅ Crawled {len(results)} high-value pages in {duration:.2f} seconds")
    print(
        f"✅ Average score: {sum(r.metadata.get('score', 0) for r in results) / len(results):.2f}"
    )

    # Group by depth
    depth_counts = {}
    for result in results:
        depth = result.metadata.get("depth", 0)
        depth_counts[depth] = depth_counts.get(depth, 0) + 1

    print("\n📊 Pages crawled by depth:")
    for depth, count in sorted(depth_counts.items()):
        print(f"  Depth {depth}: {count} pages")


async def run_tutorial():
    """
    Executes all tutorial sections in sequence.
    """
    print("\n🚀 CRAWL4AI DEEP CRAWLING TUTORIAL 🚀")
    print("======================================")
    print("This tutorial will walk you through deep crawling techniques,")
    print("from basic to advanced, using the Crawl4AI library.")

    # Define sections - uncomment to run specific parts during development
    tutorial_sections = [
        basic_deep_crawl,
        stream_vs_nonstream,
        filters_and_scorers,
        max_pages_and_thresholds, 
        advanced_filters,
        wrap_up,
    ]

    for section in tutorial_sections:
        await section()

    print("\n🎉 TUTORIAL COMPLETE! 🎉")
    print("You now have a comprehensive understanding of deep crawling with Crawl4AI.")
    print("For more information, check out https://docs.crawl4ai.com")

# Execute the tutorial when run directly
if __name__ == "__main__":
    asyncio.run(run_tutorial())