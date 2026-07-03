import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


async def main():
    dedicated_config = BrowserConfig(
        browser_runtime="camoufox",
        browser_type="firefox",
        headless=True,
        camoufox_options={
            "geoip": True,
            "humanize": True,
        },
    )

    async with AsyncWebCrawler(config=dedicated_config) as crawler:
        result = await crawler.arun(
            "https://example.com",
            config=CrawlerRunConfig(wait_for="css:body"),
        )
        print("dedicated:", result.success, len(result.html))

    persistent_config = BrowserConfig(
        browser_runtime="camoufox",
        browser_type="firefox",
        use_persistent_context=True,
        user_data_dir="./camoufox-profile",
        proxy_config={
            "server": "http://proxy.example.com:8080",
            "username": "user",
            "password": "pass",
        },
        camoufox_options={
            "geoip": True,
            "humanize": True,
        },
    )

    async with AsyncWebCrawler(config=persistent_config) as crawler:
        result = await crawler.arun(
            "https://example.com/account",
            config=CrawlerRunConfig(),
        )
        print("persistent:", result.success, len(result.html))


if __name__ == "__main__":
    asyncio.run(main())
