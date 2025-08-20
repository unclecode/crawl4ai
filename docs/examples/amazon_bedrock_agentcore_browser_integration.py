"""
This example demonstrates how to integrate Amazon Bedrock Agentcore Browser, a remote browser session using Playwright.
"""

from bedrock_agentcore.tools.browser_client import BrowserClient

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig


async def use_bedrock_agentcore():
    client = BrowserClient(region="us-east-1")
    client.start()

    ws_url, headers = client.generate_ws_headers()

    browser_config = BrowserConfig(
        browser_type="chromium",
        cdp_url=ws_url,
        cdp_headers=headers,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://aws.amazon.com/",
        )
        print(result.markdown)
