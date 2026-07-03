import asyncio
import os
import platform

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


def parse_webshare_proxy(proxy_line: str) -> dict[str, str]:
    host, port, username, password = proxy_line.strip().split(":", 3)
    return {
        "server": f"http://{host}:{port}",
        "username": username,
        "password": password,
    }


def build_camoufox_options() -> dict[str, object]:
    return {
        "headless": "virtual" if platform.system() == "Linux" else True,
        "geoip": True,
        "humanize": True,
    }


async def main():
    proxy_line = os.environ.get("WEBSHARE_PROXY")
    if not proxy_line:
        raise RuntimeError(
            "Set WEBSHARE_PROXY to a Webshare line formatted as "
            "host:port:username:password"
        )

    browser_config = BrowserConfig(
        browser_runtime="camoufox",
        browser_type="firefox",
        use_persistent_context=True,
        user_data_dir=os.environ.get("CAMOUFOX_PROFILE_DIR", "./camoufox-profile"),
        proxy_config=parse_webshare_proxy(proxy_line),
        camoufox_options=build_camoufox_options(),
    )

    run_config = CrawlerRunConfig(
        wait_for="css:body",
        wait_until="domcontentloaded",
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        target_url = os.environ.get("CAMOUFOX_TARGET_URL", "https://example.com")
        result = await crawler.arun(target_url, config=run_config)
        print("success:", result.success)
        print("url:", result.url)
        print("html_length:", len(result.html))


if __name__ == "__main__":
    asyncio.run(main())
