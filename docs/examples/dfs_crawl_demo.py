"""
Simple demonstration of the DFS deep crawler visiting multiple pages.

Run with:  python docs/examples/dfs_crawl_demo.py
"""
import asyncio

from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.cache_context import CacheMode
from crawl4ai.deep_crawling.dfs_strategy import DFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def main() -> None:
    dfs_strategy = DFSDeepCrawlStrategy(
        max_depth=3,
        max_pages=50,
        include_external=False,
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=dfs_strategy,
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(),
        stream=True,
    )

    seed_url = "https://docs.python.org/3/"  # Plenty of internal links

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        async for result in await crawler.arun(url=seed_url, config=config):
            depth = result.metadata.get("depth")
            status = "SUCCESS" if result.success else "FAILED"
            print(f"[{status}] depth={depth} url={result.url}")


if __name__ == "__main__":
    asyncio.run(main())
