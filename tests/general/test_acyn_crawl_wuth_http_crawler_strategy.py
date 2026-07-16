import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    HTTPCrawlerConfig,
    CacheMode,
    DefaultMarkdownGenerator,
    PruningContentFilter
)
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from crawl4ai.async_logger import AsyncLogger

async def main():
    # Initialize HTTP crawler strategy
    http_strategy = AsyncHTTPCrawlerStrategy(
        browser_config=HTTPCrawlerConfig(
            method="GET",
            verify_ssl=True,
            follow_redirects=True
        ),
        logger=AsyncLogger(verbose=True)
    )

    # Initialize web crawler with HTTP strategy
    async with AsyncWebCrawler(crawler_strategy=http_strategy) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.48, 
                    threshold_type="fixed", 
                    min_word_threshold=0
                )
            )
        )
        
        # Test different URLs
        urls = [
            "https://example.com",
            "https://httpbin.org/get",
            "raw://<html><body>Test content</body></html>"
        ]
        
        for url in urls:
            print(f"\n=== Testing {url} ===")
            try:
                result = await crawler.arun(url=url, config=crawler_config)
                print(f"Status: {result.status_code}")
                print(f"Raw HTML length: {len(result.html)}")
                if hasattr(result, 'markdown'):
                    print(f"Markdown length: {len(result.markdown.raw_markdown)}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())