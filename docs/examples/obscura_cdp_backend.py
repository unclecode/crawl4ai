"""
Use Obscura as a CDP backend for Crawl4AI.

Obscura (https://github.com/h4ckf0r0day/obscura) is an open-source headless
browser engine written in Rust. It runs JavaScript via V8 and speaks the Chrome
DevTools Protocol, so Crawl4AI can drive it through the standard `cdp_url` path.
It has no layout or paint engine, so it suits HTML and Markdown extraction rather
than screenshots or PDFs.

Setup:
  1. Build Obscura: `OPENSSL_NO_VENDOR=1 cargo build --release`
  2. Start the CDP server: `obscura serve --port 9222`
     (it also serves the /json/version endpoint Crawl4AI uses to find the ws URL)
  3. Run this script.

The second URL below (quotes.toscrape.com/js) builds its content client-side, so
crawling it exercises Obscura's JavaScript engine rather than just static HTML.

Obscura rejects screenshot and PDF capture (no paint engine). Use a full Chromium
for the visual leg if you need pixels.
"""

import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

OBSCURA_CDP_URL = "http://127.0.0.1:9222"


async def main():
    browser_config = BrowserConfig(browser_mode="cdp", cdp_url=OBSCURA_CDP_URL)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in ["https://example.com", "https://quotes.toscrape.com/js/"]:
            result = await crawler.arun(url=url, config=run_config)
            print("-" * 40)
            if result.success:
                markdown = result.markdown.raw_markdown
                print(f"{url}  (status {result.status_code}, {len(markdown)} chars)")
                print(markdown[:200])
            else:
                print(f"{url}  failed: {result.error_message}")
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(main())
