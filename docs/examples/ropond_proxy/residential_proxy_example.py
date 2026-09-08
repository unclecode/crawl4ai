"""
Ropond Proxy Cloud Integration Example for Crawl4AI
---------------------------------------------------
Demonstrates using Ropond Proxy Cloud (https://ropond.com) residential
proxy pool with sticky session management and anti-bot evasion.
"""
import asyncio
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    # Replace with your credentials from https://ropond.com (1GB free testing quota)
    username = os.getenv("ROPOND_USER", "customer-trial")
    password = os.getenv("ROPOND_PASS", "trial123")
    host = os.getenv("ROPOND_HOST", "gw.ropond.com")
    port = os.getenv("ROPOND_PORT", "8000")

    # Sticky session ID: all requests with this session ID use the same residential IP
    session_id = "crawl_batch_01"
    proxy_user = f"{username}-session-{session_id}"
    proxy_url = f"http://{proxy_user}:{password}@{host}:{port}"

    print(f"[Ropond Proxy] Configuring Crawl4AI with sticky session: {session_id}")

    browser_config = BrowserConfig(
        headless=True,
        verbose=True,
        proxy=proxy_url
    )

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=30000
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("[Ropond Proxy] Executing stealth crawl...")
        result = await crawler.arun(url="https://httpbin.org/ip", config=run_config)
        
        if result.success:
            print("[Ropond Proxy] Success! Origin IP response:")
            print(result.markdown.strip())
        else:
            print("[Ropond Proxy] Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
