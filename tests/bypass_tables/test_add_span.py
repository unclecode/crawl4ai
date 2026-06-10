import asyncio
import pathlib

from crawl4ai.async_configs import BrowserConfig,CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import DefaultTableExtraction
from crawl4ai import AsyncWebCrawler,CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter

target_url = "https://en.wikipedia.org/wiki/List_of_prime_ministers_of_India"
md_file = pathlib.Path(__file__).parent.absolute().joinpath('test.md').absolute()


# browser_config
browser_config = BrowserConfig(
    headless=True,
    user_agent_mode='random',
)



prune_filter = PruningContentFilter(
    threshold=0.8,
    threshold_type="dynamic",
)

# CrawlerConfig
run_config = CrawlerRunConfig(
    magic=True,
    markdown_generator=DefaultMarkdownGenerator(
        content_source = "cleaned_html",
        options={
            'bypass_tables': True,
        }
    ),
    cache_mode=CacheMode.BYPASS,
    css_selector='table.wikitable',
    table_extraction= DefaultTableExtraction()
)

async def main():
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=target_url,config=run_config)
        print(result.markdown)
        print(result.tables)
        with open(md_file,'w') as f:
            f.write(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())