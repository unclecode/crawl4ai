"""
Crawl4ai v0.4.3b2 Features Demo
============================

This demonstration showcases three major categories of new features in Crawl4ai v0.4.3:

1. Efficiency & Speed:
   - Memory-efficient dispatcher strategies
   - New scraping algorithm
   - Streaming support for batch crawling

2. LLM Integration:
   - Automatic schema generation
   - LLM-powered content filtering
   - Smart markdown generation

3. Core Improvements:
   - Robots.txt compliance
   - Proxy rotation
   - Enhanced URL handling
   - Shared data among hooks
   - add page routes

Each demo function can be run independently or as part of the full suite.
"""

import asyncio
import os
import json
import re
import random
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

from crawl4ai import (
    AsyncWebCrawler, 
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    DisplayMode,
    MemoryAdaptiveDispatcher,
    CrawlerMonitor,
    DefaultMarkdownGenerator,
    LXMLWebScrapingStrategy,
    JsonCssExtractionStrategy,
    LLMContentFilter
)


async def demo_memory_dispatcher():
    """Demonstrates the new memory-efficient dispatcher system.
    
    Key Features:
    - Adaptive memory management
    - Real-time performance monitoring
    - Concurrent session control
    """
    print("\n=== Memory Dispatcher Demo ===")
    
    try:
        # Configuration
        browser_config = BrowserConfig(headless=True, verbose=False)
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator()
        )

        # Test URLs
        urls = ["http://example.com", "http://example.org", "http://example.net"] * 3

        print("\n📈 Initializing crawler with memory monitoring...")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            monitor = CrawlerMonitor(
                max_visible_rows=10,
                display_mode=DisplayMode.DETAILED
            )
            
            dispatcher = MemoryAdaptiveDispatcher(
                memory_threshold_percent=80.0,
                check_interval=0.5,
                max_session_permit=5,
                monitor=monitor
            )
            
            print("\n🚀 Starting batch crawl...")
            results = await crawler.arun_many(
                urls=urls,
                config=crawler_config,
                dispatcher=dispatcher
            )
            print(f"\n✅ Completed {len(results)} URLs successfully")
            
    except Exception as e:
        print(f"\n❌ Error in memory dispatcher demo: {str(e)}")

async def demo_streaming_support():
    """
    2. Streaming Support Demo
    ======================
    Shows how to process URLs as they complete using streaming
    """
    print("\n=== 2. Streaming Support Demo ===")

    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=True)

    # Test URLs
    urls = ["http://example.com", "http://example.org", "http://example.net"] * 2

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Initialize dispatcher for streaming
        dispatcher = MemoryAdaptiveDispatcher(max_session_permit=3, check_interval=0.5)

        print("Starting streaming crawl...")
        async for result in await crawler.arun_many(
            urls=urls,
            config=crawler_config,
            dispatcher=dispatcher
        ):
            # Process each result as it arrives
            print(
                f"Received result for {result.url} - Success: {result.success}"
            )
            if result.success:
                print(f"Content length: {len(result.markdown)}")

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
    config = CrawlerRunConfig(
        scraping_strategy=LXMLWebScrapingStrategy(), 
        verbose=True
    )

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

async def demo_json_schema_generation():
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

async def demo_proxy_rotation():
    """
    8. Proxy Rotation Demo
    ===================
    Demonstrates how to rotate proxies for each request using Crawl4ai.
    """
    print("\n=== 8. Proxy Rotation Demo ===")

    async def get_next_proxy(proxy_file: str = f"proxies.txt") -> Optional[Dict]:
        """Get next proxy from local file"""
        try:
            proxies = os.getenv("PROXIES", "").split(",")
                
            ip, port, username, password = random.choice(proxies).split(":")
            return {
                "server": f"http://{ip}:{port}",
                "username": username,
                "password": password,
                "ip": ip  # Store original IP for verification
            }
        except Exception as e:
            print(f"Error loading proxy: {e}")
            return None    
    
    # Create 10 test requests to httpbin
    urls = ["https://httpbin.org/ip"] * 2
    
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls:
            proxy = await get_next_proxy()
            if not proxy:
                print("No proxy available, skipping...")
                continue
                
            # Create new config with proxy
            current_config = run_config.clone(proxy_config=proxy, user_agent="")
            result = await crawler.arun(url=url, config=current_config)
            
            if result.success:
                ip_match = re.search(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', result.html)
                print(f"Proxy {proxy['ip']} -> Response IP: {ip_match.group(0) if ip_match else 'Not found'}")
                verified = ip_match.group(0) == proxy['ip']
                if verified:
                    print(f"✅ Proxy working! IP matches: {proxy['ip']}")
                else:
                    print(f"❌ Proxy failed or IP mismatch!")
            else:
                print(f"Failed with proxy {proxy['ip']}")

async def main():
    """Run all feature demonstrations."""
    print("\n📊 Running Crawl4ai v0.4.3 Feature Demos\n")
    
    # Efficiency & Speed Demos
    print("\n🚀 EFFICIENCY & SPEED DEMOS")
    await demo_memory_dispatcher()
    await demo_streaming_support()
    await demo_content_scraping()
    
    # # LLM Integration Demos
    print("\n🤖 LLM INTEGRATION DEMOS")
    await demo_json_schema_generation()
    await demo_llm_markdown()
    
    # # Core Improvements
    print("\n🔧 CORE IMPROVEMENT DEMOS")
    await demo_robots_compliance()
    await demo_proxy_rotation()

if __name__ == "__main__":
    asyncio.run(main())
