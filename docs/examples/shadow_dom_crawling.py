"""
Shadow DOM Crawling Example
============================

Demonstrates how to use `flatten_shadow_dom=True` to extract content
hidden inside Shadow DOM trees on sites built with Web Components
(Stencil, Lit, Shoelace, Angular Elements, etc.).

Shadow DOM creates encapsulated sub-trees that are invisible to the
normal page serialization (page.content() / outerHTML). The
`flatten_shadow_dom` option walks these trees and produces a single
flat HTML document that includes all shadow content.

This example crawls a Bosch Rexroth product page where the product
description, technical specs, and downloads are rendered entirely
inside Shadow DOM by Stencil.js web components.
"""

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

URL = "https://store.boschrexroth.com/en/us/p/hydraulic-cylinder-r900999011"


async def main():
    browser_config = BrowserConfig(headless=True)

    # ── 1. Baseline: without shadow DOM flattening ──────────────────
    print("=" * 60)
    print("Without flatten_shadow_dom (baseline)")
    print("=" * 60)

    config = CrawlerRunConfig(
        wait_until="load",
        delay_before_return_html=3.0,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(URL, config=config)

    md = result.markdown.raw_markdown if result.markdown else ""
    print(f"Markdown length: {len(md)} chars")
    print(f"Has product description: {'mill type design' in md.lower()}")
    print(f"Has technical specs:     {'CDH1' in md}")
    print(f"Has downloads section:   {'Downloads' in md}")
    print()

    # ── 2. With shadow DOM flattening ───────────────────────────────
    print("=" * 60)
    print("With flatten_shadow_dom=True")
    print("=" * 60)

    config = CrawlerRunConfig(
        wait_until="load",
        delay_before_return_html=3.0,
        flatten_shadow_dom=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(URL, config=config)

    md = result.markdown.raw_markdown if result.markdown else ""
    print(f"Markdown length: {len(md)} chars")
    print(f"Has product description: {'mill type design' in md.lower()}")
    print(f"Has technical specs:     {'CDH1' in md}")
    print(f"Has downloads section:   {'Downloads' in md}")
    print()

    # Show the product content section
    idx = md.find("Product Description")
    if idx >= 0:
        print("── Extracted product content ──")
        print(md[idx:idx + 1200])


if __name__ == "__main__":
    asyncio.run(main())
