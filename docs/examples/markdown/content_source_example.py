"""
Example showing how to use the content_source parameter to control HTML input for markdown generation.
"""
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator

async def demo_content_source():
    """Demonstrates different content_source options for markdown generation."""
    url = "https://example.com"  # Simple demo site
    
    print("Crawling with different content_source options...")
    
    # --- Example 1: Default Behavior (cleaned_html) ---
    # This uses the HTML after it has been processed by the scraping strategy
    # The HTML is cleaned, simplified, and optimized for readability
    default_generator = DefaultMarkdownGenerator()  # content_source="cleaned_html" is default
    default_config = CrawlerRunConfig(markdown_generator=default_generator)
    
    # --- Example 2: Raw HTML ---
    # This uses the original HTML directly from the webpage
    # Preserves more original content but may include navigation, ads, etc.
    raw_generator = DefaultMarkdownGenerator(content_source="raw_html")
    raw_config = CrawlerRunConfig(markdown_generator=raw_generator)
    
    # --- Example 3: Fit HTML ---
    # This uses preprocessed HTML optimized for schema extraction
    # Better for structured data extraction but may lose some formatting
    fit_generator = DefaultMarkdownGenerator(content_source="fit_html")
    fit_config = CrawlerRunConfig(markdown_generator=fit_generator)
    
    # Execute all three crawlers in sequence
    async with AsyncWebCrawler() as crawler:
        # Default (cleaned_html)
        result_default = await crawler.arun(url=url, config=default_config)
        
        # Raw HTML
        result_raw = await crawler.arun(url=url, config=raw_config)
        
        # Fit HTML
        result_fit = await crawler.arun(url=url, config=fit_config)
    
    # Print a summary of the results
    print("\nMarkdown Generation Results:\n")
    
    print("1. Default (cleaned_html):")
    print(f"   Length: {len(result_default.markdown.raw_markdown)} chars")
    print(f"   First 80 chars: {result_default.markdown.raw_markdown[:80]}...\n")
    
    print("2. Raw HTML:")
    print(f"   Length: {len(result_raw.markdown.raw_markdown)} chars")
    print(f"   First 80 chars: {result_raw.markdown.raw_markdown[:80]}...\n")
    
    print("3. Fit HTML:")
    print(f"   Length: {len(result_fit.markdown.raw_markdown)} chars")
    print(f"   First 80 chars: {result_fit.markdown.raw_markdown[:80]}...\n")
    
    # Demonstrate differences in output
    print("\nKey Takeaways:")
    print("- cleaned_html: Best for readable, focused content")
    print("- raw_html: Preserves more original content, but may include noise")
    print("- fit_html: Optimized for schema extraction and structured data")

if __name__ == "__main__":
    asyncio.run(demo_content_source())