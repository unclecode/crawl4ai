"""
Comparison: Embedding vs Statistical Strategy

This example demonstrates the differences between statistical and embedding
strategies for adaptive crawling, showing when to use each approach.
"""

import asyncio
import time
import os
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig


async def crawl_with_strategy(url: str, query: str, strategy: str, **kwargs):
    """Helper function to crawl with a specific strategy"""
    config = AdaptiveConfig(
        strategy=strategy,
        max_pages=20,
        top_k_links=3,
        min_gain_threshold=0.05,
        **kwargs
    )
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        adaptive = AdaptiveCrawler(crawler, config)
        
        start_time = time.time()
        result = await adaptive.digest(start_url=url, query=query)
        elapsed = time.time() - start_time
        
        return {
            'result': result,
            'crawler': adaptive,
            'elapsed': elapsed,
            'pages': len(result.crawled_urls),
            'confidence': adaptive.confidence
        }


async def main():
    """Compare embedding and statistical strategies"""
    
    # Test scenarios
    test_cases = [
        {
            'name': 'Technical Documentation (Specific Terms)',
            'url': 'https://docs.python.org/3/library/asyncio.html',
            'query': 'asyncio.create_task event_loop.run_until_complete'
        },
        {
            'name': 'Conceptual Query (Semantic Understanding)',
            'url': 'https://docs.python.org/3/library/asyncio.html',
            'query': 'concurrent programming patterns'
        },
        {
            'name': 'Ambiguous Query',
            'url': 'https://realpython.com',
            'query': 'python performance optimization'
        }
    ]
    
    # Configure embedding strategy
    embedding_config = {}
    if os.getenv('OPENAI_API_KEY'):
        embedding_config['embedding_llm_config'] = {
            'provider': 'openai/text-embedding-3-small',
            'api_token': os.getenv('OPENAI_API_KEY')
        }
    
    for test in test_cases:
        print("\n" + "="*70)
        print(f"TEST: {test['name']}")
        print(f"URL: {test['url']}")
        print(f"Query: '{test['query']}'")
        print("="*70)
        
        # Run statistical strategy
        print("\n📊 Statistical Strategy:")
        stat_result = await crawl_with_strategy(
            test['url'], 
            test['query'], 
            'statistical'
        )
        
        print(f"  Pages crawled: {stat_result['pages']}")
        print(f"  Time taken: {stat_result['elapsed']:.2f}s")
        print(f"  Confidence: {stat_result['confidence']:.1%}")
        print(f"  Sufficient: {'Yes' if stat_result['crawler'].is_sufficient else 'No'}")
        
        # Show term coverage
        if hasattr(stat_result['result'], 'term_frequencies'):
            query_terms = test['query'].lower().split()
            covered = sum(1 for term in query_terms 
                         if term in stat_result['result'].term_frequencies)
            print(f"  Term coverage: {covered}/{len(query_terms)} query terms found")
        
        # Run embedding strategy
        print("\n🧠 Embedding Strategy:")
        emb_result = await crawl_with_strategy(
            test['url'], 
            test['query'], 
            'embedding',
            **embedding_config
        )
        
        print(f"  Pages crawled: {emb_result['pages']}")
        print(f"  Time taken: {emb_result['elapsed']:.2f}s")
        print(f"  Confidence: {emb_result['confidence']:.1%}")
        print(f"  Sufficient: {'Yes' if emb_result['crawler'].is_sufficient else 'No'}")
        
        # Show semantic understanding
        if emb_result['result'].expanded_queries:
            print(f"  Query variations: {len(emb_result['result'].expanded_queries)}")
            print(f"  Semantic gaps: {len(emb_result['result'].semantic_gaps)}")
        
        # Compare results
        print("\n📈 Comparison:")
        efficiency_diff = ((stat_result['pages'] - emb_result['pages']) / 
                          stat_result['pages'] * 100) if stat_result['pages'] > 0 else 0
        
        print(f"  Efficiency: ", end="")
        if efficiency_diff > 0:
            print(f"Embedding used {efficiency_diff:.0f}% fewer pages")
        else:
            print(f"Statistical used {-efficiency_diff:.0f}% fewer pages")
        
        print(f"  Speed: ", end="")
        if stat_result['elapsed'] < emb_result['elapsed']:
            print(f"Statistical was {emb_result['elapsed']/stat_result['elapsed']:.1f}x faster")
        else:
            print(f"Embedding was {stat_result['elapsed']/emb_result['elapsed']:.1f}x faster")
        
        print(f"  Confidence difference: {abs(stat_result['confidence'] - emb_result['confidence'])*100:.0f} percentage points")
        
        # Recommendation
        print("\n💡 Recommendation:")
        if 'specific' in test['name'].lower() or all(len(term) > 5 for term in test['query'].split()):
            print("  → Statistical strategy is likely better for this use case (specific terms)")
        elif 'conceptual' in test['name'].lower() or 'semantic' in test['name'].lower():
            print("  → Embedding strategy is likely better for this use case (semantic understanding)")
        else:
            if emb_result['confidence'] > stat_result['confidence'] + 0.1:
                print("  → Embedding strategy achieved significantly better understanding")
            elif stat_result['elapsed'] < emb_result['elapsed'] / 2:
                print("  → Statistical strategy is much faster with similar results")
            else:
                print("  → Both strategies performed similarly; choose based on your priorities")
    
    # Summary recommendations
    print("\n" + "="*70)
    print("STRATEGY SELECTION GUIDE")
    print("="*70)
    print("\n✅ Use STATISTICAL strategy when:")
    print("  - Queries contain specific technical terms")
    print("  - Speed is critical")
    print("  - No API access available")
    print("  - Working with well-structured documentation")
    
    print("\n✅ Use EMBEDDING strategy when:")
    print("  - Queries are conceptual or ambiguous")
    print("  - Semantic understanding is important")
    print("  - Need to detect irrelevant content")
    print("  - Working with diverse content sources")


if __name__ == "__main__":
    asyncio.run(main())