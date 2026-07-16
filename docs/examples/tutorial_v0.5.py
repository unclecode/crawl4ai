import asyncio
import time
import re

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, MemoryAdaptiveDispatcher, HTTPCrawlerConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import (
    BestFirstCrawlingStrategy,
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter,
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from crawl4ai import ProxyConfig
from crawl4ai import RoundRobinProxyStrategy
from crawl4ai.content_filter_strategy import LLMContentFilter
from crawl4ai import DefaultMarkdownGenerator
from crawl4ai import LLMConfig
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.processors.pdf import PDFCrawlerStrategy, PDFContentScrapingStrategy
from pprint import pprint


# 1️⃣ Deep Crawling with Best-First Strategy
async def deep_crawl():
    """
    PART 1: Deep Crawling with Best-First Strategy
    
    This function demonstrates:
    - Using the BestFirstCrawlingStrategy
    - Creating filter chains to narrow down crawl targets
    - Using a scorer to prioritize certain URLs
    - Respecting robots.txt rules
    """
    print("\n===== DEEP CRAWLING =====")
    print("This example shows how to implement deep crawling with filters, scorers, and robots.txt compliance.")
    
    # Create a filter chain to filter urls based on patterns, domains and content type
    filter_chain = FilterChain(
        [
            DomainFilter(
                allowed_domains=["docs.crawl4ai.com"],
                blocked_domains=["old.docs.crawl4ai.com"],
            ),
            URLPatternFilter(patterns=["*core*", "*advanced*"],),
            ContentTypeFilter(allowed_types=["text/html"]),
        ]
    )
    
    # Create a keyword scorer that prioritises the pages with certain keywords first
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"], weight=0.7
    )
    
    # Set up the configuration with robots.txt compliance enabled
    deep_crawl_config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer,
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=True,
        check_robots_txt=True,  # Enable robots.txt compliance
    )
    
    # Execute the crawl
    async with AsyncWebCrawler() as crawler:
        print("\n📊 Starting deep crawl with Best-First strategy...")
        print("  - Filtering by domain, URL patterns, and content type")
        print("  - Scoring pages based on keyword relevance")
        print("  - Respecting robots.txt rules")
        
        start_time = time.perf_counter()
        results = []
        
        async for result in await crawler.arun(url="https://docs.crawl4ai.com", config=deep_crawl_config):
            # Print each result as it comes in
            depth = result.metadata.get("depth", 0)
            score = result.metadata.get("score", 0)
            print(f"Crawled: {result.url} (Depth: {depth}), score: {score:.2f}")
            results.append(result)
            
        duration = time.perf_counter() - start_time
        
        # Print summary statistics
        print(f"\n✅ Crawled {len(results)} high-value pages in {duration:.2f} seconds")
        
        # Group by depth
        if results:
            depth_counts = {}
            for result in results:
                depth = result.metadata.get("depth", 0)
                depth_counts[depth] = depth_counts.get(depth, 0) + 1
            
            print("\n📊 Pages crawled by depth:")
            for depth, count in sorted(depth_counts.items()):
                print(f"  Depth {depth}: {count} pages")


# 2️⃣ Memory-Adaptive Dispatcher
async def memory_adaptive_dispatcher():
    """
    PART 2: Memory-Adaptive Dispatcher
    
    This function demonstrates:
    - Using MemoryAdaptiveDispatcher to manage system memory
    - Batch and streaming modes with multiple URLs
    """
    print("\n===== MEMORY-ADAPTIVE DISPATCHER =====")
    print("This example shows how to use the memory-adaptive dispatcher for resource management.")
    
    # Configure the dispatcher (optional, defaults are used if not provided)
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=80.0,  # Pause if memory usage exceeds 80%
        check_interval=0.5,  # Check memory every 0.5 seconds
    )
    
    # Test URLs
    urls = [
        "https://docs.crawl4ai.com", 
        "https://github.com/unclecode/crawl4ai"
    ]
    
    async def batch_mode():
        print("\n📊 BATCH MODE:")
        print("  In this mode, all results are collected before being returned.")
        
        async with AsyncWebCrawler() as crawler:
            start_time = time.perf_counter()
            results = await crawler.arun_many(
                urls=urls,
                config=CrawlerRunConfig(stream=False),  # Batch mode
                dispatcher=dispatcher,
            )
            
            print(f"  ✅ Received all {len(results)} results after {time.perf_counter() - start_time:.2f} seconds")
            for result in results:
                print(f"  → {result.url} with status code: {result.status_code}")
    
    async def stream_mode():
        print("\n📊 STREAMING MODE:")
        print("  In this mode, results are processed as they become available.")
        
        async with AsyncWebCrawler() as crawler:
            start_time = time.perf_counter()
            count = 0
            first_result_time = None
            
            async for result in await crawler.arun_many(
                urls=urls,
                config=CrawlerRunConfig(stream=True),  # Stream mode
                dispatcher=dispatcher,
            ):
                count += 1
                current_time = time.perf_counter() - start_time
                
                if count == 1:
                    first_result_time = current_time
                    print(f"  ✅ First result after {first_result_time:.2f} seconds: {result.url}")
                else:
                    print(f"  → Result #{count} after {current_time:.2f} seconds: {result.url}")
            
            print(f"  ✅ Total: {count} results")
            print(f"  ✅ First result: {first_result_time:.2f} seconds")
            print(f"  ✅ All results: {time.perf_counter() - start_time:.2f} seconds")
    
    # Run both examples
    await batch_mode()
    await stream_mode()
    
    print("\n🔍 Key Takeaway: The memory-adaptive dispatcher prevents OOM errors")
    print("  and manages concurrency based on system resources.")


# 3️⃣ HTTP Crawler Strategy
async def http_crawler_strategy():
    """
    PART 3: HTTP Crawler Strategy
    
    This function demonstrates:
    - Using the lightweight HTTP-only crawler
    - Setting custom headers and configurations
    """
    print("\n===== HTTP CRAWLER STRATEGY =====")
    print("This example shows how to use the fast, lightweight HTTP-only crawler.")
    
    # Use the HTTP crawler strategy
    http_config = HTTPCrawlerConfig(
        method="GET",
        headers={"User-Agent": "MyCustomBot/1.0"},
        follow_redirects=True,
        verify_ssl=True
    )
    
    print("\n📊 Initializing HTTP crawler strategy...")
    print("  - Using custom User-Agent: MyCustomBot/1.0")
    print("  - Following redirects: Enabled")
    print("  - Verifying SSL: Enabled")
    
    # Create crawler with HTTP strategy
    async with AsyncWebCrawler(
        crawler_strategy=AsyncHTTPCrawlerStrategy(browser_config=http_config)
    ) as crawler:
        start_time = time.perf_counter()
        result = await crawler.arun("https://example.com")
        duration = time.perf_counter() - start_time
        
        print(f"\n✅ Crawled in {duration:.2f} seconds")
        print(f"✅ Status code: {result.status_code}")
        print(f"✅ Content length: {len(result.html)} bytes")
        
        # Check if there was a redirect
        if result.redirected_url and result.redirected_url != result.url:
            print(f"ℹ️ Redirected from {result.url} to {result.redirected_url}")
    
    print("\n🔍 Key Takeaway: HTTP crawler is faster and more memory-efficient")
    print("  than browser-based crawling for simple pages.")


# 4️⃣ Proxy Rotation
async def proxy_rotation():
    """
    PART 4: Proxy Rotation
    
    This function demonstrates:
    - Setting up a proxy rotation strategy
    - Using multiple proxies in a round-robin fashion
    """
    print("\n===== PROXY ROTATION =====")
    print("This example shows how to implement proxy rotation for distributed crawling.")
    
    # Load proxies and create rotation strategy
    proxies = ProxyConfig.from_env()
    #eg: export PROXIES="ip1:port1:username1:password1,ip2:port2:username2:password2"
    if not proxies:
        print("No proxies found in environment. Set PROXIES env variable!")
        return
        
    proxy_strategy = RoundRobinProxyStrategy(proxies)
    
    # Create configs
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        proxy_rotation_strategy=proxy_strategy
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        urls = ["https://httpbin.org/ip"] * (len(proxies) * 2)  # Test each proxy twice

        print("\n📈 Initializing crawler with proxy rotation...")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print("\n🚀 Starting batch crawl with proxy rotation...")
            results = await crawler.arun_many(
                urls=urls,
                config=run_config
            )
            for result in results:
                if result.success:
                    ip_match = re.search(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', result.html)
                    current_proxy = run_config.proxy_config if run_config.proxy_config else None
                    
                    if current_proxy and ip_match:
                        print(f"URL {result.url}")
                        print(f"Proxy {current_proxy.server} -> Response IP: {ip_match.group(0)}")
                        verified = ip_match.group(0) == current_proxy.ip
                        if verified:
                            print(f"✅ Proxy working! IP matches: {current_proxy.ip}")
                        else:
                            print("❌ Proxy failed or IP mismatch!")
                    print("---")
                else:
                    print(f"❌ Crawl via proxy failed!: {result.error_message}")


# 5️⃣ LLM Content Filter (requires API key)
async def llm_content_filter():
    """
    PART 5: LLM Content Filter
    
    This function demonstrates:
    - Configuring LLM providers via LLMConfig
    - Using LLM to generate focused markdown
    - LLMConfig for configuration
    
    Note: Requires a valid API key for the chosen LLM provider
    """
    print("\n===== LLM CONTENT FILTER =====")
    print("This example shows how to use LLM to generate focused markdown content.")
    print("Note: This example requires an API key. Set it in environment variables.")
    
    # Create LLM configuration
    # Replace with your actual API key or set as environment variable
    llm_config = LLMConfig(
        provider="gemini/gemini-1.5-pro", 
        api_token="env:GEMINI_API_KEY"  # Will read from GEMINI_API_KEY environment variable
    )
    
    print("\n📊 Setting up LLM content filter...")
    print(f"  - Provider: {llm_config.provider}")
    print("  - API token: Using environment variable")
    print("  - Instruction: Extract key concepts and summaries")
    
    # Create markdown generator with LLM filter
    markdown_generator = DefaultMarkdownGenerator(
        content_filter=LLMContentFilter(
            llm_config=llm_config,
            instruction="Extract key concepts and summaries"
        )
    )
    
    config = CrawlerRunConfig(markdown_generator=markdown_generator)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://docs.crawl4ai.com", config=config)
        pprint(result.markdown.fit_markdown)
        print("\n✅ Generated focused markdown:")



# 6️⃣ PDF Processing
async def pdf_processing():
    """
    PART 6: PDF Processing
    
    This function demonstrates:
    - Using PDFCrawlerStrategy and PDFContentScrapingStrategy
    - Extracting text and metadata from PDFs
    """
    print("\n===== PDF PROCESSING =====")
    print("This example shows how to extract text and metadata from PDF files.")
    
    # Sample PDF URL
    pdf_url = "https://arxiv.org/pdf/2310.06825.pdf"
    
    print("\n📊 Initializing PDF crawler...")
    print(f"  - Target PDF: {pdf_url}")
    print("  - Using PDFCrawlerStrategy and PDFContentScrapingStrategy")
    
    # Create crawler with PDF strategy
    async with AsyncWebCrawler(crawler_strategy=PDFCrawlerStrategy()) as crawler:
        print("\n🚀 Starting PDF processing...")
        
        start_time = time.perf_counter()
        result = await crawler.arun(
            pdf_url,
            config=CrawlerRunConfig(scraping_strategy=PDFContentScrapingStrategy())
        )
        duration = time.perf_counter() - start_time
        
        print(f"\n✅ Processed PDF in {duration:.2f} seconds")
        
        # Show metadata
        print("\n📄 PDF Metadata:")
        if result.metadata:
            for key, value in result.metadata.items():
                if key not in ["html", "text", "markdown"] and value:
                    print(f"  - {key}: {value}")
        else:
            print("  No metadata available")
        
        # Show sample of content
        if result.markdown:
            print("\n📝 PDF Content Sample:")
            content_sample = result.markdown[:500] + "..." if len(result.markdown) > 500 else result.markdown
            print(f"---\n{content_sample}\n---")
        else:
            print("\n⚠️ No content extracted")
    
    print("\n🔍 Key Takeaway: Crawl4AI can now process PDF files")
    print("  to extract both text content and metadata.")


# 7️⃣ LLM Schema Generation (requires API key)
async def llm_schema_generation():
    """
    PART 7: LLM Schema Generation
    
    This function demonstrates:
    - Configuring LLM providers via LLMConfig
    - Using LLM to generate extraction schemas
    - JsonCssExtractionStrategy
    
    Note: Requires a valid API key for the chosen LLM provider
    """
    print("\n===== LLM SCHEMA GENERATION =====")
    print("This example shows how to use LLM to automatically generate extraction schemas.")
    print("Note: This example requires an API key. Set it in environment variables.")
    
    # Sample HTML
    sample_html = """
    <div class="product">
        <h2 class="title">Awesome Gaming Laptop</h2>
        <div class="price">$1,299.99</div>
        <div class="specs">
            <ul>
                <li>16GB RAM</li>
                <li>512GB SSD</li>
                <li>RTX 3080</li>
            </ul>
        </div>
        <div class="rating">4.7/5</div>
    </div>
    """
    print("\n📊 Setting up LLMConfig...")
    # Create LLM configuration
    llm_config = LLMConfig(
        provider="gemini/gemini-1.5-pro", 
        api_token="env:GEMINI_API_KEY"
    )
    print("\n🚀 Generating schema for product extraction...")
    print("  This would use the LLM to analyze HTML and create an extraction schema")
    schema = JsonCssExtractionStrategy.generate_schema(
    html=sample_html,
    llm_config = llm_config,
    query="Extract product name and price"
    )
    print("\n✅ Generated Schema:")
    pprint(schema)
    
# Run all sections
async def run_tutorial():
    """
    Main function to run all tutorial sections.
    """
    print("\n🚀 CRAWL4AI v0.5.0 TUTORIAL 🚀")
    print("===============================")
    print("This tutorial demonstrates the key features of Crawl4AI v0.5.0")
    print("Including deep crawling, memory-adaptive dispatching, advanced filtering,")
    print("and more powerful extraction capabilities.")
    
    # Sections to run
    sections = [
        deep_crawl,                 # 1. Deep Crawling with Best-First Strategy
        memory_adaptive_dispatcher, # 2. Memory-Adaptive Dispatcher
        http_crawler_strategy,      # 3. HTTP Crawler Strategy
        proxy_rotation,             # 4. Proxy Rotation
        llm_content_filter,         # 5. LLM Content Filter
        pdf_processing,             # 6. PDF Processing
        llm_schema_generation,      # 7. Schema Generation using LLM
    ]
    
    for section in sections:
        try:
            await section()
        except Exception as e:
            print(f"⚠️ Error in {section.__name__}: {e}")
    
    print("\n🎉 TUTORIAL COMPLETE! 🎉")
    print("You've now explored the key features of Crawl4AI v0.5.0")
    print("For more information, visit https://docs.crawl4ai.com")


# Run the tutorial
if __name__ == "__main__":
    asyncio.run(run_tutorial())