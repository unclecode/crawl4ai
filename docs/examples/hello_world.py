import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0)
            )
        )
        result = await crawler.arun(
            url="https://crawl4ai.com",
            config=crawler_config
        )
        print(result.markdown_v2.raw_markdown[:500])

if __name__ == "__main__":
    asyncio.run(main())