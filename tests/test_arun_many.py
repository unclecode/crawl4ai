"""
Test example for multiple crawler configs feature
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.processors.pdf import PDFContentScrapingStrategy


async def test_run_many():
    default_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        # scraping_strategy=PDFContentScrapingStrategy()
    )
    
    test_urls = [
        # "https://blog.python.org/",  # Blog URL  
        "https://www.python.org/",  # Generic HTTPS page
        "https://www.kidocode.com/",  # Generic HTTPS page
        "https://www.example.com/",  # Generic HTTPS page
        # "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    ]
    
    async with AsyncWebCrawler() as crawler:
        # Single config - traditional usage still works
        print("Test 1: Single config (backwards compatible)")
        result = await crawler.arun_many(
            urls=test_urls[:2],
            config=default_config
        )
        print(f"Crawled {len(result)} URLs with single config\n")
        for item in result:
            print(f"  {item.url} -> {item.status_code}")
        

if __name__ == "__main__":
    asyncio.run(test_run_many())
