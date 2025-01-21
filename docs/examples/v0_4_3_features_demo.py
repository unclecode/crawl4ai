"""
Crawl4ai v0.4.3 Features Demo
============================

This example demonstrates the major new features introduced in Crawl4ai v0.4.3.
Each section showcases a specific feature with practical examples and explanations.
"""

import asyncio
import os
from crawl4ai import *


async def demo_memory_dispatcher():
    """
    1. Memory Dispatcher System Demo
    ===============================
    Shows how to use the new memory dispatcher with monitoring
    """
    print("\n=== 1. Memory Dispatcher System Demo ===")

    # Configure crawler
    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, markdown_generator=DefaultMarkdownGenerator()
    )

    # Test URLs
    urls = ["http://example.com", "http://example.org", "http://example.net"] * 3

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Initialize dispatcher with monitoring
        monitor = CrawlerMonitor(
            max_visible_rows=10,
            display_mode=DisplayMode.DETAILED,  # Can be DETAILED or AGGREGATED
        )

        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=80.0,  # Memory usage threshold
            check_interval=0.5,  # How often to check memory
            max_session_permit=5,  # Max concurrent crawls
            monitor=monitor,  # Pass the monitor
        )

        # Run with memory monitoring
        print("Starting batch crawl with memory monitoring...")
        results = await dispatcher.run_urls(
            urls=urls,
            crawler=crawler,
            config=crawler_config,
        )
        print(f"Completed {len(results)} URLs")


async def demo_streaming_support():
    """
    2. Streaming Support Demo
    ======================
    Shows how to process URLs as they complete using streaming
    """
    print("\n=== 2. Streaming Support Demo ===")

    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=True)

    # Test URLs
    urls = ["http://example.com", "http://example.org", "http://example.net"] * 2

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Initialize dispatcher for streaming
        dispatcher = MemoryAdaptiveDispatcher(max_session_permit=3, check_interval=0.5)

        print("Starting streaming crawl...")
        async for result in dispatcher.run_urls_stream(
            urls=urls, crawler=crawler, config=crawler_config
        ):
            # Process each result as it arrives
            print(
                f"Received result for {result.url} - Success: {result.result.success}"
            )
            if result.result.success:
                print(f"Content length: {len(result.result.markdown)}")


async def demo_content_scraping():
    """
    3. Content Scraping Strategy Demo
    ==============================
    Demonstrates the new LXMLWebScrapingStrategy for faster content scraping.
    """
    print("\n=== 3. Content Scraping Strategy Demo ===")

    crawler = AsyncWebCrawler()
    url = "https://example.com/article"

    # Configure with the new LXML strategy
    config = CrawlerRunConfig(scraping_strategy=LXMLWebScrapingStrategy(), verbose=True)

    print("Scraping content with LXML strategy...")
    async with crawler:
        result = await crawler.arun(url, config=config)
        if result.success:
            print("Successfully scraped content using LXML strategy")


async def demo_llm_markdown():
    """
    4. LLM-Powered Markdown Generation Demo
    ===================================
    Shows how to use the new LLM-powered content filtering and markdown generation.
    """
    print("\n=== 4. LLM-Powered Markdown Generation Demo ===")

    crawler = AsyncWebCrawler()
    url = "https://docs.python.org/3/tutorial/classes.html"

    content_filter = LLMContentFilter(
        provider="openai/gpt-4o",
        api_token=os.getenv("OPENAI_API_KEY"),
        instruction="""
        Focus on extracting the core educational content about Python classes.
        Include:
        - Key concepts and their explanations
        - Important code examples
        - Essential technical details
        Exclude:
        - Navigation elements
        - Sidebars
        - Footer content
        - Version information
        - Any non-essential UI elements
        
        Format the output as clean markdown with proper code blocks and headers.
        """,
        verbose=True,
    )

    # Configure LLM-powered markdown generation
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=content_filter
        ), 
        cache_mode = CacheMode.BYPASS,
        verbose=True
    )

    print("Generating focused markdown with LLM...")
    async with crawler:
        result = await crawler.arun(url, config=config)
        if result.success and result.markdown_v2:
            print("Successfully generated LLM-filtered markdown")
            print("First 500 chars of filtered content:")
            print(result.markdown_v2.fit_markdown[:500])
            print("Successfully generated LLM-filtered markdown")


async def demo_robots_compliance():
    """
    5. Robots.txt Compliance Demo
    ==========================
    Demonstrates the new robots.txt compliance feature with SQLite caching.
    """
    print("\n=== 5. Robots.txt Compliance Demo ===")

    crawler = AsyncWebCrawler()
    urls = ["https://example.com", "https://facebook.com", "https://twitter.com"]

    # Enable robots.txt checking
    config = CrawlerRunConfig(check_robots_txt=True, verbose=True)

    print("Crawling with robots.txt compliance...")
    async with crawler:
        results = await crawler.arun_many(urls, config=config)
        for result in results:
            if result.status_code == 403:
                print(f"Access blocked by robots.txt: {result.url}")
            elif result.success:
                print(f"Successfully crawled: {result.url}")



async def demo_llm_schema_generation():
    """
    7. LLM-Powered Schema Generation Demo
    =================================
    Demonstrates automatic CSS and XPath schema generation using LLM models.
    """
    print("\n=== 7. LLM-Powered Schema Generation Demo ===")

    # Example HTML content for a job listing
    html_content = """
    <div class="job-listing">
        <h1 class="job-title">Senior Software Engineer</h1>
        <div class="job-details">
            <span class="location">San Francisco, CA</span>
            <span class="salary">$150,000 - $200,000</span>
            <div class="requirements">
                <h2>Requirements</h2>
                <ul>
                    <li>5+ years Python experience</li>
                    <li>Strong background in web crawling</li>
                </ul>
            </div>
        </div>
    </div>
    """

    print("Generating CSS selectors schema...")
    # Generate CSS selectors with a specific query
    css_schema = JsonCssExtractionStrategy.generate_schema(
        html_content,
        schema_type="CSS",
        query="Extract job title, location, and salary information",
        provider="openai/gpt-4o",  # or use other providers like "ollama"
    )
    print("\nGenerated CSS Schema:")
    print(css_schema)

    # Example of using the generated schema with crawler
    crawler = AsyncWebCrawler()
    url = "https://example.com/job-listing"

    # Create an extraction strategy with the generated schema
    extraction_strategy = JsonCssExtractionStrategy(schema=css_schema)

    config = CrawlerRunConfig(extraction_strategy=extraction_strategy, verbose=True)

    print("\nTesting generated schema with crawler...")
    async with crawler:
        result = await crawler.arun(url, config=config)
        if result.success:
            print(json.dumps(result.extracted_content, indent=2) if result.extracted_content else None)
            print("Successfully used generated schema for crawling")


async def main():
    """Run all feature demonstrations."""
    demo_memory_dispatcher(),
    print("\n" + "=" * 50 + "\n")
    demo_streaming_support(),
    print("\n" + "=" * 50 + "\n")
    demo_content_scraping(),
    print("\n" + "=" * 50 + "\n")
    demo_llm_schema_generation(),
    print("\n" + "=" * 50 + "\n")
    demo_llm_markdown(),
    print("\n" + "=" * 50 + "\n")
    demo_robots_compliance(),
    print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
