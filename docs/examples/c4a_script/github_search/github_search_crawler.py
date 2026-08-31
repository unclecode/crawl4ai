#!/usr/bin/env python3
"""
GitHub Advanced Search Example using Crawl4AI

This example demonstrates:
1. Using LLM to generate C4A-Script from HTML snippets
2. Single arun() call with navigation, search form filling, and extraction
3. JSON CSS extraction for structured repository data
4. Complete workflow: navigate → fill form → submit → extract results

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


class GitHubSearchScraper:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.search_script_path = self.base_dir / "generated_search_script.js"
        self.schema_path = self.base_dir / "generated_result_schema.json"
        self.results_path = self.base_dir / "extracted_repositories.json"
        self.session_id = "github_search_session"
        
    async def generate_search_script(self) -> str:
        """Generate JavaScript for GitHub advanced search interaction"""
        print("🔧 Generating search script from search_form.html...")
        
        # Check if already generated
        if self.search_script_path.exists():
            print("✅ Using cached search script")
            return self.search_script_path.read_text()
        
        # Read the search form HTML
        search_form_html = (self.base_dir / "search_form.html").read_text()
        
        # Generate script using LLM
        search_goal = """
        Search for crawl4AI repositories written in Python with more than 10000 stars:
        1. Wait for the main search input to be visible
        2. Type "crawl4AI" into the main search box
        3. Select "Python" from the language dropdown (#search_language)
        4. Type ">10000" into the stars input field (#search_stars)
        5. Click the search button to submit the form
        6. Wait for the search results to appear
        """
        
        try:
            script = C4ACompiler.generate_script(
                html=search_form_html,
                query=search_goal,
                mode="js"
            )
            
            # Save for future use
            self.search_script_path.write_text(script)
            print("✅ Search script generated and saved!")
            print(f"📄 Script preview:\n{script[:500]}...")
            return script
            
        except Exception as e:
            print(f"❌ Error generating search script: {e}")
            raise

    
    async def generate_result_schema(self) -> Dict[str, Any]:
        """Generate JSON CSS extraction schema from result HTML"""
        print("\n🔧 Generating result extraction schema...")
        
        # Check if already generated
        if self.schema_path.exists():
            print("✅ Using cached extraction schema")
            return json.loads(self.schema_path.read_text())
        
        # Read the result HTML
        result_html = (self.base_dir / "result.html").read_text()
        
        # Generate extraction schema using LLM
        schema_goal = """
        Create a JSON CSS extraction schema to extract from each repository card:
        - Repository name (the repository name only, not including owner)
        - Repository owner (organization or username)
        - Repository URL (full GitHub URL)
        - Description 
        - Primary programming language
        - Star count (numeric value)
        - Topics/tags (array of topic names)
        - Last updated (time ago string)
        - Whether it has a sponsor button
        
        The schema should handle multiple repository results on the search results page.
        """
        
        try:
            # Generate schema
            schema = JsonCssExtractionStrategy.generate_schema(
                html=result_html,
                query=schema_goal,
            )
            
            # Save for future use
            self.schema_path.write_text(json.dumps(schema, indent=2))
            print("✅ Extraction schema generated and saved!")
            print(f"📄 Schema fields: {[f['name'] for f in schema['fields']]}")
            return schema
            
        except Exception as e:
            print(f"❌ Error generating schema: {e}")
            raise
    
    async def crawl_github(self):
        """Main crawling logic with single arun() call"""
        print("\n🚀 Starting GitHub repository search...")
        
        # Generate scripts and schemas
        search_script = await self.generate_search_script()
        result_schema = await self.generate_result_schema()
        
        # Configure browser (headless=False to see the action)
        browser_config = BrowserConfig(
            headless=False,
            verbose=True,
            viewport_width=1920,
            viewport_height=1080
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print("\n📍 Navigating to GitHub advanced search and executing search...")
            
            # Single call: Navigate, execute search, and extract results
            search_config = CrawlerRunConfig(
                session_id=self.session_id,
                js_code=search_script,  # Execute generated JS
                # wait_for="[data-testid='results-list']",  # Wait for search results
                wait_for=".Box-sc-g0xbh4-0.iwUbcA",  # Wait for search results
                extraction_strategy=JsonCssExtractionStrategy(schema=result_schema),
                delay_before_return_html=3.0,  # Give time for results to fully load
                cache_mode=CacheMode.BYPASS  # Don't cache for fresh results
            )
            
            result = await crawler.arun(
                url="https://github.com/search/advanced",
                config=search_config
            )
            
            if not result.success:
                print("❌ Failed to search GitHub")
                print(f"Error: {result.error_message}")
                return
            
            print("✅ Search and extraction completed successfully!")
            
            # Extract and save results
            if result.extracted_content:
                repositories = json.loads(result.extracted_content)
                print(f"\n🔍 Found {len(repositories)} repositories matching criteria")
                
                # Save results
                self.results_path.write_text(
                    json.dumps(repositories, indent=2)
                )
                print(f"💾 Results saved to: {self.results_path}")
                
                # Print sample results
                print("\n📊 Sample Results:")
                for i, repo in enumerate(repositories[:5], 1):
                    print(f"\n{i}. {repo.get('owner', 'Unknown')}/{repo.get('name', 'Unknown')}")
                    print(f"   Description: {repo.get('description', 'No description')[:80]}...")
                    print(f"   Language: {repo.get('language', 'Unknown')}")
                    print(f"   Stars: {repo.get('stars', 'Unknown')}")
                    print(f"   Updated: {repo.get('last_updated', 'Unknown')}")
                    if repo.get('topics'):
                        print(f"   Topics: {', '.join(repo['topics'][:5])}")
                    print(f"   URL: {repo.get('url', 'Unknown')}")
                
            else:
                print("❌ No repositories extracted")
            
            # Save screenshot for reference
            if result.screenshot:
                screenshot_path = self.base_dir / "search_results_screenshot.png"
                with open(screenshot_path, "wb") as f:
                    f.write(result.screenshot)
                print(f"\n📸 Screenshot saved to: {screenshot_path}")


async def main():
    """Run the GitHub search scraper"""
    scraper = GitHubSearchScraper()
    await scraper.crawl_github()
    
    print("\n🎉 GitHub search example completed!")
    print("Check the generated files:")
    print("  - generated_search_script.js")
    print("  - generated_result_schema.json") 
    print("  - extracted_repositories.json")
    print("  - search_results_screenshot.png")


if __name__ == "__main__":
    asyncio.run(main())