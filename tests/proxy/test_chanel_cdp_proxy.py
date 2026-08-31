"""
Test: Chanel.com anti-bot bypass via crawl4ai

Requires env vars:
  MASSIVE_USERNAME  — Massive residential proxy username
  MASSIVE_PASSWORD  — Massive residential proxy password

Optional:
  --cdp URL       Connect to external browser via CDP (e.g. http://localhost:9223)
  --attempts N    Number of attempts per test (default 3)

Usage:
  export MASSIVE_USERNAME="your_user"
  export MASSIVE_PASSWORD="your_pass"
  .venv/bin/python tests/proxy/test_chanel_cdp_proxy.py
  .venv/bin/python tests/proxy/test_chanel_cdp_proxy.py --cdp http://localhost:9223
"""

import asyncio
import os
import sys
import re
import tempfile
import shutil
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import ProxyConfig

URL = "https://www.chanel.com/us/fashion/handbags/c/1x1x1/"

MASSIVE_USERNAME = os.environ.get("MASSIVE_USERNAME", "")
MASSIVE_PASSWORD = os.environ.get("MASSIVE_PASSWORD", "")
MASSIVE_SERVER = "https://network.joinmassive.com:65535"


def get_proxy_config():
    if not MASSIVE_USERNAME or not MASSIVE_PASSWORD:
        print("ERROR: Set MASSIVE_USERNAME and MASSIVE_PASSWORD env vars")
        sys.exit(1)
    return ProxyConfig(
        server=MASSIVE_SERVER,
        username=MASSIVE_USERNAME,
        password=MASSIVE_PASSWORD,
    )


async def test_isolated_context(cdp_url: str = None, attempts: int = 3):
    """Test with isolated context (works with both Playwright and CDP)."""
    mode = f"CDP ({cdp_url})" if cdp_url else "Playwright Chromium"
    print(f"\n{'='*60}")
    print(f"Mode: Isolated context — {mode}")
    print(f"{'='*60}\n")

    kwargs = dict(
        enable_stealth=True,
        create_isolated_context=True,
        viewport_width=1920,
        viewport_height=1080,
    )
    if cdp_url:
        kwargs["cdp_url"] = cdp_url
    else:
        kwargs["headless"] = True

    config = BrowserConfig(**kwargs)
    run_config = CrawlerRunConfig(
        magic=True,
        simulate_user=True,
        override_navigator=True,
        proxy_config=get_proxy_config(),
        page_timeout=120000,
        wait_until="load",
        delay_before_return_html=15.0,
    )

    passed = 0
    async with AsyncWebCrawler(config=config) as crawler:
        for i in range(attempts):
            result = await crawler.arun(URL, config=run_config)
            ok = result.status_code == 200 and len(result.html) > 10000
            title = ""
            if ok:
                passed += 1
                m = re.search(r"<title>(.*?)</title>", result.html)
                title = f"  title={m.group(1)}" if m else ""
            print(f"  Attempt {i+1}: status={result.status_code}  html={len(result.html):>10,} bytes  {'PASS' if ok else 'FAIL'}{title}")

    print(f"\nResult: {passed}/{attempts} passed")
    return passed > 0


async def main():
    cdp_url = None
    attempts = 3

    args = sys.argv[1:]
    for j, arg in enumerate(args):
        if arg == "--cdp" and j + 1 < len(args):
            cdp_url = args[j + 1]
        if arg == "--attempts" and j + 1 < len(args):
            attempts = int(args[j + 1])

    ok = await test_isolated_context(cdp_url=cdp_url, attempts=attempts)

    print(f"\n{'='*60}")
    print(f"Result: {'PASS' if ok else 'FAIL'}")
    print(f"{'='*60}")
    return ok


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
