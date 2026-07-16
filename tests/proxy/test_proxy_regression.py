"""Regression tests for proxy fix:
1. Persistent context + proxy (new path via launch_persistent_context)
2. Persistent context WITHOUT proxy (should still use launch_persistent_context)
3. Non-persistent + proxy on CrawlerRunConfig (existing path, must not break)
4. Non-persistent, no proxy (basic crawl, must not break)
"""
import asyncio
import os
import shutil
import uuid
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import ProxyConfig

TEST_URL = "https://httpbin.org/ip"  # Simple endpoint, returns IP


async def test(label, browser_config, run_config=None):
    print(f"\n{'='*60}")
    print(f"Test: {label}")
    print(f"{'='*60}")
    run_config = run_config or CrawlerRunConfig()
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(TEST_URL, config=run_config)
            print(f"  Status: {result.status_code}")
            print(f"  HTML bytes: {len(result.html)}")
            if result.markdown:
                # httpbin.org/ip returns JSON with "origin" key
                md = result.markdown.raw_markdown.strip()
                print(f"  Content: {md[:200]}")
            if result.error_message:
                print(f"  ERROR: {result.error_message}")
            return result
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        return None


async def main():
    proxy = ProxyConfig(
        server="https://network.joinmassive.com:65535",
        username="mpuQHs4sWZ-country-US",
        password="D0yWxVQo8wQ05RWqz1Bn",
    )

    # 1. Persistent context + proxy (the fixed path)
    pd = os.path.expanduser(f"~/.crawl4ai/test_{uuid.uuid4().hex[:8]}")
    os.makedirs(pd, exist_ok=True)
    try:
        await test(
            "Persistent + proxy (launch_persistent_context)",
            BrowserConfig(
                headless=True,
                use_persistent_context=True,
                user_data_dir=pd,
                proxy_config=proxy,
            ),
        )
    finally:
        shutil.rmtree(pd, ignore_errors=True)

    # 2. Persistent context WITHOUT proxy
    pd2 = os.path.expanduser(f"~/.crawl4ai/test_{uuid.uuid4().hex[:8]}")
    os.makedirs(pd2, exist_ok=True)
    try:
        await test(
            "Persistent, no proxy (launch_persistent_context)",
            BrowserConfig(
                headless=True,
                use_persistent_context=True,
                user_data_dir=pd2,
            ),
        )
    finally:
        shutil.rmtree(pd2, ignore_errors=True)

    # 3. Non-persistent + proxy on CrawlerRunConfig
    await test(
        "Non-persistent + proxy on RunConfig",
        BrowserConfig(headless=True),
        CrawlerRunConfig(
            proxy_config=proxy,
        ),
    )

    # 4. Basic crawl - no proxy, no persistent
    await test(
        "Basic crawl (no proxy, no persistent)",
        BrowserConfig(headless=True),
    )

    print("\n" + "="*60)
    print("All regression tests complete.")


asyncio.run(main())
