import asyncio
from typing import List

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BFSDeepCrawlStrategy,
    CrawlResult,
    URLFilter, # Base class for filters, not directly used in examples but good to import for context
    ContentTypeFilter,
    DomainFilter,
    FilterChain,
    URLPatternFilter,
    SEOFilter # Advanced filter, can be introduced later or as bonus
)

async def deep_crawl_filter_tutorial_part_2():
    """
    Tutorial demonstrating URL filters in Crawl4AI, focusing on isolated filter behavior
    before integrating them into a deep crawl.

    This tutorial covers:
    - Testing individual filters with synthetic URLs.
    - Understanding filter logic and behavior in isolation.
    - Combining filters using FilterChain.
    - Integrating filters into a deep crawling example.
    """

    # === Introduction: URL Filters in Isolation ===
    print("\n" + "=" * 40)
    print("=== Introduction: URL Filters in Isolation ===")
    print("=" * 40 + "\n")
    print("In this section, we will explore each filter individually using synthetic URLs.")
    print("This allows us to understand exactly how each filter works before using them in a crawl.\n")


    # === 2. ContentTypeFilter - Testing in Isolation ===
    print("\n" + "=" * 40)
    print("=== 2. ContentTypeFilter - Testing in Isolation ===")
    print("=" * 40 + "\n")

    # 2.1. Create ContentTypeFilter:
    # Create a ContentTypeFilter to allow only 'text/html' and 'application/json' content types 
    # BASED ON URL EXTENSIONS.
    content_type_filter = ContentTypeFilter(allowed_types=["text/html", "application/json"])
    print("ContentTypeFilter created, allowing types (by extension): ['text/html', 'application/json']")
    print("Note: ContentTypeFilter in Crawl4ai works by checking URL file extensions, not HTTP headers.")


    # 2.2. Synthetic URLs for Testing:
    # ContentTypeFilter checks URL extensions. We provide URLs with different extensions to test.
    test_urls_content_type = [
        "https://example.com/page.html",       # Should pass: .html extension (text/html)
        "https://example.com/data.json",       # Should pass: .json extension (application/json)
        "https://example.com/image.png",       # Should reject: .png extension (not allowed type)
        "https://example.com/document.pdf",    # Should reject: .pdf extension (not allowed type)
        "https://example.com/page",            # Should pass: no extension (defaults to allow) - check default behaviour!
        "https://example.com/page.xhtml",      # Should pass: .xhtml extension (text/html)
    ]

    # 2.3. Apply Filter and Show Results:
    print("\n=== Testing ContentTypeFilter (URL Extension based) ===")
    for url in test_urls_content_type:
        passed = content_type_filter.apply(url)
        result = "PASSED" if passed else "REJECTED"
        extension = ContentTypeFilter._extract_extension(url) # Show extracted extension for clarity
        print(f"- URL: {url} - {result} (Extension: '{extension or 'No Extension'}')")
    print("=" * 40)

    input("Press Enter to continue to DomainFilter example...")

    # === 3. DomainFilter - Testing in Isolation ===
    print("\n" + "=" * 40)
    print("=== 3. DomainFilter - Testing in Isolation ===")
    print("=" * 40 + "\n")

    # 3.1. Create DomainFilter:
    domain_filter = DomainFilter(allowed_domains=["crawl4ai.com", "example.com"])
    print("DomainFilter created, allowing domains: ['crawl4ai.com', 'example.com']")

    # 3.2. Synthetic URLs for Testing:
    test_urls_domain = [
        "https://docs.crawl4ai.com/api",
        "https://example.com/products",
        "https://another-website.org/blog",
        "https://sub.example.com/about",
        "https://crawl4ai.com.attacker.net", # Corrected example: now should be rejected
    ]

    # 3.3. Apply Filter and Show Results:
    print("\n=== Testing DomainFilter ===")
    for url in test_urls_domain:
        passed = domain_filter.apply(url)
        result = "PASSED" if passed else "REJECTED"
        print(f"- URL: {url} - {result}")
    print("=" * 40)

    input("Press Enter to continue to FilterChain example...")

    # === 4. FilterChain - Combining Filters ===
    print("\n" + "=" * 40)
    print("=== 4. FilterChain - Combining Filters ===")
    print("=" * 40 + "\n")

    combined_filter = FilterChain(
        filters=[
            URLPatternFilter(patterns=["*api*"]),
            ContentTypeFilter(allowed_types=["text/html"]), # Still URL extension based
            DomainFilter(allowed_domains=["docs.crawl4ai.com"]),
        ]
    )
    print("FilterChain created, combining URLPatternFilter, ContentTypeFilter, and DomainFilter.")


    test_urls_combined = [
        "https://docs.crawl4ai.com/api/async-webcrawler",
        "https://example.com/api/products",
        "https://docs.crawl4ai.com/core/crawling",
        "https://another-website.org/api/data",
    ]

    # 4.3. Apply FilterChain and Show Results
    print("\n=== Testing FilterChain (URLPatternFilter + ContentTypeFilter + DomainFilter) ===")
    for url in test_urls_combined:
        passed = await combined_filter.apply(url)
        result = "PASSED" if passed else "REJECTED"
        print(f"- URL: {url} - {result}")
    print("=" * 40)

    input("Press Enter to continue to Deep Crawl with FilterChain example...")

    # === 5. Deep Crawl with FilterChain ===
    print("\n" + "=" * 40)
    print("=== 5. Deep Crawl with FilterChain ===")
    print("=" * 40 + "\n")
    print("Finally, let's integrate the FilterChain into a deep crawl example.")

    config_final_crawl = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=10,
            include_external=False,
            filter_chain=combined_filter
        ),
        verbose=False,
    )

    async with AsyncWebCrawler() as crawler:
        results_final_crawl: List[CrawlResult] = await crawler.arun(
            url="https://docs.crawl4ai.com", config=config_final_crawl
        )

        print("=== Crawled URLs (Deep Crawl with FilterChain) ===")
        for result in results_final_crawl:
            print(f"- {result.url}, Depth: {result.metadata.get('depth', 0)}")
        print("=" * 40)

    print("\nTutorial Completed! Review the output of each section to understand URL filters.")


if __name__ == "__main__":
    asyncio.run(deep_crawl_filter_tutorial_part_2())