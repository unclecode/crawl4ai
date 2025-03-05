#!/usr/bin/env python
# encoding: utf-8

import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    DefaultMarkdownGenerator,
    CrawlResult,
)
from crawl4ai.configs import ProxyConfig


async def main():
    browser_config = BrowserConfig(headless=True, verbose=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            magic=True,
            fetch_ssl_certificate=True,
            proxy_config=ProxyConfig(server="socks5://127.0.0.1:1088"),
            markdown_generator=DefaultMarkdownGenerator(
                # content_filter=PruningContentFilter(
                #     threshold=0.48, threshold_type="fixed", min_word_threshold=0
                # )
            ),
        )
        result : CrawlResult = await crawler.arun(
            url="https://www.google.com", config=crawler_config
        )
        print("ssl:", result.ssl_certificate)
        print("markdown: ",result.markdown[:500])


if __name__ == "__main__":
    asyncio.run(main())
