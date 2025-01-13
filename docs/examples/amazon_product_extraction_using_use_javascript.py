"""
This example demonstrates how to use JSON CSS extraction to scrape product information 
from Amazon search results. It shows how to extract structured data like product titles,
prices, ratings, and other details using CSS selectors.
"""

from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json


async def extract_amazon_products():
    # Initialize browser config
    browser_config = BrowserConfig(
        # browser_type="chromium",
        headless=True
    )

    js_code_to_search = """
        const task = async () => {
            document.querySelector('#twotabsearchtextbox').value = 'Samsung Galaxy Tab';
            document.querySelector('#nav-search-submit-button').click();
        }
        await task();
    """
    js_code_to_search_sync = """
            document.querySelector('#twotabsearchtextbox').value = 'Samsung Galaxy Tab';
            document.querySelector('#nav-search-submit-button').click();
    """
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        js_code=js_code_to_search,
        wait_for='css:[data-component-type="s-search-result"]',
        extraction_strategy=JsonCssExtractionStrategy(
            schema={
                "name": "Amazon Product Search Results",
                "baseSelector": "[data-component-type='s-search-result']",
                "fields": [
                    {
                        "name": "asin",
                        "selector": "",
                        "type": "attribute",
                        "attribute": "data-asin",
                    },
                    {"name": "title", "selector": "h2 a span", "type": "text"},
                    {
                        "name": "url",
                        "selector": "h2 a",
                        "type": "attribute",
                        "attribute": "href",
                    },
                    {
                        "name": "image",
                        "selector": ".s-image",
                        "type": "attribute",
                        "attribute": "src",
                    },
                    {
                        "name": "rating",
                        "selector": ".a-icon-star-small .a-icon-alt",
                        "type": "text",
                    },
                    {
                        "name": "reviews_count",
                        "selector": "[data-csa-c-func-deps='aui-da-a-popover'] ~ span span",
                        "type": "text",
                    },
                    {
                        "name": "price",
                        "selector": ".a-price .a-offscreen",
                        "type": "text",
                    },
                    {
                        "name": "original_price",
                        "selector": ".a-price.a-text-price .a-offscreen",
                        "type": "text",
                    },
                    {
                        "name": "sponsored",
                        "selector": ".puis-sponsored-label-text",
                        "type": "exists",
                    },
                    {
                        "name": "delivery_info",
                        "selector": "[data-cy='delivery-recipe'] .a-color-base",
                        "type": "text",
                        "multiple": True,
                    },
                ],
            }
        ),
    )

    # Example search URL (you should replace with your actual Amazon URL)
    url = "https://www.amazon.com/"

    # Use context manager for proper resource handling
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Extract the data
        result = await crawler.arun(url=url, config=crawler_config)

        # Process and print the results
        if result and result.extracted_content:
            # Parse the JSON string into a list of products
            products = json.loads(result.extracted_content)

            # Process each product in the list
            for product in products:
                print("\nProduct Details:")
                print(f"ASIN: {product.get('asin')}")
                print(f"Title: {product.get('title')}")
                print(f"Price: {product.get('price')}")
                print(f"Original Price: {product.get('original_price')}")
                print(f"Rating: {product.get('rating')}")
                print(f"Reviews: {product.get('reviews_count')}")
                print(f"Sponsored: {'Yes' if product.get('sponsored') else 'No'}")
                if product.get("delivery_info"):
                    print(f"Delivery: {' '.join(product['delivery_info'])}")
                print("-" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(extract_amazon_products())
