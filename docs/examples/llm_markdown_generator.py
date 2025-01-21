import os
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import LLMContentFilter

async def test_llm_filter():
    # Create an HTML source that needs intelligent filtering
    url = "https://docs.python.org/3/tutorial/classes.html"
    
    browser_config = BrowserConfig(
        headless=True,
        verbose=True
    )
    
    # run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First get the raw HTML
        result = await crawler.arun(url, config=run_config)
        html = result.cleaned_html

        # Initialize LLM filter with focused instruction
        filter = LLMContentFilter(
            provider="openai/gpt-4o",
            api_token=os.getenv('OPENAI_API_KEY'),
            instruction="""
            Focus on extracting the core educational content about Python classes.
            Include:
            - Key concepts and their explanations
            - Important code examples
            - Essential technical details
            Exclude:
            - Navigation elements
            - Sidebars
            - Footer content
            - Version information
            - Any non-essential UI elements
            
            Format the output as clean markdown with proper code blocks and headers.
            """,
            verbose=True
        )
        
        filter = LLMContentFilter(
            provider="openai/gpt-4o",
            api_token=os.getenv('OPENAI_API_KEY'),
            chunk_token_threshold=2 ** 12 * 2, # 2048 * 2
            instruction="""
            Extract the main educational content while preserving its original wording and substance completely. Your task is to:

            1. Maintain the exact language and terminology used in the main content
            2. Keep all technical explanations, examples, and educational content intact
            3. Preserve the original flow and structure of the core content
            4. Remove only clearly irrelevant elements like:
            - Navigation menus
            - Advertisement sections
            - Cookie notices
            - Footers with site information
            - Sidebars with external links
            - Any UI elements that don't contribute to learning

            The goal is to create a clean markdown version that reads exactly like the original article, 
            keeping all valuable content but free from distracting elements. Imagine you're creating 
            a perfect reading experience where nothing valuable is lost, but all noise is removed.
            """,
            verbose=True
        )        

        # Apply filtering
        filtered_content = filter.filter_content(html, ignore_cache = True)
        
        # Show results
        print("\nFiltered Content Length:", len(filtered_content))
        print("\nFirst 500 chars of filtered content:")
        if filtered_content:
            print(filtered_content[0][:500])
        
        # Save on disc the markdown version
        with open("filtered_content.md", "w", encoding="utf-8") as f:
            f.write("\n".join(filtered_content))
        
        # Show token usage
        filter.show_usage()

if __name__ == "__main__":
    asyncio.run(test_llm_filter())