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

async def example_cdp():
    browser_conf = BrowserConfig(
        headless=False,
        cdp_url="http://localhost:9223"
    )
    crawler_config = CrawlerRunConfig(
        session_id="test",
        js_code = """(() => { return {"result": "Hello World!"} })()""",
        js_only=True
    )
    async with AsyncWebCrawler(
        config=browser_conf,
        verbose=True,
    ) as crawler:
        result : CrawlResult = await crawler.arun(
            url="https://www.helloworld.org",
            config=crawler_config,
        )
        print(result.js_execution_result)
                   

async def main():
    browser_config = BrowserConfig(headless=False, verbose=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                     threshold=0.48, threshold_type="fixed", min_word_threshold=0
                )
            ),
        )
        result : CrawlResult = await crawler.arun(
            url="https://www.helloworld.org", config=crawler_config
        )
        print(result.markdown.raw_markdown[:500])

if __name__ == "__main__":
    asyncio.run(main())
