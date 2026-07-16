# use_geo_location.py
"""
Example: override locale, timezone, and geolocation using Crawl4ai patterns.

This demo uses `AsyncWebCrawler.arun()` to fetch a page with
browser context primed for specific locale, timezone, and GPS,
and saves a screenshot for visual verification.
"""

import asyncio
import base64
from pathlib import Path
from typing import List
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BrowserConfig,
    GeolocationConfig,
    CrawlResult,
)

async def demo_geo_override():
    """Demo: Crawl a geolocation-test page with overrides and screenshot."""
    print("\n=== Geo-Override Crawl ===")

    # 1) Browser setup: use Playwright-managed contexts
    browser_cfg = BrowserConfig(
        headless=False,
        viewport_width=1280,
        viewport_height=720,
        use_managed_browser=False,
    )

    # 2) Run config: include locale, timezone_id, geolocation, and screenshot
    run_cfg = CrawlerRunConfig(
        url="https://browserleaks.com/geo",          # test page that shows your location
        locale="en-US",                              # Accept-Language & UI locale
        timezone_id="America/Los_Angeles",           # JS Date()/Intl timezone
        geolocation=GeolocationConfig(                 # override GPS coords
            latitude=34.0522,
            longitude=-118.2437,
            accuracy=10.0,
        ),
        screenshot=True,                               # capture screenshot after load
        session_id="geo_test",                       # reuse context if rerunning
        delay_before_return_html=5
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # 3) Run crawl (returns list even for single URL)
        results: List[CrawlResult] = await crawler.arun(
            url=run_cfg.url,
            config=run_cfg,            
        )
        result = results[0]

        # 4) Save screenshot and report path
        if result.screenshot:
            __current_dir = Path(__file__).parent
            out_dir = __current_dir / "tmp"
            out_dir.mkdir(exist_ok=True)
            shot_path = out_dir / "geo_test.png"
            with open(shot_path, "wb") as f:
                f.write(base64.b64decode(result.screenshot))
            print(f"Saved screenshot to {shot_path}")
        else:
            print("No screenshot captured, check configuration.")

if __name__ == "__main__":
    asyncio.run(demo_geo_override())
