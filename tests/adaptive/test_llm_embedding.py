import asyncio
import os
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig, LLMConfig


async def test_configuration(name: str, config: AdaptiveConfig, url: str, query: str):
    """Test a specific configuration"""
    print(f"\n{'='*60}")
    print(f"Configuration: {name}")
    print(f"{'='*60}")
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        adaptive = AdaptiveCrawler(crawler, config)
        result = await adaptive.digest(start_url=url, query=query)
        
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
        
        print(f"\n{'='*50}")
        print(f"Pages crawled: {len(result.crawled_urls)}")
        print(f"Final confidence: {adaptive.confidence:.1%}")
        print(f"Stopped reason: {result.metrics.get('stopped_reason', 'max_pages')}")
        
        if result.metrics.get('is_irrelevant', False):
            print("⚠️  Query detected as irrelevant!")
        
        return result


async def llm_embedding():
    """Demonstrate various embedding configurations"""
    
    print("EMBEDDING STRATEGY CONFIGURATION EXAMPLES")
    print("=" * 60)
    
    # Base URL and query for testing
    test_url = "https://docs.python.org/3/library/asyncio.html"
    
    openai_llm_config = LLMConfig(
        provider='openai/text-embedding-3-small',
        api_token=os.getenv('OPENAI_API_KEY'),
        temperature=0.7,
        max_tokens=2000
    )
    config_openai = AdaptiveConfig(
        strategy="embedding",
        max_pages=10,
        
        # Use OpenAI embeddings
        embedding_llm_config=openai_llm_config,
        # embedding_llm_config={
        #     'provider': 'openai/text-embedding-3-small',
        #     'api_token': os.getenv('OPENAI_API_KEY')
        # },
        
        # OpenAI embeddings are high quality, can be stricter
        embedding_k_exp=4.0,
        n_query_variations=12
    )
    
    await test_configuration(
        "OpenAI Embeddings",
        config_openai,
        test_url,
        # "event-driven architecture patterns"
        "async await context managers coroutines"
    )
    return
    
    

async def basic_adaptive_crawling():
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
        
        
        if adaptive.confidence >= 0.8:
            print("✓ High confidence - can answer detailed questions about async Python")
        elif adaptive.confidence >= 0.6:
            print("~ Moderate confidence - can answer basic questions") 
        else:
            print("✗ Low confidence - need more information")



if __name__ == "__main__":
    asyncio.run(llm_embedding())
    # asyncio.run(basic_adaptive_crawling())