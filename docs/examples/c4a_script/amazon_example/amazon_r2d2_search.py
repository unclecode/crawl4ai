#!/usr/bin/env python3
"""
Amazon R2D2 Product Search Example using Crawl4AI

This example demonstrates:
1. Using LLM to generate C4A-Script from HTML snippets
2. Multi-step crawling with session persistence
3. JSON CSS extraction for structured product data
4. Complete workflow: homepage → search → extract products

Requirements:
- Crawl4AI with generate_script support
- LLM API key (configured in environment)
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.script.c4a_compile import C4ACompiler


class AmazonR2D2Scraper:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.search_script_path = self.base_dir / "generated_search_script.js"
        self.schema_path = self.base_dir / "generated_product_schema.json"
        self.results_path = self.base_dir / "extracted_products.json"
        self.session_id = "amazon_r2d2_session"
        
    async def generate_search_script(self) -> str:
        """Generate JavaScript for Amazon search interaction"""
        print("🔧 Generating search script from header.html...")
        
        # Check if already generated
        if self.search_script_path.exists():
            print("✅ Using cached search script")
            return self.search_script_path.read_text()
        
        # Read the header HTML
        header_html = (self.base_dir / "header.html").read_text()
        
        # Generate script using LLM
        search_goal = """
        Find the search box and search button, then:
        1. Wait for the search box to be visible
        2. Click on the search box to focus it
        3. Clear any existing text
        4. Type "r2d2" into the search box
        5. Click the search submit button
        6. Wait for navigation to complete and search results to appear
        """
        
        try:
            script = C4ACompiler.generate_script(
                html=header_html,
                query=search_goal,
                mode="js"
            )
            
            # Save for future use
            self.search_script_path.write_text(script)
            print("✅ Search script generated and saved!")
            print(f"📄 Script:\n{script}")
            return script
            
        except Exception as e:
            print(f"❌ Error generating search script: {e}")

    
    async def generate_product_schema(self) -> Dict[str, Any]:
        """Generate JSON CSS extraction schema from product HTML"""
        print("\n🔧 Generating product extraction schema...")
        
        # Check if already generated
        if self.schema_path.exists():
            print("✅ Using cached extraction schema")
            return json.loads(self.schema_path.read_text())
        
        # Read the product HTML
        product_html = (self.base_dir / "product.html").read_text()
        
        # Generate extraction schema using LLM
        schema_goal = """
        Create a JSON CSS extraction schema to extract:
        - Product title (from the h2 element)
        - Price (the dollar amount)
        - Rating (star rating value)
        - Number of reviews
        - Delivery information
        - Product URL (from the main product link)
        - Whether it's sponsored
        - Small business badge if present
        
        The schema should handle multiple products on a search results page.
        """
        
        try:
            # Generate JavaScript that returns the schema
            schema = JsonCssExtractionStrategy.generate_schema(
                html=product_html,
                query=schema_goal,
            )
            
            # Save for future use
            self.schema_path.write_text(json.dumps(schema, indent=2))
            print("✅ Extraction schema generated and saved!")
            print(f"📄 Schema fields: {[f['name'] for f in schema['fields']]}")
            return schema
            
        except Exception as e:
            print(f"❌ Error generating schema: {e}")
    
    async def crawl_amazon(self):
        """Main crawling logic with 2 calls using same session"""
        print("\n🚀 Starting Amazon R2D2 product search...")
        
        # Generate scripts and schemas
        search_script = await self.generate_search_script()
        product_schema = await self.generate_product_schema()
        
        # Configure browser (headless=False to see the action)
        browser_config = BrowserConfig(
            headless=False,
            verbose=True,
            viewport_width=1920,
            viewport_height=1080
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print("\n📍 Step 1: Navigate to Amazon and search for R2D2")
            
            # FIRST CALL: Navigate to Amazon and execute search
            search_config = CrawlerRunConfig(
                session_id=self.session_id,
                js_code= f"(() => {{ {search_script} }})()",  # Execute generated JS
                wait_for=".s-search-results",  # Wait for search results
                extraction_strategy=JsonCssExtractionStrategy(schema=product_schema),
                delay_before_return_html=3.0  # Give time for results to load
            )
            
            results = await crawler.arun(
                url="https://www.amazon.com",
                config=search_config
            )
            
            if not results.success:
                print("❌ Failed to search Amazon")
                print(f"Error: {results.error_message}")
                return
            
            print("✅ Search completed successfully!")            
            print("✅ Product extraction completed!")
            
            # Extract and save results
            print("\n📍 Extracting product data")
            
            if results[0].extracted_content:
                products = json.loads(results[0].extracted_content)
                print(f"🔍 Found {len(products)} products in search results")

                print(f"✅ Extracted {len(products)} R2D2 products")

                # Save results
                self.results_path.write_text(
                    json.dumps(products, indent=2)
                )
                print(f"💾 Results saved to: {self.results_path}")
                
                # Print sample results
                print("\n📊 Sample Results:")
                for i, product in enumerate(products[:3], 1):
                    print(f"\n{i}. {product['title'][:60]}...")
                    print(f"   Price: ${product['price']}")
                    print(f"   Rating: {product['rating']} ({product['number_of_reviews']} reviews)")
                    print(f"   {'🏪 Small Business' if product['small_business_badge'] else ''}")
                    print(f"   {'📢 Sponsored' if product['sponsored'] else ''}")
                
            else:
                print("❌ No products extracted")



async def main():
    """Run the Amazon scraper"""
    scraper = AmazonR2D2Scraper()
    await scraper.crawl_amazon()
    
    print("\n🎉 Amazon R2D2 search example completed!")
    print("Check the generated files:")
    print("  - generated_search_script.js")
    print("  - generated_product_schema.json") 
    print("  - extracted_products.json")
    print("  - search_results_screenshot.png")


if __name__ == "__main__":
    asyncio.run(main())