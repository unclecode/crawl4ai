import asyncio
import os
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

# Simple concurrency test for persistent context page creation
# Usage: python scripts/test_persistent_context.py

URLS = [
    # "https://example.com",
    "https://httpbin.org/html",
    "https://www.python.org/",
    "https://www.rust-lang.org/",
]

async def main():
    profile_dir = os.path.join(os.path.expanduser("~"), ".crawl4ai", "profiles", "test-persistent-profile")
    os.makedirs(profile_dir, exist_ok=True)

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        use_persistent_context=True,
        user_data_dir=profile_dir,
        use_managed_browser=True,
        verbose=True,
    )

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=False,
        verbose=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(URLS, config=run_cfg)
        for r in results:
            print(r.url, r.success, len(r.markdown.raw_markdown) if r.markdown else 0)
        # r = await crawler.arun(url=URLS[0], config=run_cfg)
        # print(r.url, r.success, len(r.markdown.raw_markdown) if r.markdown else 0)

if __name__ == "__main__":
    asyncio.run(main())
