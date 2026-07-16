"""
🎯 Multi-Config URL Matching Demo
=================================
Learn how to use different crawler configurations for different URL patterns
in a single crawl batch with Crawl4AI's multi-config feature.

Part 1: Understanding URL Matching (Pattern Testing)
Part 2: Practical Example with Real Crawling
"""

import asyncio
from crawl4ai import (
    AsyncWebCrawler, 
    CrawlerRunConfig,
    MatchMode
)
from crawl4ai.processors.pdf import PDFContentScrapingStrategy
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}\n")


def test_url_matching(config, test_urls, config_name):
    """Test URL matching for a config and show results"""
    print(f"Config: {config_name}")
    print(f"Matcher: {config.url_matcher}")
    if hasattr(config, 'match_mode'):
        print(f"Mode: {config.match_mode.value}")
    print("-" * 40)
    
    for url in test_urls:
        matches = config.is_match(url)
        symbol = "✓" if matches else "✗"
        print(f"{symbol} {url}")
    print()


# ==============================================================================
# PART 1: Understanding URL Matching
# ==============================================================================

def demo_part1_pattern_matching():
    """Part 1: Learn how URL matching works without crawling"""
    
    print_section("PART 1: Understanding URL Matching")
    print("Let's explore different ways to match URLs with configs.\n")
    
    # Test URLs we'll use throughout
    test_urls = [
        "https://example.com/report.pdf",
        "https://example.com/data.json",
        "https://example.com/blog/post-1",
        "https://example.com/article/news",
        "https://api.example.com/v1/users",
        "https://example.com/about"
    ]
    
    # 1.1 Simple String Pattern
    print("1.1 Simple String Pattern Matching")
    print("-" * 40)
    
    pdf_config = CrawlerRunConfig(
        url_matcher="*.pdf"
    )
    
    test_url_matching(pdf_config, test_urls, "PDF Config")
    
    
    # 1.2 Multiple String Patterns
    print("1.2 Multiple String Patterns (OR logic)")
    print("-" * 40)
    
    blog_config = CrawlerRunConfig(
        url_matcher=["*/blog/*", "*/article/*", "*/news/*"],
        match_mode=MatchMode.OR  # This is default, shown for clarity
    )
    
    test_url_matching(blog_config, test_urls, "Blog/Article Config")
    
    
    # 1.3 Single Function Matcher
    print("1.3 Function-based Matching")
    print("-" * 40)
    
    api_config = CrawlerRunConfig(
        url_matcher=lambda url: 'api' in url or url.endswith('.json')
    )
    
    test_url_matching(api_config, test_urls, "API Config")
    
    
    # 1.4 List of Functions
    print("1.4 Multiple Functions with AND Logic")
    print("-" * 40)
    
    # Must be HTTPS AND contain 'api' AND have version number
    secure_api_config = CrawlerRunConfig(
        url_matcher=[
            lambda url: url.startswith('https://'),
            lambda url: 'api' in url,
            lambda url: '/v' in url  # Version indicator
        ],
        match_mode=MatchMode.AND
    )
    
    test_url_matching(secure_api_config, test_urls, "Secure API Config")
    
    
    # 1.5 Mixed: String and Function Together
    print("1.5 Mixed Patterns: String + Function")
    print("-" * 40)
    
    # Match JSON files OR any API endpoint
    json_or_api_config = CrawlerRunConfig(
        url_matcher=[
            "*.json",  # String pattern
            lambda url: 'api' in url  # Function
        ],
        match_mode=MatchMode.OR
    )
    
    test_url_matching(json_or_api_config, test_urls, "JSON or API Config")
    
    
    # 1.6 Complex: Multiple Strings + Multiple Functions
    print("1.6 Complex Matcher: Mixed Types with AND Logic")
    print("-" * 40)
    
    # Must be: HTTPS AND (.com domain) AND (blog OR article) AND NOT a PDF
    complex_config = CrawlerRunConfig(
        url_matcher=[
            lambda url: url.startswith('https://'),  # Function: HTTPS check
            "*.com/*",  # String: .com domain
            lambda url: any(pattern in url for pattern in ['/blog/', '/article/']),  # Function: Blog OR article
            lambda url: not url.endswith('.pdf')  # Function: Not PDF
        ],
        match_mode=MatchMode.AND
    )
    
    test_url_matching(complex_config, test_urls, "Complex Mixed Config")
    
    print("\n✅ Key Takeaway: First matching config wins when passed to arun_many()!")


# ==============================================================================
# PART 2: Practical Multi-URL Crawling
# ==============================================================================

async def demo_part2_practical_crawling():
    """Part 2: Real-world example with different content types"""
    
    print_section("PART 2: Practical Multi-URL Crawling")
    print("Now let's see multi-config in action with real URLs.\n")
    
    # Create specialized configs for different content types
    configs = [
        # Config 1: PDF documents - only match files ending with .pdf
        CrawlerRunConfig(
            url_matcher="*.pdf",
            scraping_strategy=PDFContentScrapingStrategy()
        ),
        
        # Config 2: Blog/article pages with content filtering
        CrawlerRunConfig(
            url_matcher=["*/blog/*", "*/article/*", "*python.org*"],
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.48)
            )
        ),
        
        # Config 3: Dynamic pages requiring JavaScript
        CrawlerRunConfig(
            url_matcher=lambda url: 'github.com' in url,
            js_code="window.scrollTo(0, 500);"  # Scroll to load content
        ),
        
        # Config 4: Mixed matcher - API endpoints (string OR function)
        CrawlerRunConfig(
            url_matcher=[
                "*.json",  # String pattern for JSON files
                lambda url: 'api' in url or 'httpbin.org' in url  # Function for API endpoints
            ],
            match_mode=MatchMode.OR,
        ),
        
        # Config 5: Complex matcher - Secure documentation sites
        CrawlerRunConfig(
            url_matcher=[
                lambda url: url.startswith('https://'),  # Must be HTTPS
                "*.org/*",  # String: .org domain
                lambda url: any(doc in url for doc in ['docs', 'documentation', 'reference']),  # Has docs
                lambda url: not url.endswith(('.pdf', '.json'))  # Not PDF or JSON
            ],
            match_mode=MatchMode.AND,
            # wait_for="css:.content, css:article"  # Wait for content to load
        ),
        
        # Default config for everything else
        # CrawlerRunConfig()  # No url_matcher means it matches everything (use it as fallback)
    ]
    
    # URLs to crawl - each will use a different config
    urls = [
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",  # → PDF config
        "https://blog.python.org/",  # → Blog config with content filter
        "https://github.com/microsoft/playwright",  # → JS config
        "https://httpbin.org/json",  # → Mixed matcher config (API)
        "https://docs.python.org/3/reference/",  # → Complex matcher config
        "https://www.w3schools.com/",  # → Default config, if you uncomment the default config line above, if not you will see `Error: No matching configuration`
    ]
    
    print("URLs to crawl:")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    
    print("\nCrawling with appropriate config for each URL...\n")
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=configs
        )
        
        # Display results
        print("Results:")
        print("-" * 60)
        
        for result in results:
            if result.success:
                # Determine which config was used
                config_type = "Default"
                if result.url.endswith('.pdf'):
                    config_type = "PDF Strategy"
                elif any(pattern in result.url for pattern in ['blog', 'python.org']) and 'docs' not in result.url:
                    config_type = "Blog + Content Filter"
                elif 'github.com' in result.url:
                    config_type = "JavaScript Enabled"
                elif 'httpbin.org' in result.url or result.url.endswith('.json'):
                    config_type = "Mixed Matcher (API)"
                elif 'docs.python.org' in result.url:
                    config_type = "Complex Matcher (Secure Docs)"
                
                print(f"\n✓ {result.url}")
                print(f"  Config used: {config_type}")
                print(f"  Content size: {len(result.markdown)} chars")
                
                # Show if we have fit_markdown (from content filter)
                if hasattr(result.markdown, 'fit_markdown') and result.markdown.fit_markdown:
                    print(f"  Fit markdown size: {len(result.markdown.fit_markdown)} chars")
                    reduction = (1 - len(result.markdown.fit_markdown) / len(result.markdown)) * 100
                    print(f"  Content reduced by: {reduction:.1f}%")
                
                # Show extracted data if using extraction strategy
                if hasattr(result, 'extracted_content') and result.extracted_content:
                    print(f"  Extracted data: {str(result.extracted_content)[:100]}...")
            else:
                print(f"\n✗ {result.url}")
                print(f"  Error: {result.error_message}")
    
    print("\n" + "=" * 60)
    print("✅ Multi-config crawling complete!")
    print("\nBenefits demonstrated:")
    print("- PDFs handled with specialized scraper")
    print("- Blog content filtered for relevance") 
    print("- JavaScript executed only where needed")
    print("- Mixed matchers (string + function) for flexible matching")
    print("- Complex matchers for precise URL targeting")
    print("- Each URL got optimal configuration automatically!")


async def main():
    """Run both parts of the demo"""
    
    print("""
🎯 Multi-Config URL Matching Demo
=================================
Learn how Crawl4AI can use different configurations
for different URLs in a single batch.
    """)
    
    # Part 1: Pattern matching
    demo_part1_pattern_matching()
    
    print("\nPress Enter to continue to Part 2...")
    try:
        input()
    except EOFError:
        # Running in non-interactive mode, skip input
        pass
    
    # Part 2: Practical crawling
    await demo_part2_practical_crawling()


if __name__ == "__main__":
    asyncio.run(main())