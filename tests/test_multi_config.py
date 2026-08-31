"""
Test example for multiple crawler configs feature
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, MatchMode, CacheMode

async def test_multi_config():
    # Create different configs for different URL patterns
    
    # Config for PDF files
    pdf_config = CrawlerRunConfig(
        url_matcher="*.pdf",
    )
    
    # Config for articles (using multiple patterns with OR logic)
    article_config = CrawlerRunConfig(
        url_matcher=["*/news/*", "*blog*", "*/article/*"],
        match_mode=MatchMode.OR,
        screenshot=True,
    )
    
    # Config using custom matcher function
    api_config = CrawlerRunConfig(
        url_matcher=lambda url: 'api' in url or 'json' in url,
    )
    
    # Config combining patterns and functions with AND logic
    secure_docs_config = CrawlerRunConfig(
        url_matcher=[
            "*.doc*",  # Matches .doc, .docx
            lambda url: url.startswith('https://')  # Must be HTTPS
        ],
        match_mode=MatchMode.AND,
    )
    
    # Default config (no url_matcher means it won't match anything unless it's the fallback)
    default_config = CrawlerRunConfig(
        # cache_mode=CacheMode.BYPASS,
    )
    
    # List of configs - order matters! First match wins
    configs = [
        pdf_config,
        article_config, 
        api_config,
        secure_docs_config,
        default_config  # Fallback
    ]
    
    # Test URLs - using real URLs that exist
    test_urls = [
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",  # Real PDF
        "https://www.bbc.com/news/articles/c5y3e3glnldo",  # News article
        "https://blog.python.org/",  # Blog URL  
        "https://api.github.com/users/github",  # GitHub API (returns JSON)
        "https://httpbin.org/json",  # API endpoint that returns JSON
        "https://www.python.org/",  # Generic HTTPS page
        "http://info.cern.ch/",  # HTTP (not HTTPS) page
        "https://example.com/",  # → Default config
    ]
    
    # Test the matching logic
    print("Config matching test:")
    print("-" * 50)
    for url in test_urls:
        for i, config in enumerate(configs):
            if config.is_match(url):
                print(f"{url} -> Config {i} matches")
                break
        else:
            print(f"{url} -> No match, will use fallback (first config)")
    
    print("\n" + "=" * 50 + "\n")
    
    # Now test with actual crawler
    async with AsyncWebCrawler() as crawler:
        # Single config - traditional usage still works
        print("Test 1: Single config (backwards compatible)")
        result = await crawler.arun_many(
            urls=["https://www.python.org/"],
            config=default_config
        )
        print(f"Crawled {len(result)} URLs with single config\n")
        
        # Multiple configs - new feature
        print("Test 2: Multiple configs")
        # Just test with 2 URLs to avoid timeout
        results = await crawler.arun_many(
            urls=test_urls[:2],  # Just test first 2 URLs
            config=configs  # Pass list of configs
        )
        print(f"Crawled {len(results)} URLs with multiple configs")
        
        # Using custom matcher inline
        print("\nTest 3: Inline custom matcher")
        custom_config = CrawlerRunConfig(
            url_matcher=lambda url: len(url) > 50 and 'python' in url.lower(),
            verbose=False
        )
        results = await crawler.arun_many(
            urls=[
                "https://docs.python.org/3/library/asyncio.html",  # Long URL with 'python'
                "https://python.org/",  # Short URL with 'python' - won't match
                "https://www.google.com/"  # No 'python' - won't match
            ],
            config=[custom_config, default_config]
        )
        print(f"Crawled {len(results)} URLs with custom matcher")

if __name__ == "__main__":
    asyncio.run(test_multi_config())