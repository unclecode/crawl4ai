import asyncio
from web_scraper_lib import scrape_website
import os

async def test_library():
    """Test the mini library directly."""
    print("=== Testing Mini Library ===")
    
    # Test 1: Scrape with a custom model
    url = "https://marketplace.mainstreet.co.in/collections/adidas-yeezy/products/adidas-yeezy-boost-350-v2-yecheil-non-reflective"
    query = "Extract the following data: Product name, Product price, Product description, Product size. DO NOT EXTRACT ANYTHING ELSE."
    if os.path.exists("models"):
        model_name = os.listdir("models")[0].split(".")[0]
    else:
        raise Exception("No models found in models directory")

    print(f"Scraping: {url}")
    print(f"Query: {query}")
    
    try:
        result = await scrape_website(url, query, model_name)
        print("✅ Library test successful!")
        print(f"Extracted data: {result['extracted_data']}")
    except Exception as e:
        print(f"❌ Library test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_library())