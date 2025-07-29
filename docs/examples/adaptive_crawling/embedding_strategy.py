"""
Embedding Strategy Example for Adaptive Crawling

This example demonstrates how to use the embedding-based strategy
for semantic understanding and intelligent crawling.
"""

import asyncio
import os
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig


async def main():
    """Demonstrate embedding strategy for adaptive crawling"""
    
    # Configure embedding strategy
    config = AdaptiveConfig(
        strategy="embedding",  # Use embedding strategy
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",  # Default model
        n_query_variations=10,  # Generate 10 semantic variations
        max_pages=15,
        top_k_links=3,
        min_gain_threshold=0.05,
        
        # Embedding-specific parameters
        embedding_k_exp=3.0,  # Higher = stricter similarity requirements
        embedding_min_confidence_threshold=0.1,  # Stop if <10% relevant
        embedding_validation_min_score=0.4  # Validation threshold
    )
    
    # Optional: Use OpenAI embeddings instead
    if os.getenv('OPENAI_API_KEY'):
        config.embedding_llm_config = {
            'provider': 'openai/text-embedding-3-small',
            'api_token': os.getenv('OPENAI_API_KEY')
        }
        print("Using OpenAI embeddings")
    else:
        print("Using sentence-transformers (local embeddings)")
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        adaptive = AdaptiveCrawler(crawler, config)
        
        # Test 1: Relevant query with semantic understanding
        print("\n" + "="*50)
        print("TEST 1: Semantic Query Understanding")
        print("="*50)
        
        result = await adaptive.digest(
            start_url="https://docs.python.org/3/library/asyncio.html",
            query="concurrent programming event-driven architecture"
        )
        
        print("\nQuery Expansion:")
        print(f"Original query expanded to {len(result.expanded_queries)} variations")
        for i, q in enumerate(result.expanded_queries[:3], 1):
            print(f"  {i}. {q}")
        print("  ...")
        
        print("\nResults:")
        adaptive.print_stats(detailed=False)
        
        # Test 2: Detecting irrelevant queries
        print("\n" + "="*50)
        print("TEST 2: Irrelevant Query Detection")
        print("="*50)
        
        # Reset crawler for new query
        adaptive = AdaptiveCrawler(crawler, config)
        
        result = await adaptive.digest(
            start_url="https://docs.python.org/3/library/asyncio.html",
            query="how to bake chocolate chip cookies"
        )
        
        if result.metrics.get('is_irrelevant', False):
            print("\n✅ Successfully detected irrelevant query!")
            print(f"Stopped after just {len(result.crawled_urls)} pages")
            print(f"Reason: {result.metrics.get('stopped_reason', 'unknown')}")
        else:
            print("\n❌ Failed to detect irrelevance")
        
        print(f"Final confidence: {adaptive.confidence:.1%}")
        
        # Test 3: Semantic gap analysis
        print("\n" + "="*50)
        print("TEST 3: Semantic Gap Analysis")
        print("="*50)
        
        # Show how embedding strategy identifies gaps
        adaptive = AdaptiveCrawler(crawler, config)
        
        result = await adaptive.digest(
            start_url="https://realpython.com",
            query="python decorators advanced patterns"
        )
        
        print(f"\nSemantic gaps identified: {len(result.semantic_gaps)}")
        print(f"Knowledge base embeddings shape: {result.kb_embeddings.shape if result.kb_embeddings is not None else 'None'}")
        
        # Show coverage metrics specific to embedding strategy
        print("\nEmbedding-specific metrics:")
        print(f"  Average best similarity: {result.metrics.get('avg_best_similarity', 0):.3f}")
        print(f"  Coverage score: {result.metrics.get('coverage_score', 0):.3f}")
        print(f"  Validation confidence: {result.metrics.get('validation_confidence', 0):.2%}")


if __name__ == "__main__":
    asyncio.run(main())