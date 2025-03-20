import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    CrawlResult
)


async def main():
    browser_config = BrowserConfig(headless=True, verbose=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                # content_filter=PruningContentFilter(
                #     threshold=0.48, threshold_type="fixed", min_word_threshold=0
                # )
            ),
        )
        result : CrawlResult = await crawler.arun(
            # url="https://www.helloworld.org", config=crawler_config
            url="https://www.kidocode.com", config=crawler_config
        )
        print(result.markdown.raw_markdown[:500])
        # print(result.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
