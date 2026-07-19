"""
CloakBrowser + Crawl4AI: Stealth crawling with source-level fingerprint patches.

CloakBrowser is a patched Chromium binary that modifies fingerprints at the C++ source
level, rather than through JavaScript injection. This makes it effective against sites
that detect runtime fingerprint overrides (e.g. Cloudflare, reCAPTCHA, DataDome).

This example connects Crawl4AI to CloakBrowser via CDP, then runs bot detection tests
to verify stealth effectiveness.

Install: pip install cloakbrowser crawl4ai
The CloakBrowser binary (~200MB) auto-downloads on first run.
https://github.com/CloakHQ/CloakBrowser
"""

import asyncio
import base64

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from cloakbrowser import launch_async


async def example_basic():
    """Basic usage: crawl a page through CloakBrowser."""
    print("\n=== Example 1: Basic Stealth Crawling ===")

    cb_browser = await launch_async(
        headless=True,
        args=["--remote-debugging-port=9243", "--remote-debugging-address=127.0.0.1"],
    )

    async with AsyncWebCrawler(
        config=BrowserConfig(browser_mode="cdp", cdp_url="http://127.0.0.1:9243")
    ) as crawler:
        result = await crawler.arun(
            url="https://www.example.com",
            config=CrawlerRunConfig(),
        )
        print(f"Status: {result.status_code}")
        print(f"Extracted {len(result.markdown)} chars of markdown")

    await cb_browser.close()


async def example_bot_detection():
    """Verify stealth: run bot detection tests, save screenshot, and print results."""
    print("\n=== Example 2: Bot Detection Verification ===")

    cb_browser = await launch_async(
        headless=True,
        args=["--remote-debugging-port=9243", "--remote-debugging-address=127.0.0.1"],
    )

    async with AsyncWebCrawler(
        config=BrowserConfig(browser_mode="cdp", cdp_url="http://127.0.0.1:9243")
    ) as crawler:
        result = await crawler.arun(
            url="https://bot.sannysoft.com",
            config=CrawlerRunConfig(
                wait_until="networkidle",
                screenshot=True,
            ),
        )
        print(f"Status: {result.status_code}")

        # Save screenshot for visual verification
        if result.screenshot:
            with open("cloakbrowser_bot_detection.png", "wb") as f:
                f.write(base64.b64decode(result.screenshot))
            print("Screenshot saved: cloakbrowser_bot_detection.png")

        # Parse detection results from the HTML table
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(result.html, "html.parser")
        passed = failed = 0
        for row in soup.select("table tr"):
            cells = row.select("td")
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                style = cells[1].get("style", "")
                if "#f45159" in style:
                    print(f"  ✗ {name:35s} {value}")
                    failed += 1
                else:
                    print(f"  ✓ {name:35s} {value}")
                    passed += 1
        print(f"\nResults: {passed} passed, {failed} failed")

    await cb_browser.close()


async def example_with_proxy():
    """Use a proxy with CloakBrowser for geo-targeted crawling."""
    print("\n=== Example 3: With Proxy ===")

    # Pass proxy to CloakBrowser. Crawl4AI doesn't need to know about it.
    cb_browser = await launch_async(
        headless=True,
        proxy="http://user:pass@proxy-host:port",  # Replace with your proxy
        args=["--remote-debugging-port=9243", "--remote-debugging-address=127.0.0.1"],
    )

    async with AsyncWebCrawler(
        config=BrowserConfig(browser_mode="cdp", cdp_url="http://127.0.0.1:9243")
    ) as crawler:
        result = await crawler.arun(
            url="https://httpbin.org/ip",
            config=CrawlerRunConfig(),
        )
        print(f"IP result: {result.markdown[:200]}")

    await cb_browser.close()


async def main():
    await example_basic()
    await example_bot_detection()
    # Uncomment after setting your proxy:
    # await example_with_proxy()


if __name__ == "__main__":
    asyncio.run(main())
