import nest_asyncio

nest_asyncio.apply()

import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    LXMLWebScrapingStrategy,
    CacheMode,
)


async def main():
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        scraping_strategy=LXMLWebScrapingStrategy(),  # Faster alternative to default BeautifulSoup
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        print(f"Success: {result.success}")
        print(f"Markdown length: {len(result.markdown.raw_markdown)}")


if __name__ == "__main__":
    asyncio.run(main())
