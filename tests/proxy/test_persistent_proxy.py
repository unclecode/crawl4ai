import asyncio
import os
import shutil
import uuid
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import ProxyConfig


async def crawl_chanel(url: str):
    profile_dir = os.path.expanduser(f"~/.crawl4ai/chanel_{uuid.uuid4().hex[:8]}")
    os.makedirs(profile_dir, exist_ok=True)

    browser_config = BrowserConfig(
        headless=True,
        enable_stealth=True,
        use_persistent_context=True,
        user_data_dir=profile_dir,
        viewport_width=1920,
        viewport_height=1080,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        },
        proxy_config=ProxyConfig(
            server="https://network.joinmassive.com:65535",
            username="mpuQHs4sWZ-country-US",
            password="D0yWxVQo8wQ05RWqz1Bn",
        ),
    )

    run_config = CrawlerRunConfig(
        magic=True,
        simulate_user=True,
        override_navigator=True,
        page_timeout=120000,
        wait_until="load",
        delay_before_return_html=10.0,
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url, config=run_config)
            return result
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)


async def main():
    url = "https://www.chanel.com/us/fashion/handbags/c/1x1x1/"
    result = await crawl_chanel(url)
    print(f"Status: {result.status_code}")
    print(f"Success: {result.success}")
    print(f"HTML: {len(result.html):,} bytes")
    if result.markdown:
        md_len = len(result.markdown.raw_markdown)
        print(f"Markdown: {md_len:,} chars")
        if md_len > 500:
            print(f"\nFirst 500 chars of markdown:\n{result.markdown.raw_markdown[:500]}")
    if result.error_message:
        print(f"Error: {result.error_message}")


asyncio.run(main())
