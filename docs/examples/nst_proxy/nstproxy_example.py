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
    """
    Example: Using NSTProxy with AsyncWebCrawler.
    """

    NST_TOKEN = "YOUR_NST_PROXY_TOKEN"  # Get from https://app.nstproxy.com/profile
    CHANNEL_ID = "YOUR_NST_PROXY_CHANNEL_ID"  # Your NSTProxy Channel ID

    browser_config = BrowserConfig()
    browser_config.set_nstproxy(
        token=NST_TOKEN,
        channel_id=CHANNEL_ID,
        country="ANY",  # e.g. "US", "JP", or "ANY"
        state="",  # optional, leave empty if not needed
        city="",  # optional, leave empty if not needed
        session_duration=0  # Session duration in minutes,0 = rotate on every request
    )

    # === Run crawler ===
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com")
        print("[Nstproxy] Status:", result.status_code)


if __name__ == "__main__":
    asyncio.run(main())