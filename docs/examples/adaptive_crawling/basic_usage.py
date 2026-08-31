"""
Basic Adaptive Crawling Example

This example demonstrates the simplest use case of adaptive crawling:
finding information about a specific topic and knowing when to stop.
"""

import asyncio
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler


async def main():
    """Basic adaptive crawling example"""
    
    # Initialize the crawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Create an adaptive crawler with default settings (statistical strategy)
        adaptive = AdaptiveCrawler(crawler)
        
        # Note: You can also use embedding strategy for semantic understanding:
        # from crawl4ai import AdaptiveConfig
        # config = AdaptiveConfig(strategy="embedding")
        # adaptive = AdaptiveCrawler(crawler, config)
        
        # Start adaptive crawling
        print("Starting adaptive crawl for Python async programming information...")
        result = await adaptive.digest(
            start_url="https://docs.python.org/3/library/asyncio.html",
            query="async await context managers coroutines"
        )
        
        # Display crawl statistics
        print("\n" + "="*50)
        print("CRAWL STATISTICS")
        print("="*50)
        adaptive.print_stats(detailed=False)
        
        # Get the most relevant content found
        print("\n" + "="*50)
        print("MOST RELEVANT PAGES")
        print("="*50)
        
        relevant_pages = adaptive.get_relevant_content(top_k=5)
        for i, page in enumerate(relevant_pages, 1):
            print(f"\n{i}. {page['url']}")
            print(f"   Relevance Score: {page['score']:.2%}")
            
            # Show a snippet of the content
            content = page['content'] or ""
            if content:
                snippet = content[:200].replace('\n', ' ')
                if len(content) > 200:
                    snippet += "..."
                print(f"   Preview: {snippet}")
        
        # Show final confidence
        print(f"\n{'='*50}")
        print(f"Final Confidence: {adaptive.confidence:.2%}")
        print(f"Total Pages Crawled: {len(result.crawled_urls)}")
        print(f"Knowledge Base Size: {len(adaptive.state.knowledge_base)} documents")
        
        # Example: Check if we can answer specific questions
        print(f"\n{'='*50}")
        print("INFORMATION SUFFICIENCY CHECK")
        print(f"{'='*50}")
        
        if adaptive.confidence >= 0.8:
            print("✓ High confidence - can answer detailed questions about async Python")
        elif adaptive.confidence >= 0.6:
            print("~ Moderate confidence - can answer basic questions") 
        else:
            print("✗ Low confidence - need more information")


if __name__ == "__main__":
    asyncio.run(main())