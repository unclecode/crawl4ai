#!/usr/bin/env python3
"""
Prefetch Mode and Two-Phase Crawling Example

Prefetch mode is a fast path that skips heavy processing and returns
only HTML + links. This is ideal for:

- Site mapping: Quickly discover all URLs
- Selective crawling: Find URLs first, then process only what you need
- Link validation: Check which pages exist without full processing
- Crawl planning: Estimate size before committing resources

Key concept:
- `prefetch=True` in CrawlerRunConfig enables fast link-only extraction
- Skips: markdown generation, content scraping, media extraction, LLM extraction
- Returns: HTML and links dictionary

Performance benefit: ~5-10x faster than full processing
"""

import asyncio
import time
from typing import List, Dict

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig


async def example_basic_prefetch():
    """
    Example 1: Basic prefetch mode.

    Shows how prefetch returns HTML and links without heavy processing.
    """
    print("\n" + "=" * 60)
    print("Example 1: Basic Prefetch Mode")
    print("=" * 60)

    async with AsyncWebCrawler(verbose=False) as crawler:
        # Enable prefetch mode
        config = CrawlerRunConfig(prefetch=True)

        print("\nFetching with prefetch=True...")
        result = await crawler.arun("https://books.toscrape.com", config=config)

        print(f"\nResult summary:")
        print(f"  Success: {result.success}")
        print(f"  HTML length: {len(result.html) if result.html else 0} chars")
        print(f"  Internal links: {len(result.links.get('internal', []))}")
        print(f"  External links: {len(result.links.get('external', []))}")

        # These should be None/empty in prefetch mode
        print(f"\n  Skipped processing:")
        print(f"    Markdown: {result.markdown}")
        print(f"    Cleaned HTML: {result.cleaned_html}")
        print(f"    Extracted content: {result.extracted_content}")

        # Show some discovered links
        internal_links = result.links.get("internal", [])
        if internal_links:
            print(f"\n  Sample internal links:")
            for link in internal_links[:5]:
                print(f"    - {link['href'][:60]}...")


async def example_performance_comparison():
    """
    Example 2: Compare prefetch vs full processing performance.
    """
    print("\n" + "=" * 60)
    print("Example 2: Performance Comparison")
    print("=" * 60)

    url = "https://books.toscrape.com"

    async with AsyncWebCrawler(verbose=False) as crawler:
        # Warm up - first request is slower due to browser startup
        await crawler.arun(url, config=CrawlerRunConfig())

        # Prefetch mode timing
        start = time.time()
        prefetch_result = await crawler.arun(url, config=CrawlerRunConfig(prefetch=True))
        prefetch_time = time.time() - start

        # Full processing timing
        start = time.time()
        full_result = await crawler.arun(url, config=CrawlerRunConfig())
        full_time = time.time() - start

        print(f"\nTiming comparison:")
        print(f"  Prefetch mode: {prefetch_time:.3f}s")
        print(f"  Full processing: {full_time:.3f}s")
        print(f"  Speedup: {full_time / prefetch_time:.1f}x faster")

        print(f"\nOutput comparison:")
        print(f"  Prefetch - Links found: {len(prefetch_result.links.get('internal', []))}")
        print(f"  Full - Links found: {len(full_result.links.get('internal', []))}")
        print(f"  Full - Markdown length: {len(full_result.markdown.raw_markdown) if full_result.markdown else 0}")


async def example_two_phase_crawl():
    """
    Example 3: Two-phase crawling pattern.

    Phase 1: Fast discovery with prefetch
    Phase 2: Full processing on selected URLs
    """
    print("\n" + "=" * 60)
    print("Example 3: Two-Phase Crawling")
    print("=" * 60)

    async with AsyncWebCrawler(verbose=False) as crawler:
        # ═══════════════════════════════════════════════════════════
        # Phase 1: Fast URL discovery
        # ═══════════════════════════════════════════════════════════
        print("\n--- Phase 1: Fast Discovery ---")

        prefetch_config = CrawlerRunConfig(prefetch=True)
        start = time.time()
        discovery = await crawler.arun("https://books.toscrape.com", config=prefetch_config)
        discovery_time = time.time() - start

        all_urls = [link["href"] for link in discovery.links.get("internal", [])]
        print(f"  Discovered {len(all_urls)} URLs in {discovery_time:.2f}s")

        # Filter to URLs we care about (e.g., book detail pages)
        # On books.toscrape.com, book pages contain "catalogue/" but not "category/"
        book_urls = [
            url for url in all_urls
            if "catalogue/" in url and "category/" not in url
        ][:5]  # Limit to 5 for demo

        print(f"  Filtered to {len(book_urls)} book pages")

        # ═══════════════════════════════════════════════════════════
        # Phase 2: Full processing on selected URLs
        # ═══════════════════════════════════════════════════════════
        print("\n--- Phase 2: Full Processing ---")

        full_config = CrawlerRunConfig(
            word_count_threshold=10,
            remove_overlay_elements=True,
        )

        results = []
        start = time.time()

        for url in book_urls:
            result = await crawler.arun(url, config=full_config)
            if result.success:
                results.append(result)
                title = result.url.split("/")[-2].replace("-", " ").title()[:40]
                md_len = len(result.markdown.raw_markdown) if result.markdown else 0
                print(f"    Processed: {title}... ({md_len} chars)")

        processing_time = time.time() - start
        print(f"\n  Processed {len(results)} pages in {processing_time:.2f}s")

        # ═══════════════════════════════════════════════════════════
        # Summary
        # ═══════════════════════════════════════════════════════════
        print(f"\n--- Summary ---")
        print(f"  Discovery phase: {discovery_time:.2f}s ({len(all_urls)} URLs)")
        print(f"  Processing phase: {processing_time:.2f}s ({len(results)} pages)")
        print(f"  Total time: {discovery_time + processing_time:.2f}s")
        print(f"  URLs skipped: {len(all_urls) - len(book_urls)} (not matching filter)")


async def example_prefetch_with_deep_crawl():
    """
    Example 4: Combine prefetch with deep crawl strategy.

    Use prefetch mode during deep crawl for maximum speed.
    """
    print("\n" + "=" * 60)
    print("Example 4: Prefetch with Deep Crawl")
    print("=" * 60)

    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

    async with AsyncWebCrawler(verbose=False) as crawler:
        # Deep crawl with prefetch - maximum discovery speed
        config = CrawlerRunConfig(
            prefetch=True,  # Fast mode
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=1,
                max_pages=10,
            )
        )

        print("\nDeep crawling with prefetch mode...")
        start = time.time()

        result_container = await crawler.arun("https://books.toscrape.com", config=config)

        # Handle iterator result from deep crawl
        if hasattr(result_container, '__iter__'):
            results = list(result_container)
        else:
            results = [result_container]

        elapsed = time.time() - start

        # Collect all discovered links
        all_internal_links = set()
        all_external_links = set()

        for result in results:
            for link in result.links.get("internal", []):
                all_internal_links.add(link["href"])
            for link in result.links.get("external", []):
                all_external_links.add(link["href"])

        print(f"\nResults:")
        print(f"  Pages crawled: {len(results)}")
        print(f"  Total internal links discovered: {len(all_internal_links)}")
        print(f"  Total external links discovered: {len(all_external_links)}")
        print(f"  Time: {elapsed:.2f}s")


async def example_prefetch_with_raw_html():
    """
    Example 5: Prefetch with raw HTML input.

    You can also use prefetch mode with raw: URLs for cached content.
    """
    print("\n" + "=" * 60)
    print("Example 5: Prefetch with Raw HTML")
    print("=" * 60)

    sample_html = """
    <html>
        <head><title>Sample Page</title></head>
        <body>
            <h1>Hello World</h1>
            <nav>
                <a href="/page1">Internal Page 1</a>
                <a href="/page2">Internal Page 2</a>
                <a href="https://example.com/external">External Link</a>
            </nav>
            <main>
                <p>This is the main content with <a href="/page3">another link</a>.</p>
            </main>
        </body>
    </html>
    """

    async with AsyncWebCrawler(verbose=False) as crawler:
        config = CrawlerRunConfig(
            prefetch=True,
            base_url="https://mysite.com",  # For resolving relative links
        )

        result = await crawler.arun(f"raw:{sample_html}", config=config)

        print(f"\nExtracted from raw HTML:")
        print(f"  Internal links: {len(result.links.get('internal', []))}")
        for link in result.links.get("internal", []):
            print(f"    - {link['href']} ({link['text']})")

        print(f"\n  External links: {len(result.links.get('external', []))}")
        for link in result.links.get("external", []):
            print(f"    - {link['href']} ({link['text']})")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Prefetch Mode and Two-Phase Crawling Examples")
    print("=" * 60)

    await example_basic_prefetch()
    await example_performance_comparison()
    await example_two_phase_crawl()
    await example_prefetch_with_deep_crawl()
    await example_prefetch_with_raw_html()


if __name__ == "__main__":
    asyncio.run(main())
