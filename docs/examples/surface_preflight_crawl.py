#!/usr/bin/env python3
"""
URL Preflight with Surface Before Crawling

Before handing a list of URLs to AsyncWebCrawler, this example asks
Surface (https://nova-otter-delta-cloud.grok.me) whether each URL is
worth fetching. Surface follows shortened links (t.co, bit.ly, ...),
checks reachability, and answers with `next: "fetch"` or `next: "skip"`.
URLs marked "skip" never launch a browser page, which saves time on
dead domains and broken short links.

Surface notes:
- Endpoint: POST /v1/preflight with JSON {"url": "..."}
- No API key is needed for this demo.
- The first 1,000,000 requests each month are free.

Usage:
    pip install crawl4ai
    crawl4ai-setup
    python surface_preflight_crawl.py
"""

import asyncio
import json
import urllib.request
from typing import Dict, List

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

SURFACE_PREFLIGHT_URL = "https://nova-otter-delta-cloud.grok.me/v1/preflight"

URLS: List[str] = [
    "https://bit.ly/github",                       # bit.ly link to a removed page
    "https://t.co/",                               # t.co shortener root
    "https://example.com",                         # normal site
    "https://this-domain-does-not-exist-c4a.invalid/",  # unreachable domain
]


def surface_preflight(url: str, timeout: float = 15.0) -> Dict:
    """Ask Surface whether `url` should be fetched. Never raises."""
    req = urllib.request.Request(
        SURFACE_PREFLIGHT_URL,
        data=json.dumps({"url": url}).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "crawl4ai-surface-preflight-example/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        # If the preflight itself fails, fall back to crawling as usual.
        return {"next": "fetch", "reason": f"preflight unavailable: {e}"}


async def main():
    # 1) Preflight every URL (urllib is blocking, so run in threads)
    verdicts = await asyncio.gather(
        *(asyncio.to_thread(surface_preflight, u) for u in URLS)
    )

    to_crawl, skipped = [], []
    for url, v in zip(URLS, verdicts):
        (to_crawl if v.get("next") == "fetch" else skipped).append((url, v))

    for url, v in zip(URLS, verdicts):
        print(
            f"[PRE  ] {url} -> verdict={v.get('verdict')}, next={v.get('next')}, "
            f"final_url={v.get('final_url')}, reason={v.get('reason')}"
        )
    for url, v in skipped:
        print(f"[SKIP ] {url} -> {v.get('reason')}")

    # 2) Crawl only the URLs Surface says to fetch
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    crawled_ok = 0
    if to_crawl:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun_many(
                urls=[u for u, _ in to_crawl], config=run_config
            )
            for result in results:
                if result.success:
                    crawled_ok += 1
                    chars = len(result.markdown.raw_markdown or "")
                    print(f"[CRAWL] {result.url} -> {result.status_code}, {chars} chars of markdown")
                else:
                    print(f"[FAIL ] {result.url} -> {result.error_message}")

    # 3) Summary
    print("\nSummary")
    print(f"  URLs checked : {len(URLS)}")
    print(f"  Skipped      : {len(skipped)}")
    print(f"  Crawled OK   : {crawled_ok}/{len(to_crawl)}")
    if verdicts:
        last = verdicts[-1]
        if "free_remaining" in last:
            print(f"  Surface free requests remaining this month: {last['free_remaining']}")


if __name__ == "__main__":
    asyncio.run(main())
