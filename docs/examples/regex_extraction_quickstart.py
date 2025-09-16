# == File: regex_extraction_quickstart.py ==
"""
Mini–quick-start for RegexExtractionStrategy
────────────────────────────────────────────
3 bite-sized demos that parallel the style of *quickstart_examples_set_1.py*:

1.  **Default catalog** – scrape a page and pull out e-mails / phones / URLs, etc.
2.  **Custom pattern**  – add your own regex at instantiation time.
3.  **LLM-assisted schema** – ask the model to write a pattern, cache it, then
    run extraction _without_ further LLM calls.

Run the whole thing with::

    python regex_extraction_quickstart.py
"""

import os, json, asyncio
from pathlib import Path
from typing import List

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CrawlResult,
    RegexExtractionStrategy,
    LLMConfig,
)

# ────────────────────────────────────────────────────────────────────────────
# 1. Default-catalog extraction
# ────────────────────────────────────────────────────────────────────────────
async def demo_regex_default() -> None:
    print("\n=== 1. Regex extraction – default patterns ===")

    url = "https://www.iana.org/domains/example"      # has e-mail + URLs
    strategy = RegexExtractionStrategy(
        pattern = RegexExtractionStrategy.Url | RegexExtractionStrategy.Currency
    )               
    config   = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result: CrawlResult = await crawler.arun(url, config=config)

    print(f"Fetched {url} - success={result.success}")
    if result.success:
        data = json.loads(result.extracted_content)
        for d in data[:10]:
            print(f"  {d['label']:<12} {d['value']}")
        print(f"... total matches: {len(data)}")
    else:
        print("  !!! crawl failed")


# ────────────────────────────────────────────────────────────────────────────
# 2. Custom pattern override / extension
# ────────────────────────────────────────────────────────────────────────────
async def demo_regex_custom() -> None:
    print("\n=== 2. Regex extraction – custom price pattern ===")

    url = "https://www.apple.com/shop/buy-mac/macbook-pro"
    price_pattern = {"usd_price": r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?"}

    strategy = RegexExtractionStrategy(custom = price_pattern)
    config   = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result: CrawlResult = await crawler.arun(url, config=config)

    if result.success:
        data = json.loads(result.extracted_content)
        for d in data:
            print(f"  {d['value']}")
        if not data:
            print("  (No prices found - page layout may have changed)")
    else:
        print("  !!! crawl failed")


# ────────────────────────────────────────────────────────────────────────────
# 3. One-shot LLM pattern generation, then fast extraction
# ────────────────────────────────────────────────────────────────────────────
async def demo_regex_generate_pattern() -> None:
    print("\n=== 3. generate_pattern → regex extraction ===")

    cache_dir   = Path(__file__).parent / "tmp"
    cache_dir.mkdir(exist_ok=True)
    pattern_file = cache_dir / "price_pattern.json"

    url = "https://www.lazada.sg/tag/smartphone/"

    # ── 3-A. build or load the cached pattern
    if pattern_file.exists():
        pattern = json.load(pattern_file.open(encoding="utf-8"))
        print("Loaded cached pattern:", pattern)
    else:
        print("Generating pattern via LLM…")

        llm_cfg = LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token="env:OPENAI_API_KEY",
        )

        # pull one sample page as HTML context
        async with AsyncWebCrawler() as crawler:
            html = (await crawler.arun(url)).fit_html 

        pattern = RegexExtractionStrategy.generate_pattern(
            label="price",
            html=html,
            query="Prices in Malaysian Ringgit (e.g. RM1,299.00 or RM200)",
            llm_config=llm_cfg,
        )

        json.dump(pattern, pattern_file.open("w", encoding="utf-8"), indent=2)
        print("Saved pattern:", pattern_file)

    # ── 3-B. extraction pass – zero LLM calls
    strategy = RegexExtractionStrategy(custom=pattern)
    config   = CrawlerRunConfig(extraction_strategy=strategy, delay_before_return_html=3)

    async with AsyncWebCrawler() as crawler:
        result: CrawlResult = await crawler.arun(url, config=config)

    if result.success:
        data = json.loads(result.extracted_content)
        for d in data[:15]:
            print(f"  {d['value']}")
        print(f"... total matches: {len(data)}")
    else:
        print("  !!! crawl failed")


# ────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ────────────────────────────────────────────────────────────────────────────
async def main() -> None:
    # await demo_regex_default()
    # await demo_regex_custom()
    await demo_regex_generate_pattern()


if __name__ == "__main__":
    asyncio.run(main())
