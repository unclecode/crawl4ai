"""
Simple example script to crawl batdongsan.com.vn
Quickly modify the URL and run to get property data

Usage:
    python crawl_batdongsan_simple.py
"""

import asyncio
import json
import os
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


async def crawl_batdongsan(url: str, num_pages: int = 1):
    """
    Crawl batdongsan.com.vn and extract property listings

    Args:
        url: The URL to crawl (e.g., search page or category page)
        num_pages: Number of pages to crawl

    Returns:
        List of property dictionaries
    """
    # Configure browser
    browser_config = BrowserConfig(
        headless=True,  # Set to False to see the browser
        verbose=True,
        java_script_enabled=True
    )

    # Define what data to extract using CSS selectors
    # Note: You may need to update these selectors if the website structure changes
    extraction_schema = {
        "name": "BatDongSan Properties",
        "baseSelector": "div.re__card-full",  # Main container for each property
        "fields": [
            {
                "name": "title",
                "selector": "a.pr-title",
                "type": "text",
            },
            {
                "name": "link",
                "selector": "a.pr-title",
                "type": "attribute",
                "attribute": "href"
            },
            {
                "name": "price",
                "selector": "span.re__card-config-price",
                "type": "text",
            },
            {
                "name": "area",
                "selector": "span.re__card-config-area",
                "type": "text",
            },
            {
                "name": "location",
                "selector": "div.re__card-location",
                "type": "text",
            },
            {
                "name": "bedrooms",
                "selector": "span.re__card-config-bedroom",
                "type": "text",
            },
            {
                "name": "description",
                "selector": "div.re__card-description",
                "type": "text",
            },
            {
                "name": "image",
                "selector": "img.re__card-image",
                "type": "attribute",
                "attribute": "src"
            }
        ]
    }

    all_properties = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page_num in range(1, num_pages + 1):
            # Build URL for each page
            if page_num == 1:
                page_url = url
            else:
                page_url = f"{url}/p{page_num}"

            print(f"\nCrawling page {page_num}: {page_url}")

            # Configure crawler
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=JsonCssExtractionStrategy(extraction_schema),
                wait_until="networkidle",
                delay_before_return_html=2  # Wait for content to load
            )

            # Crawl the page
            result = await crawler.arun(url=page_url, config=crawler_config)

            if result.success:
                try:
                    properties = json.loads(result.extracted_content)
                    all_properties.extend(properties)
                    print(f"✓ Found {len(properties)} properties on page {page_num}")
                except json.JSONDecodeError:
                    print(f"✗ Error parsing data from page {page_num}")
            else:
                print(f"✗ Failed to crawl page {page_num}")

            # Delay between pages
            if page_num < num_pages:
                await asyncio.sleep(2)

    return all_properties


def save_results(properties, filename=None):
    """Save properties to JSON file"""
    if not properties:
        print("\nNo properties to save!")
        return

    # Create output directory
    output_dir = "crawled_data"
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batdongsan_{timestamp}.json"

    filepath = os.path.join(output_dir, filename)

    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(properties, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ Saved {len(properties)} properties to: {filepath}")
    print(f"{'='*60}")

    return filepath


async def main():
    """Main function"""
    print("="*60)
    print("BatDongSan.com.vn Crawler - Simple Version")
    print("="*60)

    # ========================================
    # CUSTOMIZE THESE SETTINGS
    # ========================================

    # URL to crawl - Change this to your desired category/search URL
    # Examples:
    # - Apartments for sale in HCMC: https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-hcm
    # - Houses for rent in Hanoi: https://batdongsan.com.vn/cho-thue-nha-rieng-ha-noi
    # - Land for sale in Binh Duong: https://batdongsan.com.vn/ban-dat-nen-binh-duong

    URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-hcm"

    # Number of pages to crawl
    NUM_PAGES = 3

    # Output filename (optional)
    OUTPUT_FILE = "properties.json"

    # ========================================

    print(f"\nURL: {URL}")
    print(f"Pages to crawl: {NUM_PAGES}")

    # Crawl the website
    properties = await crawl_batdongsan(URL, num_pages=NUM_PAGES)

    # Save results
    if properties:
        save_results(properties, OUTPUT_FILE)

        # Print sample property
        print("\nSample property:")
        print(json.dumps(properties[0], ensure_ascii=False, indent=2))

        # Print statistics
        print(f"\nTotal properties crawled: {len(properties)}")

        # Show price range if available
        prices = [p.get('price', '') for p in properties if p.get('price')]
        if prices:
            print(f"Found {len(prices)} properties with prices")

        # Show locations
        locations = {}
        for prop in properties:
            loc = prop.get('location', 'Unknown')
            if loc:
                locations[loc] = locations.get(loc, 0) + 1

        if locations:
            print("\nTop 5 locations:")
            sorted_locs = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]
            for loc, count in sorted_locs:
                print(f"  - {loc}: {count} properties")

    else:
        print("\n✗ No properties found. This might mean:")
        print("  1. The URL is incorrect")
        print("  2. The CSS selectors need to be updated")
        print("  3. The website structure has changed")
        print("\nTry running with headless=False to see what's happening")


if __name__ == "__main__":
    asyncio.run(main())
