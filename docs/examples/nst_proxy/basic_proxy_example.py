"""
NSTProxy Integration Examples for crawl4ai
------------------------------------------

NSTProxy is a premium residential proxy provider.
👉 Purchase Proxies: https://nstproxy.com
💰 Use coupon code "crawl4ai" for 10% off your plan.

"""
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig


async def main():
    # Using HTTP proxy
    browser_config = BrowserConfig(proxy_config={"server": "http://gate.nstproxy.io:24125"})
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com")
        print("[HTTP Proxy] Status:", result.status_code)

    # Using SOCKS proxy
    browser_config = BrowserConfig(proxy_config={"server": "socks5://gate.nstproxy.io:24125"})
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com")
        print("[SOCKS5 Proxy] Status:", result.status_code)


if __name__ == "__main__":
    asyncio.run(main())