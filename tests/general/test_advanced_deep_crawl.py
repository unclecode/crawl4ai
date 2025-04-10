import asyncio
import time


from crawl4ai import CrawlerRunConfig, AsyncWebCrawler, CacheMode
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter, ContentTypeFilter, ContentRelevanceFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
# from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy


async def main():
    """Example deep crawl of documentation site."""
    filter_chain = FilterChain([
        URLPatternFilter(patterns=["*2025*"]),
        DomainFilter(allowed_domains=["techcrunch.com"]),
        ContentRelevanceFilter(query="Use of artificial intelligence in Defence applications", threshold=1),
        ContentTypeFilter(allowed_types=["text/html","application/javascript"])
    ])
    config = CrawlerRunConfig(
        deep_crawl_strategy = BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=KeywordRelevanceScorer(keywords=["anduril", "defence", "AI"]),
        ),
        stream=False,
        verbose=True,
        cache_mode=CacheMode.BYPASS,
        scraping_strategy=LXMLWebScrapingStrategy()
    )

    async with AsyncWebCrawler() as crawler:
        print("Starting deep crawl in streaming mode:")
        config.stream = True
        start_time = time.perf_counter()
        async for result in await crawler.arun(
            url="https://techcrunch.com",
            config=config
        ):
            print(f"→ {result.url} (Depth: {result.metadata.get('depth', 0)})")
        print(f"Duration: {time.perf_counter() - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())