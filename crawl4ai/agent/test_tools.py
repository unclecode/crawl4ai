#!/usr/bin/env python
"""Test script for Crawl4AI tools - tests tools directly without the agent."""

import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def test_quick_crawl():
    """Test quick_crawl tool logic directly."""
    print("\n" + "="*60)
    print("TEST 1: Quick Crawl - Markdown Format")
    print("="*60)

    crawler_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=crawler_config) as crawler:
        result = await crawler.arun(url="https://example.com", config=run_config)

        print(f"Success: {result.success}")
        print(f"URL: {result.url}")

        # Handle markdown - can be string or MarkdownGenerationResult object
        if isinstance(result.markdown, str):
            markdown_content = result.markdown
        elif hasattr(result.markdown, 'raw_markdown'):
            markdown_content = result.markdown.raw_markdown
        else:
            markdown_content = str(result.markdown)

        print(f"Markdown type: {type(result.markdown)}")
        print(f"Markdown length: {len(markdown_content)}")
        print(f"Markdown preview:\n{markdown_content[:300]}")

        return result.success


async def test_session_workflow():
    """Test session-based workflow."""
    print("\n" + "="*60)
    print("TEST 2: Session-Based Workflow")
    print("="*60)

    crawler_config = BrowserConfig(headless=True, verbose=False)

    # Start session
    crawler = AsyncWebCrawler(config=crawler_config)
    await crawler.__aenter__()
    print("✓ Session started")

    try:
        # Navigate to URL
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(url="https://example.com", config=run_config)
        print(f"✓ Navigated to {result.url}, success: {result.success}")

        # Extract data
        if isinstance(result.markdown, str):
            markdown_content = result.markdown
        elif hasattr(result.markdown, 'raw_markdown'):
            markdown_content = result.markdown.raw_markdown
        else:
            markdown_content = str(result.markdown)

        print(f"✓ Extracted {len(markdown_content)} chars of markdown")
        print(f"  Preview: {markdown_content[:200]}")

        # Screenshot test - need to re-fetch with screenshot enabled
        screenshot_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, screenshot=True)
        result2 = await crawler.arun(url=result.url, config=screenshot_config)
        print(f"✓ Screenshot captured: {result2.screenshot is not None}")

        return True

    finally:
        # Close session
        await crawler.__aexit__(None, None, None)
        print("✓ Session closed")


async def test_html_format():
    """Test HTML output format."""
    print("\n" + "="*60)
    print("TEST 3: Quick Crawl - HTML Format")
    print("="*60)

    crawler_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=crawler_config) as crawler:
        result = await crawler.arun(url="https://example.com", config=run_config)

        print(f"Success: {result.success}")
        print(f"HTML length: {len(result.html)}")
        print(f"HTML preview:\n{result.html[:300]}")

        return result.success


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print(" CRAWL4AI TOOLS TEST SUITE")
    print("="*70)

    tests = [
        ("Quick Crawl (Markdown)", test_quick_crawl),
        ("Session Workflow", test_session_workflow),
        ("Quick Crawl (HTML)", test_html_format),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))

    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)

    for name, success, error in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {name}")
        if error:
            print(f"     Error: {error}")

    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    print(f"\nTotal: {total} | Passed: {passed} | Failed: {total - passed}")

    return all(success for _, success, _ in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
