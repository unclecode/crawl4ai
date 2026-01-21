"""
Crawler for batdongsan.com.vn - Vietnamese Real Estate Website
This script crawls property listings from batdongsan.com.vn and extracts structured data.

Usage:
    python crawl_batdongsan.py

Features:
- Crawl property listings with detailed information
- Support for pagination
- Export data to JSON format
- Handle dynamic content loading
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


class BatDongSanCrawler:
    """Crawler for batdongsan.com.vn"""

    def __init__(self, headless: bool = True):
        """
        Initialize the crawler

        Args:
            headless: Run browser in headless mode (default: True)
        """
        self.browser_config = BrowserConfig(
            headless=headless,
            verbose=True,
            java_script_enabled=True
        )

    def get_listing_schema(self):
        """
        Define CSS extraction schema for property listings

        Returns:
            dict: CSS extraction schema
        """
        schema = {
            "name": "BatDongSan Property Listings",
            "baseSelector": "div.re__card-full",  # Main container for each listing
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
                    "name": "toilets",
                    "selector": "span.re__card-config-toilet",
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
                },
                {
                    "name": "publish_date",
                    "selector": "span.re__card-published-info-date",
                    "type": "text",
                }
            ]
        }
        return schema

    async def crawl_listing_page(self, url: str, session_id: str = None) -> List[Dict]:
        """
        Crawl a single listing page

        Args:
            url: URL of the listing page
            session_id: Optional session ID to maintain state across requests

        Returns:
            List of property dictionaries
        """
        extraction_strategy = JsonCssExtractionStrategy(self.get_listing_schema())

        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
            session_id=session_id,
            wait_until="networkidle",  # Wait for network to be idle
            delay_before_return_html=2  # Wait 2 seconds for dynamic content
        )

        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)

            if result.success:
                try:
                    properties = json.loads(result.extracted_content)
                    return properties
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                    return []
            else:
                print(f"Failed to crawl {url}")
                return []

    async def crawl_multiple_pages(self, base_url: str, num_pages: int = 3) -> List[Dict]:
        """
        Crawl multiple pages of listings

        Args:
            base_url: Base URL for the search/category
            num_pages: Number of pages to crawl (default: 3)

        Returns:
            List of all properties from all pages
        """
        all_properties = []

        for page_num in range(1, num_pages + 1):
            # Construct URL for pagination
            # batdongsan.com.vn typically uses /p{page_num} for pagination
            if page_num == 1:
                url = base_url
            else:
                # Add pagination parameter (adjust based on actual URL structure)
                url = f"{base_url}/p{page_num}"

            print(f"\n{'='*60}")
            print(f"Crawling page {page_num}: {url}")
            print(f"{'='*60}")

            properties = await self.crawl_listing_page(url)

            if properties:
                all_properties.extend(properties)
                print(f"Found {len(properties)} properties on page {page_num}")
            else:
                print(f"No properties found on page {page_num}")
                # If no results, might have reached the last page
                if page_num > 1:
                    break

            # Add delay between pages to be respectful
            if page_num < num_pages:
                await asyncio.sleep(2)

        return all_properties

    def save_to_json(self, data: List[Dict], filename: str = None):
        """
        Save crawled data to JSON file

        Args:
            data: List of property dictionaries
            filename: Output filename (default: batdongsan_YYYYMMDD_HHMMSS.json)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batdongsan_{timestamp}.json"

        output_dir = "crawled_data"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"Data saved to: {filepath}")
        print(f"Total properties: {len(data)}")
        print(f"{'='*60}")

        return filepath


async def example_crawl_ban_can_ho():
    """
    Example: Crawl apartment listings for sale
    """
    print("Example: Crawling apartment listings for sale in Ho Chi Minh City")
    print("="*60)

    crawler = BatDongSanCrawler(headless=True)

    # Example URL for apartments for sale in HCMC
    # Note: Update this URL based on actual batdongsan.com.vn structure
    url = "https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-hcm"

    # Crawl 3 pages
    properties = await crawler.crawl_multiple_pages(url, num_pages=3)

    # Save to JSON
    if properties:
        filepath = crawler.save_to_json(properties, "ban_can_ho_hcm.json")

        # Print sample data
        print("\nSample property:")
        print(json.dumps(properties[0], ensure_ascii=False, indent=2))
    else:
        print("No properties found")


async def example_crawl_cho_thue_nha():
    """
    Example: Crawl house rental listings
    """
    print("\nExample: Crawling house rental listings in Hanoi")
    print("="*60)

    crawler = BatDongSanCrawler(headless=True)

    # Example URL for house rentals in Hanoi
    url = "https://batdongsan.com.vn/cho-thue-nha-rieng-ha-noi"

    # Crawl 2 pages
    properties = await crawler.crawl_multiple_pages(url, num_pages=2)

    # Save to JSON
    if properties:
        filepath = crawler.save_to_json(properties, "cho_thue_nha_hanoi.json")
    else:
        print("No properties found")


async def example_custom_url():
    """
    Example: Crawl from a custom URL
    You can modify this to use any search URL from batdongsan.com.vn
    """
    print("\nExample: Custom URL crawling")
    print("="*60)

    crawler = BatDongSanCrawler(headless=True)

    # Replace this with your desired URL
    custom_url = "https://batdongsan.com.vn/ban-nha-rieng-tp-hcm"

    properties = await crawler.crawl_multiple_pages(custom_url, num_pages=2)

    if properties:
        crawler.save_to_json(properties)

        # Print statistics
        print(f"\nCrawling Statistics:")
        print(f"Total properties: {len(properties)}")

        # Count properties by location if available
        locations = {}
        for prop in properties:
            location = prop.get('location', 'Unknown')
            locations[location] = locations.get(location, 0) + 1

        print("\nTop 5 locations:")
        sorted_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]
        for location, count in sorted_locations:
            print(f"  {location}: {count} properties")


async def main():
    """
    Main function with multiple examples
    """
    print("="*60)
    print("BatDongSan.com.vn Crawler")
    print("="*60)

    # Run example - crawl apartments for sale
    await example_crawl_ban_can_ho()

    # Uncomment to run other examples:
    # await example_crawl_cho_thue_nha()
    # await example_custom_url()


if __name__ == "__main__":
    asyncio.run(main())
